"""Build presentation-v2 cues from newly acquired, preserved CC0 game assets.

Authoring: numpy in bundled Python; OGG decoding in installed system Python's
pico2d/SDL_mixer (dummy device). Runtime needs only the finished PCM WAVs.
No network, playback, game configuration changes, or old G sources are used.
Run from any directory. --decoder-python can replace the default `py -3`.
Prints the exact suggested SOUND_FILES mapping and measured, decoded limits.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import subprocess
import wave
import zipfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "assets/audio"
LICENSES = ROOT / "assets/licenses/presentation-v2"
RATE = 44100
PACKS = {
    "rubberduck": {
        "archive": "source-presentation-v2-rubberduck-rpg.zip",
        "sha256": "1c2f06ff4e8563b5b8b745b23cf213c1474142a69bb82bd8f5e10d9b3f7a7bbd",
        "author": "rubberduck",
        "page": "https://opengameart.org/content/80-cc0-rpg-sfx",
        "download": "https://opengameart.org/sites/default/files/80-CC0-RPG-SFX_0.zip",
    },
    "rpg": {
        "archive": "source-presentation-v2-kenney-rpg.zip",
        "sha256": "6dbeaf8544da958d8f2adcb4a4a4b76c1ade34a05f8ab9edccd327da7375f38b",
        "author": "Kenney Vleugels / Kenney",
        "page": "https://kenney.nl/assets/rpg-audio",
    },
    "impact": {
        "archive": "source-presentation-v2-kenney-impact.zip",
        "sha256": "029d734af1582474edf3a694d1b0cebc97c1c152f2f39fa34d4c2bafc5de77f8",
        "author": "Kenney",
        "page": "https://kenney.nl/assets/impact-sounds",
    },
    "interface": {
        "archive": "source-presentation-v2-kenney-interface.zip",
        "sha256": "f2193d072726d6758a5f7871b2dcc54dcce0d5c35c6f0a62f92549b327c81232",
        "author": "Kenney",
        "page": "https://kenney.nl/assets/interface-sounds",
    },
}
# Fixed archive members, never extractall(): only this new bank's originals.
SOURCES = {
    **{f"blade{i}": ("rubberduck", f"blade_0{i}.ogg") for i in range(1, 4)},
    "slice1": ("rpg", "Audio/knifeSlice.ogg"),
    "slice2": ("rpg", "Audio/knifeSlice2.ogg"),
    "chop": ("rpg", "Audio/chop.ogg"),
    "footstep1": ("rpg", "Audio/footstep00.ogg"),
    "footstep2": ("rpg", "Audio/footstep01.ogg"),
    "cloth1": ("rpg", "Audio/cloth1.ogg"),
    "cloth2": ("rpg", "Audio/cloth2.ogg"),
    "metal1": ("impact", "Audio/impactMetal_medium_000.ogg"),
    "metal2": ("impact", "Audio/impactMetal_medium_003.ogg"),
    "metal3": ("impact", "Audio/impactMetal_light_000.ogg"),
    "select": ("interface", "Audio/select_003.ogg"),
}
SOUND_FILES = {
    **{f"swing{i}": f"presentation-v2-swing-{i}.wav" for i in range(1, 4)},
    **{f"impact{i}": f"presentation-v2-impact-{i}.wav" for i in range(1, 4)},
    **{f"parry{i}": f"presentation-v2-parry-{i}.wav" for i in range(1, 4)},
    "echo": "presentation-v2-impact-1.wav",
    "counter": "presentation-v2-impact-3.wav",
    "hurt": "impact-2-soft.wav",
    "reward": "presentation-v2-select.wav",
    "footstep1": "presentation-v2-footstep-1.wav",
    "footstep2": "presentation-v2-footstep-2.wav",
    "jump": "presentation-v2-jump.wav",
    "land": "presentation-v2-land.wav",
}

DECODER = r'''
import base64, contextlib, ctypes, json, os, sys
os.environ['SDL_AUDIODRIVER'] = 'dummy'
with contextlib.redirect_stdout(sys.stderr):
    from pico2d import pico2d as p
if p.SDL_Init(p.SDL_INIT_AUDIO):
    raise RuntimeError('SDL audio initialization failed')
if p.Mix_OpenAudio(44100, p.AUDIO_S16LSB, 2, 1024):
    p.SDL_Quit()
    raise RuntimeError('SDL_mixer decoder unavailable')
try:
    rate, fmt, channels = ctypes.c_int(), ctypes.c_ushort(), ctypes.c_int()
    if not p.Mix_QuerySpec(ctypes.byref(rate), ctypes.byref(fmt), ctypes.byref(channels)):
        raise RuntimeError('Cannot query mixer format')
    if (rate.value, fmt.value, channels.value) != (44100, p.AUDIO_S16LSB, 2):
        raise RuntimeError('Unexpected decoder format')
    result = {}
    for key, path in json.load(sys.stdin).items():
        chunk = p.Mix_LoadWAV(path.encode('utf8'))
        if not chunk:
            raise RuntimeError('Cannot decode ' + path)
        try:
            raw = ctypes.string_at(chunk.contents.abuf, chunk.contents.alen)
            result[key] = base64.b64encode(raw).decode('ascii')
        finally:
            p.Mix_FreeChunk(chunk)
    print(json.dumps(result))
finally:
    p.Mix_CloseAudio()
    p.SDL_Quit()
'''


def digest(data):
    return hashlib.sha256(data).hexdigest()


def extract_sources():
    rows, paths, archives = [], {}, {}
    for pack, info in PACKS.items():
        archive = BASE / info["archive"]
        actual = digest(archive.read_bytes())
        if actual != info["sha256"]:
            raise ValueError(f"Archive changed: {archive.name}")
        with zipfile.ZipFile(archive) as z:
            # CRC validation also inspects the complete downloaded pack contents.
            if z.testzip() is not None:
                raise ValueError(f"Corrupt archive: {archive.name}")
            archives[pack] = {**info, "license": "CC0-1.0", "members": z.namelist()}
            if pack != "rubberduck":
                license_path = LICENSES / f"kenney-{pack}-License.txt"
                license_data = z.read("License.txt")
                if license_path.exists():
                    if license_path.read_bytes() != license_data:
                        raise ValueError(f"Preserved license changed: {license_path.name}")
                else:
                    license_path.write_bytes(license_data)
            for key, (source_pack, member) in SOURCES.items():
                if source_pack != pack:
                    continue
                prefix = "rubberduck" if pack == "rubberduck" else f"kenney-{pack}"
                name = f"source-presentation-v2-{prefix}-{Path(member).name}"
                data = z.read(member)
                destination = BASE / name
                if destination.exists() and destination.read_bytes() != data:
                    raise ValueError(f"Refusing to replace changed original: {name}")
                if not destination.exists():
                    destination.write_bytes(data)
                paths[key] = str(destination)
                rows.append({"key": key, "file": name, "pack": pack,
                             "member": member, "sha256": digest(data)})
    return paths, rows, archives


def decode_sources(paths, command):
    process = subprocess.run([*command, "-B", "-c", DECODER],
                             input=json.dumps(paths), capture_output=True,
                             text=True, check=True, timeout=60)
    decoded = json.loads(process.stdout)
    arrays = {}
    for key, encoded in decoded.items():
        pcm = np.frombuffer(base64.b64decode(encoded), dtype="<i2")
        samples = pcm.astype(np.float64).reshape(-1, 2).mean(axis=1) / 32768.0
        if not len(samples) or not np.isfinite(samples).all() or np.max(abs(samples)) == 0:
            raise ValueError(f"Empty/invalid decoded source: {key}")
        arrays[key] = samples
    return arrays


def rms(x):
    return float(np.sqrt(np.mean(x * x)))


def piece(source, duration, speed=1.0, delay=0.0, offset=0.0):
    """Remove only leading silence; preserve original transient and pitch family."""
    active = np.flatnonzero(abs(source) > np.max(abs(source)) * 0.025)
    source = source[max(0, int(active[0]) - round(0.002 * RATE)):]
    source = source[round(offset * RATE):]
    positions = (np.arange(round(duration * RATE)) - round(delay * RATE)) * speed
    result = np.interp(positions, np.arange(len(source)), source, left=0.0, right=0.0)
    # Equal-RMS layers with a peak limit before mixing; no transient compression.
    return result * min(0.1 / max(rms(result), 1e-12), 0.8 / max(abs(result)))


def finish(x, hold, decay, target, ceiling, shelf=0.25):
    """Shorten resonance rather than removing the blade's entire upper midrange."""
    x = x - x.mean()
    # Broad, smooth shelf keeps 0.1-4 kHz blade detail, reduces 7 kHz+ hiss.
    # Zero padding and output fades avoid circular FFT edit boundaries.
    nfft = 1 << (2 * len(x) - 1).bit_length()
    frequencies = np.fft.rfftfreq(nfft, 1 / RATE)
    ramp = np.clip((frequencies - 4000) / 3000, 0, 1)
    ramp = ramp * ramp * (3 - 2 * ramp)
    transfer = (1 - (1 - shelf) * ramp) * (1 - np.exp(-(frequencies / 70) ** 2))
    result = np.fft.irfft(np.fft.rfft(x, nfft) * transfer, nfft)[:len(x)]
    t = np.arange(len(x)) / RATE
    envelope = np.exp(-np.maximum(0.0, t - hold) / decay)
    # Half-millisecond start and 12 ms end fades prevent edit-boundary clicks.
    envelope *= np.minimum(1.0, t / 0.0005)
    envelope *= np.minimum(1.0, np.maximum(0, (len(x) - 1 - np.arange(len(x))) / (0.012 * RATE)))
    result *= envelope
    # Envelope-weighted DC correction leaves both faded endpoints at zero.
    result -= envelope * (result.sum() / envelope.sum())
    result *= min(target / max(rms(result), 1e-12), ceiling / max(abs(result)))
    return result


def write_cue(name, samples, layers):
    peak = float(np.max(abs(samples)))
    if not (np.isfinite(samples).all() and 0 < peak <= 0.48 and 0 < len(samples) / RATE < 1.2):
        raise ValueError(f"Invalid output: {name}")
    pcm = np.rint(samples * 32767).astype("<i2")
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(pcm.tobytes())
    destination = BASE / name
    data = buffer.getvalue()
    if not destination.exists() or destination.read_bytes() != data:
        destination.write_bytes(data)
    # Measurements refer to the final quantized/reopened WAV, not the float buffer.
    with wave.open(str(BASE / name), "rb") as w:
        assert (w.getnchannels(), w.getsampwidth(), w.getframerate()) == (1, 2, RATE)
        output = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(float) / 32768
    spectrum = abs(np.fft.rfft(output)) ** 2
    frequencies = np.fft.rfftfreq(len(output), 1 / RATE)
    late = output[round(0.15 * RATE):]
    return {"file": name, "seconds": len(output) / RATE,
            "peak": float(np.max(abs(output))), "rms": rms(output),
            "dc": float(output.mean()), "endpoints": [float(output[0]), float(output[-1])],
            "energy_above_6khz": float(spectrum[frequencies > 6000].sum() / spectrum.sum()),
            "energy_after_150ms": float(np.sum(late * late) / np.sum(output * output)),
            "sha256": digest((BASE / name).read_bytes()), "layers": layers}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decoder-python", nargs="+", default=["py", "-3"])
    args = parser.parse_args()
    LICENSES.mkdir(parents=True, exist_ok=True)
    paths, sources, archives = extract_sources()
    audio = decode_sources(paths, args.decoder_python)
    rows = []
    for i, duration in enumerate((0.20, 0.22, 0.26), 1):
        cue = finish(piece(audio[f"blade{i}"], duration), hold=0.055,
                     decay=0.060, target=0.055, ceiling=0.34)
        rows.append(write_cue(SOUND_FILES[f"swing{i}"], cue, [{"source": f"blade{i}", "gain": 1.0}]))
    for i, (duration, speed) in enumerate(((0.24, 1.04), (0.27, 1.0), (0.32, 0.91)), 1):
        source = "slice1" if i == 1 else "slice2"
        # A knife-cut texture plus a contact chop, never a body punch or empty wind.
        # knifeSlice2 contains an initial isolated click before its dense cut.
        # Select that cut, not the click; offsets are after silence trimming.
        offset = 0.085 if source == "slice1" else 0.180
        cut = piece(audio[source], duration, speed=speed, delay=0.004, offset=offset)
        contact = piece(audio["chop"], duration, speed=speed)
        cue = finish(0.72 * cut + 0.48 * contact, hold=0.070,
                     decay=0.065 + (i - 1) * 0.008,
                     target=0.065 + (i - 1) * 0.004, ceiling=0.44)
        rows.append(write_cue(SOUND_FILES[f"impact{i}"], cue,
                             [{"source": source, "gain": 0.72, "speed": speed, "delay": 0.004, "offset_after_trim": offset},
                              {"source": "chop", "gain": 0.48, "speed": speed}]))
    for i, duration in enumerate((0.18, 0.19, 0.21), 1):
        metal = piece(audio[f"metal{i}"], duration)
        cut = piece(audio["chop"], duration, speed=1.1)
        cue = finish(0.84 * metal + 0.16 * cut, hold=0.018,
                     decay=0.038, target=0.060, ceiling=0.38, shelf=0.20)
        rows.append(write_cue(SOUND_FILES[f"parry{i}"], cue,
                             [{"source": f"metal{i}", "gain": 0.84},
                              {"source": "chop", "gain": 0.16, "speed": 1.1}]))
    cue = finish(piece(audio["select"], 0.22), hold=0.080,
                 decay=0.055, target=0.045, ceiling=0.23)
    rows.append(write_cue(SOUND_FILES["reward"], cue, [{"source": "select", "gain": 1.0}]))
    # Quiet movement textures on the separate runtime foley channel. All layers
    # are excerpts of preserved recordings; no synthesized tones or oscillators.
    for i, duration in enumerate((0.10, 0.11), 1):
        source = f"footstep{i}"
        cue = finish(piece(audio[source], duration), hold=0.018,
                     decay=0.030, target=0.030, ceiling=0.24, shelf=0.16)
        rows.append(write_cue(SOUND_FILES[source], cue, [{"source": source, "gain": 1.0}]))
    cue = finish(piece(audio["cloth1"], 0.12), hold=0.030,
                 decay=0.035, target=0.028, ceiling=0.24, shelf=0.16)
    rows.append(write_cue(SOUND_FILES["jump"], cue, [{"source": "cloth1", "gain": 1.0}]))
    duration = 0.14
    contact = piece(audio["footstep2"], duration, speed=0.92)
    cloth = piece(audio["cloth2"], duration, delay=0.008)
    cue = finish(0.85 * contact + 0.25 * cloth, hold=0.025,
                 decay=0.040, target=0.038, ceiling=0.28, shelf=0.16)
    rows.append(write_cue(SOUND_FILES["land"], cue,
                         [{"source": "footstep2", "gain": 0.85, "speed": 0.92},
                          {"source": "cloth2", "gain": 0.25, "delay": 0.008}]))
    for row in rows[-4:]:
        ceiling = 0.28 if row["file"] == SOUND_FILES["land"] else 0.24
        if not (0.08 <= row["seconds"] <= 0.16 and row["peak"] <= ceiling
                and 0.025 <= row["rms"] <= 0.040):
            raise ValueError(f"Movement cue outside quiet limits: {row}")
    manifest = {"version": 2, "license": "CC0-1.0",
                "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
                "format": {"rate": RATE, "channels": 1, "bits": 16},
                "decoder": "system Python pico2d SDL_mixer, dummy audio device",
                "listened": False, "game_configuration_modified": False,
                "packs": archives, "sources": sources, "outputs": rows,
                "recommended_SOUND_FILES": SOUND_FILES}
    (LICENSES / "build-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf8")
    print(json.dumps({"outputs": rows, "recommended_SOUND_FILES": SOUND_FILES}, indent=2))


if __name__ == "__main__":
    main()

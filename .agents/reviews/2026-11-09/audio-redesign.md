# Bounded audio replacement — 2026-11-09

## D24 integration completed after this handoff

The initial scoped report below describes the ten-cue authoring handoff. The main work subsequently connected those cues in `bladegame/config.py`, added four quiet movement cues from the same licensed Kenney pack, and connected six-channel runtime playback. The current authoring manifest's `game_configuration_modified: false` describes the authoring script's own side effects; the live game mapping has been changed separately. Actual runtime evidence is `verification/polish/runs/20261109-140758/report.json`. Source and cue hashes match. Human/device listening and user preference remain unverified.

Completed: ten new WAV cues and a reproducible authoring script using genuinely
different CC0 game-audio sources. Integration is deliberately left to the main
presentation work: this task did not edit `render.py`, `config.py`, `main.py`,
existing docs/credits, or the executable ZIP. No human listening occurred.

## Scope and direction

Read repository `AGENTS.md`, the local `blade-game-polish` skill,
`QUALITY_REVIEW.md` (latest D23 and failed audio directions), related D15–D18
decisions, `assets/CREDITS.md`, both existing audio authoring scripts, and
`render.py`'s event/channel roles plus the existing `SOUND_FILES` definition.
The current explicit request restricts writes to the new audio script, new audio
files/sources, new audio licenses, and this review. Consequently no broad polish
run, DEVLOG edit, runtime edit, or package rebuild was performed here.

The earlier failures were excessive brightness/ringing, soft punch replacing
the blade, realistic metal scraping, and empty wind replacing actual contact.
The new bank uses three authored blade cues for swings, knife-cut texture plus
a chop contact for hits, short metal collisions for parries, and a dedicated UI
cue. No qubodup/StarNinjas/colorsCrimsonTears/artisticdude/Independent.nu source
from the old G bank was reused. The existing hurt cue can remain separately.

## Primary sources, license, and reputation evidence

| Source | Confirmed evidence / selected content |
| --- | --- |
| [rubberduck — 80 CC0 RPG SFX](https://opengameart.org/content/80-cc0-rpg-sfx) | Author says the pack was created for fantasy/RPG games; three distinct `blade_01/02/03.ogg` files exist in the actual ZIP. Downloaded primary-page HTML states CC0 and shows 85 favorites / 9,935 downloads at retrieval. The ZIP contains 80 OGG files and no embedded license text; the author page is retained as the license designation. |
| [Kenney — RPG Audio](https://kenney.nl/assets/rpg-audio) | Official page CC0; actual archive contains the selected `knifeSlice`, `knifeSlice2`, and `chop` OGGs and its own License.txt. |
| [Kenney — Impact Sounds](https://kenney.nl/assets/impact-sounds) | Official page CC0; actual archive has the three selected short metal impact variants and its own License.txt. Bell/plate/punch sources were inspected in the inventory but are not used. |
| [Kenney — Interface Sounds](https://kenney.nl/assets/interface-sounds) | Official page CC0; selected `select_003.ogg` exists in the archive with License.txt. |

Kenney's [author-published all-in-one listing](https://kenney.itch.io/kenney-game-assets)
showed 5.0/5 across 603 ratings when browsed. That is a publisher/bundle reputation
signal, not a rating of these individual sounds. The downloaded
[publisher support page](https://kenney.nl/support) also explicitly confirms CC0
and commercial game use. Download/favorite/rating counts are evidence of use and
reception, not proof of professional employment, listening quality, or this
user's acceptance. These edited cues remain an unlistened design candidate.

All four used packs are CC0-1.0, permitting modification and redistribution.
Full legal text, original Kenney notices, author-page snapshots, and voluntary
credits are in `assets/licenses/presentation-v2/`. `build-manifest.json` preserves
the exact archive inventories and SHA-256 hashes of all archives, selected
originals and finished cues. Four complete ZIPs and ten selected original OGGs
remain in `assets/audio/`; unused extracted audition candidates were removed,
while their complete original packs remain intact in the ZIPs.

### Concrete access problems and resolution

- Initial ordinary network command failed DNS with `socket.gaierror [Errno
  11001]`. Authorized network execution allowed public downloads.
- Old Kenney `/media/...zip` URLs returned HTML rather than ZIP data. The live
  author page now obtains a public signed link through `/download-link/`.
  Following that official download-button flow produced valid ZIPs, all CRC
  checked. The temporary HTML response was replaced by the verified RPG ZIP.
- [Helton Yan — FREE Pixel Combat SFX](https://heltonyan.itch.io/pixelcombat)
  explicitly describes retro-stylized combat design, CC BY 4.0, and showed
  4.9/5 with 160 ratings in the primary web page. Direct author-page retrieval
  for download returned HTTP 429 Too Many Requests. No Helton audio was
  downloaded or claimed as inspected/listened. This bank instead uses the new
  successfully retrieved rubberduck/Kenney sources above, rather than old G EQ.
- Direct Creative Commons legal-code retrieval returned HTTP 403. The official
  SPDX license repository supplied the full CC0 text; the source designation
  still comes from the actual authors' pages/pack notices.

## Authoring choices supported by decoded evidence

The script runs with bundled Python/numpy and invokes installed `py -3` only
for pico2d/SDL_mixer decoding, with `SDL_AUDIODRIVER=dummy`. Default execution
does no network access and performs no physical audio playback. It verifies
the pinned ZIP hashes and CRCs before extracting the ten exact members.

Swings use one distinct rubberduck blade source each. Hits use at most two
layers: Kenney knife cut and chop contact, with 1.04/1.00/0.91 speed choices.
Rolling decoded RMS revealed an isolated initial click in `knifeSlice2`
followed by a later dense cut. The hit builder selects that dense region:
offsets after leading-silence trim are 85 ms (`knifeSlice`) / 180 ms
(`knifeSlice2`), then a 4 ms cut-layer delay. This is a waveform-based edit,
not an assertion about what was heard.

A smooth shelf begins at 4 kHz and reaches 25% gain above 7 kHz (20% for
parries), retaining the blade midrange instead of applying the old 2 kHz
blanket filter. Parries retain three dry collision variants plus 16% chop,
with an 18 ms hold and 38 ms decay. Edits include 0.5 ms/12 ms boundary fades
and envelope-weighted DC correction. No generated oscillators or added bare
noise were used. RMS targets are subordinate to the peak ceilings; no hard
clipping or transient compression was added.

## Exact integration recommendation

```python
SOUND_FILES = {
    **{f'swing{i}': f'presentation-v2-swing-{i}.wav' for i in range(1, 4)},
    **{f'impact{i}': f'presentation-v2-impact-{i}.wav' for i in range(1, 4)},
    **{f'parry{i}': f'presentation-v2-parry-{i}.wav' for i in range(1, 4)},
    'echo': 'presentation-v2-impact-1.wav',
    'counter': 'presentation-v2-impact-3.wav',
    'hurt': 'impact-2-soft.wav',
    'reward': 'presentation-v2-select.wav',
}
```

This preserves all thirteen existing keys. In the inspected renderer, `reward`
serves both reward-screen entry and `reward_selected`; the bank itself does
not add menu navigation events. The main UI work can reuse the select WAV for
new selection feedback if it adds those events. Swing channel 0 is halted by
parry; echo remains separate on channel 4 and counter remains channel 1.
Keep existing duplicate-event suppression and channel separation during wiring.

## Final-file measurements and verification

All ten finished cues were reopened as WAV and separately decoded through the
actual installed pico2d SDL_mixer. Both decoders agree exactly on duration and
peak. Format: **44,100 Hz / mono / signed 16-bit PCM**.

| File suffix (`presentation-v2-`) | Seconds | Measured peak | RMS |
| --- | ---: | ---: | ---: |
| swing-1.wav | .200 | .339996 | .023192 |
| swing-2.wav | .220 | .339996 | .040877 |
| swing-3.wav | .260 | .339996 | .020117 |
| impact-1.wav | .240 | .439972 | .059179 |
| impact-2.wav | .270 | .439972 | .062943 |
| impact-3.wav | .320 | .439972 | .065626 |
| parry-1.wav | .180 | .379974 | .046578 |
| parry-2.wav | .190 | .379974 | .045339 |
| parry-3.wav | .210 | .379974 | .044919 |
| select.wav | .220 | .229980 | .035321 |

- Required peak <= .48 and duration < 1.2 seconds: all passed. All endpoints
  are exactly zero and absolute quantized DC is below .00001.
- For parries, energy after 150 ms is at most .000032% of total energy. This
  measures tail shortening, not whether the remaining timbre is pleasant.
- Two successive builds produce identical SHA-256 hashes for all ten WAVs.
- All ten files load with pico2d's SDL_mixer. Five simultaneous channels were
  scheduled successfully with a dummy device and zero channel volume, then
  halted; this was not physical playback or listening.
- Conservative phase-independent sum of all five channel peak ceilings is
  `.65*.34 + .85*.44 + 1*.38 + .45*.23 + .25*.44 = 1.1885` before master gain.
  With the inspected renderer's default .15 gain this bounds the sum at
  **.178275**; at its maximum .50 gain, **.59425**. This assumes the inspected
  five-channel routing and no additional audio buses. It is an upper bound,
  not an actual human-listened mix or loudness measurement. Integer mixer
  gain rounding only reduces that bound.

Rebuild from any working directory with:

```powershell
& 'C:/Users/USER/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B 'C:/Users/USER/.codex/.chatgpt-projects/g-p-6a97caa7ea248191b2878f60cd43e3b0/2DGP_Project-upload/tools/prepare_presentation_audio.py'
```

Changed/added files in this task: the new authoring script, ten new
`presentation-v2-*.wav` cues, four `source-presentation-v2-*.zip` archives,
ten selected `source-presentation-v2-*.ogg` originals, the new
`assets/licenses/presentation-v2/` evidence/notice/manifest files, and this
review. No external uploads, credentials, new dependencies, or game-code edits.

Remaining: main-work integration of the mapping, relaunch of any existing game
window, then actual device listening during repeated swings, contacts,
parries and UI selection at normal play volume. Separation, fatigue, subjective
blade character and user acceptance remain unverified. No full-game success,
commercial quality, or human listening is claimed from the decoded checks.

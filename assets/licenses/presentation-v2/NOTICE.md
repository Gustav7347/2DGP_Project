# Presentation-v2 audio attribution and redistribution evidence

All fourteen `assets/audio/presentation-v2-*.wav` cues use preserved CC0-1.0
sources. These are adaptations of authored game audio, not commercial-game rips
or generative-model audio. No existing G-bank source is included in these cues.

| Creator | Pack / primary author page | Original files actually used |
| --- | --- | --- |
| rubberduck | [80 CC0 RPG SFX](https://opengameart.org/content/80-cc0-rpg-sfx) | `blade_01.ogg`, `blade_02.ogg`, `blade_03.ogg` |
| Kenney Vleugels / Kenney | [RPG Audio](https://kenney.nl/assets/rpg-audio) | `Audio/knifeSlice.ogg`, `Audio/knifeSlice2.ogg`, `Audio/chop.ogg`, `Audio/footstep00.ogg`, `Audio/footstep01.ogg`, `Audio/cloth1.ogg`, `Audio/cloth2.ogg` |
| Kenney | [Impact Sounds](https://kenney.nl/assets/impact-sounds) | `Audio/impactMetal_medium_000.ogg`, `Audio/impactMetal_medium_003.ogg`, `Audio/impactMetal_light_000.ogg` |
| Kenney | [Interface Sounds](https://kenney.nl/assets/interface-sounds) | `Audio/select_003.ogg` |

License: [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
The author's license designation is preserved in `rubberduck-source.html`;
that ZIP does not contain an additional license file. The three Kenney
`*-License.txt` files are unmodified copies from their downloaded ZIPs.
`kenney-support.html` preserves the publisher's commercial-use/CC0 explanation.
Attribution is voluntary under these source designations; it is retained here.
No additional restriction is asserted on these CC0 source sounds or cue edits.

`CC0-1.0.txt` is the full CC0 legal text from the
[official SPDX license-list-data repository](https://raw.githubusercontent.com/spdx/license-list-data/main/text/CC0-1.0.txt).
Creative Commons' own legal-code URLs were readable through web browsing but
returned HTTP 403 for file retrieval. The SPDX copy was downloaded successfully.
The canonical license remains the Creative Commons URL above.

The four complete original ZIPs and fourteen byte-identical extracted OGG originals
are retained under `assets/audio/source-presentation-v2-*`. These are OGG
sources as distributed by the authors, not lossless recording masters. Derived
WAVs are 44.1 kHz mono 16-bit PCM. Conversion does not restore lossy information.

Edits: stereo downmix, silence trimming, short cue excerpts, small speed changes
on hit layers, at most two source layers, broad high-frequency shelf, DC
correction, short resonance decay and click-prevention fades, conservative level
normalization. Detailed per-output source keys, offsets, levels, speed changes,
source member hashes, complete ZIP inventories and ZIP hashes are in
`build-manifest.json`. Authoring parameters are in
`tools/prepare_presentation_audio.py`.

The four movement cues reuse the already retained Kenney RPG ZIP, without new
downloads: `presentation-v2-footstep-1.wav` uses `footstep00.ogg`,
`presentation-v2-footstep-2.wav` uses `footstep01.ogg`,
`presentation-v2-jump.wav` uses `cloth1.ogg`, and `presentation-v2-land.wav`
layers `footstep01.ogg` (0.92 speed) with `cloth2.ogg` (8 ms delay).
Their durations are 100, 110, 120 and 140 ms respectively. Final decoded RMS
must remain 0.025-0.040; peak ceilings are 0.24 for steps/jump and 0.28 for
landing. These are recording excerpts, without oscillators. The original ten
cue WAVs remain byte-identical after this rebuild. Verification is numerical;
no human listening or runtime channel validation is claimed.

`source-retrieval.json` records successful primary-page retrievals and the
unsuccessful direct Creative Commons text request. The source HTML snapshots
are evidence files, not game UI or code to execute.

The retained preexisting `hurt` recommendation uses `impact-2-soft.wav`; its
earlier sources remain documented in `assets/CREDITS.md`. This notice does not
relicense that unrelated file or replace its credits.

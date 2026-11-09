# Spec reference for scripts/podcast.py

One JSON file per output video. Times are seconds in the raw clip. Clip names are file names without extension
inside `--src` (`camA` -> `raw/camA.mp4`/`.mov`/...), and must match the transcript name in `--tx`.

## Top level
| key | default | meaning |
|---|---|---|
| `id`, `slug` | required / `edit` | output name `<id>_<slug>.mp4` |
| `title`, `topic` | | shown in the client tracker (`scripts/report.py`) |
| `master` | none | multicam: camera whose audio + transcript are used for every segment (best mic) |
| `sync` | `{}` | multicam: `{"camB": 2.507}` delay of each camera vs master, from `scripts/sync.py`. Segment times = master times |
| `format` | `short` | `short` 1080x1920 · `long` 1920x1080 |
| `layout` | `full` | default layout for segments (short only): `full`, `letterbox`, `band`, `split` |
| `captions` | `lockup` (short) / `none` (long) | `minimal`, `lockup`, `creator`, `none` |
| `keywords` | `[]` | words or phrases (`"pain point"`) promoted to the big lockup word. Match is on spoken words, case-insensitive |
| `fixes` | `{}` | caption text corrections `{"hyrox": "HYROX", "fine friends": "find friends"}` |
| `accent` | `#FFFFFF` | colour of the lockup keyword and last headline line |
| `cap_y`, `cap_x` | per layout | caption centre height (0-1) / left margin for `creator` |
| `look` | none | default grade: `bw`, `dim`, `warm`, `teal` |
| `auto_frame` | none | one wide two-person camera: `{"zoom": 1.9, "punch": 1.12, "wide_every": 4}` cut at speaker changes and frame the talker (needs `scripts/speakers.py` labels) |
| `captions_until` | none | output-timeline seconds after which captions stop (long-form: end of the intro) |
| `tighten` | none | jump-cut every pause longer than this (s). 0.35 clips, 0.6 long-form |
| `drop_fillers` | `true` | with `tighten`: also cut um/uh |
| `jump_zoom` | none | e.g. `[1.0, 1.12]` alternate framing on each tightened piece |
| `denoise` | `true` | FFT denoise on voice (turn off for clean studio audio) |
| `music` | none | `{"file": "assets/music/bed.mp3", "db": -24}` looped, ducked under voice, faded out |
| `no_sfx` | `false` | mute all automatic SFX |
| `sfx` | `[]` | manual hits `{"at": 3.2, "file": "whoosh_fast.mp3", "vol": 0.4}` (files in `assets/sfx/`) |

## Segment
| key | meaning |
|---|---|
| `clip`, `start`, `end` | source and range (cut on word boundaries from the `.txt`/`.json`) |
| `zoom` | punch-in factor (1.0-1.35 on 1080p sources, up to 1.6 on 4K) |
| `cx`, `cy` | crop centre 0-1, or `"auto"` (largest face), `"left"`/`"right"` (face in a two-shot). Default auto when cropping |
| `layout` | override: `full` / `letterbox` / `band` / `split` |
| `open` | letterbox only: band opens from a thin strip (use on the first segment) |
| `clip2`, `start2`, `cx2` | split only: top panel source (default same clip, other face) |
| `look` | per-segment grade (`bw` for "before..." beats) |
| `text` | clean caption text for this segment (re-timed onto the speech); `""` = no captions |
| `nocaps` | true = no captions on this segment |
| `broll` | `{"file": "projects/ep01/broll/runner.mp4", "at": 2.0, "push": 0.03, "cx": 0.5}` picture from the B-roll file (video from `at` s, or a photo), speaker's audio and captions continue. `push` = slow push-in (default 0.03 video / 0.06 photo, 0 = static). In `letterbox` it fills the band. Split a sentence into two segments to drop B-roll in mid-line |
| `tighten` | per-segment override (0 = keep pauses) |
| `chapter` | long-form: chapter title starting here |
| `card` | `{"card": true, "dur": 1.5, "logo": "path.png", "bg": ["0x08161b", "0x1f5f6e"]}` a sting / title card |

## Overlays (output timeline seconds)
| key | example |
|---|---|
| `hook` | `{"text": ["The best advice", "he ever gave"], "until": 3, "y": 0.17}` headline (top black area in letterbox) |
| `names` | `[{"at": 0.3, "dur": 2.6, "name": "Asha Rao", "role": "Founder - @asha", "y": 0.44, "x": 0.09}]` |
| `counters` | `[{"at": 3.2, "dur": 2.2, "from": 0, "to": 10000, "suffix": "", "label": "followers", "y": 0.3}]` |
| `stamps` | `[{"at": 7.3, "text": "SCRIPT", "color": "#FFD84D", "dur": 1.2, "y": 0.3}]` |
| `stacks` | `[{"at": 10.5, "items": ["Topic","Hook","Format","CTA"], "every": 0.4, "color": "#2FB4D6", "y": 0.18}]` |
| `endcard` | `{"text": ["COMMENT \"LINK\"", "to get the full episode"], "dur": 1.8, "logo": "...png"}` appended at the end |

Output-timeline times = sum of segment durations before the moment. Easiest: render `--draft` once, read
`work/<id>/captions.txt` + the sheet, then place overlays.

## Outputs
`<out>/<id>_<slug>.mp4`, optional `_sheet.jpg` (`--sheet`), `_chapters.txt` (when chapters are set),
`<work>/<id>/caps.ass` (all caption events, editable) and `captions.txt`.

## Added 2026-11-06 (long-form with B-roll and motion, Carrie ep01 v2)
| key | meaning |
|---|---|
| `captions: "pod"` | long-form podcast captions: bold white chunk (up to 6 words) at the bottom, the spoken word in the accent colour. `cap_size` (default 58 px at 1080p), `cap_y` (0.935 = just above the bottom edge) |
| `stickers` | `[{"at": 12.4, "file": "projects/<ep>/stickers/banana-1-banana.mov", "x": 0.8, "y": 0.3}]` floating 3D element (alpha .mov from `scripts/stickers.py`), centre position, output timeline; drawn under the captions |
| `stickers[].w` | element width as a fraction of the frame; with `"x": "auto"` the whole element is kept off the faces (split screens count one face per half) |
| `tags` | `[{"at": 3.4, "num": "04", "text": "Salt + cramps"}]` chapter tag pill, top-left, until `until` (default: end) |
| segment `layout: "sbs"` | 16:9 side-by-side split from ONE wide camera: left person / right person, faces from the face track; `zoom`, `zoom_r`, `cy` |
| segment `broll.panel: "left"/"right"` (16:9) | side card: card (806x1080 from `scripts/cards.py`, `"w": 806, "h": 1080`) on that side, the talker cropped on the other (`cx` "left"/"right", `zoom`, `cy`) |
| env `PODCAST_HWDEC=cuda` | GPU-decode the 4K HEVC sources (big speed-up; NVENC encode not needed) |
| env `PODCAST_FINAL_PRESET` | x264 preset of the final pass (default `medium`; `fast` for long-forms on a deadline) |
Tools: `scripts/broll_sheet.py` (keyless photo search -> numbered contact sheets -> `--get picks.json` with credits),
`scripts/stickers.py` (Fluent 3D emoji, MIT: pop-in, slow float, label pill, pop-out). `scripts/fx.py` renders emoji, floating photo cards and kinetic keywords from one fx.json (re-renders only changed elements).

## v4 (2026-11-07, Carrie ep01 v4 "FUEL LAB" long-form) — engine keys
Design rules live in `projects/carrie-ep01/v4/style_guide.md`; status + examples in `projects/carrie-ep01/v4/ENGINE_STATUS.md`.

### Captions `"captions": "v4"` (long-form, whole episode)
| key | default | meaning |
|---|---|---|
| `cap_size` | 66 | design px (em) of the guest's base word; connective 52, keyword 88, serif keyword 100, host 62 scale with it |
| `cap_y` / `cap_y_frame` / `cap_y_broll` | 1004/1080 · 1010/1080 · = cap_y | bottom of the caption line per layout (segment `cap_y` overrides) |
| `cap_x` (segment) | per layout | centre x; wide two-shots default under the speaker (600 / 1320 px) |
| `cap_key` | `mix` | keyword look: `mix` (numbers + data words HIGHLIGHT heavy, contrast words Instrument Serif Italic), `serif`, `none` |
| `cap_color` | `#FFD84D` | keyword colour for the guest (host keyword = ACCENT `#FF5A1F`) |
| `cap_host` / `host_box` | `"L"` / true | speaker label whose chunks sit on an INK 90 % box |
| `keywords`, `fixes`, `drop_fillers` | | as before; v4 also strips um/uh, em/en dashes and trailing , . ; : |
Chunks: one line, 2-5 words, <= 30 chars, break at punctuation / pause > 0.35 s; words build in place (blur-to-sharp,
3 f; keyword 6 f), stay lit to the chunk end; one keyword per chunk (spec keyword > number+unit > contrast word > longest
content word). Every word is its own ASS event at a measured position (`font_metrics()`: libass \fs = winAscent+winDescent).

### Layouts (segment `layout`, 16:9 only)
| key | meaning |
|---|---|
| `"layout": "frame"` | background plate + two 840x780 panels (x 80 / 1000, y 80, radius 24): the talker in one, `panel` media in the other |
| `"layout": "frame2"` | both people, Nizam (L) left panel, Carrie (R) right panel |
| `bg` | `paper` / `grid` (= `bg_paper.png` / `bg_grid.png` in `gfx_dir`, spec dir `gfx/`, or `projects/carrie-ep01/v4/gfx/`; flat PAPER / TRACK-green grid fallback), `blur` (the wide, blurred + darkened), or a png path. Spec-level `bg` = default |
| `who` | `"L"` / `"R"` talker (default: who talks most in the segment) |
| `side` | `"left"` / `"right"`: where the talker panel goes (default Nizam left, Carrie right) |
| `panel` | `{"file": ".jpg/.png/.mp4/.mov", "at": 0, "push": 0.06 photo / 0.03 video, "cx": 0.5, "cy": 0.5, "label": "EGGS + GUAC", "index": "07 — FIG.", "style": "hi"/"ink"}` cover-cropped to 840x780 with a slow push; label = caps pill bottom-left (INK on HIGHLIGHT, `ink` = PAPER on INK), index = Space Mono chip top-left |
| `enter` | panels slide 60 px + fade in over 8 f (2nd panel +3 f). Automatically off when the previous segment has the same layout + side + panel file, and on tightened pieces after the first; `false` forces off |
| `shadow` | drop shadow under the panels (default: on `paper` only) |
| `pzoom`, `pcx`, `pcy` | manual talker-panel framing (default: zoom 1.62, whole person with ~8 % headroom, guarded) |

### Full-person framing guard (all long-form talking crops: auto_frame, explicit cx/zoom, panels, camera moves)
Head positions come from a per-keyframe detector (`detect_heads`: dark hair left, blonde hair/skin right, cached in
`<work>/_cache/<clip>_heads.json`) plus the face track. Body model `PEOPLE` (head-and-shoulders box, reach incl. hands,
knees for low crops) relative to the head. A crop must hold the subject's head (>= 7 % headroom, 7.5 % in panels) and
shoulders (panels: hands too); the other person is either fully outside (reach box + 0.02) or fully inside; `AVOID`
boxes (the desk monitor) are kept out when that is still possible. The guard changes zoom/cx/cy minimally (zoom up to
`zmax` 2.3, panels 2.0), else falls back to the wide two-shot. Changes are printed and written to `<work>/<id>/guard.log`.
`"guard": false` (spec or segment) opts out; `"people"` / `"avoid"` override the body model for another show.

### Full-screen B-roll additions
`broll.label`, `broll.index`, `broll.style`: label pill + index chip top-left (96, 88). Video B-roll (`.mp4`) honours
`at`, `push`, and continues (time + push) across the jump cuts of a tightened segment. Captions continue over B-roll.

### Overlays (`stickers`)
`dur` (cut the overlay early, applied as input `-t`), `fade` (alpha fade in, and out when `dur` is set), `w` (v4 specs:
drawn width as a fraction of 1920, rescaled only if the file is > 4 px off; v3 specs keep `w` as a placement hint).
Overlays composite over every layout (final pass), are converted with the bt709 matrix, and only cost CPU inside their
own time window. Full-frame alpha: keep them short (stingers) or bake long full-frame graphics as opaque B-roll mp4s.

### Virtual camera (talking-head full-frame segments)
| key | meaning |
|---|---|
| `cam: {"move": "push", "from": 1.0, "to": 1.08, "at": 0, "dur": seg}` | slow eased push (or `"pull"`, default to 0.93) relative to the guarded framing, zooming about the subject's head top |
| `punch: [{"at": 2.3, "to": 1.15, "dur": 0.25, "hold": 1.0}]` | quick ease-out punch-in at segment-relative seconds; holds to the end, or eases back after `hold` |
| `cam: {"move": "pan", "to_cx": "right", "at": 0, "dur": 0.6, "to_zoom": z}` | eased pan/track to the other person's guarded framing |
| `drift` | handheld drift amplitude (frame fraction, e.g. 0.004), off by default |
The zoom range is clamped so the tightest crop keeps the shoulders and the widest keeps the other person out (logged).
Rendered as zoompan on a 2x supersampled union crop of the 4K source (integer steps = 1/2 output px: no visible stepping).

### Other v4 behaviour
Every cut part is normalised to bt709 / tv range (full-range JPEG B-roll used to stall the concat and shift colours).

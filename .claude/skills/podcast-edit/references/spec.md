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

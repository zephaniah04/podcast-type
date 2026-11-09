# Carrie ep01 — v4 long-form: shared brief for every specialist agent

Read this whole file first. You are one specialist on a small team; the orchestrator (main Claude session)
assembles your output into one finished YouTube episode. Stay inside your own deliverable and files.

## The job (Nizam's words, condensed)
One long-form YouTube podcast episode, 16:9 1920x1080 30 fps, **60-70 minutes**, from two consecutive raw files.
"Edited like Premiere/After Effects": strong hook (cold open), clean outro, chapter cards between chapters,
**big good-looking captions the whole time someone speaks**, **lots of B-roll** that matches the exact words
("if she says apple, an apple appears"), **split screens that explain** (talker on one side, the thing being
talked about on the other), creative motion graphics, good fonts. No CTA, no music (Nizam adds music himself;
we deliver voice -14 LUFS + light SFX). Hard rule: **when zooming or splitting, keep the person fully in frame —
never slice a head, face or body at a frame or panel edge.**
Export: `I:\edited\` (final only).

## People
| Side in the wide shot | Who | Lower third |
|---|---|---|
| LEFT, male, navy top, grey sofa | **Nizam** — host; training to become an endurance athlete (HYROX, Ironman) | Nizam / Training to become an endurance athlete |
| RIGHT, female, beige outfit, at a desk, often facing her monitor | **Carrie Mullin Innes** — High-Performance Sports Dietitian · IOC Diploma in Sports Nutrition · Elite & collegiate athlete nutrition · Sports medicine & performance | Carrie Mullin Innes / High-Performance Sports Dietitian · IOC Dip. Sports Nutrition |
Angle: a new endurance athlete learning from an elite sports dietitian. Language: English.

## Source footage + data (all paths relative to repo root `I:\podcast-type` unless absolute)
- Raw: `I:\claude to edit\IMG_4342-001.MOV` (file **A**, 2351 s) then `IMG_4343-002.MOV` (file **B**, 3151 s).
  ONE locked-off wide iPhone camera, 4K 3840x2160 HEVC 60 fps, mono AAC. B continues right after A.
- Transcripts (faster-whisper, word timings): `projects/carrie-ep01/tx/IMG_4342-001.json|.txt`, `IMG_4343-002.json|.txt`.
  JSON = list of segments `{"s","e","text","w":[[start,end,word,prob,speaker], ...]}`; speaker "L" = Nizam, "R" = Carrie.
  `tx/<clip>_speakers.txt` = readable lines with NIZAM:/CARRIE: labels (read THIS to follow the conversation).
- Face track: `tx/<clip>_faces.json` = `[[t, nizam_face_x, carrie_face_x], ...]` every 3 s (x 0-1 of frame, null = not
  detected). Nizam x 0.25-0.43 (median 0.32); Carrie x 0.76-0.86 (median 0.81), often turned to her monitor.
  In the 4K wide: Nizam's body spans roughly x 0.03-0.58 (knees reach ~0.58 when he leans forward), head top y ~0.08-0.15;
  Carrie spans x ~0.55-0.95, head top y ~0.10. Her monitor shows client data: never zoom into the screen.
- Existing helpers (Python, import with `sys.path.insert(0, "projects/carrie-ep01")`):
  `build_long2.py`: `WS[f]` = list of `(start, end, bare_word, speaker)` per file "A"/"B"; `find(f, "MM:SS", "exact phrase")`
  returns `(word_index, n)` searching ±25 s (raises SystemExit if the phrase is not there); `span()`; `talker()`.
  `build_shorts.py`: `FILES = {"A": "IMG_4342-001", "B": "IMG_4343-002"}`, `sec("MM:SS.s")`, `snap()`, `ACCENT = "#FFB238"`.
  `build_long.py`: `CH` = the v1-v3 17-chapter map, `END`, cold-open `BEATS`. `build_long3.py`: v3 device list (`NEW`).
- Python: `/c/Users/raika/AppData/Local/Programs/Python/Python313/python.exe` (`python` on PATH is a stub). Use it.
- ffmpeg 9 on PATH (libx264 CPU encode; NVENC broken; `PODCAST_HWDEC=cuda` GPU decode works). 12 CPU threads.

## The engine + assets already in the repo
- `scripts/podcast.py` (spec format: `.claude/skills/podcast-edit/references/spec.md`, read it) renders one JSON spec ->
  mp4 (ffmpeg filtergraph per segment + libass captions + alpha .mov overlays + SFX + -14 LUFS).
- `scripts/cards.py` animated data cards; `scripts/fx.py` (3D emoji, floating photo cards, kinetic word bars -> alpha .mov
  from `projects/carrie-ep01/fx.json`); `scripts/stickers.py`; `scripts/find_broll.py` + `scripts/fetch_broll.py`
  (keyless Openverse/Wikimedia photo search + download with credits); `scripts/broll_sheet.py`.
- B-roll photos: `projects/carrie-ep01/broll/*.jpg` (90, credits in `broll/credits.json`). Cards: `projects/carrie-ep01/cards/`.
  FX clips: `projects/carrie-ep01/fx/*.mov` (e_ = 3D emoji, p_ = floating photo card, w_ = kinetic word).
- Fonts: `assets/fonts/` InterTight-Heavy, InterTight-Medium, InstrumentSerif-Italic, ArchivoBlack-Regular, Jost-Regular
  (more OFL Google fonts may be added to `assets/fonts/` with their licence txt). SFX: `assets/sfx/`.
- v3 (previous attempt, 81 min) looked like: small white bottom captions, 3D emoji stickers, floating photo pips,
  tight single shots that often sliced the other person at the frame edge, chapter cards on dark gradient. v4 must
  clearly beat it: bigger captions, real split-screen explainers, more and better B-roll, cleaner framing, shorter.

## Style references (vertical reels; learn the grammar, adapt to 16:9; never reuse their footage/logos)
`references/studies/ig4|ig5|ig6/src.mp4` (+ `sheet.jpg` contact sheets). Older study: `.claude/skills/podcast-edit/references/reference-study.md`.
Orchestrator's first read: captions are word-by-word builds in clean white grotesk with size contrast (small connective
words, one big keyword, often italic serif), sitting on the chest area, no boxes; lower third = white box name card or
pill; full-screen illustrative B-roll every few seconds with a kinetic word over it; typographic cards on solid or
green-grid backgrounds with stacked/tilted photo collages and heavy caps; the talker sometimes shown inside a rounded
frame on a flat colour background; big numbers with blur-in; black screens with bold white+red type for punchlines.

## Disk + safety rules (important)
- `I:` has only ~9 GB free. Put renders, work dirs and test outputs on C: under `C:\Users\raika\AppData\Local\Temp\v4\`.
  Small assets (photos, json, scripts, small mp4/mov graphics) may go in the repo. Don't create files > 50 MB in the repo.
- Never delete or overwrite Nizam's existing files (raws, exports, broll, cards, fx, previous build scripts).
  Write new files only, under the paths given in your task. Don't commit or push.
- Downloads: only free-licence media (CC0 / Public Domain / CC BY / CC BY-SA, or Pexels / Pixabay / Mixkit / Coverr
  free licences), no watermarks, no brand logos as hero, no recognisable public figures. Log every credit.

## Team (who owns what)
| Specialist | Owns | Deliverable |
|---|---|---|
| Story editor | the cut | `projects/carrie-ep01/v4/edit_plan.json` + `edit_plan.md` |
| B-roll supervisor | visuals matched to words | `projects/carrie-ep01/v4/broll_map.json` + new media in `broll/`, `broll_video/` |
| Motion designer | look + graphics | `projects/carrie-ep01/v4/style_guide.md` + `scripts/gfx4.py` + `v4/gfx/` test renders |
| Engine engineer | `scripts/podcast.py` features | new caption style, framed split-screen layouts, framing guard; documented in spec.md |
| Orchestrator | everything else | `build_long4.py`, renders, QA, export |

## Art direction (orchestrator, binding for every visual specialist)
Nizam (2026-11-07): "a LOT of motion graphics, visual graphics, cards, elements, B-roll, chapters... visually
attractive, not lame... professional aesthetic... brutalism, kinetic motion... like the big informational YouTube
channels... the best video you have ever made." The previous version was "only captions, nothing else". So:
**something designed is on screen almost all the time** — talking shots are dressed with captions + a tag or an
element; every concrete noun, number, list, comparison or instruction gets a visual.

Look name: **"FUEL LAB" — editorial brutalism + kinetic type** (think informational YouTube: bold grid, big type,
data made physical, stacked photo cut-outs, snappy motion; clean, not cluttered).
- Palette: INK `#0D0D0D`, PAPER `#EFEBE3` (warm off-white), ACCENT `#FF5A1F` (electrolyte orange),
  HIGHLIGHT `#FFD84D` (numbers, caption keyword on video), TRACK GREEN `#1F6B45` + grid line `#2E8A5C` (grid
  backgrounds), plus white. Max 2 accent colours in one frame.
- Type: ArchivoBlack (display, ALL CAPS, tight -2% tracking) · InterTight Heavy/Medium (UI, captions, numbers) ·
  InstrumentSerif Italic (the elegant contrast word: "*the* problem", "*why*") · one mono for labels/indices/timecodes
  (add Space Mono or JetBrains Mono, OFL, to assets/fonts with licence). Big type, hard edges, 2-4 px rules, index
  numbers ("04 / 13"), registration marks/crosshairs, thin grid lines, subtle film grain. No glossy gradients, no bevels.
- Motion: fast in, calm hold, fast out. Entrances 6-10 frames (expo/back-out), staggered 2-3 frames per element;
  masked wipes, slide+scale, counters that roll up with motion blur, lines that draw on, photo cards that drop in with
  a tilt and a shadow, marquee tickers, typewriter labels. Every entrance has an SFX hit (whoosh / pop / click / ding
  from `assets/sfx/`, quiet). Nothing idles: slow push (2-4 %) on holds.
- Grid: 1920x1080, 96 px outer margins, 12 columns. Keep captions zone (bottom 230 px) free on every overlay, and
  never cover a face.
- Talking-shot framing: full person in frame (head + shoulders + hands at minimum, with headroom); either show the other
  person completely or not at all — never a sliced face/shoulder at an edge.
- Split-screen explainer (the signature device): background PAPER or TRACK-GREEN grid, talker inside a rounded
  (24 px) panel on one side, the B-roll / graphic in a second rounded panel on the other side with a mono index label
  and a short caption pill; panels slide in; caption continues underneath.

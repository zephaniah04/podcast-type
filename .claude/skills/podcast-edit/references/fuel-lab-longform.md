# FUEL LAB long-form system (Carrie ep01 v4, approved look + Nizam's review rules)

The 16:9 long-form recipe that Nizam signed off on ("the designs, animations are pretty cool"), plus the rules from
his review of the first export (2026-11-09). Reuse it for every informational podcast episode. Project files:
`projects/carrie-ep01/v4/` (BRIEF.md, style_guide.md, ENGINE_STATUS.md, PROGRESS.md) and `build_long4.py`,
`render_long4.sh`, `assemble_long4.py` next to it.

## 1. Look: "FUEL LAB" = editorial brutalism + kinetic type
- Palette: INK `#0D0D0D`, PAPER `#EFEBE3`, ACCENT `#FF5A1F`, HIGHLIGHT `#FFD84D`, TRACK GREEN `#1F6B45` (+ grid
  `#2E8A5C`), white. Max 2 accent colours per frame; on green the accent word is HIGHLIGHT.
- Type: Archivo Black (display caps, -2 %), Inter Tight Heavy/Medium (UI, captions, numbers), Instrument Serif Italic
  (the elegant contrast word on cards only), Space Mono (labels, indices "FIG.012", timecodes). All in `assets/fonts/`.
- Plates: `bg_paper.png` (warm paper, grain, 60 px grid, registration marks, mono header) and `bg_grid.png` (green grid).
- Grid: 1920x1080, 96 px margins, 12 columns; bottom 230 px kept for captions on every overlay; never cover a face.

## 2. Episode structure
cold open (10 beats, ~55 s, captions on) -> title sting (4.5 s) -> [chapter card (3 s) -> chapter body] x N ->
wrap-up talk -> outro card (6 s, no CTA). Chapter body starts with a chapter tag (top-left, 4 s) and, in chapter 1,
lower thirds when each person first speaks **and is on screen**. 60-70 min from ~90 min raw: a story editor agent
writes `edit_plan.json` (chapters[].keep ranges, cold_open beats, hero_lines, key_facts) before anything is built.

## 3. Visual devices (one every ~12-15 s on top of camera cuts)
| device | when | how |
|---|---|---|
| split-screen panel (`layout: frame`) | a concrete noun / food / object / place is said | talker in a rounded 840x780 panel on paper/grid plate, photo or video in the other panel with mono `FIG.###` index + caption pill |
| full-screen B-roll | strong visual nouns, actions | real photo/video with a 3-7 % push (real footage only), label + index |
| infographic (`info/`) | numbers, timelines, comparisons, myth vs fact, step lists | HyperFrames GSAP renders, full screen or in a panel |
| hero card (`hero_*.mp4`) | a quotable line, a key number | punch / number / quote / myth styles, no captions over it |
| wide two-shot | quick back-and-forths | zoom 1.0, captions under the speaker |
B-roll map: phrase-anchored beats (`build_long2.find`), every photo picked by eye, free licences only, credits logged,
no recognisable people / brand logos (keep a blocklist: `AVOID` in build_long4.py, also refused by `scripts/gfx4.py`).

## 4. Captions (Nizam's rules — these override style_guide.md section 3)
- **One font (Inter Tight Heavy), one size, one baseline** for every word and both speakers. Never make connective
  words smaller, never switch a word to another font, never move a word up or down.
- **No box behind anyone's captions** (host or guest). Thin soft outline + small shadow only (bord ~1.6, shad ~1.2,
  half-transparent INK). No glow, no heavy stroke.
- **No blur**: words appear with a 2-frame fade, nothing else.
- Keyword = **colour only** (HIGHLIGHT on video, ACCENT on paper), and **rare**: numbers or explicit keywords, at most
  one every 12 s (~one per 4-5 sentences). On the paper plate and on light full-screen graphics (auto-detected,
  `cap_ink`) the caption is INK, not white.
- One line, 2-5 words / <= 30 chars, break on punctuation or > 0.35 s pause; capital "I"; no um/uh; no dashes.
- Engine: `captions_v4()` in `scripts/podcast.py`; knobs `cap_size`, `cap_key` (`mix`/`none`), `cap_key_gap`.

## 5. Motion rules
- Graphics are **still** while they hold: no camera push, zoom, 3D drift, parallax, float or shake on any graphic
  (chapter cards, hero cards, infographics, title, outro). Elements animate IN (slide / mask-rise / draw-on / counter
  roll / photo drop) and OUT (fade), then sit still. Exits fade — no scale-up push-through, no blur.
- No punch-in zooms or virtual camera moves on talking shots (`auto_frame.punch` 1.0, no `cam`/`punch`/`drift`).
  Static single framings and cuts between single / wide / split are fine.
- Real-life photo/video B-roll may keep a gentle push (Nizam liked it).
- Every graphic entrance gets one quiet SFX hit (whoosh/click/pop, ~-12 dB under voice); no music (Nizam adds it).

## 6. Framing (hard rule)
Keep every person fully in frame in singles, splits and panels: whole head with headroom, shoulders and back, hands.
Either show the other person completely or not at all. The engine's guard (`PEOPLE` body boxes in podcast.py) does
this for the current room; widen a box if a render still slices someone. Check raw footage for camera-angle changes
(Carrie ep01: the first 45 s of file A were shot from another angle -> shown wide, `OLD_ANGLE_END`).

## 7. Pipeline + team
1. Specialist agents with one shared BRIEF.md: story editor (cut), B-roll supervisor (`broll_map.json`), motion
   designer (`scripts/gfx4.py`, templates `v4/gfx_src/`), infographic animator (`v4/info_src/build.py`), engine engineer
   (`scripts/podcast.py`). Fixed hand-off schemas; orchestrator assembles + QAs.
2. `build_long4.py` -> one spec per chapter (`long4/L4_NN.json`); `render_long4.sh` renders 4 chunks in parallel
   (~40 min each for a 5 min chapter on this PC); `assemble_long4.py` re-encodes cards to the piece format and
   concat-copies to `I:\edited\` + `_chapters.txt`; `v4/tools/credits_list.py` writes the credits.
3. Keep renders on a drive with >= 30 GB free (each chapter piece is 150-300 MB plus work files); a full drive kills
   chunks silently — check `render_long4.log` for FAIL lines and re-run (finished pieces are skipped).
4. QA: frame sheets every few seconds of every chapter (framing, captions, empty shots), loudness -14 LUFS.

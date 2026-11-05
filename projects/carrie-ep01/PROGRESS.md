# Carrie ep01: progress log (resume from here)

Nizam (2026-11-05 05:40): "allow everything, don't ask, render all the videos". Check-ins 1 and 2 are SKIPPED;
work straight through: 25 shorts (C01-C25) + L01 + L02 + L03 + tracker.

## Facts
- Raw: `I:\claude to edit\IMG_4342-001.MOV` (2351 s) + `IMG_4343-002.MOV` (3151 s). ONE camera, consecutive
  (4342 ends 23:02:18, 4343 starts 23:02:20). 4K HEVC 60 fps, mono AAC. Clip names = `IMG_4342-001`, `IMG_4343-002`.
- Python: `/c/Users/raika/AppData/Local/Programs/Python/Python313/python.exe` (`python` on PATH is a stub).
- NVENC does NOT work (driver too old): encode with libx264 on CPU.
- Room: office consult. Nizam LEFT on grey sofa, Carrie RIGHT at a desk, often facing her monitor (profile/back).
  Food tray on desk. Monitor shows a document: never punch into the screen (client data).
- Disk: I: ~41 GB free at start.

## Steps
- [x] transcribe (done 06:36: tx/IMG_4342-001.json|.txt, IMG_4343-002.json|.txt)
- [x] speakers: done by VOICE PITCH (`scripts/pitch_speakers.py --split 148 --win 1.5`), mouth motion was wrong (Carrie faces monitor)
- [x] 1080p edit copies: SKIPPED on purpose. Long-forms cut from the 4K with `PODCAST_HWDEC=cuda` (GPU decode works,
  only NVENC encode fails). L02/L03 = their own cold open + title card + a slice of the rendered L01 body.
- [x] plan: `build_shorts.py` (25 shorts) + `build_long.py` (17 chapters, split at B 04:08 after creatine) + moments.md
- [x] shorts C01-C25 -> exports/carrie/ep01 (final 09:55, clean phrase-anchored edges, -14 LUFS)
- [x] tracker (refresh again after the long-forms: python scripts/report.py projects/carrie-ep01 --exports exports/carrie/ep01)
- [x] L01, L02, L03 -> exports/carrie/ep01 (+ _chapters.txt), P1 redone 11:20
- [ ] commit + push specs / moments / tracker

## Done so far (06:05)
- Engine: `PODCAST_HWDEC=cuda` env = GPU decode; `broll.panel: "top"` = card top half + talker bottom half
  (set segment `cx` "left"/"right" and `zoom` ~2.0); face track per file cached in `tx/<clip>_faces.json`
  (left/right resolve from it, with lead room); auto_frame `cy` (default 0.36 = head in upper third).
  Shorts framing: full = zoom ~1.45, cy 0.36; panel bottom = zoom 2.0, cy 0.33.
- `scripts/cards.py`: animated cards (bignum, list, dodont, timeline, bars, title, versus) -> mp4 B-roll. Tested.
- Face track: Nizam x 0.25-0.43 (median 0.32), Carrie x 0.76-0.86 (median 0.81); Carrie often not detected (faces monitor).
- YouTube refs studied, notes added to `reference-study.md`. Downloads in `references/studies/yt1|yt2/src.mp4` (git-ignored).
- NEXT: QA finished shorts (sheets), write moments.md + tracker, QA long pieces, commit.
- TODO after ALL-SHORTS-DONE: re-run build_shorts.py + cards.py (C17/C23 cards moved to the spoken words, panel cy 0.26),
  delete exports C01, C02, C17, C23 (+ _sheet) and re-run render_shorts.sh (it skips the rest). Then report.py.
- 08:08: phrase-anchored edges added (EDGES in build_shorts.py). ALL 25 shorts must be re-rendered: when the redo job
  is done -> `python scripts/cards.py projects/carrie-ep01/cards.json --out projects/carrie-ep01/cards`, delete
  exports/carrie/ep01/C*.mp4 + C*_sheet.jpg, run render_shorts.sh again (log render_shorts2.log).
- 08:15: shorts re-render running (render_shorts2.log, all 25, old renders in exports/carrie/ep01/_old -> delete when
  new ones are checked). Cold-open beats phrase-anchored (build_long.py BEATS). Long job (render_long.log) rendering pieces.
- 09:02: start/end caps added to anchors; 20 shorts re-rendering one at a time (render_shorts3.log); 5 untouched
  (C11 C13 C16 C17 C24). Older renders in exports/carrie/ep01/_old, _old2 (delete at the end). Long: P1 done 08:57.
- 09:35: P1 QA -> caption on chapter-1 title card + name/caption overlap. Fixed in build_long.py. AFTER the long job
  prints ALL-LONG-DONE: delete exports/carrie/ep01/long_pieces/L_P1_body* and re-run render_long.sh (re-renders P1,
  re-assembles L01-L03).
- 10:30: L01/L02/L03 assembled (80.5 / 38.4 / 42.7 min). P1 re-render running (render_long2.log) -> re-assembles.
  Then: report.py, commit ONLY carrie files (NOT projects/calvin-ep01, scripts/coach_reel.py, studies_*.log: not ours),
  push to claude/keen-bardeen-3q8pez.

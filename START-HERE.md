# START HERE: brief for the local editing session

You are Claude, editing on Nizam's Windows PC. Everything below was agreed with Nizam in the cloud setup session.
Read this file fully, then `CLAUDE.md`, `.claude/skills/podcast-edit/SKILL.md` (+ every file in its `references/`),
and `brand-kit/carrie-podcast/BRAND.md`. Don't ask Nizam to re-explain anything that is written here.

## 1. The job: one podcast episode -> 28 videos + a tracker

**Raw footage:** `I:\claude to edit\` - `IMG_4342.MOV` (~14 GB) and `IMG_4343.MOV` (~19 GB), iPhone.
Consecutive file numbers: most likely ONE camera split into part 1 + part 2 (check `ffprobe` creation_time and
durations; if they overlap in time they are 2 cameras -> `scripts/sync.py`). Both speakers wear mics.
Nizam may attach more paths (B-roll, photos); use them first.

**People (wide two-shot):**
| Side | Who | Lower third |
|---|---|---|
| LEFT, male, blue top | **Nizam** - host; training to become an endurance athlete (the athlete/client learning) | Nizam / *Training to become an endurance athlete* |
| RIGHT, female | **Carrie Mullin Innes** - High-Performance Sports Dietitian, IOC Diploma in Sports Nutrition, elite & collegiate athlete nutrition, sports medicine & performance | Carrie Mullin Innes / *High-Performance Sports Dietitian · IOC Dip. Sports Nutrition* |

Language: **English only.** No CTA, no logo, no end card for now. **No music** (Nizam adds music himself in his app):
deliver voice + SFX, voice at -14 LUFS.

**Deliverables**
| ID | What | Rules |
|---|---|---|
| **L01** | The whole podcast as ONE long-form (16:9, 1920x1080) | cut every pause, silence, dead gap, false start, filler; cold open (best Q->A beats, ends on a cliffhanger); B-roll matched to the topic; cards/overlays with good motion; chapters. **Captions only through the cold open + intro, then off.** |
| **L02, L03** | L01 cut into 2 halves (Part 1 / Part 2) | split at the topic boundary nearest the middle so each stands alone as its own YouTube video; each gets its own short cold open + "Part 1/2" title; chapters restart; same caption rule |
| **C01-C25** | 25 shorts for Instagram Reels + YouTube Shorts (1080x1920) | mix of ~40 s, ~50 s and ~60 s (never over 60 s); captions on all; each = one topic, strong hook in the first 1.5 s, B-roll + cards + punch-ins + split/band layouts driven by what is said; no two shorts on the same point; spread across the whole episode |
| **Tracker** | `projects/carrie-ep01/deliverables.md` + `.csv` (`python scripts/report.py projects/carrie-ep01 --exports exports/carrie/ep01`) | every video: ID, title, topic, type, length, source timecodes, B-roll count, status. Nizam sends it to the client: refresh after every batch, give every spec a `"title"` and `"topic"` |

**Quality bar - Nizam's words:** "make it in meaning and intent with good visuals", "creative", "take the attention of
the audience using good assets, motions, elements and effects", "B-roll coming in with the topic, cards appearing with
good motion, overlay and upfront motions, showing what to do". Every zoom, split screen, card and B-roll must have a
reason in the words: follow `.claude/skills/podcast-edit/references/edit-decisions.md` (beat -> device table,
zoom rules, split rules, topic -> look). Angle: a new endurance athlete learning from an elite sports dietitian -
each clip should make a beginner athlete think "this is exactly what I needed".

**B-roll - Claude sources it (no API keys exist):**
1. Motion-graphic cards Claude builds (engine overlays or HyperFrames): macros, g/kg counters, race-day fuelling
   timelines, hydration/electrolyte visuals, do/don't splits, checklists, big numbers.
2. Anything Nizam attaches.
3. Keyless photos: `python scripts/find_broll.py "<nouns>" --kind photo --orient portrait` then `scripts/fetch_broll.py`
   (credits logged in `broll/credits.json`; CC BY/BY-SA credits go in the video description).
4. AI stills/clips with HyperFrames `media-use` (ask Nizam to run `npx hyperframes auth login` once - free).
Keyless stock video is thin; if a topic needs real footage you can't find, add it to a short shot list for Nizam.

## 2. Order of work (with check-ins)
1. `powershell -ExecutionPolicy Bypass -File scripts\setup.ps1` (first run only). Use `python`, not `python3`.
   Send Nizam any error. Check free disk space (raws are 33 GB; renders + 1080p edit copies need ~30-60 GB more).
2. `ffprobe` both files (resolution, fps, HEVC?, duration, audio channels, creation_time). For long-forms make
   1080p H.264 edit copies (SKILL.md section 1); cut shorts from the original 4K.
3. Transcribe: `python scripts\transcribe.py "I:\claude to edit\IMG_4342.MOV" "I:\claude to edit\IMG_4343.MOV" --out projects\carrie-ep01\tx --model medium --prompt "Carrie Mullin Innes, Nizam, IOC, glycogen, electrolytes, carbohydrate, protein, creatine, VO2 max, hydration, RED-S, periodization"`
4. Speakers: `python scripts\speakers.py "<file>" --tx projects\carrie-ep01\tx --left Nizam --right Carrie` for each file.
5. Read EVERY transcript line. Write `projects/carrie-ep01/moments.md`: topic map with timecodes, the L02/L03 split
   point, 30+ short candidates (hook line, timecodes, target length 40/50/60, look A/B/C, B-roll/card ideas).
   **CHECK-IN 1:** show Nizam the topic map + the 25-short plan (as a table). Wait for OK.
6. Render 3-5 shorts as `--draft --sheet`, Read the sheets + full-size frames (QA in SKILL.md section 6).
   **CHECK-IN 2:** send Nizam those drafts for style approval. Wait for OK, then apply notes to the skill.
7. Render all 25 shorts (finals) -> `exports\carrie\ep01\`. Update the tracker.
8. L01 (in 20-30 min parts, then concat), then L02 + L03. Update the tracker. **CHECK-IN 3:** deliver.
9. Commit + push specs, `moments.md`, tracker, skill learnings (never raw footage or renders: git-ignored).

## 3. References (style study already in the repo)
Measured analysis: `.claude/skills/podcast-edit/references/reference-study.md` + `edit-decisions.md`.
- Instagram reels (podcast clip styles): https://www.instagram.com/reel/DeacquZB7oM/ (look C, clean minimal) ·
  https://www.instagram.com/reel/DULMz8cj9yn/ (look B, creator hyper-edit; yt-dlp needs `/p/DULMz8cj9yn/`) ·
  https://www.instagram.com/reel/DTvMK1vkbTw/ (look A, letterbox lockup)
- YouTube long-form: https://youtu.be/BV7QRw8wtjs (Raj Shamani, Figuring Out FO578) · https://youtu.be/67AUqNeRf6U
  **The cloud session could not download YouTube; this PC can.** Before the long-forms, study both with
  `/watch` or `.claude/skills/reverse-engineer/scripts/study.py` (cold open, a story chapter, an advice chapter:
  B-roll timing, zoom moves, cards, lower thirds, split screens, caption use), save to `references/studies/<slug>/`,
  and add the rules to `reference-study.md` / `edit-decisions.md`.
Learn their grammar only; never use their footage, music, logos or show names.

## 4. Also
- Nizam's client may push their own trained skills to this repo: `git pull` before starting, read any new
  `.claude/skills/*` and merge useful rules into podcast-edit.
- Keep replies to Nizam short and direct; show tables for plans and progress.

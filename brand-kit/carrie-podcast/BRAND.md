# Podcast with dietitian: Carrie Mullin Innes x Nizam (brand + brief, 2026-11-04)

## People (on screen, wide shot)
| Side | Who | Lower third |
|---|---|---|
| LEFT, blue top, male | **Nizam**: host; training to become an endurance athlete (the athlete / client learning) | `Nizam` / *Training to become an endurance athlete* |
| RIGHT, female | **Carrie Mullin Innes**: guest; High-Performance Sports Dietitian, IOC Diploma in Sports Nutrition, elite & collegiate athlete nutrition, sports medicine & performance | `Carrie Mullin Innes` / *High-Performance Sports Dietitian · IOC Dip. Sports Nutrition* |
Angle of the show: a new endurance athlete learning from an elite sports dietitian. Every clip should make a
beginner athlete feel "this is exactly what I needed to know".

## Raw
`I:\claude to edit\IMG_4342.MOV` (14 GB), `IMG_4343.MOV` (19 GB): consecutive iPhone files, so most likely ONE camera,
part 1 + part 2 (verify with ffprobe creation_time / durations; if they overlap in time they are 2 cameras -> scripts/sync.py).
Both speakers have mics. Speaker per word: `scripts/speakers.py` (mic channels if separate, else mouth motion).

## Decisions
- Language: English only. Fix sports/nutrition terms in Whisper with --prompt
  "Carrie Mullin Innes, IOC, glycogen, electrolytes, carbohydrate, protein, creatine, VO2 max, hydration, RED-S, periodization".
- No CTA, no logo for now (end on the strongest line / open loop; no end card).
- Music: Nizam adds it himself. Deliver voice + SFX only.
- B-roll: Claude sources it (keyless stock via scripts/find_broll.py, motion-graphic cards, AI-generated stills if signed in).
- Captions: ALL shorts captioned. Long-forms: captions through the cold open + intro, then off (`captions_until`).

## Deliverables
| # | What | Notes |
|---|---|---|
| L01 | Full podcast, tightened | all pauses / silences / dead gaps / false starts removed; cold open; B-roll; cards; chapters |
| L02, L03 | L01 split in two halves | split at the topic boundary nearest the middle; each gets its own short cold open + "Part 1/2" title; chapters restart |
| C01-C25 | 25 shorts (Reels + YouTube Shorts) | lengths ~40 s / ~50 s / ~60 s (max 60 s), 1080x1920, captions, B-roll + cards, creative hooks |
| tracker | `projects/carrie-ep01/deliverables.md` + `.csv` | topic, type, length, source timecodes, status. Update after each batch for the client |

## Look
Default short look: **B (creator hyper-edit)** for nutrition tips / numbers / protocols, **A (letterbox lockup)**
for mindset lines, **C** for long careful answers. Accent: use one warm sport colour (e.g. #FFB238) until a brand exists.
Nutrition B-roll ideas: plates/food prep, carb sources, gels/bottles on a run, labels, scales, training footage,
plus motion cards: macro bars, timeline of a race-day fuelling plan, "grams per kg" counters, do/don't split.

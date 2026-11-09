---
name: podcast-edit
description: Edit raw podcast footage into finished videos - vertical clips (Reels / Shorts / TikTok) in three measured house looks (letterbox lockup, creator hyper-edit, clean minimal) and full 16:9 YouTube episodes with a cold open, jump-cut tightening and chapters. Claude picks the moments from Whisper transcripts, cuts on word boundaries, writes the JSON spec and renders with scripts/podcast.py. Use when Nizam drops raw podcast clips, asks for podcast reels/shorts, a long-form episode edit, a cold open, captions on podcast footage, or says "/podcast-edit".
---

# /podcast-edit — raw podcast footage -> finished clips and episodes

Built from a measured study of 5 references (3 Instagram podcast reels + 2 long-form YouTube episodes),
see `references/reference-study.md`. Learn their grammar; never reuse their footage, music, logos or show names.

**Engine:** `scripts/podcast.py` (ffmpeg + libass, deterministic, no browser). **Transcripts:** `scripts/transcribe.py`
(faster-whisper word timings). **Spec format:** `references/spec.md`. **Long-form structure:** `references/longform.md`.
**Which device when (zoom, split, B&W, stamps... decided by what is said):** `references/edit-decisions.md` — read it before writing any spec.
**Starter specs:** `examples/`.

Heavier motion graphics (text behind the head, 3D phone mockups, glossy buttons with real depth, animated charts)
go through **HyperFrames** (`/hyperframes`, `hyperframes-registry`, `media-use` for cutouts) layered on top of an
engine render — only when the beat earns it.

## Episode package (Nizam's standard order)

From ONE recorded episode (usually 2 cameras + their audio) deliver:
| # | Deliverable | Length | Spec folder |
|---|---|---|---|
| 1 | **Full long-form**: whole conversation, all pauses/silences/dead gaps/false starts cut, cold open, B-roll, cards, chapters | whatever it tightens to | `long/L01_full.json` |
| 2-3 | **Two topic long-forms**: the conversation split into its 2 biggest themes (each self-contained: own cold open, intro line, chapters) | 15-40 min each | `long/L02_<topic>.json`, `long/L03_<topic>.json` |
| 4-28 | **25 shorts** for Reels + YouTube Shorts, mixed lengths **~40 s, ~50 s, ~60 s** (never > 60 s for Shorts) | 40-60 s | `clips/C01.json` ... `C25.json` |
Plus `deliverables.md` / `.csv` (client tracker: `python scripts/report.py projects/<ep> --exports exports/<show>/<ep>`),
refreshed after every render batch; every spec carries `"title"` and `"topic"`.

Order of work:
1. Probe + sync the cameras (`scripts/sync.py camA camB` -> `"master"` + `"sync"` in every spec).
2. Transcribe the MASTER audio only (best mic). Read it all. Write `projects/<ep>/moments.md`:
   topic map (timecodes per topic), the 2 long-form themes, 30+ candidate shorts with hook line + length + look.
3. Send Nizam the plan + a **B-roll shot list** (what, where in the episode, search words, vertical/landscape).
   He downloads the clips by hand (no API key needed) into `projects/<ep>/broll/` and names them by shot number.
4. Render shorts first (fast feedback, `--draft --sheet`), fix the style, then finals.
5. Long-forms last (biggest renders): full episode in 20-30 min parts, then concat.
Distribute topics: no two shorts on the same point; spread across the whole episode; strongest 5 first.

### One wide camera, two people (Nizam's setup)
1. `python scripts/speakers.py raw/IMG_4342.MOV --tx tx --left Nizam --right Carrie` labels every word L/R
   (mic channels if separate, else mouth motion) and writes `tx/<clip>_speakers.txt` (read THIS to find Q -> A).
2. Specs use `"auto_frame": {}`: the engine cuts at every speaker change, frames the talker tight
   (long-form zoom ~1.9-2.0 on a 4K two-shot = native 1080p single; shorts = 9:16 crop on the talker, alternating
   1.0 / 1.12 punch-in when the same person keeps going) and returns to the wide two-shot every ~4th turn
   in long-forms. Explicit `cx`/`zoom`/`layout: split`/`broll` on a segment always win.
3. Long-forms: `"captions": "minimal", "captions_until": <seconds of cold open + intro>` (captions then switch off).
4. Halves (L02/L03): split L01 at the topic boundary nearest its midpoint; each half = its own 45-90 s cold open
   from that half, a "Part 1 / Part 2" title card, chapters restarting at 00:00.

## 0. Before the first edit of a new show (once)

Ask for anything missing from this list, in one message, then save answers to `brand-kit/<show>/BRAND.md`:
1. Show name, host + guest names and how to write their handles/roles (lower thirds).
2. Camera setup: how many cameras, which file is which (wide / host / guest), are they already synced?
   Separate mic tracks per speaker? (decides multicam switching, see section 3)
3. Language (English / Hinglish / Hindi) and words Whisper will get wrong (names, brands, jargon).
4. Look: pick a default clip look (A / B / C below) + accent colour + logo PNG (transparent) + CTA text
   ("Comment LINK", "Full episode on YouTube", "Follow for part 2").
5. Music: **Nizam adds music himself in his editing app.** Render voice + SFX only (no `music` key) unless he asks.
6. Targets: clips per episode, clip length (default 30-60 s), long-form yes/no.

## 1. Ingest

On Windows use `python` instead of `python3`; paths like `"I:\claude to edit\IMG_4342.MOV"` work (quote them).
Big iPhone 4K HEVC files (10-20 GB/hour) seek slowly: for the long-forms make a 1080p edit copy once
(`ffmpeg -i IMG.MOV -vf scale=-2:1080 -c:v libx264 -crf 17 -preset fast -g 30 -c:a aac -b:a 256k camA_1080.mp4`);
cut shorts from the original 4K (room for punch-ins on the vertical crop).
Multicam: `python scripts/sync.py <master> <other cams>` prints `"master"` / `"sync"` for the spec; all segment times
are then master times, sound and captions always come from the master.

```bash
mkdir -p projects/<ep>/raw projects/<ep>/tx          # raw/ is git-ignored
# raw clips usually come as a Google Drive link: pull them with the Google Drive connector
# (search/download the files) into projects/<ep>/raw/. If a file is too big for the connector,
# ask Nizam to share it as "anyone with the link" and download it directly.
python3 scripts/transcribe.py projects/<ep>/raw/* --out projects/<ep>/tx --model small --prompt "<names, jargon>"
```
- Use `--model medium` for Hinglish or noisy rooms (slower, much better). `--lang hi` only for mostly-Hindi speech.
- Check sync if multicam: the same sentence should have the same timestamp in every camera's `.txt`.
  If not, measure the offset (first shared sentence) and use `start2` / per-clip offsets in the spec.
- `ffprobe` every file: resolution, fps, rotation, audio channels (two channels can mean two lav mics).

## 2. Find the moments (this is the editor's job — do it properly)

Read every `tx/<clip>.txt` in full. Score candidate moments; a clip must have ALL of:
- **Hook in the first 1.5 s**: a bold claim, a number, a contrarian line, or a question the viewer wants answered.
  Start mid-thought if needed ("A friend is not someone who tells you what you want to hear").
- **One idea, closed loop**: setup -> turn -> payoff. Cut the clip on the payoff line, not after it.
- **Stands alone**: no "as I said earlier", no unexplained "he/that".
Good sources: Q -> A pairs (host question + guest's sharpest answer), lists ("three things..."), stories with a
twist, numbers/proof, disagreements. Write a shortlist (time range, hook line, why it works, suggested look)
in `projects/<ep>/moments.md` and show it to Nizam before rendering if more than 3 clips.

**Tightening rules (all formats):**
- Cut on word boundaries from the transcript, pad 0.1 s. Remove dead air > 0.35 s (clips) / > 0.6 s (long-form),
  "um/uh", false starts, repeated phrases, "you know"/"like" chains.
- You may re-order lines inside a clip if the meaning holds (question after the answer is a classic hook).
- Never cut a word in half; never change what someone meant.

## 3. Pick shots (multicam logic) — full rules in references/edit-decisions.md

- Speaker on camera: show whoever is talking. Cut to the listener for reactions (laugh, nod, shock) <= 1.5 s.
- With separate mic tracks: the louder track is the speaker; switch only after >= 1.2 s of the new speaker.
- One wide camera only: fake two cameras with alternating `zoom` 1.0 / 1.2-1.3 every 3-6 s (cuts on sentence ends)
  and `cx` to follow the speaker (`"auto"` = largest face, `"left"`/`"right"` in a two-shot).
- Wide two-shot = the "breath" shot: use it on topic changes and as cutaway, max once per ~15 s.

## 4. The three clip looks (vertical 1080x1920, -14 LUFS, 30 fps)

| | **A. Letterbox lockup** (ref ig3) | **B. Creator hyper-edit** (ref ig2) | **C. Clean minimal** (ref ig1) |
|---|---|---|---|
| Use for | quotes, wisdom, emotional lines | how-to, frameworks, numbers, founder/creator talk | calm deep talk, long answers, YouTube Shorts |
| `layout` | `letterbox` (16:9 band on black; first seg `"open": true`) | mix: `full` punch-ins, `band` (blur-fill), `split` intro | `full` (or `letterbox`) |
| `captions` | `lockup`: tiny grotesk builds word by word; keyword -> HUGE heavy sans + italic serif connectors | `creator`: left stack, bold lines; keyword -> HUGE | `minimal`: small geometric sans, 2-4 words, swap, no animation |
| Cuts | 1-3 per clip, slow; wide two-shot as cutaway | every 0.8-6 s (median 1.7 s, ~22 cuts/min) | host Q -> hard cut -> guest A, ~1 cut / 7 s |
| Extras | headline in the top black (`hook`), logo sting end (`endcard.logo`) | `names` typed on, `counters`, `stamps`, `stacks`, `look: "bw"` for "before" beats | none |
| Keywords | 1 per 4-6 s, the word that carries the meaning | 1 per 3-5 s, numbers and nouns | none |
| End | 1-1.5 s logo sting on black/gradient | "COMMENT 'LINK'" card | hard out / follow card |

Caption rules for every look: never over the face or mouth, max 2 lines, keep spoken wording (fix spelling via
`fixes`), one accent colour at most, no em dashes on screen.

## 5. Write the spec and render

Copy the closest file from `examples/` to `projects/<ep>/clips/<id>.json`, fill segments from the transcript.
```bash
python3 scripts/podcast.py projects/<ep>/clips/C01.json --src projects/<ep>/raw --tx projects/<ep>/tx \
    --out exports/<show>/<ep> --draft --sheet      # review render (fast) + contact sheet
python3 scripts/podcast.py ... (same, without --draft)                 # final
```

## 5b. B-roll

When (see `references/edit-decisions.md`): a named place / person / event / object, the start of a story,
"imagine..." or anything the speaker describes visually. Not on emotional peaks or punchlines (stay on the face).
2-4 s each, max ~1 per 10 s in clips, slow push-in, voice continues underneath.

Sources, in order (no API key needed for 1-4):
1. **Motion-graphic cards built by Claude** (engine overlays or HyperFrames): macros bars, g/kg counters, fuelling
   timelines, do / don't splits, checklists, big numbers. For a talk podcast these carry most "B-roll" beats.
2. **Own footage** (Nizam's Drive / local `broll/` folder).
3. **Keyless stock photos**: `python scripts/find_broll.py "<concrete nouns>" --kind photo --orient portrait`
   (Openverse + Wikimedia Commons; CC0 / PD / CC BY / BY-SA only, NC/ND filtered out). Use with the slow push-in.
   Keyless *video* is thin (Wikimedia / Internet Archive): try `--kind video`, expect few hits.
4. AI-generated stills/clips via HyperFrames `media-use` (free HeyGen sign-in on Nizam's PC: `npx hyperframes auth login`).
5. Pexels MCP / Pixabay if a key is ever added.
Download with `scripts/fetch_broll.py <url> --ep projects/<ep> --name <slug> --source openverse|pexels|drive --author <name> --page <url>`
(writes `broll/credits.json`; CC BY / BY-SA credits go in the video description), then `"broll": {"file": ...}`.
Never: logos/brands as hero, recognisable public figures out of context, watermarks, NC/ND licenses.

## 6. QA — LOOK before you hand anything over

1. Read the `_sheet.jpg`. Then pull full-size frames at every keyword lockup, overlay and cut
   (`ffmpeg -ss <t> -i out.mp4 -frames:v 1 f.png`) and Read them. Check: face framed (not cut by crop),
   captions off the face, nothing overflows the frame, lockups readable, no caption on a card.
2. Read `work/<id>/captions.txt` against the audio transcript: spelling of names, Hinglish kept as spoken.
3. Loudness: the engine trims to -14 LUFS integrated; confirm with
   `ffmpeg -nostats -i out.mp4 -af ebur128=peak=true -f null - 2>&1 | tail -12` (I ~ -14, true peak < -1).
4. First frame: would it stop a scroll with the sound off? If not, fix the hook (re-order, headline, punch-in).
5. Send Nizam the render + 1-line "why this moment" for each clip. Delivered without music: leave voice at
   -14 LUFS and tell him to sit music around -20 to -24 dB under the voice in his app.

## Long-form episodes (16:9, 1920x1080)

**Informational episodes: use the approved FUEL LAB system — `references/fuel-lab-longform.md`** (look, devices,
Nizam's caption + motion rules, pipeline). Follow `references/longform.md` (cold-open trailer -> sting -> intro -> chapters). Engine: `"format": "long"`,
`"tighten": 0.6`, `"jump_zoom": [1.0, 1.12]` on single-camera stretches, `"chapter"` on the first segment of each
chapter (writes `_chapters.txt` for the YouTube description). Render 20-30 min sections separately, then concat.

## Don'ts
- Don't render before reading the full transcript. Don't pick a moment for its first line alone.
- Don't cover faces with captions or crop through a head. Don't leave a punch-in on a soft source (> 1.3x on 1080p).
- Don't stack more than 2 overlays at once. No idle wobble, no random emoji, no stock "subscribe" animations.
- Never commit raw footage or renders (git-ignored). Never use reference footage, music or logos.

## Learnings
- 2026-11-04: v1. Engine verified on reference stand-in footage: letterbox band-open, lockups, creator stack,
  split, band blur-fill, B&W look, counters, stamps, stacks, end card, jump-cut tightening, chapters, -14 LUFS.
  `alimiter` auto-levels by default in ffmpeg 6 — always `level=0`. OpenCV 5 has no Haar cascades — pin 4.12.
- 2026-11-05 (Carrie ep01, 25 shorts + 3 long-forms, built overnight):
  - **Speakers by voice pitch** (`scripts/pitch_speakers.py --split <Hz> --win 1.5`) when someone faces away from the
    camera (mouth motion labels were ~50% wrong). Measure each voice on a known stretch first (male ~130 Hz, female
    ~165 Hz here -> split 148). Still set `cx` per part by hand from the content for shorts.
  - **Cut on phrases, not transcript lines**: Whisper lines start mid-sentence. Anchor every part with a from/to
    phrase (see `projects/carrie-ep01/build_shorts.py` EDGES + `anchor()`), start after the previous word's end,
    end before the next word's start. Otherwise clips open on "home." / end on "What".
  - **Cards in a top panel** (`broll.panel: "top"`, card 1080x960 from `scripts/cards.py`) keep the talker visible;
    start the card when its first item is spoken (no 5+ s of empty card); bottom crop `zoom 2.0, cy 0.26`;
    captions drop to `cap_y 0.88` on those segments automatically.
  - Look A: captions under the band (`cap_y 0.76`), headline held the whole clip. Names never overlap: dur <= shot.
  - Long-forms: `auto_frame` with `min_turn 1.6` (no choppy cuts from label flips) and `zoom_right` wider for a
    person at a desk; chapter title card over the first 3 s of each chapter with `nocaps`; render the body in chunks
    once and build the halves (L02/L03) from the same chunks + their own cold open.
  - Windows: NVENC failed on this driver (needs 610+); `PODCAST_HWDEC=cuda` GPU *decode* still speeds 4K HEVC cuts.
- 2026-11-06 (Carrie long-form v2, after Nizam: "no B-roll, no elements, very bad"): a podcast long-form needs a
  visual every ~40-60 s, all driven by the words. Recipe in `projects/carrie-ep01/build_long2.py`: beats pinned to
  phrases (`("A", "05:31", "one banana", "st", [("Banana", "1 banana")])`): full-frame photo B-roll 3 s with push-in
  for named things (food, places, gear, a cramp), floating 3D element for objects/numbers said in passing, side card
  for numbers/lists/protocols (talker stays on screen), side-by-side split for quick Q -> A, captions on the whole
  episode ("pod" style). Pick every photo by eye from contact sheets: keyless search returns junk (bees for "salt
  sweat") - drop a beat rather than show a wrong picture. Wikimedia needs a User-Agent with a contact URL or it 429s.
  Face track every 3 s (`face_track(step=3)`) and a +-4 s window keeps leaning people in frame.
- 2026-11-07 (Carrie long-form v3, after Nizam: "I can't see any B-roll, motion cards or split screens"): v2's one
  visual per 40-60 s reads as *nothing* over 80 min. Target **one device every ~10-15 s** plus the camera cuts.
  Recipe: `projects/carrie-ep01/build_long3.py` + `scripts/fx.py` (alpha .mov overlays):
  - kinds: `br` full-frame photo, `card` side card, `sbs` split, `pip` floating photo card (rounded, white rim,
    label tab; the shot goes **wide** underneath and the card sits centred between the two people at y 0.42),
    `wd` kinetic keyword (heavy type on an accent bar, y 0.72, a real quote or the number), `st` 3D emoji (330 px).
  - two automatic passes: emoji on spoken keywords (each <= 7x, 70 s apart) and split screens wherever both people
    talk >= 1.2 s inside 4-11 s with 3+ turns. Greedy by priority (card > br > sbs > pip > wd > st > auto).
  - `L3_FLAGS=--gaps python build_long3.py --no-render` prints every 22+ s stretch with nothing on screen and the
    words said there: write beats for those. One render chunk per chapter keeps each final pass to <= ~60 overlays.
  - Overlay placement: tight single shots assume the person fills the middle (profile faces are missed by the
    detector) and use the side they face; elements carry their real width (`w`) so nothing clips a face or the edge.
  - Chapter tag top-left for the whole chapter (`"tags"`), pop/whoosh sfx on every element at low volume.
- 2026-11-09 (Carrie long-form v4, FUEL LAB, 64.8 min, approved look): specialist agents + `build_long4.py`; full
  system in `references/fuel-lab-longform.md`. Nizam's review: captions must be ONE font, ONE size, one baseline, no
  box behind the host, no blur, light outline only, keyword = colour only and rare; graphics must sit still (no
  push / zoom / shake / 3D drift); no punch-in zooms. Designs, split screens and real B-roll were praised.

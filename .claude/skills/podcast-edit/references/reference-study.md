# Reference study (2026-11-04)

Measured with ffmpeg (scene detection, ebur128), contact sheets at 1-2 fps and full-size frames.
Learn the grammar only. No reference footage, music, logos or show names go into our edits.

| id | link | format | length | cuts | loudness |
|---|---|---|---|---|---|
| ig1 | https://www.instagram.com/reel/DeacquZB7oM/ | 1916x1078 @60, landscape reel | 13.9 s | 1 (host Q -> guest A at ~3 s) | -14.2 LUFS |
| ig2 | https://www.instagram.com/reel/DULMz8cj9yn/ (yt-dlp needs the `/p/` URL) | 720x1280 (served 360x640) @25 | 54.1 s | 21 shots, median 1.7 s, mean 2.6 s, p10 0.8 s, p90 5.6 s, ~22 cuts/min | -14.3 LUFS |
| ig3 | https://www.instagram.com/reel/DTvMK1vkbTw/ | 720x1280 @30 | 14.0 s | 2 + logo sting | -14.1 LUFS |
| yt1 | https://youtu.be/67AUqNeRf6U | long-form | ? | not studied yet (YouTube blocked download from this environment) | |
| yt2 | https://youtu.be/BV7QRw8wtjs | 1280x720 @24, 2 h 50 min (Figuring Out / Raj Shamani, ultra-runner guest) | 10209 s | structure from transcript + chapters | |

Takeaway: every reference masters to **-14 LUFS**. All are 2-person sit-down podcasts with dark, warm,
shallow-depth rooms (bookshelves, practical lamps, brick), cardioid broadcast mics in frame.

## ig1 — clean minimal (look C)
- Two single-person cameras. Host asks the question (0-3 s) -> hard cut -> guest answers the rest. That's it.
- Captions: small geometric sans (Jost/Futura-like), white, ~2% of frame height, centred on the speaker's chest
  at frame centre, original casing, 2-4 words, chunk swaps on phrase boundaries, no animation, soft shadow.
- No title, no music, no SFX, no end card. The line carries it. Hook = the question itself.

## ig2 — creator hyper-edit (look B, the most "edited")
- Opening: guest close-up, hook line "You don't need BIG CAMERAS and everything", within 1 s.
- Layout devices: full-frame 9:16 punch-ins (alternating ~1.0x / ~1.4x), **band** (sharp 16:9 strip across the
  middle, the same shot blurred + scaled as the background above/below), **split** stacked intro
  (guest top / host bottom) with name lower-thirds at the seam.
- Name lower-thirds: bold sans name + tiny italic serif role/handle ("IG COACH | CREATOR - @handle"), typed on with
  an underscore cursor.
- Counter: "0 ———— 10,0_" line grows while the number counts up (follower goal).
- Giant text BEHIND the speaker (person cut out in front): "100,000", "SKILL", "Pattern" + glowing line graph.
  -> HyperFrames + media-use cutout, not the engine.
- Captions: left-of-centre stack; small medium-weight words + ONE huge bold keyword ("BIG CAMERAS",
  "pain point", "N", "3 seconds"), typewriter cursor on questions ("Contrary Vi_").
- Mood: black-and-white for "before you even..." beats; teal-cyan world otherwise; yellow grunge glow stamps
  ("SCRIPT", "FRAMEWORK") over warm shots.
- B-roll 3D insert: phone mockup on rocks showing reels thumbnails ("Performing Ideas in your niche").
- Checklist: glossy cyan buttons stack one per beat: Topic -> Hook -> Format -> CTA.
- End card: teal gradient, "COMMENT "LINK"" + small "TO GET THE FULL EPISODE". Caption in post says the same.
- SFX: whooshes on band/split transitions, clicks on typing, pops on stamps/buttons. Music bed low under voice.

## ig3 — letterbox lockup (look A)
- 16:9 shot in a black 9:16 frame (band 1080x608 at centre). **Opens from a thin strip** that expands to the full
  band in ~0.4 s.
- Captions build word by word in a tiny tight white grotesk inside the band. On the meaning-carrying words the
  line becomes a **lockup**: HUGE heavy tight sans ("Good", "good", "guarantee", "universe", "respond.") with small
  *italic serif* connectors around it ("to *others*", "*won't do* good *to you.*", "*the* universe *will*").
- Cutaway: wide two-shot of both chairs for the middle beat (~2.5 s).
- Ends on a white logo mark on black (~1.5 s). No music audible over speech; no SFX.

## yt2 — long-form episode structure (see longform.md)
- **Cold open 0:00-3:03**: ~35 rapid Q -> A beats pulled from the whole episode, each 3-10 s, music under,
  starts on a prop/visual moment ("I want to start by showing this picture"), stacks escalating stakes
  (pain, sleep, "why didn't you quit?", "what if you lost your leg?"), then practical value (exercises, 30-day plan)
  and ends on a **cliffhanger**: question asked, answer cut after its first words ("I think the first thing, very simple.").
- 3:03-4:05: subscribe/Spotify ask (~20 s) -> sponsor read (~40 s, laptop brand).
- 4:08: "Okay, so hello. Welcome to the show." -> episode proper.
- **25 chapters** in 2 h 50 min (every 4-20 min), titles are curiosity promises, not labels:
  "Why He Quit After Running 623 Kilometers", "His Darkest Moment During the 93-Hour Race".
- Ends with BTS + outro. Description: sponsor link, free PDF "playbook" lead magnet, guest suggestion form.

## Mapping to our tools
| Device | Where |
|---|---|
| word timings, transcript | `scripts/transcribe.py` |
| cuts, crops, band, blur-fill, split, B&W, punch-ins, jump-cut tightening, loudness | `scripts/podcast.py` |
| captions minimal / lockup / creator, names, counters, stamps, stacks, headline, end card | `scripts/podcast.py` (ASS) |
| text behind head, 3D phone mockup, line graphs, glossy 3D buttons | HyperFrames (`/hyperframes`, `hyperframes-registry`, `media-use`) |
| watching a new reference | `/watch`, then `/reverse-engineer` to measure it |

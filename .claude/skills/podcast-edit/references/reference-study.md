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

## Coach / triathlon references (added 2026-11-05)
Local files from Nizam, measured with `reverse-engineer/scripts/study.py` and checked frame by frame.
This is the kind of video he wants for the coach show: a coach teaching an athlete (bike fit, race strategy).

| id | file | format | length | cuts | loudness |
|---|---|---|---|---|---|
| coach1 | `D:\work\nizam\coach\coach cal (what).mp4` | 1920x1440 (4:3) @60 | 55.2 s | 7 shots, median 6.5 s (p10 1.3 / p90 14 s) | -11.4 LUFS |
| cyc25 | `D:\work\nizam\coach\cycle training sesh\25\reel-01.mp4` (one of 25 reels, `with-outro/` variants) | 1080x1920 @30 | 34.1 s | 1 take, layers do the work (a new element every ~4.5 s) | -15.6 LUFS |

### coach1 — handheld coaching with bold word captions
- Real-life footage in a bike shop: coach (left) explaining while the athlete rides the trainer (right).
  Full frame, no reframing gimmicks. Cutaways to detail shots (pedal/legs, hands on the aero bars) every 6-14 s
  while the coach's voice runs on. Face on screen only ~41%: the action carries it.
- Captions: heavy rounded geometric caps (Montserrat Black / "The Bold Font" feel), white, thin dark outline
  + soft shadow, 2-3 words at a time, lower-middle of the frame. **One keyword per chunk in yellow**
  ("ISSUES", "RACE", "OK", "IF"). Small and tight, not giant.
- Named brands become a logo-styled word inside the caption ("IRONMAN" with its M-dot treatment).
- No title card, no music audible over speech, no end card. Hook = the coach mid-action.

### cyc25 — Nizam's own house look for the coach show (match this)
- **Layout:** 9:16, the 16:9/4:3 source as a **sharp rounded-corner card** (~93% width, roughly y 33-72%),
  over the same footage **scaled up and heavily blurred** as the background.
- **Top:** a thin orange **progress bar** at the very top edge, growing over the clip.
- **Hook headline (first beat):** small orange monospace kicker with a square bullet ("■ IRONMAN · SWIM EXIT"),
  then a 3-line heavy white caps headline, left-aligned, with the key word knocked out in an **orange box**
  ("STOP **SPRINTING** OUT OF THE SWIM").
- **Data cards replace the headline above the video**, one per teaching beat: dark translucent rounded panel
  with an orange top rule, orange mono label ("■ WHAT A SPRINT DOES", "■ THE RULE", "■ YOUR HEART RATE TRACE"),
  then either a big caps statement with orange keyword ("AVOID SPIKES **ALL DAY**") or a line chart that draws
  on (single HR spike; flat orange line vs white zig-zag) with tiny mono annotations
  ("▲ HEART RATE SPIKE", "✓ FLAT = THE GOAL", "✕ SPIKES = RECIPE FOR DISASTER").
- **Captions below the card:** heavy caps, wide letter-spacing, white with **one orange keyword** per chunk,
  2-3 words, soft drop shadow. Final word keeps its full stop ("FOR DISASTER.").
- Palette: near-black `#110f0f` panels, orange `~#ff5a1f`, white. No yellow in this look.
- Mix sat at -15.6 LUFS; our masters still go to -14.
- -> Engine: card + blur-fill + captions + progress bar in `podcast.py`; headline/data cards and line charts
  in HyperFrames layered on top.

## Mapping to our tools
| Device | Where |
|---|---|
| word timings, transcript | `scripts/transcribe.py` |
| cuts, crops, band, blur-fill, split, B&W, punch-ins, jump-cut tightening, loudness | `scripts/podcast.py` |
| captions minimal / lockup / creator, names, counters, stamps, stacks, headline, end card | `scripts/podcast.py` (ASS) |
| text behind head, 3D phone mockup, line graphs, glossy 3D buttons | HyperFrames (`/hyperframes`, `hyperframes-registry`, `media-use`) |
| watching a new reference | `/watch`, then `/reverse-engineer` to measure it |

## yt1 + yt2 measured on Nizam's PC (2026-11-05, 720p downloads, scene threshold 0.3)
- **Cold open is the busiest part of the episode**: yt1 54 cuts / first 240 s, yt2 79 cuts / first 240 s (one cut every 3-4.5 s).
  Body (min 15-19): almost no hard scene changes, just speaker <-> two-shot switches every ~4-15 s and a wide every ~1 min.
- yt1 cold open devices: B&W beats with HUGE condensed words beside the head ("DON'T UNDERSTAND", "IT'S NOT EASY",
  "CHANGED"), the guest's name as a giant title over a hero photo, one mini "framework" motion segment (purple board,
  word "PASSION" + cut-out figure + rules typed on), archive photos/video of the guest's real career.
- Then: host-only intro to camera, a disclaimer card, chapter list ("TODAY WE FIGURE OUT") card, two-shot with both name
  lower thirds (white name, small grey role) -> body.
- Body inserts are SMALL and on the wide/two-shot: a logo or a book cover pops in floating over the wide shot when
  it's named (XBOX logo, two book covers, a portrait photo), 2-4 s, then gone. Subscribe/"clips channel" pills pop in
  bottom-left a few times per hour.
- yt1 chapters: 27 in 150 min, titles = "How/Why + specific noun/number" ("How a New Driver Helped Bryson Shoot 58").
Applied to our long-forms: busy cold open (cards + B&W + big words), calm body with auto-frame, card inserts only
when a number/list/protocol is spoken, wide on topic changes, names once at the first two-shot.

# Long-form YouTube episode recipe (16:9, 1920x1080)

Modelled on the big Indian/English interview podcasts (ref yt2). Our job: turn a 1-3 h raw conversation into an
episode people don't click away from, plus the chapters text.

## Structure
| Part | Length | What |
|---|---|---|
| 1. Cold open | 60-180 s | 15-35 Q -> A beats from across the episode, 3-10 s each, music bed under (-24 dB, ducked). Escalate: stakes -> emotion -> practical value. Start on the most visual/surprising beat. End on a cliffhanger: the question + first words of the answer, then cut. |
| 2. Sting | 1-2 s | `{"card": true, "dur": 1.5, "logo": "brand-kit/<show>/logo.png"}` |
| 3. Asks | 20-60 s | Subscribe ask, sponsor read if any (host records these; place them here, not mid-story). |
| 4. Welcome | ~15 s | "Welcome to the show" + who the guest is, in one line. |
| 5. Body | rest | Chapters in conversation order. Cut tangents that go nowhere; keep stories intact. |
| 6. Outro | 10-60 s | Last question ("one piece of advice...") -> thank you -> BTS optional. |

## Cold-open picking rules
- Read the whole transcript first. Mark every line that is: a number, a superlative, pain/fear/stakes,
  a contrarian opinion, a laugh, a "how do I..." with a concrete answer.
- Pair each answer with the host's question when the question adds tension; otherwise answer alone.
- Never reveal the punchline of the best story — tease it.
- Same beat must not appear twice in the open.

## Body editing
- `"tighten": 0.6` removes pauses > 0.6 s; `"drop_fillers": true` (default) removes um/uh.
  Keep natural laughs and reaction pauses on emotional beats (put `"tighten": 0` on that segment).
- Single camera: `"jump_zoom": [1.0, 1.12]` alternates framing on each jump cut so it reads as a camera change.
- Multicam: switch to the speaker; listener reaction cutaways 1-1.5 s on strong lines; wide two-shot every
  ~1-2 min or on topic changes.
- Captions on long-form: `"captions": "none"` (YouTube CC) or `"minimal"` low (cap_y 0.83). Lockups only in the open.
- Lower-third name once, at the welcome (`names`).

## Chapters
- Put `"chapter": "<title>"` on the first segment of each chapter. Engine writes `<id>_chapters.txt`
  (first line 00:00 as YouTube requires).
- Every 4-15 min. Titles are curiosity promises in Title Case, 4-9 words, with a specific number or noun:
  "Why He Quit After Running 623 Kilometers", not "Running career".

## Deliverables per episode
1. `exports/<show>/<ep>/E<nn>_episode.mp4` (+ `_chapters.txt`)
2. 5-10 vertical clips (looks A/B/C) cut from the same transcripts
3. `projects/<ep>/description.md`: title options (3), description with chapters, pinned-comment line
4. Thumbnail frame suggestions: 3 timestamps with a strong expression (pull with ffmpeg, show Nizam)

## Render tips
- Render the body in 20-30 min parts (separate specs), then concat with
  `ffmpeg -f concat -safe 0 -i list.txt -c copy episode.mp4` — all parts share codec settings.
- `--draft` first for a watch-through; finals overnight if long.

# Reference studies (pushed from Nizam's computer)

YouTube blocks downloads from Claude's cloud environment, so long-form references are studied on Nizam's
computer and only the RESULTS are pushed here (small: report + contact sheets + cut list + transcript).
Videos/audio stay out of git automatically (*.mp4, *.wav are ignored).

## Run one study (on your computer, inside this repo)
```bash
bash scripts/setup.sh            # once
python3 .claude/skills/reverse-engineer/scripts/study.py \
    --url "https://youtu.be/BV7QRw8wtjs" --start 0 --dur 300 \
    --slug rajshamani-fo578-coldopen --out references/studies/rajshamani-fo578-coldopen
git add references/studies && git commit -m "Study: Raj Shamani FO578 cold open" && git push
```
`--start/--dur` pick a 3-5 min section (max 600 s). One folder per section.

## What to study (3 sections per long-form video)
| Section | Why | Where in the video |
|---|---|---|
| `coldopen` | cuts, music hits, text, how the trailer is built | 0:00 -> start of the welcome (~3-4 min) |
| `story` | B-roll, photo/news inserts, slow zooms on emotion | a chapter where the guest tells a story |
| `explainer` | stat cards, full-screen text, split screens, lists | a chapter with numbers / advice / "how to" |

Videos to study (add your own):
- Raj Shamani, Figuring Out FO578: https://youtu.be/BV7QRw8wtjs (already have transcript + chapters)
- https://youtu.be/67AUqNeRf6U (not studied yet)
- 1-2 more Raj Shamani episodes + any other channel whose editing you want (send links).

Each folder ends up with: `report.md`, `report.json`, `frames/shots_*.jpg`, `frames/hook.jpg`,
`frames/dense_*.jpg`, `cuts/cuts.txt`, `cuts/events.txt`, `audio/words.json`, `audio/transcript.txt`.
Claude reads these, fills `.claude/skills/podcast-edit/references/reference-study.md` and the
edit-decisions rulebook.

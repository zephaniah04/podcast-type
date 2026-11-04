# podcast-type

Podcast editing studio. Drop raw podcast footage in, get finished vertical clips (Reels / Shorts / TikTok)
and full YouTube episodes out. Claude does the editing: reads the transcripts, picks the moments, cuts on
word boundaries, captions and renders.

## Setup

```bash
bash scripts/setup.sh                                          # Mac / Linux
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1     # Windows
```

## Edit an episode

```bash
# 1. raw footage (git-ignored)
mkdir -p projects/ep01/raw && cp /path/to/*.mp4 projects/ep01/raw/

# 2. transcripts with word timings
python3 scripts/transcribe.py projects/ep01/raw/* --out projects/ep01/tx --model small

# 3. one JSON spec per clip (start from .claude/skills/podcast-edit/examples/)
python3 scripts/podcast.py projects/ep01/clips/C01.json --src projects/ep01/raw --tx projects/ep01/tx \
    --out exports/myshow/ep01 --draft --sheet
```

Or just tell Claude: "new episode in projects/ep01/raw — make 6 clips and the long-form".

## Looks (measured from the reference reels)

| Look | Feel | Captions |
|---|---|---|
| **A. Letterbox lockup** | 16:9 band on black that opens from a strip, headline above | tiny words build up; key word goes HUGE with italic-serif connectors |
| **B. Creator hyper-edit** | punch-ins, blur-fill band, split intro, B&W "before" beats, counters, stamps, checklists | left stack, one huge bold keyword |
| **C. Clean minimal** | host question -> hard cut -> guest answer | small geometric sans, no animation |
| **Long-form** | cold-open trailer -> sting -> episode, jump-cut tightening, chapters | none / minimal |

All masters: 1080x1920 or 1920x1080, 30 fps, -14 LUFS (what every reference measured).

## What's inside

| Tool | For |
|---|---|
| `scripts/transcribe.py` | faster-whisper transcripts + word timings (`.json` for the engine, `.txt` to read) |
| `scripts/podcast.py` | the edit engine: cuts, layouts, captions, overlays, B-roll, audio chain, chapters |
| `scripts/sync.py` | multicam: find each camera's offset from the audio |
| `scripts/report.py` | client tracker table (topics, lengths, status) as .md + .csv |
| `scripts/fetch_broll.py` | download a B-roll file into the episode + log its source/license |
| `tools/mcp-pexels` (+ `.mcp.json`) | Pexels MCP server: Claude searches free stock videos/photos from chat (needs `PEXELS_API_KEY`) |
| `.claude/skills/podcast-edit/` | the podcast editing skill: looks, moment-picking rules, long-form recipe, spec format, QA |
| ffmpeg, yt-dlp, Whisper | under the hood |
| HyperFrames, Remotion (+ skills) | heavier motion graphics: text behind head, 3D mockups, charts |
| `watch`, `reverse-engineer`, `reverse-any-video` | study new reference videos and turn them into rules |

Skills and toolkit carried over from [zephaniah04/bijen-vids](https://github.com/zephaniah04/bijen-vids);
licenses in `third_party/`.

## Folders

```
brand-kit/<show>/      logo, colours, CTA, host/guest names and handles
references/            reference links (analysis lives in the skill)
projects/<ep>/         raw/ (ignored), tx/ transcripts, clips/ specs, moments.md
exports/               renders (ignored)
assets/fonts, sfx      caption fonts (OFL) and sound effects
```

## Pushing your own skills and studies (from another computer)

- **Your trained skills** -> `.claude/skills/<skill-name>/` (one folder each, `SKILL.md` with `name:` and
  `description:` frontmatter, plus any `references/`, `scripts/`, `assets/`). Use a name that doesn't clash with
  an existing folder here (e.g. `nizam-podcast-broll`, not `hyperframes`).
- **Reference studies** (YouTube editing analysed on your computer) -> `references/studies/<slug>/`,
  see `references/studies/README.md`.
- **Raw footage and reference videos** -> Google Drive (never git; GitHub rejects files > 100 MB).
- Push to `main` (merge Claude's branch first) or tell Claude the branch name; Claude pulls and merges the
  knowledge into `.claude/skills/podcast-edit/`.

# podcast-type

Podcast editing studio. Drop raw podcast footage in, get finished vertical clips (Reels / Shorts / TikTok)
and full YouTube episodes out. Claude does the editing: reads the transcripts, picks the moments, cuts on
word boundaries, captions and renders.

## Setup

```bash
bash scripts/setup.sh
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
| `scripts/podcast.py` | the edit engine: cuts, layouts, captions, overlays, audio chain, chapters |
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

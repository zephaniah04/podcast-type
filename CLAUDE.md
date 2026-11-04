# podcast-type — notes for Claude

Podcast editing studio for Nizam. Claude is the editor: Nizam drops raw podcast footage, Claude picks the
moments, cuts, captions and renders. Two outputs: vertical clips (Reels/Shorts) and 16:9 YouTube episodes.

- Fresh environment: `bash scripts/setup.sh` (ffmpeg, yt-dlp, faster-whisper, OpenCV 4.12, HyperFrames, Remotion).
- **Main skill: `.claude/skills/podcast-edit/`** — read its SKILL.md before any podcast edit. It holds the three
  measured clip looks (A letterbox lockup, B creator hyper-edit, C clean minimal), the long-form recipe,
  the spec format and the QA loop.
- Flow: `scripts/transcribe.py` (word timings) -> read every transcript, shortlist moments in
  `projects/<ep>/moments.md` -> JSON spec per clip -> `scripts/podcast.py --draft --sheet` -> LOOK at frames ->
  final render to `exports/`.
- Heavier motion graphics (text behind the head, 3D mockups, charts): HyperFrames skills, layered on an engine render.
- New reference video: `/watch` it, `/reverse-engineer` to measure it, add findings to
  `.claude/skills/podcast-edit/references/reference-study.md`.
- One folder per show in `brand-kit/<show>/` (BRAND.md, logo, colours, CTA, names/handles).
- Learn a reference's grammar; never copy its footage, music, logos or show name.
- Never commit raw footage or renders (git-ignored). Masters are 1080x1920 / 1920x1080, 30 fps, -14 LUFS.

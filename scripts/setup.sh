#!/usr/bin/env bash
# One-shot setup for the podcast editing toolkit. Safe to re-run.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> ffmpeg"
if ! command -v ffmpeg >/dev/null; then
  if command -v apt-get >/dev/null; then sudo apt-get update && sudo apt-get install -y ffmpeg
  elif command -v brew >/dev/null; then brew install ffmpeg
  else echo "Install ffmpeg manually: https://ffmpeg.org/download.html"; exit 1; fi
fi
ffmpeg -version | head -1

echo "==> Python tools (yt-dlp, Whisper, OpenCV)"
# CPU-only torch keeps the Whisper install small; drop the index URL if you have a GPU.
pip install --upgrade torch --index-url https://download.pytorch.org/whl/cpu
pip install --upgrade -r requirements.txt

echo "==> Node tools (HyperFrames, Remotion)"
npm install

echo "==> Check"
yt-dlp --version
python3 -c "import whisper; print('whisper', whisper.__version__)"
npx hyperframes --version || true
npx remotion --version
echo "Done. Start with .claude/skills/podcast-edit/SKILL.md (also: watch, reverse-engineer, hyperframes, remotion-*)."

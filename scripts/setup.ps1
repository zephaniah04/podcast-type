# Windows setup for the podcast editing toolkit. Safe to re-run.
# Run from the repo folder in PowerShell:
#   powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

function Need($cmd, $id) {
  if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
    Write-Host "==> installing $id"
    winget install --id $id -e --accept-source-agreements --accept-package-agreements
  } else { Write-Host "==> $cmd found" }
}

Need ffmpeg Gyan.FFmpeg
Need python Python.Python.3.12
Need node OpenJS.NodeJS.LTS
Need git Git.Git

# pick up PATH changes from the installs above without reopening the terminal
$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")

Write-Host "==> Python packages (faster-whisper, OpenCV 4.12, yt-dlp)"
python -m pip install --upgrade pip
python -m pip install yt-dlp faster-whisper "opencv-python-headless==4.12.0.88" "numpy>=1.24" "pillow>=10" fonttools

Write-Host "==> Node packages (HyperFrames, Remotion)"
npm install

Write-Host "==> Check"
ffmpeg -version | Select-Object -First 1
python -c "import faster_whisper, cv2; print('faster-whisper ok, opencv', cv2.__version__)"
node tools/mcp-pexels/dist/index.js 2>&1 | Select-Object -First 1   # prints 'PEXELS_API_KEY ... required' = server OK
Write-Host "Done. On Windows use 'python' (not python3) for the scripts. Start with .claude/skills/podcast-edit/SKILL.md"

#!/usr/bin/env python3
"""Join the v3 chunks (cold open + 17 chapters) into exports/carrie/ep01/L01v3_full-episode.mp4 + YouTube chapters."""
import glob, os, re, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "exports", "carrie", "ep01"); PCS = os.path.join(OUT, "long3_pieces")
files = []
for k in range(18):
    m = glob.glob(os.path.join(PCS, f"L3_{k:02d}_*.mp4"))
    if not m:
        raise SystemExit(f"missing chunk L3_{k:02d}")
    files.append(m[0])
lst = os.path.join(PCS, "list.txt")
open(lst, "w").write("".join(f"file '{f.replace(os.sep, '/')}'\n" for f in files))
out = os.path.join(OUT, "L01v3_full-episode.mp4")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", out], check=True)
dur = lambda p: float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout)
hms = lambda t: (lambda h, m, s: f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}")(int(t) // 3600, int(t) % 3600 // 60, int(t) % 60)
chap, t = ["00:00 Cold open"], 0.0
for f in files:
    cf = f[:-4] + "_chapters.txt"
    if os.path.exists(cf):
        for ln in open(cf, encoding="utf-8").read().splitlines():
            m = re.match(r"(\d+(?::\d+){1,2}) (.*)", ln)
            if m and m.group(2) != "Intro":
                p = [int(x) for x in m.group(1).split(":")]
                sec = p[-1] + 60 * p[-2] + (3600 * p[0] if len(p) == 3 else 0)
                chap.append(f"{hms(t + sec)} {m.group(2)}")
    t += dur(f)
open(out[:-4] + "_chapters.txt", "w", encoding="utf-8").write("Fuelling Like an Endurance Athlete (full episode)\n\n" + "\n".join(chap) + "\n")
print(out, f"{t / 60:.1f} min", len(chap), "chapters")

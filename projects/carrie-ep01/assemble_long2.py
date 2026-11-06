#!/usr/bin/env python3
"""Join the v2 pieces into exports/carrie/ep01/L01_full-episode_v2.mp4 + its YouTube chapter list."""
import os, re, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "exports", "carrie", "ep01"); PCS = os.path.join(OUT, "long2_v3")
keys = ["CO1", "P1", "P2", "P3", "P4"]
files = [os.path.join(PCS, f"L2_{k}_{'body' if k.startswith('P') else 'open'}.mp4") for k in keys]
missing = [f for f in files if not os.path.exists(f)]
if missing:
    raise SystemExit(f"missing: {missing}")
lst = os.path.join(PCS, "list.txt")
open(lst, "w").write("".join(f"file '{f.replace(os.sep, '/')}'\n" for f in files))
out = os.path.join(OUT, "L01v2_full-episode_v2.mp4")
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
                parts = [int(x) for x in m.group(1).split(":")]
                sec = parts[-1] + 60 * parts[-2] + (3600 * parts[0] if len(parts) == 3 else 0)
                chap.append(f"{hms(t + sec)} {m.group(2)}")
    t += dur(f)
open(out[:-4] + "_chapters.txt", "w", encoding="utf-8").write("Fuelling Like an Endurance Athlete (full episode)\n\n" + "\n".join(chap) + "\n")
print(out, f"{t / 60:.1f} min", len(chap), "chapters")

#!/usr/bin/env python3
"""Join rendered long pieces into L01 / L02 / L03 (stream copy) and write each one's YouTube chapter list."""
import json, os, re, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "exports", "carrie", "ep01")
PIECES = os.path.join(OUT, "long_pieces")
PLAN = {"L01_full-episode": ["CO1", "P1", "P2", "P3", "P4"],
        "L02_part-1-hydration-cramps-race-fuel": ["CO2", "P1", "P2"],
        "L03_part-2-daily-eating-protein-recovery": ["CO3", "P3", "P4"]}
TITLES = {"L01_full-episode": "Fuelling Like an Endurance Athlete (full episode)",
          "L02_part-1-hydration-cramps-race-fuel": "Part 1: Hydration, Cramps and Race Fuelling",
          "L03_part-2-daily-eating-protein-recovery": "Part 2: Daily Eating, Protein and Recovery"}


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                capture_output=True, text=True).stdout)


def piece(k):
    return os.path.join(PIECES, f"L_{k}_{'open' if k.startswith('CO') else 'body'}.mp4")


def hms(t):
    t = int(t); h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


for name, keys in PLAN.items():
    files = [piece(k) for k in keys]
    if not all(os.path.exists(f) for f in files):
        print("missing pieces for", name); continue
    lst = os.path.join(PIECES, name + ".txt")
    open(lst, "w").write("".join(f"file '{f.replace(os.sep, '/')}'\n" for f in files))
    out = os.path.join(OUT, name + ".mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                    "-movflags", "+faststart", out], check=True)
    chap, t = ["00:00 Cold open"], 0.0
    for k, f in zip(keys, files):
        cf = f[:-4] + "_chapters.txt"
        if os.path.exists(cf):
            for ln in open(cf, encoding="utf-8").read().splitlines():
                m = re.match(r"(?:(\d+):)?(\d+):(\d+) (.*)", ln)
                if m and m.group(4) != "Intro":
                    hh = int(m.group(1)) if m.group(1) and ln.count(":") == 2 else 0
                    mm, ss = (int(m.group(2)), int(m.group(3)))
                    chap.append(f"{hms(t + hh * 3600 + mm * 60 + ss)} {m.group(4)}")
        t += dur(f)
    open(out[:-4] + "_chapters.txt", "w", encoding="utf-8").write(TITLES[name] + "\n\n" + "\n".join(chap) + "\n")
    print(name, f"{t / 60:.1f} min", len(chap), "chapters")

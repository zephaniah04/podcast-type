#!/usr/bin/env python3
"""Join the v4 pieces into the finished episode.

Order: cold open (L4_00) -> title sting -> [chapter card NN -> chapter NN] x N -> outro talk (L4_99) -> outro card.
Cards (motion designer's mp4s) are re-encoded to the exact stream format of the engine pieces (H.264 High yuv420p
30 fps, AAC stereo 96 kHz) with their SFX, so the final join is a lossless stream copy.
  python projects/carrie-ep01/assemble_long4.py [--pieces DIR] [--out FILE]
"""
import json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
V4 = os.path.join(HERE, "v4")
TMP = os.path.join(os.environ.get("TEMP", "C:/Temp"), "v4")
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
PCS = arg("--pieces", os.path.join(TMP, "pieces"))
OUT = arg("--out", "I:/edited/Fuelling-Like-an-Endurance-Athlete_Nizam-x-Carrie-Mullin-Innes.mp4")
PRESET = os.environ.get("PODCAST_FINAL_PRESET", "fast")
plan = json.load(open(os.path.join(V4, "edit_plan.json"), encoding="utf-8"))


def gfx(name):
    for base in (os.path.join(V4, "gfx"), os.path.join(TMP, "gfx_big")):
        p = os.path.join(base, name)
        if os.path.exists(p):
            return p
    return None


def man_hits(name, default):
    """SFX cue sheet for a card from the designer's manifest: [(file under assets/sfx, at, linear vol)]"""
    try:
        m = json.load(open(os.path.join(V4, "gfx", "manifest.json"), encoding="utf-8"))
        for it in (m.get("files", []) if isinstance(m, dict) else m):
            if it.get("id") == name and it.get("sfx"):
                return [(os.path.basename(f), float(a), round(10 ** (float(g) / 20), 3))
                        for f, a, g in zip(it["sfx"], it["sfx_at"], it.get("sfx_gain_db") or [-12] * len(it["sfx"]))]
    except (OSError, ValueError, KeyError):
        pass
    return default


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                capture_output=True, text=True).stdout)


def card(src, name, hits):
    """re-encode a designer card to the piece format, with SFX hits [(file, at, vol)] on a silent bed"""
    out = os.path.join(PCS, f"card_{name}.mp4")
    if os.path.exists(out) and os.path.getmtime(out) > os.path.getmtime(src):
        return out
    d = dur(src)
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", src, "-f", "lavfi", "-t", f"{d}", "-i", "anullsrc=r=96000:cl=stereo"]
    fc, mix = "", ["[1:a]"]
    for j, (f, at, vol) in enumerate(hits):
        cmd += ["-i", os.path.join(ROOT, "assets", "sfx", f)]
        ms = int(at * 1000)
        fc += f"[{j + 2}:a]aresample=96000,aformat=channel_layouts=stereo,volume={vol},adelay={ms}|{ms}[s{j}];"
        mix.append(f"[s{j}]")
    fc += f"{''.join(mix)}amix=inputs={len(mix)}:normalize=0:duration=first,atrim=0:{d:.3f}[a];"
    fc += "[0:v]scale=1920:1080:flags=lanczos,fps=30,setsar=1,format=yuv420p[v]"
    cmd += ["-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", PRESET, "-crf", "18",
            "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-ar", "96000", "-ac", "2",
            "-movflags", "+faststart", "-t", f"{d:.3f}", out]
    subprocess.run(cmd, check=True)
    return out


def piece(k):
    for f in os.listdir(PCS):
        if f.startswith(f"L4_{k}_") and f.endswith(".mp4") and "_chapters" not in f:
            return os.path.join(PCS, f)
    raise SystemExit(f"missing piece L4_{k}")


def nice(title):
    """YouTube chapter title in sentence case: 'CHATGPT WAS MY DIETITIAN' -> 'ChatGPT was my dietitian'"""
    if not title.isupper():
        return title
    t = " " + title.lower() + " "
    for a_, b_ in ((" i ", " I "), ("chatgpt", "ChatGPT"), ("30-min ", "30-minute "), ("don't", "Don't")):
        t = t.replace(a_, b_)
    t = t.strip()
    return t[:1].upper() + t[1:]


seq, chap = [], []
seq.append(("L4_00", piece("00"), None))
ts = gfx("title_sting.mp4")
if ts:
    seq.append(("title", card(ts, "title", man_hits("title_sting", [("whoosh_slow.mp3", 0.0, 0.5), ("ding.mp3", 0.6, 0.25)])), None))
for c in plan["chapters"]:
    n = int(c["n"])
    cc = gfx(f"chap_{n:02d}.mp4")
    if cc:
        seq.append((f"chap{n}", card(cc, f"chap_{n:02d}", man_hits(f"chap_{n:02d}", [("whoosh_fast.mp3", 0.0, 0.45), ("click.wav", 0.35, 0.3)])), c["title"]))
        seq.append((f"L4_{n:02d}", piece(f"{n:02d}"), None))
    else:
        seq.append((f"L4_{n:02d}", piece(f"{n:02d}"), c["title"]))
if plan.get("outro"):
    seq.append(("L4_99", piece("99"), None))
oc = gfx("outro.mp4")
if oc:
    seq.append(("outro", card(oc, "outro", man_hits("outro", [("whoosh_soft2.mp3", 0.0, 0.4)])), None))

lst = os.path.join(PCS, "list4.txt")
open(lst, "w").write("".join(f"file '{p.replace(os.sep, '/')}'\n" for _, p, _ in seq))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                "-movflags", "+faststart", OUT], check=True)
hms = lambda t: (lambda h, m, s: f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}")(int(t) // 3600, int(t) % 3600 // 60, int(t) % 60)
t, lines = 0.0, ["00:00 Cold open"]
for name, p, title in seq:
    if title:
        lines.append(f"{hms(t)} {nice(title)}")
    if name == "L4_99":
        lines.append(f"{hms(t)} Wrap-up")
    t += dur(p)
open(OUT[:-4] + "_chapters.txt", "w", encoding="utf-8").write(
    f"{plan.get('title', 'Fuelling Like an Endurance Athlete')} | Nizam x Carrie Mullin Innes\n\n" + "\n".join(lines) + "\n")
print(OUT, f"{t / 60:.1f} min", len(lines), "chapters")

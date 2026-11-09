#!/usr/bin/env python3
"""Floating 3D elements for podcast edits: Microsoft Fluent 3D emoji (MIT licence) as short transparent clips.

Each sticker pops in (scale with a small overshoot + a little rotation), drifts upward slowly while it is on screen
(purposeful float, no idle wobble), shows an optional label pill under it, then pops out. Output: .mov (qtrle, alpha),
overlaid by podcast.py via the spec's "stickers" list.

usage: python scripts/stickers.py stickers.json --out projects/<ep>/stickers
stickers.json: {"accent": "#FFB238", "stickers": [{"id": "apple", "emoji": "Red apple", "label": "1 apple", "dur": 2.6,
                "size": 230}, ...]}   emoji = Fluent asset folder name (github.com/microsoft/fluentui-emoji/tree/main/assets)
"""
import argparse, json, math, os, subprocess, urllib.parse
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 30
BASE = "https://raw.githubusercontent.com/microsoft/fluentui-emoji/main/assets/"


def fetch(name, cache):
    os.makedirs(cache, exist_ok=True)
    dst = os.path.join(cache, name.replace(" ", "_").lower() + ".png")
    if os.path.exists(dst) and os.path.getsize(dst) > 1000:
        return dst
    snake = name.lower().replace(" ", "_").replace("-", "_")
    for rel in (f"{name}/3D/{snake}_3d.png", f"{name}/Default/3D/{snake}_3d_default.png"):
        url = BASE + urllib.parse.quote(rel)
        r = subprocess.run(["curl", "-sSL", "--max-time", "30", "-o", dst, "-w", "%{http_code}", url], capture_output=True, text=True)
        if r.stdout.strip() == "200" and os.path.getsize(dst) > 1000:
            return dst
    raise SystemExit(f"emoji '{name}' not found in fluentui-emoji")


def back(x, c=1.7):
    x = min(max(x, 0.0), 1.0); return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def render(st, src, out, accent):
    S = int(st.get("size", 220)); dur = float(st.get("dur", 2.6)); label = st.get("label", "")
    emo = Image.open(src).convert("RGBA").resize((S, S), Image.LANCZOS)
    shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    shadow.putalpha(emo.getchannel("A").point(lambda a: int(a * 0.45)))
    shadow = shadow.filter(ImageFilter.GaussianBlur(S * 0.06))
    f = ImageFont.truetype(os.path.join(ROOT, "assets/fonts/InterTight-Heavy.ttf"), int(S * 0.17))
    lw = int(f.getlength(label)) + int(S * 0.22) if label else 0
    W = max(int(S * 1.5), lw + 20) // 2 * 2
    H = (int(S * 1.35) + (int(S * 0.36) if label else 0)) // 2 * 2
    n = int(round(dur * FPS))
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "qtrle", "-g", "9999", "-pix_fmt", "argb", out], stdin=subprocess.PIPE)
    for i in range(n):
        t = i / FPS
        frame = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        tin, tout = t / 0.38, (dur - t) / 0.24
        sc = back(tin) if tin < 1 else 1.0
        if tout < 1:
            sc *= 0.55 + 0.45 * max(tout, 0)
        alpha = min(1.0, t / 0.12, max(tout, 0) * 1.4)
        rot = -12 * (1 - min(tin, 1)) ** 2
        drift = -S * 0.07 * (t / dur)  # slow rise: it floats, it doesn't jiggle
        if sc > 0.02:
            sz = max(2, int(S * sc))
            e = emo.resize((sz, sz), Image.LANCZOS).rotate(rot, resample=Image.BICUBIC, expand=True)
            sh = shadow.resize((sz, sz), Image.LANCZOS)
            cx, cy = W / 2, S * 0.62 + drift
            frame.alpha_composite(sh, (int(cx - sz / 2 + S * 0.03), int(cy - sz / 2 + S * 0.07)))
            frame.alpha_composite(e, (int(cx - e.width / 2), int(cy - e.height / 2)))
        if label:
            la = min(1.0, max(0.0, (t - 0.25) / 0.2), max(tout, 0) * 1.4)
            if la > 0:
                pill = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(pill)
                ph = int(S * 0.28); py = int(S * 1.27 + drift)
                x0 = W / 2 - lw / 2
                d.rounded_rectangle([x0, py, x0 + lw, py + ph], radius=ph // 2, fill=(14, 17, 22, int(225 * la)),
                                    outline=tuple(accent) + (int(255 * la),), width=max(2, S // 70))
                d.text((W / 2, py + ph / 2), label, font=f, fill=(255, 255, 255, int(255 * la)), anchor="mm")
                frame.alpha_composite(pill)
        if alpha < 1:
            a = frame.getchannel("A").point(lambda v: int(v * alpha)); frame.putalpha(a)
        p.stdin.write(frame.tobytes())
    p.stdin.close(); p.wait()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec"); ap.add_argument("--out", required=True); ap.add_argument("--still", type=float)
    a = ap.parse_args()
    s = json.load(open(a.spec, encoding="utf-8"))
    h = s.get("accent", "#FFB238").lstrip("#"); accent = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    os.makedirs(a.out, exist_ok=True)
    cache = os.path.join(a.out, "_emoji")
    for st in s["stickers"]:
        src = fetch(st["emoji"], cache)
        dst = os.path.join(a.out, st["id"] + ".mov")
        if os.path.exists(dst) and os.path.getmtime(dst) > os.path.getmtime(a.spec):
            continue
        render(st, src, dst, accent)
        print("sticker", st["id"])


if __name__ == "__main__":
    main()

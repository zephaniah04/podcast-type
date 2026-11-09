#!/usr/bin/env python3
"""Overlay elements for long-form podcast edits, rendered as short transparent clips (qtrle .mov, alpha) that
podcast.py lays over the picture via the spec's "stickers" list (x "auto" = placed away from the faces).

Kinds
  emoji  Microsoft Fluent 3D emoji (MIT) that pops in, floats up slowly, label pill under it, pops out.
  photo  a photo as a floating card: rounded corners, thin white rim, soft shadow, slight tilt, label tab.
         Pops in (back ease), holds dead still (still frames = tiny qtrle files), drops out.
  word   kinetic keyword: big heavy uppercase type on an accent bar that wipes in, optional small kicker line.

usage: python scripts/fx.py fx.json --out projects/<ep>/fx [-j 6]
fx.json: {"accent": "#FFB238", "fx": [
   {"id": "banana", "kind": "emoji", "emoji": "Banana", "label": "1 banana", "size": 300, "dur": 2.8},
   {"id": "cramp", "kind": "photo", "file": "projects/<ep>/broll/cramp.jpg", "label": "calf cramp", "w": 620, "dur": 3.6},
   {"id": "salty", "kind": "word", "text": "SALTY SWEATER", "kicker": "what Carrie calls it", "size": 112, "dur": 2.6}]}
"""
import argparse, json, math, os, subprocess, sys
from concurrent.futures import ProcessPoolExecutor
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stickers as STK  # noqa: E402

FPS = 30
HEAVY = os.path.join(ROOT, "assets/fonts/InterTight-Heavy.ttf")
MED = os.path.join(ROOT, "assets/fonts/InterTight-Medium.ttf")


def back(x, c=1.6):
    x = min(max(x, 0.0), 1.0); return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def out_cubic(x):
    x = min(max(x, 0.0), 1.0); return 1 - (1 - x) ** 3


def writer(path, W, H):
    return subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-c:v", "qtrle", "-g", "9999", "-pix_fmt", "argb", path], stdin=subprocess.PIPE)


def fade(img, a):
    if a >= 1:
        return img
    img = img.copy(); img.putalpha(img.getchannel("A").point(lambda v: int(v * max(a, 0))))
    return img


def shadow_of(img, blur, alpha=0.5):
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sh.putalpha(img.getchannel("A").point(lambda v: int(v * alpha)))
    return sh.filter(ImageFilter.GaussianBlur(blur))


def pill(text, font, accent, pad_x, h, fill=(14, 17, 22, 235)):
    w = int(font.getlength(text)) + 2 * pad_x
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=fill, outline=tuple(accent) + (255,), width=max(2, h // 18))
    d.text((w / 2, h / 2), text, font=font, fill=(255, 255, 255, 255), anchor="mm")
    return im


# ----------------------------------------------------------------------------- photo card
def render_photo(fx, out, accent):
    cw = int(fx.get("w", 620)); dur = float(fx.get("dur", 3.6)); tilt = float(fx.get("tilt", -2.5))
    src = Image.open(fx["file"] if os.path.isabs(fx["file"]) else os.path.join(ROOT, fx["file"])).convert("RGB")
    ch = int(cw * float(fx.get("aspect", 0.68)))
    photo = ImageOps.fit(src, (cw, ch), Image.LANCZOS, centering=(float(fx.get("cx", 0.5)), float(fx.get("cy", 0.5))))
    rim, rad = max(6, cw // 90), max(18, cw // 28)
    card = Image.new("RGBA", (cw + 2 * rim, ch + 2 * rim), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, card.width - 1, card.height - 1], radius=rad + rim, fill=(255, 255, 255, 255))
    mask = Image.new("L", (cw, ch), 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, cw - 1, ch - 1], radius=rad, fill=255)
    card.paste(photo, (rim, rim), mask)
    label = fx.get("label", "")
    if label:  # label tab hanging off the bottom-left corner
        f = ImageFont.truetype(HEAVY, int(cw * 0.052))
        tab = pill(label, f, accent, int(cw * 0.035), int(cw * 0.085), fill=tuple(accent) + (255,))
        d2 = ImageDraw.Draw(tab)  # dark text on the accent tab
        d2.rounded_rectangle([0, 0, tab.width - 1, tab.height - 1], radius=tab.height // 2, fill=tuple(accent) + (255,))
        d2.text((tab.width / 2, tab.height / 2), label, font=f, fill=(16, 16, 16, 255), anchor="mm")
        big = Image.new("RGBA", (max(card.width, tab.width + int(cw * 0.06)), card.height + tab.height // 2), (0, 0, 0, 0))
        big.alpha_composite(card, (0, 0)); big.alpha_composite(tab, (int(cw * 0.05), card.height - tab.height // 2))
        card = big
    card = card.rotate(tilt, resample=Image.BICUBIC, expand=True)
    sh = shadow_of(card, cw * 0.025, 0.55)
    W = (card.width + int(cw * 0.16)) // 2 * 2; H = (card.height + int(cw * 0.16)) // 2 * 2
    base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    base.alpha_composite(sh, ((W - card.width) // 2 + int(cw * 0.012), (H - card.height) // 2 + int(cw * 0.03)))
    base.alpha_composite(card, ((W - card.width) // 2, (H - card.height) // 2))
    n = int(round(dur * FPS)); p = writer(out, W, H); still = None
    for i in range(n):
        t = i / FPS; tin, tout = t / 0.42, (dur - t) / 0.26
        if tin >= 1 and tout >= 1:
            if still is None:
                still = base.tobytes()
            p.stdin.write(still); continue
        sc = back(tin) if tin < 1 else 1.0
        a = min(1.0, t / 0.14)
        dy = 0
        if tout < 1:
            sc *= 0.86 + 0.14 * max(tout, 0); a = min(a, max(tout, 0)); dy = int((1 - max(tout, 0)) * H * 0.06)
        frame = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if sc > 0.03:
            sz = (max(2, int(W * sc)), max(2, int(H * sc)))
            im = base.resize(sz, Image.BILINEAR)
            rot = (1 - min(tin, 1)) ** 2 * 6
            if rot > 0.2:
                im = im.rotate(rot, resample=Image.BICUBIC)
            frame.alpha_composite(im, ((W - sz[0]) // 2, (H - sz[1]) // 2 + dy))
        p.stdin.write(fade(frame, a).tobytes())
    p.stdin.close(); p.wait()


# ----------------------------------------------------------------------------- kinetic word
def render_word(fx, out, accent):
    text = fx["text"]; kicker = fx.get("kicker", ""); dur = float(fx.get("dur", 2.6))
    fs = int(fx.get("size", 108)); f = ImageFont.truetype(HEAVY, fs)
    lines = text.split("\n")
    tw = max(int(f.getlength(ln)) for ln in lines); lh = int(fs * 1.06)
    pad = int(fs * 0.28)
    fk = ImageFont.truetype(MED, int(fs * 0.30)) if kicker else None
    kh = int(fs * 0.48) if kicker else 0
    bw, bh = tw + 2 * pad, lh * len(lines) + int(pad * 0.9)
    W = (bw + 80) // 2 * 2; H = (bh + kh + 80) // 2 * 2
    x0, y0 = (W - bw) // 2, 40 + kh
    n = int(round(dur * FPS)); p = writer(out, W, H); still = None
    for i in range(n):
        t = i / FPS
        hold = t > 0.62 and (dur - t) > 0.28
        if hold and still is not None:
            p.stdin.write(still); continue
        frame = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(frame)
        tout = (dur - t) / 0.28
        a = min(1.0, max(tout, 0)) if tout < 1 else 1.0
        lift = int((1 - min(max(tout, 0), 1)) * fs * 0.35) if tout < 1 else 0
        wipe = out_cubic(t / 0.30)  # accent bar wipes in left -> right
        if wipe > 0:
            sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(sh).rounded_rectangle([x0 + 6, y0 + 10 - lift, x0 + 6 + int(bw * wipe), y0 + bh + 10 - lift], radius=int(fs * 0.16), fill=(0, 0, 0, 150))
            frame.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
            d.rounded_rectangle([x0, y0 - lift, x0 + int(bw * wipe), y0 + bh - lift], radius=int(fs * 0.16), fill=tuple(accent) + (255,))
        if kicker:
            ka = min(1.0, max(0.0, (t - 0.12) / 0.2))
            if ka > 0:
                kl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                ImageDraw.Draw(kl).text((x0 + 4, y0 - kh * 0.55 - lift), kicker.upper(), font=fk, fill=(255, 255, 255, 255), anchor="lm",
                                         stroke_width=3, stroke_fill=(0, 0, 0, 200))
                frame.alpha_composite(fade(kl, ka))
        ta = min(1.0, max(0.0, (t - 0.10) / 0.16))
        if ta > 0:  # text rises into the bar
            tl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dt = ImageDraw.Draw(tl)
            rise = int((1 - out_cubic((t - 0.10) / 0.32)) * fs * 0.35)
            for k, ln in enumerate(lines):
                dt.text((W / 2, y0 + pad * 0.45 + lh * k + lh / 2 + rise - lift), ln, font=f, fill=(16, 16, 16, 255), anchor="mm")
            m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rectangle([x0, y0 - lift, x0 + bw, y0 + bh - lift], fill=255)
            tl.putalpha(Image.composite(tl.getchannel("A"), Image.new("L", (W, H), 0), m))
            frame.alpha_composite(fade(tl, ta))
        frame = fade(frame, a)
        if hold:
            still = frame.tobytes()
        p.stdin.write(frame.tobytes())
    p.stdin.close(); p.wait()


def render_one(job):
    fx, out, accent, cache = job
    k = fx.get("kind", "emoji")
    if k == "emoji":
        STK.render({"size": 300, **fx}, STK.fetch(fx["emoji"], cache), out, accent)
    elif k == "photo":
        render_photo(fx, out, accent)
    elif k == "word":
        render_word(fx, out, accent)
    else:
        raise SystemExit(f"unknown fx kind {k}")
    return fx["id"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec"); ap.add_argument("--out", required=True); ap.add_argument("-j", type=int, default=6)
    ap.add_argument("--only")
    a = ap.parse_args()
    s = json.load(open(a.spec, encoding="utf-8"))
    h = s.get("accent", "#FFB238").lstrip("#"); accent = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    os.makedirs(a.out, exist_ok=True); cache = os.path.join(a.out, "_emoji")
    jobs = []
    for fx in s["fx"]:
        if a.only and fx["id"] not in a.only.split(","):
            continue
        dst = os.path.join(a.out, fx["id"] + ".mov")
        sig = json.dumps(fx, sort_keys=True)  # re-render only when this element's own settings changed
        sp = dst[:-4] + ".sig"
        if not a.only and os.path.exists(dst) and os.path.getsize(dst) > 2000 and os.path.exists(sp) and open(sp, encoding="utf-8").read() == sig:
            continue
        open(sp, "w", encoding="utf-8").write(sig)
        if fx.get("kind", "emoji") == "emoji":
            try:
                STK.fetch(fx["emoji"], cache)  # download once, before the pool
            except SystemExit as e:
                print("  skip:", e); continue
        jobs.append((fx, dst, accent, cache))
    with ProcessPoolExecutor(a.j) as ex:
        for i, fid in enumerate(ex.map(render_one, jobs)):
            print(f"fx {i + 1}/{len(jobs)} {fid}", flush=True)


if __name__ == "__main__":
    main()

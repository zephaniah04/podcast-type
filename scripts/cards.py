#!/usr/bin/env python3
"""Animated motion-graphic cards (B-roll for talk podcasts): big numbers, checklists, do/don't, timelines, bars.

Every card is drawn frame by frame with PIL and piped to ffmpeg -> an .mp4 the engine uses as `broll`.
Motion is purposeful only: things arrive when they are said (ease-out), then hold still. No idle wobble.

usage:
  python scripts/cards.py <cards.json> --out projects/<ep>/cards [--only ID]
cards.json: {"accent": "#FFB238", "cards": [{"id": "c01_carbs", "type": "bignum", "w": 1080, "h": 960, "dur": 4,
             "value": 90, "prefix": "", "suffix": "g", "label": "carbs per hour", "kicker": "RACE DAY"}, ...]}
types:
  bignum    value (counts up), prefix, suffix, label, kicker, [sub]
  list      title, items [str], [every] s between items, [check] true -> tick marks, [numbered]
  dodont    title, dont [str], do [str]
  timeline  title, points [{"t": "-3 h", "label": "meal"}...]  (vertical on tall cards, horizontal on wide)
  bars      title, bars [{"label": "Carbs", "value": 60, "unit": "%"}...], [max]
  title     kicker, title (2-6 words), [sub]   chapter / part title card
  versus    left {"title","lines"}, right {"title","lines"}, [title]
`at` per item (list/timeline/bars) = seconds into the card when that item lands (sync to the spoken word);
default spacing is `every` (0.5 s).
"""
import argparse, json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = os.path.join(ROOT, "assets/fonts")
FPS = 30
BG0, BG1 = (11, 14, 19), (24, 30, 38)
INK, MUTED = (245, 243, 238), (150, 158, 168)
RED, GREEN = (240, 84, 84), (88, 214, 141)


def font(name, size):
    return ImageFont.truetype(os.path.join(F, name), int(size))


HEAVY, MED, SERIF, BLACK = "InterTight-Heavy.ttf", "InterTight-Medium.ttf", "InstrumentSerif-Italic.ttf", "ArchivoBlack-Regular.ttf"


def hexrgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def ease(x):  # ease-out cubic, clamped
    x = min(max(x, 0.0), 1.0); return 1 - (1 - x) ** 3


def back(x):  # ease-out back (small overshoot) for pops
    x = min(max(x, 0.0), 1.0); c = 1.5; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def background(w, h, accent):
    img = Image.new("RGB", (w, h), BG0)
    d = ImageDraw.Draw(img)
    for y in range(h):  # vertical gradient
        k = y / h
        d.line([(0, y), (w, y)], fill=tuple(int(BG0[i] + (BG1[i] - BG0[i]) * k) for i in range(3)))
    glow = Image.new("RGB", (w, h), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    r = int(max(w, h) * 0.45)
    gd.ellipse([w * 0.75 - r, -r * 0.6, w * 0.75 + r, r * 1.0], fill=tuple(int(c * 0.22) for c in accent))
    glow = glow.filter(ImageFilter.GaussianBlur(r * 0.35))
    img = Image.fromarray(np.clip(np.asarray(img, dtype="int16") + np.asarray(glow, dtype="int16"), 0, 255).astype("uint8"))
    d = ImageDraw.Draw(img)
    step = int(min(w, h) / 12)  # faint grid: reads as "data" without shouting
    for x in range(0, w, step):
        d.line([(x, 0), (x, h)], fill=(30, 36, 44))
    for y in range(0, h, step):
        d.line([(0, y), (w, y)], fill=(30, 36, 44))
    return img


def text_c(d, xy, s, f, fill, anchor="mm"):
    d.text(xy, s, font=f, fill=fill, anchor=anchor)


def fit(s, fname, size, maxw):
    f = font(fname, size)
    while f.getlength(s) > maxw and size > 20:
        size *= 0.93; f = font(fname, size)
    return f


def alpha_blend(c, bg, a):
    return tuple(int(bg[i] + (c[i] - bg[i]) * a) for i in range(3))


def kicker(d, w, y, s, accent, t, S):
    if not s:
        return
    a = ease(t / 0.35)
    f = font(MED, 34 * S)
    tw = f.getlength(s.upper()) + 40 * S
    x0 = w / 2 - tw / 2
    d.rounded_rectangle([x0, y - 26 * S, x0 + tw * a, y + 26 * S], radius=26 * S, outline=accent, width=max(2, int(3 * S)))
    if a > 0.6:
        text_c(d, (w / 2, y), s.upper(), f, alpha_blend(accent, BG0, (a - 0.6) / 0.4))


def frame(card, t, base, accent):
    w, h = card["w"], card["h"]
    S = min(w, h) / 960  # scale unit
    img = base.copy(); d = ImageDraw.Draw(img)
    ty = card["type"]
    tall = h > w * 1.05
    if ty == "bignum":
        kicker(d, w, h * 0.22, card.get("kicker", ""), accent, t, S)
        v = float(card["value"]); run = card.get("run", 1.1)
        cur = v * ease(t / run) if card.get("count", True) else v
        dec = card.get("decimals", 0)
        num = f"{card.get('prefix', '')}{cur:,.{dec}f}"
        sfx = card.get("suffix", "")
        f = fit(num + sfx, BLACK, 300 * S, w * 0.86)
        sc = back(t / 0.45)
        fs = font(BLACK, f.size * (0.85 + 0.15 * sc))
        nw = fs.getlength(num); sw_ = font(BLACK, fs.size * 0.45).getlength(sfx)
        x = w / 2 - (nw + sw_) / 2; y = h * 0.50
        d.text((x, y), num, font=fs, fill=INK, anchor="lm")
        d.text((x + nw + 8 * S, y + fs.size * 0.18), sfx, font=font(BLACK, fs.size * 0.45), fill=accent, anchor="lm")
        lab = card.get("label", "")
        if lab:
            a = ease((t - 0.5) / 0.4)
            text_c(d, (w / 2, y + fs.size * 0.62 + 20 * (1 - a) * S), lab, fit(lab, SERIF, 70 * S, w * 0.86), alpha_blend(INK, BG0, a))
        if card.get("sub"):
            a = ease((t - 0.9) / 0.4)
            text_c(d, (w / 2, y + fs.size * 0.62 + 90 * S), card["sub"], fit(card["sub"], MED, 38 * S, w * 0.86), alpha_blend(MUTED, BG0, a))
        # underline grows under the number
        ln = (nw + sw_) * ease((t - 0.2) / 0.8)
        d.rectangle([w / 2 - ln / 2, y + fs.size * 0.36, w / 2 + ln / 2, y + fs.size * 0.36 + 6 * S], fill=accent)
    elif ty in ("list", "dodont", "versus"):
        title = card.get("title", "")
        ty0 = h * (0.13 if tall else 0.15)
        if title:
            a = ease(t / 0.35)
            text_c(d, (w / 2, ty0 + 16 * (1 - a) * S), title, fit(title, HEAVY, 64 * S, w * 0.88), alpha_blend(INK, BG0, a))
            d.rectangle([w / 2 - 50 * S * a, ty0 + 52 * S, w / 2 + 50 * S * a, ty0 + 58 * S], fill=accent)
        if ty == "list":
            items = card["items"]; every = card.get("every", 0.5)
            ats = card.get("at") or [0.35 + every * k for k in range(len(items))]
            top = ty0 + 120 * S; gap = min(120 * S, (h * 0.92 - top) / max(len(items), 1))
            top += max(0, (h * 0.92 - top - gap * len(items)) / 2)  # few items: centre the block, no empty half-card
            fz = min(52 * S, gap * 0.48)
            for k, it in enumerate(items):
                a = ease((t - ats[k]) / 0.3)
                if a <= 0:
                    continue
                y = top + gap * k + gap / 2
                x = w * 0.12 + 40 * S * (1 - a)
                r = fz * 0.62
                if card.get("numbered"):
                    d.ellipse([x - r, y - r, x + r, y + r], fill=alpha_blend(accent, BG0, a))
                    text_c(d, (x, y), str(k + 1), font(BLACK, fz * 0.8), BG0)
                else:
                    d.rounded_rectangle([x - r, y - r, x + r, y + r], radius=r * 0.35, outline=alpha_blend(accent, BG0, a), width=max(2, int(4 * S)))
                    if card.get("check", True) and t - ats[k] > 0.15:
                        p = ease((t - ats[k] - 0.15) / 0.25)
                        pts = [(x - r * 0.5, y), (x - r * 0.1, y + r * 0.4), (x + r * 0.55, y - r * 0.45)]
                        seg = pts[:2] if p < 0.4 else pts
                        d.line(seg, fill=accent, width=max(3, int(6 * S)), joint="curve")
                d.text((x + r + 26 * S, y), it, font=fit(it, HEAVY, fz, w * 0.88 - (x + r + 26 * S)), fill=alpha_blend(INK, BG0, a), anchor="lm")
        else:
            L = card.get("dont") if ty == "dodont" else card["left"]["lines"]
            R = card.get("do") if ty == "dodont" else card["right"]["lines"]
            lt = "DON'T" if ty == "dodont" else card["left"]["title"]
            rt = "DO" if ty == "dodont" else card["right"]["title"]
            lc, rc = (RED, GREEN) if ty == "dodont" else (MUTED, accent)
            top = ty0 + (110 if title else 20) * S
            colw = w * 0.42
            for side, (head, lines, col, x0, t0) in enumerate([(lt, L, lc, w * 0.06, 0.3), (rt, R, rc, w * 0.52, 0.3 + card.get("delay", 1.2))]):
                a = ease((t - t0) / 0.35)
                if a <= 0:
                    continue
                d.rounded_rectangle([x0, top, x0 + colw, h * 0.92], radius=28 * S, fill=alpha_blend(tuple(int(c * 0.18) for c in col), BG0, a), outline=alpha_blend(col, BG0, a), width=max(2, int(3 * S)))
                hf = fit(head, BLACK, 56 * S, colw * 0.8)
                d.text((x0 + colw / 2, top + 60 * S), head, font=hf, fill=alpha_blend(col, BG0, a), anchor="mm")
                gap = min(110 * S, (h * 0.92 - top - 130 * S) / max(len(lines), 1))
                for k, ln in enumerate(lines):
                    b = ease((t - t0 - 0.25 - 0.35 * k) / 0.3)
                    if b <= 0:
                        continue
                    yy = top + 130 * S + gap * k + gap / 2
                    mx_, r_ = x0 + 44 * S, 12 * S; cc = alpha_blend(col, BG0, b); lw = max(3, int(6 * S))
                    if ty == "dodont" and side == 0:  # cross
                        d.line([(mx_ - r_, yy - r_), (mx_ + r_, yy + r_)], fill=cc, width=lw)
                        d.line([(mx_ - r_, yy + r_), (mx_ + r_, yy - r_)], fill=cc, width=lw)
                    elif ty == "dodont":  # tick
                        d.line([(mx_ - r_, yy), (mx_ - r_ * 0.2, yy + r_ * 0.8), (mx_ + r_ * 1.1, yy - r_ * 0.9)], fill=cc, width=lw, joint="curve")
                    else:
                        d.ellipse([mx_ - r_ * 0.6, yy - r_ * 0.6, mx_ + r_ * 0.6, yy + r_ * 0.6], fill=cc)
                    words = ln.split(); lines2 = [""]
                    ff = font(MED, min(40 * S, gap * 0.4))
                    for wd in words:
                        if ff.getlength((lines2[-1] + " " + wd).strip()) > colw - 100 * S:
                            lines2.append(wd)
                        else:
                            lines2[-1] = (lines2[-1] + " " + wd).strip()
                    for j, l2 in enumerate(lines2[:2]):
                        d.text((x0 + 80 * S, yy + (j - (len(lines2[:2]) - 1) / 2) * ff.size * 1.1), l2, font=ff, fill=alpha_blend(INK, BG0, b), anchor="lm")
    elif ty == "timeline":
        title = card.get("title", "")
        pts = card["points"]; every = card.get("every", 0.55)
        ats = [p.get("at", 0.5 + every * k) for k, p in enumerate(pts)]
        ty0 = h * 0.12
        if title:
            a = ease(t / 0.35)
            text_c(d, (w / 2, ty0), title, fit(title, HEAVY, 62 * S, w * 0.88), alpha_blend(INK, BG0, a))
        if tall:  # vertical rail
            x = w * 0.22; y0, y1 = ty0 + 110 * S, h * 0.92
            prog = ease((t - 0.2) / max(ats[-1] + 0.3, 0.5))
            d.line([(x, y0), (x, y1)], fill=(52, 60, 70), width=int(6 * S))
            d.line([(x, y0), (x, y0 + (y1 - y0) * prog)], fill=accent, width=int(6 * S))
            gap = (y1 - y0) / len(pts)
            for k, p in enumerate(pts):
                a = back((t - ats[k]) / 0.35)
                if a <= 0:
                    continue
                y = y0 + gap * k + gap / 2; r = 20 * S * a
                d.ellipse([x - r, y - r, x + r, y + r], fill=accent)
                al = min(a, 1)
                d.text((x + 50 * S, y - 26 * S), p["t"], font=fit(p["t"], BLACK, 54 * S, w * 0.66), fill=alpha_blend(accent, BG0, al), anchor="lm")
                d.text((x + 50 * S, y + 30 * S), p["label"], font=fit(p["label"], MED, 40 * S, w * 0.66), fill=alpha_blend(INK, BG0, al), anchor="lm")
        else:  # horizontal rail
            y = h * 0.52; x0, x1 = w * 0.08, w * 0.92
            prog = ease((t - 0.2) / max(ats[-1] + 0.3, 0.5))
            d.line([(x0, y), (x1, y)], fill=(52, 60, 70), width=int(6 * S))
            d.line([(x0, y), (x0 + (x1 - x0) * prog, y)], fill=accent, width=int(6 * S))
            gap = (x1 - x0) / len(pts)
            for k, p in enumerate(pts):
                a = back((t - ats[k]) / 0.35)
                if a <= 0:
                    continue
                x = x0 + gap * k + gap / 2; r = 18 * S * a; al = min(a, 1)
                d.ellipse([x - r, y - r, x + r, y + r], fill=accent)
                d.text((x, y - 70 * S), p["t"], font=fit(p["t"], BLACK, 52 * S, gap * 0.92), fill=alpha_blend(accent, BG0, al), anchor="mm")
                d.text((x, y + 70 * S), p["label"], font=fit(p["label"], MED, 36 * S, gap * 0.92), fill=alpha_blend(INK, BG0, al), anchor="mm")
    elif ty == "bars":
        title = card.get("title", "")
        bars = card["bars"]; every = card.get("every", 0.45)
        mx = card.get("max") or max(b["value"] for b in bars)
        ty0 = h * 0.13
        if title:
            a = ease(t / 0.35)
            text_c(d, (w / 2, ty0), title, fit(title, HEAVY, 62 * S, w * 0.88), alpha_blend(INK, BG0, a))
        top = ty0 + 100 * S; gap = (h * 0.9 - top) / len(bars)
        bh = min(gap * 0.42, 70 * S)
        for k, b in enumerate(bars):
            at = b.get("at", 0.4 + every * k)
            a = ease((t - at) / 0.8)
            if t < at:
                continue
            y = top + gap * k + gap * 0.5
            lx = w * 0.08
            d.text((lx, y - bh * 0.95), b["label"], font=font(HEAVY, 44 * S), fill=INK, anchor="ls")
            d.rounded_rectangle([lx, y - bh / 2, w * 0.92, y + bh / 2], radius=bh / 2, fill=(36, 42, 50))
            ww = (w * 0.84) * (b["value"] / mx) * a
            if ww > bh:
                d.rounded_rectangle([lx, y - bh / 2, lx + ww, y + bh / 2], radius=bh / 2, fill=hexrgb(b["color"]) if b.get("color") else accent)
            val = f"{b['value'] * a:,.0f}{b.get('unit', '')}"
            d.text((w * 0.92, y - bh * 0.95), val, font=font(BLACK, 44 * S), fill=accent, anchor="rs")
    elif ty == "title":
        a = ease(t / 0.5)
        kicker(d, w, h * 0.36, card.get("kicker", ""), accent, t, S)
        tt = card["title"]
        f = fit(tt, BLACK, 110 * S, w * 0.86)
        words = tt.split()
        if f.getlength(tt) > w * 0.8 and len(words) > 1:  # two balanced lines, never an orphan word
            best = min(range(1, len(words)), key=lambda k: abs(f.getlength(" ".join(words[:k])) - f.getlength(" ".join(words[k:]))))
            lines = [" ".join(words[:best]), " ".join(words[best:])]
        else:
            lines = [tt]
        f = fit(max(lines, key=len), BLACK, 110 * S, w * 0.84)
        for j, ln in enumerate(lines):
            b = ease((t - 0.15 - 0.12 * j) / 0.45)
            text_c(d, (w / 2, h * 0.50 + j * f.size * 1.08 + 30 * (1 - b) * S), ln, f, alpha_blend(INK, BG0, b))
        if card.get("sub"):
            b = ease((t - 0.6) / 0.4)
            text_c(d, (w / 2, h * 0.50 + len(lines) * f.size * 1.08 + 20 * S), card["sub"], fit(card["sub"], SERIF, 56 * S, w * 0.8), alpha_blend(MUTED, BG0, b))
    else:
        sys.exit(f"unknown card type {ty}")
    # fade-in from black over the first 4 frames so the cut into the card is soft but quick
    if t < 0.13:
        img = Image.blend(Image.new("RGB", (w, h), BG0), img, t / 0.13)
    return img


def render(card, out, accent):
    w, h = card.setdefault("w", 1080), card.setdefault("h", 960)
    dur = float(card.get("dur", 4.0))
    base = background(w, h, accent)
    n = int(round(dur * FPS))
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p", out],
                         stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(frame(card, i / FPS, base, accent).tobytes())
    p.stdin.close(); p.wait()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec"); ap.add_argument("--out", required=True); ap.add_argument("--only")
    ap.add_argument("--still", type=float, help="write a PNG of each card at this second instead (quick look)")
    a = ap.parse_args()
    s = json.load(open(a.spec, encoding="utf-8"))
    accent = hexrgb(s.get("accent", "#FFB238"))
    os.makedirs(a.out, exist_ok=True)
    for c in s["cards"]:
        if a.only and c["id"] not in a.only.split(","):
            continue
        if a.still is not None:
            c.setdefault("w", 1080); c.setdefault("h", 960)
            frame(c, a.still, background(c["w"], c["h"], accent), accent).save(os.path.join(a.out, c["id"] + ".png"))
        else:
            dst = os.path.join(a.out, c["id"] + ".mp4")
            if os.path.exists(dst) and os.path.getmtime(dst) > os.path.getmtime(a.spec):
                continue
            render(c, dst, accent)
        print("card", c["id"])


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Podcast edit engine: raw camera files + Whisper word timings + a JSON spec -> finished video.

One engine, two formats:
  "format": "short"  1080x1920 clip (Reels / Shorts / TikTok)
  "format": "long"   1920x1080 YouTube episode (cold open, chapters, jump-cut tightening)

Full spec reference: .claude/skills/podcast-edit/references/spec.md
Minimal spec:
{
  "id": "S01", "slug": "best-advice", "format": "short",
  "layout": "letterbox",                    # full | letterbox | band | split   (per segment override)
  "captions": "lockup",                     # minimal | lockup | creator | none
  "keywords": ["truth", "pain point"],      # words/phrases promoted to the big lockup word
  "segments": [{"clip": "camB", "start": 12.3, "end": 20.1}]
}

usage:
  python3 scripts/podcast.py <spec.json> --src <raw dir> --tx <transcript dir> --out exports/<show>
        [--work <temp dir>/podcast-work] [--draft] [--sheet]
Works on Linux, macOS and Windows (paths with drive letters and spaces are escaped for ffmpeg).
"""
import argparse, glob, json, os, re, subprocess, sys, tempfile
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "assets/fonts")
SFX = os.path.join(ROOT, "assets/sfx")
FPS = 30
FILLERS = {"um", "uh", "umm", "uhh", "erm", "hmm", "uhm", "mm"}

# font family names (see assets/fonts) -> file, for width measuring
FONT_FILES = {
    "Inter Tight Heavy": "InterTight-Heavy.ttf",
    "Inter Tight Medium": "InterTight-Medium.ttf",
    "Instrument Serif Italic": "InstrumentSerif-Italic.ttf",
    "Jost Regular": "Jost-Regular.ttf",
    "Archivo Black": "ArchivoBlack-Regular.ttf",
    "Space Mono": "SpaceMono-Regular.ttf",
    "Space Mono Bold": "SpaceMono-Bold.ttf",  # ASS: \fnSpace Mono\b1
}
# v4 "FUEL LAB" palette (projects/carrie-ep01/v4/BRIEF.md)
INK, PAPER, ACCENT4, HIGHLIGHT, TRACK, GRIDLINE = "#0D0D0D", "#EFEBE3", "#FF5A1F", "#FFD84D", "#1F6B45", "#2E8A5C"
CACHE = None  # <work>/_cache: per-clip head samples, panel masks (set in main)


# ----------------------------------------------------------------------------- helpers
def sh(cmd, cwd=None):
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, cwd=cwd)
    if r.returncode:
        sys.exit("ffmpeg failed:\n" + " ".join(cmd) + "\n" + r.stderr[-3000:])


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height:stream_side_data=rotation", "-of", "json", path],
                         capture_output=True, text=True, check=True).stdout
    st = json.loads(out)["streams"][0]
    w, h = st["width"], st["height"]
    rot = 0
    for sd in st.get("side_data_list", []) or []:
        rot = abs(int(sd.get("rotation", 0)))
    return (h, w) if rot in (90, 270) else (w, h)


def find_clip(src, name):
    if os.path.isfile(name):
        return name
    hits = [p for p in glob.glob(os.path.join(src, name + ".*")) if not p.endswith((".json", ".txt"))]
    if not hits:
        sys.exit(f"clip '{name}' not found in {src}")
    return hits[0]


_measure_cache = {}


def text_w(font, text, size, spacing=0):
    """Rendered width in px of text in one of our fonts (for auto-fitting big lockup words)."""
    from fontTools.ttLib import TTFont
    if font not in _measure_cache:
        f = TTFont(os.path.join(FONTS, FONT_FILES[font]))
        _measure_cache[font] = (f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm)
    cmap, hmtx, upm = _measure_cache[font]
    adv = sum(hmtx[cmap.get(ord(c), cmap.get(ord("n")))][0] for c in text)
    return adv * size / upm + spacing * max(len(text) - 1, 0)


_fm = {}


def font_metrics(font):
    """How libass sizes a font: (em px per ASS \\fs unit, descent per \\fs, ascent per \\fs).
    libass maps \\fs to usWinAscent+usWinDescent, so the em is smaller than \\fs (Inter Tight: 0.70)."""
    if font not in _fm:
        from fontTools.ttLib import TTFont
        f = TTFont(os.path.join(FONTS, FONT_FILES[font]))
        os2 = f["OS/2"].usWinAscent + f["OS/2"].usWinDescent
        _fm[font] = (f["head"].unitsPerEm / os2, -f["hhea"].descent / os2, f["hhea"].ascent / os2)
    return _fm[font]


def fs_of(font, em):
    """ASS \\fs that renders `font` at an em size of `em` px (design-tool font size)."""
    return em / font_metrics(font)[0]


def faces_x(path, t, n=1):
    """Horizontal centres (0..1) of the n largest faces at time t, left to right. [] if none."""
    import cv2
    w, h = probe(path)
    sw, shh = 640, int(640 * h / w) // 2 * 2
    hw = ["-hwaccel", os.environ["PODCAST_HWDEC"]] if os.environ.get("PODCAST_HWDEC") else []
    p = subprocess.run(["ffmpeg", "-v", "error", *hw, "-ss", f"{t:.2f}", "-i", path, "-frames:v", "1",
                        "-vf", f"scale={sw}:{shh}", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                       capture_output=True)
    if len(p.stdout) != sw * shh:
        return []
    img = np.frombuffer(p.stdout, np.uint8).reshape(shh, sw)
    casc = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml"))
    faces = list(casc.detectMultiScale(img, 1.1, 5, minSize=(sw // 25, sw // 25)))
    prof = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, "haarcascade_profileface.xml"))
    faces += list(prof.detectMultiScale(img, 1.1, 5, minSize=(sw // 25, sw // 25)))
    faces += [(sw - x - fw, y, fw, fh) for x, y, fw, fh in prof.detectMultiScale(img[:, ::-1].copy(), 1.1, 5, minSize=(sw // 25, sw // 25))]
    if not faces:
        return []
    faces.sort(key=lambda f: -f[2] * f[3])
    picked = []
    for f in faces:  # drop overlapping detections of the same face
        cx = (f[0] + f[2] / 2) / sw
        if all(abs(cx - q) > 0.08 for q in picked):
            picked.append(cx)
        if len(picked) == n:
            break
    return sorted(picked)


_sides = {}


def face_sides(path):
    """Left / right person x-centres for a static two-person camera, measured once per file (median of 7 looks)."""
    if path not in _sides:
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                                   capture_output=True, text=True).stdout.strip() or 10)
        ls, rs = [], []
        for t in np.linspace(dur * 0.1, dur * 0.9, 7):
            xs = faces_x(path, t, 2)
            if len(xs) == 2:
                ls.append(xs[0]); rs.append(xs[1])
        _sides[path] = (float(np.median(ls)), float(np.median(rs))) if ls else (0.3, 0.7)
    return _sides[path]


TXDIR = None
_tracks = {}


def face_track(path, step=8.0):
    """Static wide camera, people who lean and turn: left/right face x-centres sampled every `step` s over the whole
    file (cached in <tx>/<clip>_faces.json). Returns sorted [(t, left_x|None, right_x|None)]."""
    if path in _tracks:
        return _tracks[path]
    name = os.path.splitext(os.path.basename(path))[0]
    cache = os.path.join(TXDIR or tempfile.gettempdir(), name + "_faces.json")
    if os.path.exists(cache):
        _tracks[path] = json.load(open(cache))
        return _tracks[path]
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                               capture_output=True, text=True).stdout.strip() or 10)
    tr = []
    for t in np.arange(1.0, dur - 1, step):
        xs = faces_x(path, float(t), 3)
        l = [x for x in xs if x < 0.56]; r = [x for x in xs if x >= 0.56]
        tr.append((float(t), l[-1] if l else None, r[0] if r else None))
        print(f"  faces {t:.0f}/{dur:.0f}s", end="\r", flush=True)
    json.dump(tr, open(cache, "w"))
    _tracks[path] = tr
    return tr


def tracked_x(path, t0, t1, side):
    """Median face x of `side` near [t0, t1] from the track; falls back to the file-wide median."""
    tr = face_track(path)
    k = 1 if side == "left" else 2
    allv = [p[k] for p in tr if p[k] is not None]
    if not allv:
        return 0.3 if side == "left" else 0.75
    near = [p[k] for p in tr if p[k] is not None and t0 - 4 <= p[0] <= t1 + 4]
    return float(np.median(near if near else allv))


# ----------------------------------------------------------------------------- v4: heads + full-person framing guard
# One locked-off two-person wide (left = "L", right = "R"). Body boxes are offsets from the head centre x (frame
# fractions): "sh" head-and-shoulders, "reach" incl. gesturing hands; "knee" = (x, below y) of knees that poke into
# low crops. Override per show with spec "people".
PEOPLE = {
    "L": {"x": 0.30, "top": 0.09, "sh": (-0.155, 0.08), "reach": (-0.155, 0.17), "knee": (0.58, 0.64)},  # back + shoulder fully in (review 2026-11-09)
    "R": {"x": 0.79, "top": 0.10, "sh": (-0.08, 0.10), "reach": (-0.15, 0.10), "knee": (0.61, 0.60)},
}
# things to keep out of a crop when it is possible without breaking the person rules (desk monitor with client data)
AVOID = [(0.565, 0.29, 0.70, 0.48)]


_rot = {}


def rotation(path):
    if path not in _rot:
        _rot[path] = _rotation(path)
    return _rot[path]


def _rotation(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream_side_data=rotation",
                          "-of", "csv=p=0", path], capture_output=True, text=True).stdout
    m = re.findall(r"-?\d+", out)
    return int(m[0]) % 360 if m else 0


def detect_heads(img):
    """Head centre x, head top y (0-1) of the two people in a 480x270 RGB still of the wide: dark hair on the left
    against the light wall, blonde hair / skin on the right above the desk monitor. {"L": (x, top), "R": (x, top)}."""
    H_, W_ = img.shape[:2]
    f = img.astype(np.float32) / 255
    mx = f.max(2); mn = f.min(2); s = (mx - mn) / np.maximum(mx, 1e-3)
    res = {}
    for side, mask, (x0, x1, y1) in (("L", mx < 0.30, (0.03, 0.57, 0.55)),
                                     ("R", ((s > 0.17) & (mx > 0.35)) | (mx < 0.40), (0.585, 0.925, 0.285))):
        m = np.zeros_like(mask)
        m[:int(y1 * H_), int(x0 * W_):int(x1 * W_)] = mask[:int(y1 * H_), int(x0 * W_):int(x1 * W_)]
        if side == "L":
            m[int(0.19 * H_):, int(0.40 * W_):int(0.52 * W_)] = False  # desk lamp
        rows = m.sum(1)
        r = [y for y in np.nonzero(rows >= 4)[0] if y + 2 < H_ and rows[y + 1] >= 4 and rows[y + 2] >= 4]
        if r:
            xs = np.nonzero(m[r[0]:r[0] + int(0.10 * H_)])[1]
            res[side] = (float(xs.mean() / W_), float(r[0] / H_))
    return res


_heads = {}


def head_samples(path, times):
    """detect_heads() at the keyframes nearest `times` (2 s grid), cached in <work>/_cache/<clip>_heads.json."""
    name = os.path.splitext(os.path.basename(path))[0]
    cp = os.path.join(CACHE or tempfile.gettempdir(), name + "_heads.json")
    if path not in _heads:
        _heads[path] = json.load(open(cp)) if os.path.exists(cp) else {}
    db = _heads[path]
    grid = sorted({f"{max(0.0, round(t / 2) * 2):.0f}" for t in times})
    todo = [g for g in grid if g not in db]
    if todo:
        rot = rotation(path)
        flip = {180: ",hflip,vflip", 90: ",transpose=2", 270: ",transpose=1"}.get(rot, "")

        def one(g):
            hw = os.environ.get("PODCAST_HWDEC") == "cuda"
            vf = (f"scale_cuda=480:270,hwdownload,format=nv12{flip},format=rgb24" if hw else "scale=480:270,format=rgb24")
            if hw and rot in (90, 270):
                vf = f"scale_cuda=270:480,hwdownload,format=nv12{flip},format=rgb24"
            cmd = ["ffmpeg", "-v", "error", *(["-hwaccel", "cuda", "-hwaccel_output_format", "cuda"] if hw else []),
                   "-skip_frame", "nokey", "-ss", g, "-i", path, "-frames:v", "1", "-vf", vf, "-f", "rawvideo", "-"]
            p = subprocess.run(cmd, capture_output=True)
            if len(p.stdout) < 480 * 270 * 3:
                return g, {}
            return g, detect_heads(np.frombuffer(p.stdout[:480 * 270 * 3], np.uint8).reshape(270, 480, 3))
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(4) as ex:
            for g, r in ex.map(one, todo):
                db[g] = r
        os.makedirs(os.path.dirname(cp), exist_ok=True)
        try:
            json.dump(db, open(cp + ".tmp", "w")); os.replace(cp + ".tmp", cp)
        except OSError:
            pass
    return [db[g] for g in grid if g in db]


def people_near(path, t0, t1, spec=None):
    """Both people around source window [t0, t1]: {"L"|"R": {"x", "xmin", "xmax", "top"}} from head samples (2 s grid,
    plus the face track), falling back to the show defaults."""
    P = {**PEOPLE, **((spec or {}).get("people") or {})}
    ts_ = [t0 + 0.3, (t0 + t1) / 2, t1 - 0.3] + list(np.arange(t0 + 2, t1 - 1, 4.0))
    smp = head_samples(path, ts_)
    out = {}
    for k, side in (("L", 1), ("R", 2)):
        xs = [s_[k][0] for s_ in smp if k in s_]
        tops = [s_[k][1] for s_ in smp if k in s_]
        try:
            xs += [p[side] for p in face_track(path) if p[side] is not None and t0 - 3 <= p[0] <= t1 + 3]
        except Exception:
            pass
        d = P[k]
        if xs:
            out[k] = {"x": float(np.median(xs)), "xmin": float(min(xs)), "xmax": float(max(xs)),
                      # the detector finds the dense part of the hair: curly / blonde wisps sit ~0.03 / 0.015 higher
                      "top": max(0.0, min(tops) - (0.03 if k == "L" else 0.015)) if tops else d["top"] - 0.02}
        else:
            out[k] = {"x": d["x"], "xmin": d["x"] - 0.04, "xmax": d["x"] + 0.06, "top": d["top"] - 0.02}
        out[k]["cfg"] = d
    out["avoid"] = [tuple(b) for b in (spec or {}).get("avoid", AVOID)]
    return out


def guard_rect(sw, sh_, aspect, z, cx, cy, subj, ppl, hr=0.07, zmax=2.3, box="sh", m=0.015, g=0.02):
    """Full-person framing guard. Smallest change of (zoom, cx, cy) so that the subject's head-and-shoulders box sits
    inside the crop with `hr` headroom above the head top, and the other person is either fully outside (reach box,
    knees for low crops) or fully inside. Returns (zoom, cx, cy, note)."""
    bw = min(1.0, aspect * sh_ / sw); bh = min(1.0, sw / (aspect * sh_))
    o = "R" if subj == "L" else "L"
    S, O = ppl[subj], ppl[o]
    sl = S["xmin"] + S["cfg"][box][0]; sr = S["xmax"] + S["cfg"][box][1]
    ol = O["xmin"] + O["cfg"]["reach"][0]; orr = O["xmax"] + O["cfg"]["reach"][1]
    right = O["x"] > S["x"]
    avoid = ppl.get("avoid", AVOID)

    def fit(zz):
        w, h = bw / zz, bh / zz
        y0 = min(max(cy - h / 2, 0), 1 - h)
        y0 = max(0.0, min(y0, S["top"] - hr * h))
        y1 = y0 + h
        kx, ky = O["cfg"]["knee"]
        lo, hi = max(sr + m - w, 0.0), min(sl - m, 1 - w)
        if right:
            hi = min(hi, min(ol, kx if y1 > ky else 9) - g - w)
        else:
            lo = max(lo, max(orr, kx if y1 > ky else -9) + g)
        if lo <= hi:
            for ax0, ay0, ax1, ay1 in avoid:  # soft: only when the person rules still hold
                if ay1 > y0 and ay0 < y1:
                    if ax0 > S["x"] and lo <= min(hi, ax0 - 0.01 - w):
                        hi = min(hi, ax0 - 0.01 - w)
                    elif ax1 < S["x"] and max(lo, ax1 + 0.01) <= hi:
                        lo = max(lo, ax1 + 0.01)
            x0 = min(max(cx - w / 2, lo), hi)
            return x0 + w / 2, y0 + h / 2
        return None
    cands = sorted(set([z] + [round(z + 0.02 * k, 3) for k in range(1, 80) if z + 0.02 * k <= zmax] +
                       [round(z - 0.02 * k, 3) for k in range(1, 80) if z - 0.02 * k >= 1.0]), key=lambda q: (abs(q - z), -q))
    for zz in cands:
        r = fit(zz)
        if r:
            note = ""
            if abs(zz - z) > 0.004 or abs(r[0] - cx) > 0.004 or abs(r[1] - cy) > 0.004:
                note = f"guard {subj}: zoom {z:.2f}->{zz:.2f} cx {cx:.3f}->{r[0]:.3f} cy {cy:.3f}->{r[1]:.3f}"
            return zz, r[0], r[1], note
    # cannot isolate the subject: show both people completely (wide)
    return 1.0, 0.5, 0.5, f"guard {subj}: no clean single at zoom <= {zmax}: wide two-shot"


def resolve_cx(seg, path, which="cx"):
    v = seg.get(which, "auto")
    if isinstance(v, (int, float)):
        return float(v)
    if v in ("left", "right") and seg.get("_static", True):
        x = tracked_x(path, seg["start"], seg["end"], v)
        # lead room: people face each other, so shift the crop toward where they look (Nizam looks right, Carrie left)
        return x + (0.035 if v == "left" else -0.03)
    mid = (seg["start"] + seg["end"]) / 2
    if v == "auto":
        xs = [x for t in (seg["start"] + 0.3, mid, seg["end"] - 0.3) for x in faces_x(path, t, 1)]
        return float(np.median(xs)) if xs else 0.5
    if v in ("left", "right"):
        xs = faces_x(path, mid, 2)
        if len(xs) == 2:
            return xs[0] if v == "left" else xs[1]
        return 0.3 if v == "left" else 0.7
    return 0.5


def crop_expr(sw, sh_, aspect, zoom, cx, cy):
    """ffmpeg crop=w:h:x:y for a region of `aspect` (w/h), zoomed, centred on cx, cy (0..1)."""
    if sw / sh_ > aspect:
        cw, ch = sh_ * aspect, sh_
    else:
        cw, ch = sw, sw / aspect
    cw, ch = int(cw / zoom) // 2 * 2, int(ch / zoom) // 2 * 2
    x = int(min(max(cx * sw - cw / 2, 0), sw - cw))
    y = int(min(max(cy * sh_ - ch / 2, 0), sh_ - ch))
    return f"crop={cw}:{ch}:{x}:{y}"


LOOKS = {
    "bw": "hue=s=0,eq=contrast=1.12:brightness=-0.02",
    "dim": "eq=brightness=-0.08:saturation=0.85",
    "warm": "colorbalance=rs=0.04:gs=0.01:bs=-0.04:rm=0.03:bm=-0.03,eq=saturation=1.05",
    "teal": "colorbalance=rs=-0.05:bs=0.06:rh=0.04:bh=-0.03,eq=saturation=1.08",
}


# ----------------------------------------------------------------------------- v4: framed split-screen
PANEL_W, PANEL_H, PANEL_R, PANEL_Y, PANEL_X = 840, 780, 24, 80, (80, 1000)


def glog(out, msg):
    if msg:
        print("  " + msg)
        try:
            open(os.path.join(os.path.dirname(out), "guard.log"), "a", encoding="utf-8").write(
                f"{os.path.basename(out)}: {msg}\n")
        except OSError:
            pass


def guard_on(seg, spec, W, H):
    return W > H and spec.get("guard", True) is not False and seg.get("guard", True) is not False


def subject_of(seg, cx, ppl):
    v = seg.get("cx")
    if v in ("left", "right"):
        return "L" if v == "left" else "R"
    return "L" if abs(cx - ppl["L"]["x"]) <= abs(cx - ppl["R"]["x"]) else "R"


def panel_crop(seg, spec, path, sw, sh_, vseg, who, out, guard=True):
    """crop=... for a talker panel (840x780): the whole person (head with ~8 % headroom, shoulders, hands), nobody
    else. who = "L" / "R"."""
    ppl = people_near(path, vseg["start"], vseg["end"], spec)
    a = PANEL_W / PANEL_H
    z = float(seg.get("pzoom", 1.62))
    h = 1 / z
    P = ppl[who]
    rch = P["cfg"]["reach"]
    cx = float(seg["pcx"]) if isinstance(seg.get("pcx"), (int, float)) else P["x"] + (rch[0] + rch[1]) / 2
    cy = float(seg["pcy"]) if isinstance(seg.get("pcy"), (int, float)) else P["top"] - 0.08 * h + h / 2
    if guard:
        z, cx, cy, note = guard_rect(sw, sh_, a, z, cx, cy, who, ppl, hr=0.075, zmax=2.0, box="reach")
        glog(out, note and f"panel {note}")
    return crop_expr(sw, sh_, a, z, cx, cy)


def panel_assets(w, h, r):
    """Anti-aliased rounded-corner alpha mask + soft drop shadow (PNG, cached)."""
    from PIL import Image, ImageDraw, ImageFilter
    d = CACHE or tempfile.gettempdir(); os.makedirs(d, exist_ok=True)
    mp = os.path.join(d, f"mask_{w}x{h}_r{r}.png"); sp = os.path.join(d, f"shadow_{w}x{h}_r{r}.png")
    if not os.path.exists(mp):
        k = 4
        im = Image.new("L", (w * k, h * k), 0)
        ImageDraw.Draw(im).rounded_rectangle([0, 0, w * k - 1, h * k - 1], r * k, fill=255)
        im.resize((w, h), Image.LANCZOS).save(mp)
    if not os.path.exists(sp):
        pad = 90
        a = Image.new("L", (w + 2 * pad, h + 2 * pad), 0)
        ImageDraw.Draw(a).rounded_rectangle([pad, pad + 20, pad + w, pad + h + 20], r, fill=int(255 * 0.28))
        a = a.filter(ImageFilter.GaussianBlur(25))  # css 0 20 50 rgba(0,0,0,.28)
        rgba = Image.new("RGBA", a.size, (0, 0, 0, 255)); rgba.putalpha(a); rgba.save(sp)
    return mp, sp, 90


TV709 = "scale=out_range=tv:out_color_matrix=bt709,format=yuv420p,setparams=range=tv:colorspace=bt709:color_primaries=bt709:color_trc=bt709"


def hold(d):
    """A still decoded and processed ONCE, repeated in memory for the segment (`-loop 1` re-decodes every frame)."""
    n = max(int(round(d * FPS)) + 2, 1)
    return f"loop=loop={n}:size=1:start=0,setpts=N/({FPS}*TB)"


def fallback_plate(name, w, h):
    """Flat PAPER / TRACK-green grid / INK plate (PNG, cached) when the designer's background is missing."""
    from PIL import Image, ImageDraw
    d = CACHE or tempfile.gettempdir(); os.makedirs(d, exist_ok=True)
    p = os.path.join(d, f"plate_{name}_{w}x{h}.png")
    if not os.path.exists(p):
        col = {"grid": TRACK, "ink": INK}.get(name, PAPER)
        im = Image.new("RGB", (w, h), col)
        if name == "grid":
            dr = ImageDraw.Draw(im)
            for x in range(0, w, 96):
                dr.rectangle([x, 0, x + 1, h], fill=GRIDLINE)
            for y in range(0, h, 96):
                dr.rectangle([0, y, w, y + 1], fill=GRIDLINE)
        im.save(p)
    return p


def bg_file(name, spec):
    if os.path.isfile(name):
        return name
    for d in (spec.get("gfx_dir"), os.path.join(spec.get("_dir", ""), "gfx"), os.path.join(spec.get("_dir", ""), "v4", "gfx"),
              os.path.join(ROOT, "projects", "carrie-ep01", "v4", "gfx")):
        if d:
            p = d if os.path.isabs(d) else os.path.join(ROOT, d)
            p = os.path.join(p, f"bg_{name}.png")
            if os.path.isfile(p):
                return p
    return None


def media_chain(bpath, label, tw, th, d, br, goff, gdur, inputs, look=""):
    """Input + filter chain that fills tw x th with a photo / video (cover crop + slow push), continuing the video time
    and the push across the pieces of one tightened segment (goff / gdur = offset / length of the whole group)."""
    bw, bhh = probe(bpath)
    still = bpath.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
    k = inputs.count("-i")
    if still:
        inputs += ["-i", bpath]  # decoded + scaled once, then held in memory (hold())
    else:
        inputs += ["-stream_loop", "-1", "-ss", f"{float(br.get('at', 0)) + goff:.3f}", "-t", f"{d:.3f}", "-i", bpath]
    push = float(br.get("push", 0.06 if still else 0.03))
    n = max(int(round(gdur * FPS)), 1); o = int(round(goff * FPS))
    zp = (f"zoompan=z='1+{push}*({o}+on)/{n}':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={tw}x{th}:fps={FPS}"
          if push > 0 else f"scale={tw}:{th}")
    return (f"[{k}:v]{crop_expr(bw, bhh, tw / th, 1.0, float(br.get('cx', 0.5)), float(br.get('cy', 0.5)))},"
            f"scale={tw * 2 if push > 0 else tw}:{th * 2 if push > 0 else th}:flags=lanczos:out_range=tv:out_color_matrix=bt709,"
            f"format=yuv420p,{hold(d) if still else f'fps={FPS}'},setsar=1,{zp}{look}[{label}]")


def frame_graph(seg, spec, path, sw, sh_, vseg, d, inputs, lk, W, H, out, tx):
    """layout "frame": talker + panel media in two rounded 840x780 panels on a background plate.
    layout "frame2": both people (left = L, right = R) in the two panels."""
    lay = seg["layout"]
    gd = guard_on(seg, spec, W, H)
    goff, gdur = float(seg.get("_goff", 0.0)), float(seg.get("_gdur", d))
    bgk = seg.get("bg", spec.get("bg", "paper"))
    parts = []
    if bgk == "blur":
        parts.append(f"[0:v]fps={FPS},split=2[src][bgs];[bgs]scale=480:270,gblur=sigma=9,eq=brightness=-0.13:saturation=0.75,"
                     f"scale={W}:{H}:flags=bilinear,setsar=1[bg]")
    else:
        parts.append(f"[0:v]fps={FPS}[src]")
        f = bg_file(bgk, spec) or fallback_plate(bgk, W, H)
        k = inputs.count("-i")
        inputs += ["-i", f]
        parts.append(f"[{k}:v]scale={W}:{H}:force_original_aspect_ratio=increase:out_range=tv:out_color_matrix=bt709,"
                     f"crop={W}:{H},setsar=1,format=yuv420p,{hold(d)}[bg]")
    mp, sp, pad = panel_assets(PANEL_W, PANEL_H, PANEL_R)
    km = inputs.count("-i"); inputs += ["-i", mp]
    shadow = seg.get("shadow", bgk == "paper")  # style guide: drop shadow on paper only
    parts.append(f"[{km}:v]format=gray,{hold(d)},split=2[m0][m1]")
    if shadow:
        ks = inputs.count("-i"); inputs += ["-i", sp]
        parts.append(f"[{ks}:v]format=rgba,{hold(d)},split=2[h0][h1]")
    # who goes where
    if lay == "frame2":
        cl = panel_crop(seg, spec, path, sw, sh_, vseg, "L", out, gd)
        cr = panel_crop(seg, spec, path, sw, sh_, vseg, "R", out, gd)
        parts.append(f"[src]split=2[s0][s1];[s0]{cl},scale={PANEL_W}:{PANEL_H}:flags=lanczos{lk},setsar=1[p0];"
                     f"[s1]{cr},scale={PANEL_W}:{PANEL_H}:flags=lanczos{lk},setsar=1[p1]")
    else:
        who, side = frame_who_side(seg, spec, tx)
        ct = panel_crop(seg, spec, path, sw, sh_, vseg, who, out, gd)
        parts.append(f"[src]{ct},scale={PANEL_W}:{PANEL_H}:flags=lanczos{lk},setsar=1[pt]")
        pn = seg.get("panel") or {}
        pf = pn.get("file")
        if pf:
            bpath = pf if os.path.isfile(pf) else os.path.join(ROOT, pf)
            parts.append(media_chain(bpath, "pm", PANEL_W, PANEL_H, d, pn, goff, gdur, inputs))
        else:
            kc = inputs.count("-i")
            inputs += ["-i", fallback_plate("ink", PANEL_W, PANEL_H)]
            parts.append(f"[{kc}:v]scale=out_range=tv:out_color_matrix=bt709,format=yuv420p,setsar=1,{hold(d)}[pm]")
        a, b = ("pt", "pm") if side == "left" else ("pm", "pt")
        parts.append(f"[{a}]null[p0];[{b}]null[p1]")
    enter = seg.get("enter", True) is not False and goff < 0.01
    T, D = 8 / FPS, 60  # entrance (style guide s4): slide 60 px + fade, 8 f expo-out, second panel 3 f later
    cur = "bg"
    for i, x in enumerate(PANEL_X):
        dl = 3 / FPS * i
        if enter:
            sgn = -1 if i == 0 else 1
            off = f"{sgn * D}*if(lt(t,{dl:.3f}),1,if(lt(t,{dl + T:.3f}),pow(2,-10*(t-{dl:.3f})/{T}),0))"
            fx = f"fade=t=in:st={dl:.3f}:d={T:.3f}:alpha=1,"
            xe, xs_ = f"'{x}+{off}'", f"'{x - pad}+{off}'"
        else:
            fx, xe, xs_ = "", str(x), str(x - pad)
        if shadow:
            parts.append(f"[h{i}]{fx}null[hh{i}];[{cur}][hh{i}]overlay=x={xs_}:y={PANEL_Y - pad}:eval={'frame' if enter else 'init'}[b{i}a]")
        else:
            parts.append(f"[{cur}]null[b{i}a]")
        parts.append(f"[p{i}]format=yuva420p[pa{i}];[pa{i}][m{i}]alphamerge,{fx}null[pq{i}];"
                     f"[b{i}a][pq{i}]overlay=x={xe}:y={PANEL_Y}:eval={'frame' if enter else 'init'}:format=auto[b{i}]")
        cur = f"b{i}"
    return ";".join(parts) + f";[{cur}]null[v]"


import math


class Ex:
    """A tiny expression that renders to ffmpeg expr syntax AND evaluates in Python (camera moves are planned on a
    per-frame Python sample, rendered by ffmpeg with the identical formula)."""
    def __init__(self, s, f):
        self.s, self.f = s, f

    def __call__(self, t):
        return self.f(t)


def K(v):
    return Ex(f"({v:.6f})", lambda t, v=v: v)


def ex_add(a, b): return Ex(f"({a.s}+{b.s})", lambda t: a(t) + b(t))
def ex_sub(a, b): return Ex(f"({a.s}-{b.s})", lambda t: a(t) - b(t))
def ex_mul(a, b): return Ex(f"({a.s}*{b.s})", lambda t: a(t) * b(t))
def ex_div(a, b): return Ex(f"({a.s}/{b.s})", lambda t: a(t) / b(t))
def ex_clip(a, lo, hi): return Ex(f"clip({a.s},{lo.s},{hi.s})", lambda t: min(max(a(t), lo(t)), hi(t)))


def ex_ramp(at, dur, kind="io"):
    """0 -> 1 over [at, at + dur]: "io" sine ease in-out, "out" cubic ease-out (fast in)."""
    p = f"clip((TIME-{at:.4f})/{max(dur, 1e-3):.4f},0,1)"
    pf = lambda t: min(max((t - at) / max(dur, 1e-3), 0.0), 1.0)
    if kind == "out":
        return Ex(f"(1-pow(1-{p},3))", lambda t: 1 - (1 - pf(t)) ** 3)
    return Ex(f"(0.5-0.5*cos(PI*{p}))", lambda t: 0.5 - 0.5 * math.cos(math.pi * pf(t)))


def ex_lerp(a, b, e):  # a + (b - a) * e   (a, b numbers)
    return K(a) if abs(b - a) < 1e-9 else ex_add(K(a), ex_mul(K(b - a), e))


def camera_graph(seg, spec, path, sw, sh_, vs, d, z, cx, cy, lk, W, H, out):
    """v4 virtual camera on a talking-head segment: slow push / pull ("cam" move push|pull), punch-ins on words
    ("punch"), a pan to the other person ("cam" move pan) and an optional handheld "drift". (z, cx, cy) is the guarded
    base framing; the extremes of the move are re-checked against the full-person guard and clamped (logged).
    Render: crop the union of all crops from the 4K source, scale it so the base crop is ~2x the output, then zoompan
    (integer steps there = 1/2 output pixel: no visible stepping)."""
    cam = dict(seg.get("cam") or {})
    gd = guard_on(seg, spec, W, H)
    ppl = people_near(path, vs, vs + d, spec)
    subj = subject_of(seg, cx, ppl)
    a = W / H
    bw = min(1.0, a * sh_ / sw); bh = min(1.0, sw / (a * sh_))
    ar = bh / bw  # crop height / width in normalised units
    S = ppl[subj]
    A = (cx - bw / z / 2, cy - bh / z / 2, bw / z)
    anc = (S["x"], S["top"])  # zoom about the head top: headroom stays the same fraction of the frame
    B, ancB, pan = A, anc, K(0)
    if cam.get("move") == "pan":
        tc = cam.get("to_cx", "right" if subj == "L" else "left")
        tsub = ("L" if tc == "left" else "R") if tc in ("left", "right") else \
            ("L" if abs(float(tc) - ppl["L"]["x"]) < abs(float(tc) - ppl["R"]["x"]) else "R")
        tz = float(cam.get("to_zoom", z))
        tcx = float(tc) if isinstance(tc, (int, float)) else ppl[tsub]["x"] + (0.035 if tsub == "L" else -0.03)
        tcy = float(cam.get("to_cy", cy))
        if gd and tz > 1:
            tz, tcx, tcy, note = guard_rect(sw, sh_, a, tz, tcx, tcy, tsub, ppl)
            glog(out, note and "pan target " + note)
        B = (tcx - bw / tz / 2, tcy - bh / tz / 2, bw / tz)
        ancB = (ppl[tsub]["x"], ppl[tsub]["top"])
        pan = ex_ramp(float(cam.get("at", 0.0)), float(cam.get("dur", 0.6)))
    # zoom factor M(t) relative to the base framing
    terms = []
    if cam.get("move") in ("push", "pull"):
        f0 = float(cam.get("from", 1.0)); f1 = float(cam.get("to", 1.08 if cam["move"] == "push" else 0.93))
        at = float(cam.get("at", 0.0))
        terms.append((f0, f1, ex_lerp(f0, f1, ex_ramp(at, float(cam.get("dur", max(d - at, 0.1)))))))
    for pu in seg.get("punch", []) or []:
        at = float(pu["at"]); du = float(pu.get("dur", 0.25)); to = float(pu.get("to", 1.15))
        e = ex_ramp(at, du, "out")
        if pu.get("hold") is not None:
            he = at + du + float(pu["hold"])
            e = ex_mul(e, ex_sub(K(1), ex_ramp(he, du)))
        terms.append((1.0, to, ex_lerp(1.0, to, e)))
    M = K(1)
    for _, _, e in terms:
        M = ex_mul(M, e)
    hi = 1.0
    for f0, f1, _ in terms:
        hi *= max(f0, f1)
    lo = min([1.0] + [min(f0, f1) for f0, f1, _ in terms])
    if gd and terms:  # the tightest crop keeps the shoulders, the widest keeps the other person out
        sl = S["xmin"] + S["cfg"]["sh"][0]; sr = S["xmax"] + S["cfg"]["sh"][1]
        cap_hi = min(A[2], B[2]) / ((sr - sl) + 0.03)
        cap_lo = lo
        if lo < 1.0:
            gz, _, _, _ = guard_rect(sw, sh_, a, z * lo, cx, cy, subj, ppl)
            cap_lo = max(lo, gz / z)
        if hi > cap_hi or cap_lo > lo:
            glog(out, f"cam: zoom range x{lo:.3f}-x{hi:.3f} clamped to x{cap_lo:.3f}-x{min(hi, cap_hi):.3f} (guard)")
            M = ex_clip(M, K(cap_lo), K(max(min(hi, cap_hi), cap_lo)))
    dr = float(seg.get("drift", 0) or 0)
    if dr:  # handheld: two slow sines per axis, plus a little zoom so the drift never reaches an edge of the frame
        M = ex_mul(M, K(1 + 3 * dr * z))
        dxe = Ex(f"{dr:.5f}*(sin(2*PI*TIME/6.7+0.7)+0.5*sin(2*PI*TIME/2.9+1.9))",
                 lambda t: dr * (math.sin(2 * math.pi * t / 6.7 + 0.7) + 0.5 * math.sin(2 * math.pi * t / 2.9 + 1.9)))
        dye = Ex(f"{dr * 0.7:.5f}*(sin(2*PI*TIME/5.3+2.1)+0.5*sin(2*PI*TIME/3.7+0.4))",
                 lambda t: 0.7 * dr * (math.sin(2 * math.pi * t / 5.3 + 2.1) + 0.5 * math.sin(2 * math.pi * t / 3.7 + 0.4)))
    else:
        dxe = dye = K(0)
    bwid = ex_lerp(A[2], B[2], pan)  # base crop width (pan interpolates base rects and anchors)
    wn = ex_div(bwid, M)
    hn = ex_mul(wn, K(ar))
    ax = ex_lerp(anc[0], ancB[0], pan); ay = ex_lerp(anc[1], ancB[1], pan)
    bx = ex_lerp(A[0], B[0], pan); by = ex_lerp(A[1], B[1], pan)
    xn = ex_clip(ex_add(ex_sub(ax, ex_mul(ex_sub(ax, bx), ex_div(wn, bwid))), dxe), K(0), ex_sub(K(1), wn))
    yn = ex_clip(ex_add(ex_sub(ay, ex_mul(ex_sub(ay, by), ex_div(wn, bwid))), dye), K(0), ex_sub(K(1), hn))
    # union of every crop of the move (per-frame sample), widened to the output aspect
    tsm = [k / FPS for k in range(int(d * FPS) + 2)]
    x0 = min(xn(t) for t in tsm); y0 = min(yn(t) for t in tsm)
    x1 = max(xn(t) + wn(t) for t in tsm); y1 = max(yn(t) + hn(t) for t in tsm)
    uw = max(x1 - x0, (y1 - y0) / ar); uh = uw * ar
    if uh > 1:
        uh = 1.0; uw = uh / ar
    ux = min(max((x0 + x1) / 2 - uw / 2, 0), 1 - uw); uy = min(max((y0 + y1) / 2 - uh / 2, 0), 1 - uh)
    ss = float(os.environ.get("PODCAST_CAM_SS", 1.5))  # supersampling of the base crop (zoompan integer steps = 1/ss px)
    upx = int(min(ss * W * uw / min(A[2], B[2]), 2 * sw * uw, 3840)) // 2 * 2
    uph = int(round(upx * uh * sh_ / (uw * sw))) // 2 * 2
    cw_, ch_ = int(uw * sw) // 2 * 2, int(uh * sh_) // 2 * 2
    cx_, cy_ = int(ux * sw), int(uy * sh_)
    rx = lambda e: e.s.replace("TIME", "it")
    zx = f"{uw:.6f}/{rx(wn)}"
    xx = f"iw*({rx(xn)}-{ux:.6f})/{uw:.6f}"
    yy = f"ih*({rx(yn)}-{uy:.6f})/{uh:.6f}"
    return (f"[0:v]fps={FPS},crop={cw_}:{ch_}:{cx_}:{cy_},scale={upx}:{uph}:flags=bicubic,"
            f"zoompan=z='{zx}':x='{xx}':y='{yy}':d=1:s={W}x{H}:fps={FPS}{lk}[v]")


# ----------------------------------------------------------------------------- cutting
def cut_segment(seg, spec, src, tx_src, out, W, H, enc):
    if seg.get("card"):
        return cut_card(seg, out, W, H, enc)
    path = find_clip(src, seg["clip"])
    sw, sh_ = probe(path)
    d = seg["end"] - seg["start"]
    layout = seg.get("layout", spec.get("layout", "full"))
    z = float(seg.get("zoom", 1.0))
    cy = float(seg.get("cy", 0.42 if z > 1 else 0.5))
    look = seg.get("look", spec.get("look"))
    lk = ("," + LOOKS[look]) if look else ""
    # multicam: segment times are on the MASTER timeline; each camera is shifted by its sync delay
    sync = spec.get("sync", {})
    vs = seg["start"] - float(sync.get(seg["clip"], 0.0))
    vseg = {**seg, "start": vs, "end": vs + d}
    hw = ["-hwaccel", os.environ["PODCAST_HWDEC"]] if os.environ.get("PODCAST_HWDEC") else []  # e.g. cuda: GPU-decode 4K HEVC
    inputs = [*hw, "-ss", f"{vs:.3f}", "-t", f"{d:.3f}", "-i", path]

    br = seg.get("broll")
    goff, gdur = float(seg.get("_goff", 0.0)), float(seg.get("_gdur", d))  # position inside a tightened group
    if layout in ("frame", "frame2") and W > H:
        fc = frame_graph(seg, spec, path, sw, sh_, vseg, d, inputs, lk, W, H, out, tx_src)
    elif br:  # B-roll over the speaker's voice: picture from the B-roll file, audio (and captions) from the clip
        bpath = br["file"] if os.path.isfile(br["file"]) else os.path.join(ROOT, br["file"])
        bw, bhh = probe(bpath)
        still = bpath.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
        if still:
            inputs += ["-i", bpath]
        else:  # video B-roll continues across the jump cuts of its segment (goff)
            inputs += ["-stream_loop", "-1", "-ss", f"{float(br.get('at', 0)) + goff:.3f}", "-t", f"{d:.3f}", "-i", bpath]
        panel = br.get("panel")  # "top": card/B-roll in the top half, the talker cropped in the bottom half
        side = panel in ("left", "right") and W > H  # 16:9 side card: card on that side, talker on the other
        if side:
            tw, th = int(W * float(br.get("frac", 0.42))) // 2 * 2, H
        else:
            tw, th = (W, int(W * 9 / 16) // 2 * 2) if (layout == "letterbox" and H > W) else (W, H // 2) if panel else (W, H)
        push = float(br.get("push", 0.06 if still else 0.03))  # slow push-in (Ken Burns); 0 = static
        n = max(int(round(gdur * FPS)), 1); o_ = int(round(goff * FPS))
        zp = (f"zoompan=z='1+{push}*({o_}+on)/{n}':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={tw}x{th}:fps={FPS}"
              if push > 0 else f"scale={tw}:{th}")
        fc = (f"[1:v]{crop_expr(bw, bhh, tw / th, 1.0, float(br.get('cx', 0.5)), float(br.get('cy', 0.5)))},"
              f"scale={tw * 2 if push > 0 else tw}:{th * 2 if push > 0 else th}:flags=lanczos:out_range=tv:out_color_matrix=bt709,"
              f"format=yuv420p,{hold(d) if still else f'fps={FPS}'},{zp}{lk if not panel else ''}")
        if side:
            rw = W - tw
            cx = resolve_cx(vseg, path) if not isinstance(seg.get("cx"), (int, float)) else float(seg["cx"])
            order = "[c][p]" if panel == "left" else "[p][c]"
            fc += (f"[c];[0:v]{crop_expr(sw, sh_, rw / H, max(z, 1.0), cx, cy)},scale={rw}:{H}:flags=lanczos{lk}[p];"
                   f"{order}hstack,drawbox=x={tw - 3 if panel == 'left' else rw - 3}:y=0:w=6:h=ih:color={spec.get('accent', '#FFB238').replace('#', '0x')}@1:t=fill")
        elif panel:
            hh = H - th
            cx = resolve_cx(vseg, path) if "cx" not in seg or not isinstance(seg.get("cx"), (int, float)) else float(seg["cx"])
            fc += (f"[t];[0:v]{crop_expr(sw, sh_, W / hh, max(z, 1.0), cx, float(seg.get('cy', 0.40)))},scale={W}:{hh}:flags=lanczos{lk}[b];"
                   f"[t][b]vstack,drawbox=x=0:y={th - 3}:w=iw:h=6:color={spec.get('accent', '#FFB238').replace('#', '0x')}@1:t=fill")
        elif (tw, th) != (W, H):
            fc += f",pad={W}:{H}:0:(oh-ih)/2:black"
        fc += "[v]"
    elif layout == "sbs" and W > H:  # side-by-side split: left person | right person (one wide camera)
        hw = W // 2
        cl = resolve_cx({**vseg, "cx": "left"}, path) if not isinstance(seg.get("cxl"), (int, float)) else seg["cxl"]
        cr = resolve_cx({**vseg, "cx": "right"}, path) if not isinstance(seg.get("cxr"), (int, float)) else seg["cxr"]
        zz = max(z, 1.0)
        fc = (f"[0:v]split[a][b];[a]{crop_expr(sw, sh_, hw / H, zz, cl, cy)},scale={hw}:{H}:flags=lanczos{lk}[l];"
              f"[b]{crop_expr(sw, sh_, hw / H, float(seg.get('zoom_r', zz)), cr, cy)},scale={hw}:{H}:flags=lanczos{lk}[r];"
              f"[l][r]hstack,drawbox=x={hw - 3}:y=0:w=6:h=ih:color={spec.get('accent', '#FFB238').replace('#', '0x')}@1:t=fill[v]")
    elif layout == "full" or W > H:  # long-form is always full frame
        cx = resolve_cx(vseg, path) if (z > 1 or sw / sh_ > W / H + 0.05) else 0.5
        cam = seg.get("cam") or seg.get("punch") or seg.get("drift")
        if guard_on(seg, spec, W, H) and z > 1.0:  # full-person framing guard (v4)
            ppl = people_near(path, vs, vs + d, spec)
            subj = subject_of(seg, cx, ppl)
            z, cx, cy, note = guard_rect(sw, sh_, W / H, z, cx, cy, subj, ppl, zmax=float(seg.get("zmax", spec.get("zmax", 2.3))))
            glog(out, note)
        if cam and W > H:  # v4 virtual camera: time-varying sub-pixel crop on the 4K source
            fc = camera_graph(seg, spec, path, sw, sh_, vs, d, z, cx, cy, lk, W, H, out)
        else:
            fc = f"[0:v]{crop_expr(sw, sh_, W / H, z, cx, cy)},scale={W}:{H}:flags=lanczos{lk}[v]"
    elif layout in ("letterbox", "band"):
        bh = int(W * 9 / 16) // 2 * 2
        cx = resolve_cx(vseg, path) if z > 1 else 0.5
        band = f"{crop_expr(sw, sh_, 16 / 9, z, cx, cy)},scale={W}:{bh}:flags=lanczos{lk}"
        if layout == "letterbox":
            fc = f"[0:v]{band},pad={W}:{H}:0:(oh-ih)/2:black"
            if seg.get("open"):  # band opens from a thin strip (ig-style reveal): two black bars slide apart
                top = f"({(H - bh) // 2}+{bh // 2 - 40}*pow(max(0,1-t/0.45),2))"
                fc += (f"[pb];color=black:s={W}x{H}:r={FPS}:d={d:.3f}[k1];color=black:s={W}x{H}:r={FPS}:d={d:.3f}[k2];"
                       f"[pb][k1]overlay=0:'{top}-H':eval=frame:shortest=1[pc];[pc][k2]overlay=0:'H-{top}':eval=frame:shortest=1")
            fc = fc + "[v]"
        else:
            fc = (f"[0:v]split[a][b];[a]{crop_expr(sw, sh_, W / H, 1.0, 0.5, 0.5)},scale={W // 4}:{H // 4},"
                  f"gblur=sigma=12,eq=brightness=-0.10:saturation=0.9{lk},scale={W}:{H}[bg];"
                  f"[b]{band}[fg];[bg][fg]overlay=0:(H-h)/2[v]")
    elif layout == "split":  # two speakers stacked; top = clip2 (or same clip, other face)
        c2 = seg.get("clip2", seg["clip"])
        p2 = find_clip(src, c2)
        s2 = seg.get("start2", seg["start"] - float(sync.get(c2, 0.0)))
        same = p2 == path
        cx1 = resolve_cx(vseg, path, "cx") if not same else resolve_cx({**vseg, "cx": seg.get("cx", "right")}, path)
        seg2 = {**seg, "start": s2, "end": s2 + d, "cx": seg.get("cx2", "left" if same else "auto")}
        cx2 = resolve_cx(seg2, p2, "cx")
        w2, h2 = probe(p2)
        inputs += ["-ss", f"{s2:.3f}", "-t", f"{d:.3f}", "-i", p2]
        hh = H // 2
        fc = (f"[1:v]{crop_expr(w2, h2, W / hh, z, cx2, cy)},scale={W}:{hh}:flags=lanczos{lk}[t];"
              f"[0:v]{crop_expr(sw, sh_, W / hh, z, cx1, cy)},scale={W}:{hh}:flags=lanczos{lk}[b];"
              f"[t][b]vstack,drawbox=x=0:y={hh - 2}:w=iw:h=4:color=black@0.9:t=fill[v]")
    else:
        sys.exit(f"unknown layout {layout}")
    # exact length: every part is N whole frames and its audio exactly N/FPS s, so hundreds of cuts never drift
    if fc.count("[0:v]") == 1 and rotation(path) == 180 and inputs[inputs.index("-i") + 1] == path:
        # iPhone upside-down files: drop to 30 fps BEFORE the 4K flip (autorotate would flip all 60 frames)
        k0 = inputs.index("-i")
        inputs[k0:k0] = ["-noautorotate"]
        fc = f"[0:v]sidedata=mode=delete:type=DISPLAYMATRIX,fps={FPS},hflip,vflip[r0];" + fc.replace("[0:v]", "[r0]")
    nfr = max(1, round(d * FPS)); dq = nfr / FPS
    fc += (f";[v]fps={FPS},tpad=stop_mode=clone:stop_duration=0.5,trim=end_frame={nfr},setpts=N/({FPS}*TB),setsar=1,"
           f"{TV709}[vo]")
    amap = "0:a:0"
    master = spec.get("master")
    if master and master != seg["clip"]:  # sound always from the master camera / best mic
        amap = f"{inputs.count('-i')}:a:0"
        inputs += ["-ss", f"{seg['start']:.3f}", "-t", f"{d:.3f}", "-i", find_clip(src, master)]
    af = ("volume=0," if seg.get("mute") else "") + f"aresample=48000,apad,atrim=0:{dq:.6f},afade=t=in:d=0.03,afade=t=out:st={max(dq - 0.04, 0):.3f}:d=0.04"
    sh(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", fc, "-map", "[vo]", "-map", amap,
        "-af", af, "-ac", "2", *enc, "-fps_mode", "passthrough", "-c:a", "pcm_s16le", out])
    return dq


def cut_card(seg, out, W, H, enc):
    d = float(seg.get("dur", 2.0))
    c0, c1 = seg.get("bg", ["0x08161b", "0x1f5f6e"])
    inputs = ["-f", "lavfi", "-t", f"{d}", "-i", f"gradients=s={W}x{H}:c0={c0}:c1={c1}:x0=0:y0=0:x1={W}:y1={H}:d=1:speed=0.0001:r={FPS}",
              "-f", "lavfi", "-t", f"{d}", "-i", "anullsrc=r=48000:cl=stereo"]
    fc = "[0:v]format=yuv420p"
    if seg.get("logo"):
        inputs += ["-loop", "1", "-t", f"{d}", "-i", seg["logo"]]
        fc += f"[bg];[2:v]scale={W // 5}:-1,format=rgba,fade=t=in:d=0.25:alpha=1[lg];[bg][lg]overlay=(W-w)/2:(H-h)/2"
    fc += f",fps={FPS},setsar=1[vo]"
    sh(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", fc, "-map", "[vo]", "-map", "1:a",
        *enc, "-c:a", "pcm_s16le", "-t", f"{d}", out])
    return d


# ----------------------------------------------------------------------------- words
def clip_words(tx, clip, s, e):
    p = os.path.join(tx, clip + ".json")
    if not os.path.exists(p):
        return []
    d = json.load(open(p, encoding="utf-8"))
    return [[w[0] - s, w[1] - s, w[2].strip()] for sg in d for w in sg["w"] if s - 0.05 <= w[0] < e - 0.05 and w[2].strip()]


def speaker_of(tx, clip, s, e):
    """Majority speaker label ("L"/"R"/"?") of the words in [s, e] (labels written by scripts/speakers.py)."""
    p = os.path.join(tx, clip + ".json")
    if not os.path.exists(p):
        return "?"
    labs = [w[4] for sg in json.load(open(p, encoding="utf-8")) for w in sg["w"]
            if s - 0.05 <= w[0] < e - 0.05 and len(w) > 4 and w[4] in "LR"]
    return max(set(labs), key=labs.count) if labs else "?"


def align(words, text, dur):
    """Lay clean caption text onto the timing of the spoken words (character-proportional)."""
    toks = text.split()
    if not words:
        return [[dur * i / len(toks), dur * (i + 1) / len(toks), t] for i, t in enumerate(toks)]
    if len(toks) == len(words):
        return [[w[0], w[1], t] for w, t in zip(words, toks)]
    pts, c = [], 0
    for w in words:
        pts.append((c, w[0])); c += len(w[2]) + 1; pts.append((c - 1, w[1]))
    total_o, total_n = c, sum(len(t) + 1 for t in toks)
    cs, tt = [p[0] for p in pts], [p[1] for p in pts]
    out, c = [], 0
    for t in toks:
        a = np.interp(c * total_o / total_n, cs, tt); c += len(t) + 1
        b = np.interp((c - 1) * total_o / total_n, cs, tt)
        out.append([float(a), float(max(b, a + 0.05)), t])
    return out


def apply_fixes(words, fixes):
    if not fixes:
        return words
    text = " ".join(w[2] for w in words)
    for a, b in fixes.items():
        text = re.sub(r"(?<!\w)" + re.escape(a) + r"(?!\w)", b, text, flags=re.I)
    toks = text.split()
    if len(toks) == len(words):
        return [[w[0], w[1], t] for w, t in zip(words, toks)]
    t0, t1, n = words[0][0], words[-1][1], len(toks)
    return [[t0 + (t1 - t0) * i / n, t0 + (t1 - t0) * (i + 1) / n, t] for i, t in enumerate(toks)]


def tighten(seg, tx, gap, drop_fillers, tx_clip=None):
    """Split one segment into pieces at pauses > gap (and around filler words): jump-cut tightening."""
    words = clip_words(tx, tx_clip or seg["clip"], seg["start"], seg["end"])
    if drop_fillers:
        words = [w for w in words if re.sub(r"[^\w]", "", w[2]).lower() not in FILLERS]
    if not words:
        return [seg]
    pad = 0.12
    pieces, cur = [], [words[0][0], words[0][1]]
    for w in words[1:]:
        if w[0] - cur[1] > gap:
            pieces.append(cur); cur = [w[0], w[1]]
        else:
            cur[1] = w[1]
    pieces.append(cur)
    out = []
    for a, b in pieces:
        s = max(seg["start"], seg["start"] + a - pad)
        e = min(seg["end"], seg["start"] + b + pad)
        if e - s > 0.25:
            out.append({**seg, "start": round(s, 3), "end": round(e, 3)})
    return out or [seg]


def chunk(words, maxw, maxdur=1.8):
    out, cur = [], []
    for w in words:
        if cur and (len(cur) >= maxw or w[1] - cur[0][0] > maxdur or w[0] - cur[-1][1] > 0.35):
            out.append(cur); cur = []
        cur.append(w)
        if re.search(r"[.?!]$", w[2]) or (w[2].endswith(",") and len(cur) >= 2):
            out.append(cur); cur = []
    if cur:
        out.append(cur)
    merged = []
    for c in out:  # no orphan single words
        if merged and (len(c) == 1 or len(merged[-1]) == 1) and len(merged[-1]) + len(c) <= maxw + 1 \
                and c[0][0] - merged[-1][-1][1] < 0.9 and not re.search(r"[.?!]$", merged[-1][-1][2]):
            merged[-1] = merged[-1] + c
        else:
            merged.append(c)
    return merged


def bare(s):
    return re.sub(r"[^\w%'-]", "", s).lower()


def find_key(c, keywords):
    """(i, j) span of the first keyword phrase inside chunk c, else None."""
    toks = [bare(w[2]) for w in c]
    for kw in keywords:
        k = kw.lower().split()
        for i in range(len(toks) - len(k) + 1):
            if toks[i:i + len(k)] == k:
                return i, i + len(k)
    return None


# ----------------------------------------------------------------------------- ASS
def ts(t):
    t = max(t, 0); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def esc(s):
    return s.replace("{", "(").replace("}", ")").replace("\\", "/")


def ass_color(hexstr, alpha=0):
    h = hexstr.lstrip("#")
    return f"&H{alpha:02X}{h[4:6]}{h[2:4]}{h[0:2]}&".upper()


class ASS:
    def __init__(self, W, H):
        self.W, self.H, self.ev = W, H, []
        self.head = [
            "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 2",
            "ScaledBorderAndShadow: yes", "YCbCr Matrix: TV.709", "", "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
            "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            "Style: Base,Inter Tight Medium,50,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,0,2,5,0,0,0,1",
            "Style: Box,Inter Tight Heavy,50,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,3,18,0,5,0,0,0,1",
            "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        ]

    def add(self, st, en, text, layer=0, style="Base"):
        if en - st > 0.02:
            self.ev.append(f"Dialogue: {layer},{ts(st)},{ts(en)},{style},,0,0,0,,{text}")

    def write(self, path):
        open(path, "w", encoding="utf-8").write("\n".join(self.head + self.ev) + "\n")


def tag(font, size, x, y, an=5, color="FFFFFF", sp=0, extra=""):
    return (f"{{\\an{an}\\pos({x:.0f},{y:.0f})\\fn{font}\\fs{size:.0f}\\fsp{sp}\\c{ass_color(color)}"
            f"\\shad{2 if size < 90 else 3}\\4a&H90&\\blur0.6{extra}}}")


def caption_events(ass, caps, limits, keywords, style, cfg, accent, ys=None):
    """caps: chunks [[st, en, word], ...] on the output timeline; limits: end of each chunk's segment
    (a caption never runs past its own cut, so nothing spills onto the next shot or a card)."""
    W, H = ass.W, ass.H
    sc = W / 1080 if H > W else H / 1080 * 0.9  # size scale: short = 1, long ~0.9
    x0 = W / 2
    for i, c in enumerate(caps):
        y0 = (ys[i] if ys and ys[i] is not None else cfg["cap_y"]) * H
        st = c[0][0]
        en = caps[i + 1][0][0] if i + 1 < len(caps) else c[-1][1] + 0.35
        en = min(en, c[-1][1] + 0.5, limits[i])
        words = [esc(w[2]) for w in c]
        if style == "pod":  # long-form podcast: bold white chunk at the bottom, current word in the accent colour
            fs = cfg.get("cap_size", 58) * (H / 1080 if W > H else W / 1080)
            base = (f"{{\\an2\\pos({x0:.0f},{y0:.0f})\\fnInter Tight Heavy\\fs{fs:.0f}\\fsp-1\\bord{fs * 0.07:.1f}"
                    f"\\3c&H000000&\\shad{fs * 0.05:.1f}\\4a&H60&\\blur0.4}}")
            ac = ass_color(accent)
            for k in range(len(c)):
                s2 = c[k][0]; e2 = c[k + 1][0] if k + 1 < len(c) else en
                txt = " ".join((f"{{\\c{ac}}}{w}{{\\c&HFFFFFF&}}" if j == k else w) for j, w in enumerate(words))
                ass.add(s2 if k else st, e2, base + txt)
            continue
        if style == "minimal":  # ref ig1: small geometric sans, whole chunk swaps, no animation
            ass.add(st, en, tag("Jost Regular", 54 * sc, x0, y0) + " ".join(words))
            continue
        key = find_key(c, keywords)
        if style == "lockup":  # ref ig3: tiny grotesk builds word by word; key moment -> big sans + italic serif
            small = ("Inter Tight Medium", 48 * sc)
            if not key:
                for k in range(len(c)):
                    e2 = c[k + 1][0] if k + 1 < len(c) else en
                    ass.add(c[k][0], e2, tag(*small, x0, y0, sp=-1) + " ".join(words[:k + 1]))
                continue
            i0, i1 = key
            ktxt = " ".join(words[i0:i1])
            ks = 170 * sc
            while text_w("Inter Tight Heavy", ktxt, ks, -6 * sc) > W * 0.86 and ks > 60:
                ks *= 0.92
            ss = 78 * sc
            pre, post = " ".join(words[:i0]), " ".join(words[i1:])
            while max(text_w("Instrument Serif Italic", pre, ss), text_w("Instrument Serif Italic", post, ss)) > W * 0.86 and ss > 36:
                ss *= 0.92
            y_pre, y_post = y0 - ks * 0.50 - ss * 0.30, y0 + ks * 0.46 + ss * 0.30
            for k in range(len(c)):
                s2 = c[k][0]; e2 = c[k + 1][0] if k + 1 < len(c) else en
                pr = " ".join(words[:min(k + 1, i0)])
                if pr:
                    ass.add(s2, e2, tag("Instrument Serif Italic", ss, x0, y_pre) + pr, 1)
                if k >= i0:
                    pop = "\\fscx82\\fscy82\\t(0,120,\\fscx100\\fscy100)" if k == i0 else ""
                    ass.add(s2, e2, tag("Inter Tight Heavy", ks, x0, y0, sp=-6 * sc, color=accent, extra=pop) + ktxt, 2)
                if k >= i1:
                    ass.add(s2, e2, tag("Instrument Serif Italic", ss, x0, y_post) + " ".join(words[i1:k + 1]), 1)
            continue
        if style == "creator":  # ref ig2: left-aligned stack, small light words + one HUGE bold key
            xl = cfg.get("cap_x", 0.09) * W
            if not key:
                ass.add(st, en, tag("Inter Tight Heavy", 64 * sc, xl, y0, an=4, sp=-2) + " ".join(words))
                continue
            i0, i1 = key
            ktxt = " ".join(words[i0:i1])
            ks = 150 * sc
            while text_w("Inter Tight Heavy", ktxt, ks, -4 * sc) > W * 0.82 and ks > 60:
                ks *= 0.92
            ss = 46 * sc
            pre, post = " ".join(words[:i0]), " ".join(words[i1:])
            pop = "\\fscx85\\fscy85\\t(0,140,\\fscx100\\fscy100)"
            if pre:
                ass.add(st, en, tag("Inter Tight Medium", ss, xl + 6, y0 - ks * 0.52, an=4) + pre, 1)
            kst = c[i0][0]
            if kst > st and not pre:
                kst = st
            ass.add(kst, en, tag("Inter Tight Heavy", ks, xl, y0, an=4, sp=-4 * sc, color=accent, extra=pop) + ktxt, 2)
            if post:
                ass.add(c[i1][0] if i1 < len(c) else kst, en,
                        tag("Inter Tight Medium", ss, xl + 6, y0 + ks * 0.50, an=4) + post, 1)


STOP = set("""the a an and or but so to of in on at for with from by as is are was were be been being it its it's this that
these those i you he she we they me him her us them my your his our their just like really very what when where which who
how then than there here have has had do does did not no yes yeah okay ok um uh i'm you're that's don't can can't will
would could should about into out up down over also because if gonna wanna kind sort thing things know mean get got going
go right well actually maybe some any all more most much many even still too only now said say says want need make made
let's let there's they're we're it'll i'll i've you've what's doesn't didn't isn't wasn't aren't""".split())
NUMWORDS = set("""one two three four five six seven eight nine ten eleven twelve fifteen twenty thirty forty fifty sixty
hundred thousand million half double triple""".split())


CONNECT = set("a an the of to in on for and or but is it i you my we that this with at be so".split())
CONTRAST = set("why actually problem never real enough emotions really truth wrong mistake secret always only "
               "huge massive crazy exactly".split())


def v4_key(c, keywords):
    """(i0, i1, kind) of the ONE keyword in a chunk (style guide s3): spec / accent keyword phrase > number (+ unit)
    > contrast word (serif) > longest content word (data). kind: "kw" | "num" | "contrast" | "word"."""
    k = find_key(c, keywords)
    if k:
        return k[0], k[1], "kw"
    toks = [bare(w[2]) for w in c]
    for i, t in enumerate(toks):
        if re.search(r"\d", t) or t in NUMWORDS:
            j = i + 1  # "150 grams", "2 gels": the unit rides along
            if j < len(toks) and re.match(r"(g|grams?|kg|kilos?|ml|l|litres?|liters?|mg|percent|%|hours?|minutes?|min|k|x|"
                                          r"gels?|eggs?|cups?|calories|kcal|ish|am|pm|a\.m\.|p\.m\.)$", toks[j]):
                j += 1
            return i, j, "num"
    for i, t in enumerate(toks):
        if t in CONTRAST:
            return i, i + 1, "contrast"
    best, bl = None, 3
    for i, t in enumerate(toks):
        if t not in STOP and len(t) > bl:
            best, bl = i, len(t)
    return (best, best + 1, "word") if best is not None else None


def v4_clean(w):
    """Caption token: no em/en dashes, drop trailing , . ; : (keep ? ! and inner punctuation)."""
    w = w.replace("—", "").replace("–", "").replace("--", "").strip()
    w = re.sub(r"^i(?=$|'|’|[,.;:?!])", "I", w)  # "i", "i'm", "i'll" -> capital I
    if re.fullmatch(r"(\w\.){2,}", w):  # p.m. / a.m. / U.S. keep their dots
        return w
    return re.sub(r"[,.;:]+$", "", w)


def v4_chunks(words, maxw=5, maxc=30):
    """Style guide s3 chunking: 2-5 words, <= 30 characters, one line; break at punctuation or a pause > 0.35 s."""
    out = []
    for c in chunk(words, maxw, 2.4):
        cur = []
        for w in c:
            if cur and len(" ".join(x[2] for x in cur + [w])) > maxc:
                out.append(cur); cur = []
            cur.append(w)
        if cur:
            if out and len(cur) == 1 and out[-1] is not None and len(out[-1]) < maxw and \
                    len(" ".join(x[2] for x in out[-1] + cur)) <= maxc + 4 and cur[0][0] - out[-1][-1][1] < 0.35:
                out[-1] = out[-1] + cur
            else:
                out.append(cur)
    return out


def captions_v4(ass, caps, limits, keywords, cfg, meta):
    """v4 captions, revised after Nizam's review (2026-11-09): ONE font (Inter Tight Heavy), ONE size, one baseline for
    every word of every speaker; no box behind anyone; no blur; a thin soft outline only. Word-by-word reveal with a
    2-frame fade. A keyword changes COLOUR only (never size or font), and keywords are rare: numbers / spec keywords,
    at most one every `cap_key_gap` seconds (default 12 s, about one per 4-5 sentences). On the paper plate (light
    split-screen background) the text is INK with an ACCENT keyword instead of white."""
    W, H = ass.W, ass.H
    keymode = cfg.get("cap_key", "mix")
    gap = float(cfg.get("cap_key_gap", 12.0))
    last_key = -1e9
    f0 = "Inter Tight Heavy"
    for i, c in enumerate(caps):
        m = meta[i]
        c = [[a, b, v4_clean(w)] for a, b, w in c]
        c = [w for w in c if w[2]]
        if not c:
            continue
        k = float(m["size"]) / 66.0
        st = c[0][0]
        nxt = caps[i + 1][0][0] if i + 1 < len(caps) else None
        en = min(nxt if nxt is not None else 9e9, c[-1][1] + 0.6)
        if nxt is not None and 0 < nxt - en < 0.25:
            en = nxt  # no flicker between chunks
        en = min(en, limits[i])
        if en - st < 0.1:
            continue
        key = None
        if keymode != "none" and st - last_key >= gap:
            kk = v4_key(c, keywords)
            if kk and kk[2] in ("kw", "num"):
                key = kk; last_key = st
        paper = m.get("paper")
        base_col = INK if paper else "#FFFFFF"
        hi_col = ACCENT4 if paper else cfg.get("cap_color", HIGHLIGHT)
        e0 = 66 * k
        maxw = float(m.get("maxw", 1500))
        sp_ = text_w(f0, " ", e0)
        ws = [text_w(f0, w[2], e0, -0.01 * e0) for w in c]
        tot = sum(ws) + sp_ * (len(ws) - 1)
        sc = min(1.0, maxw / tot) if tot > 0 else 1.0  # shrink the whole line (all words together) to fit
        ws = [x * sc for x in ws]; sp = sp_ * sc; tot *= sc
        e = e0 * sc; fs = fs_of(f0, e)
        yb = float(m["y"]) * H  # one baseline for the whole line
        x = float(m.get("x", 0.5)) * W - tot / 2
        if paper:
            edge = "\\bord0\\shad0"
        else:
            edge = (f"\\3c{ass_color(INK)}\\bord{1.6 * k * sc:.1f}\\3a&H90&"
                    f"\\4c{ass_color(INK)}\\shad{1.2 * k * sc:.1f}\\4a&HB0&")
        for j, w in enumerate(c):
            col = hi_col if (key and key[0] <= j < key[1]) else base_col
            xc = x + ws[j] / 2; x += ws[j] + sp
            s2 = max(c[j][0], st)
            if s2 >= en - 0.04:
                s2 = max(st, en - 0.3)
            tg = (f"{{\\an2\\pos({xc:.1f},{yb:.1f})\\fn{f0}\\fs{fs:.1f}\\fsp{-0.01 * e:.2f}\\c{ass_color(col)}{edge}"
                  f"\\alpha&HFF&\\t(0,60,\\alpha&H00&)}}")
            ass.add(s2, en, tg + esc(w[2]), 6)


def rrect(w, h, r):
    """ASS vector path of a w x h rectangle with radius-r corners (origin top-left)."""
    r = min(r, w / 2, h / 2); k = 0.4477 * r
    return (f"m {r:.1f} 0 l {w - r:.1f} 0 b {w - k:.1f} 0 {w:.1f} {k:.1f} {w:.1f} {r:.1f} l {w:.1f} {h - r:.1f} "
            f"b {w:.1f} {h - k:.1f} {w - k:.1f} {h:.1f} {w - r:.1f} {h:.1f} l {r:.1f} {h:.1f} b {k:.1f} {h:.1f} 0 {h - k:.1f} 0 {h - r:.1f} "
            f"l 0 {r:.1f} b 0 {k:.1f} {k:.1f} 0 {r:.1f} 0")


def label_events(ass, st, en, x, y, label, index, anim, style="hi", idx_y=None):
    """Mono index box (top) + caps label pill. (x, y) = top-left of the pill; idx_y = top of the index box (None:
    index sits left of the pill on the same row). anim: wipe / fade in. style "hi" INK on HIGHLIGHT, "ink" PAPER on INK."""
    if en - st < 0.1:
        return
    d0 = 0.0
    if index:
        em = 20; fs = fs_of("Space Mono Bold", em)
        tw = text_w("Space Mono Bold", index, em, 2.4); bw, bh = tw + 20, 34
        iy = y if idx_y is None else idx_y
        fad = "\\fad(140,0)" if anim else ""
        ass.add(st, en, f"{{\\an7\\pos({x:.0f},{iy:.0f})\\p1\\bord0\\shad0\\c{ass_color(INK)}{fad}}}{rrect(bw, bh, 6)}{{\\p0}}", 8)
        ass.add(st, en, f"{{\\an4\\pos({x + 10:.0f},{iy + bh / 2:.0f})\\fnSpace Mono\\b1\\fs{fs:.1f}\\fsp2.4\\bord0\\shad0"
                        f"\\c{ass_color(PAPER)}{fad}}}{esc(index)}", 9)
        if idx_y is None:
            x += bw + 10
        d0 = 0.06
    if label:
        txt = label.upper()
        em = 30; fs = fs_of("Inter Tight Heavy", em)
        tw = text_w("Inter Tight Heavy", txt, em, 1); bw, bh = tw + 36, 44
        if idx_y is None and index:
            y = y - 5  # centre the taller pill on the index row (44 vs 34)
        bgc, fgc = (HIGHLIGHT, INK) if style == "hi" else (INK, PAPER)
        clip = (f"\\clip({x:.0f},{y - 4:.0f},{x + 1:.0f},{y + bh + 4:.0f})\\t(0,230,0.5,\\clip({x:.0f},{y - 4:.0f},{x + bw:.0f},{y + bh + 4:.0f}))"
                if anim else "")
        s2 = st + (d0 if anim else 0)
        ass.add(s2, en, f"{{\\an7\\pos({x:.0f},{y:.0f})\\p1\\bord0\\shad0\\c{ass_color(bgc)}{clip}}}{rrect(bw, bh, bh / 2)}{{\\p0}}", 8)
        ass.add(s2, en, f"{{\\an4\\pos({x + 18:.0f},{y + bh / 2:.0f})\\fnInter Tight Heavy\\fs{fs:.1f}\\fsp1\\bord0\\shad0"
                        f"\\c{ass_color(fgc)}{clip}}}{esc(txt)}", 9)


def frame_who_side(seg, spec, tx):
    who = seg.get("who")
    if who not in ("L", "R"):
        who = speaker_of(tx, spec.get("master") or seg["clip"], seg["start"], seg["end"])
        who = who if who in ("L", "R") else "L"
    return who, seg.get("side", "left" if who == "L" else "right")


def panel_labels(ass, seginfo, spec, tx):
    """Labels + indices of frame panels and full-screen B-roll (output timeline)."""
    W, H = ass.W, ass.H
    for t0, d, seg in seginfo:
        if seg.get("card"):
            continue
        enter = seg.get("enter", True) is not False and float(seg.get("_goff", 0)) < 0.01
        if seg.get("layout") == "frame" and W > H:
            pn = seg.get("panel") or {}
            if pn.get("label") or pn.get("index"):
                _, side = frame_who_side(seg, spec, tx)
                px = PANEL_X[1] if side == "left" else PANEL_X[0]
                st = t0 + (0.30 if enter else 0.0)
                label_events(ass, st, t0 + d, px + 24, PANEL_Y + PANEL_H - 24 - 44, pn.get("label"), pn.get("index"),
                             enter, pn.get("style", "hi"), idx_y=PANEL_Y + 24)
        br = seg.get("broll") or {}
        if br and not br.get("panel") and (br.get("label") or br.get("index")) and W > H:
            st = t0 + (0.12 if enter else 0.0)
            label_events(ass, st, t0 + d, 96, 88, br.get("label"), br.get("index"), enter, br.get("style", "hi"))


def build_overlays(ass, spec, total, cfg, sfx):
    W, H = ass.W, ass.H
    sc = W / 1080 if H > W else H / 1080 * 0.9
    accent = spec.get("accent", "#FFFFFF")
    hk = spec.get("hook")
    if hk:  # headline in the top band (great over letterbox / band layouts)
        lines = hk["text"] if isinstance(hk["text"], list) else [hk["text"]]
        until = min(float(hk.get("until", total)), total)
        y = hk.get("y", 0.17) * H
        fs = 92 * sc
        while max(text_w("Inter Tight Heavy", ln.upper(), fs, -1) for ln in lines) > W * 0.88 and fs > 40:
            fs *= 0.93
        for j, ln in enumerate(lines):
            col = accent if j == len(lines) - 1 and len(lines) > 1 else "FFFFFF"
            ass.add(0, until, tag("Inter Tight Heavy", fs, W / 2, y + j * fs * 1.02, sp=-1, color=col,
                                  extra="\\fscx90\\fscy90\\t(0,180,\\fscx100\\fscy100)") + esc(ln.upper()), 3)
        sfx.append(("whoosh_soft2.mp3", 0.0, 0.45))
    for nm in spec.get("names", []):  # lower third: bold name + italic serif role, typed on
        at, d = float(nm["at"]), float(nm.get("dur", 3.0))
        x = nm.get("x", 0.09) * W; y = nm.get("y", 0.40) * H
        name, role = nm["name"], nm.get("role", "")
        n = len(name)
        for k in range(1, n + 1):
            s2 = at + 0.035 * (k - 1)
            e2 = at + 0.035 * k if k < n else at + d
            cur = "_" if k < n else ""
            ass.add(s2, e2, tag("Inter Tight Heavy", 62 * sc, x, y, an=4, sp=-2) + esc(name[:k]) + cur, 4)
        if role:
            ass.add(at + 0.035 * n, at + d, tag("Instrument Serif Italic", 38 * sc, x + 4, y + 52 * sc, an=4,
                                                color=nm.get("role_color", "D9D9D9"), extra="\\fad(150,0)") + esc(role), 4)
        sfx.append(("click.wav", at, 0.35))
    for cn in spec.get("counters", []):  # 0 ----- 10,000 ticker
        at, d = float(cn["at"]), float(cn.get("dur", 2.5))
        a, b = float(cn.get("from", 0)), float(cn["to"])
        y = cn.get("y", 0.5) * H
        x1, x2 = 0.12 * W, 0.66 * W
        run = min(1.4, d * 0.6)
        steps = int(run * FPS)
        for k in range(steps + 1):
            v = a + (b - a) * (1 - (1 - k / steps) ** 3)
            s2 = at + k / FPS; e2 = at + (k + 1) / FPS if k < steps else at + d
            txt = f"{v:,.0f}" + (cn.get("suffix", ""))
            ass.add(s2, e2, tag("Inter Tight Heavy", 72 * sc, 0.90 * W, y, an=6, sp=-2) + txt, 4)
        ass.add(at, at + d, tag("Inter Tight Heavy", 72 * sc, 0.06 * W, y, an=4) + f"{a:,.0f}", 4)
        ln = x2 - x1
        ass.add(at, at + d, f"{{\\an4\\pos({x1:.0f},{y:.0f})\\p1\\c&HFFFFFF&\\clip({x1:.0f},0,{x1 + 1:.0f},{H})"
                            f"\\t(0,{int(run * 1000)},\\clip({x1:.0f},0,{x2:.0f},{H}))\\shad0}}"
                            f"m 0 -3 l {ln:.0f} -3 l {ln:.0f} 3 l 0 3{{\\p0}}", 4)
        if cn.get("label"):
            ass.add(at, at + d, tag("Instrument Serif Italic", 44 * sc, W / 2, y + 70 * sc) + esc(cn["label"]), 4)
        sfx.append(("whoosh_fast.mp3", at, 0.3)); sfx.append(("ding.mp3", at + run, 0.25))
    for stp in spec.get("stamps", []):  # big glowing word, e.g. SCRIPT / FRAMEWORK
        at, d = float(stp["at"]), float(stp.get("dur", 1.2))
        col = stp.get("color", "#FFD84D")
        fs = 150 * sc
        while text_w("Archivo Black", stp["text"].upper(), fs) > W * 0.86 and fs > 50:
            fs *= 0.92
        y = stp.get("y", 0.5) * H
        glow = f"{{\\an5\\pos({W / 2:.0f},{y:.0f})\\fnArchivo Black\\fs{fs:.0f}\\c{ass_color(col)}\\alpha&H70&\\blur14\\bord6\\3c{ass_color(col)}\\shad0}}"
        ass.add(at, at + d, glow + esc(stp["text"].upper()), 5)
        ass.add(at, at + d, f"{{\\an5\\pos({W / 2:.0f},{y:.0f})\\fnArchivo Black\\fs{fs:.0f}\\c{ass_color(col)}\\shad0"
                            f"\\fscx115\\fscy115\\t(0,110,\\fscx100\\fscy100)}}" + esc(stp["text"].upper()), 6)
        sfx.append(("pop.mp3", at, 0.35))
    for stk in spec.get("stacks", []):  # glossy checklist that builds: Topic -> Hook -> Format -> CTA
        at = float(stk["at"]); every = float(stk.get("every", 0.5)); items = stk["items"]
        end = at + float(stk.get("dur", every * len(items) + 1.5))
        col = stk.get("color", "#2FB4D6")
        y0 = stk.get("y", 0.30) * H; gap = 108 * sc
        for k, it in enumerate(items):
            s2 = at + every * k
            box = (f"{{\\an5\\pos({W / 2:.0f},{y0 + k * gap:.0f})\\fnInter Tight Heavy\\fs{56 * sc:.0f}\\c&HFFFFFF&"
                   f"\\3c{ass_color(col)}\\bord{30 * sc:.0f}\\shad0\\fad(120,0)\\fscx90\\fscy90\\t(0,140,\\fscx100\\fscy100)}}")
            ass.add(s2, end, box + esc(it), 5, "Box")
            sfx.append(("pop.mp3", s2, 0.3))
    for tg in spec.get("tags", []):  # chapter tag, top-left: [03] VITAMIN D  (fades in/out, stays put)
        at, until = float(tg["at"]), min(float(tg.get("until", total)), total)
        if until - at < 1.0:
            continue
        fs = 25 * sc; x = 0.034 * W; y = 0.062 * H
        num, txt = tg.get("num", ""), tg["text"].upper()
        nw = text_w("Inter Tight Heavy", num, fs) + 26 * sc
        tw = text_w("Inter Tight Medium", txt, fs, 1) + 30 * sc
        h = fs * 1.75
        box = lambda x0, w, col, a: (f"{{\\an7\\pos({x0:.0f},{y - h / 2:.0f})\\p1\\bord0\\shad0\\c{ass_color(col)}\\alpha&H{a}&\\fad(300,300)}}"
                                     f"m 0 0 l {w:.0f} 0 l {w:.0f} {h:.0f} l 0 {h:.0f}{{\\p0}}")
        ass.add(at, until, box(x, nw, accent, "00"), 2)
        ass.add(at, until, box(x + nw, tw, "#0E1116", "38"), 2)
        ass.add(at, until, tag("Inter Tight Heavy", fs, x + nw / 2, y, color="101010", extra="\\fad(300,300)\\bord0\\shad0") + esc(num), 3)
        ass.add(at, until, tag("Inter Tight Medium", fs, x + nw + 15 * sc, y, an=4, sp=1, extra="\\fad(300,300)\\bord0\\shad0") + esc(txt), 3)
    ec = cfg.get("endcard")
    if ec:
        st, en = ec["_at"], total
        lines = ec.get("text", [])
        if lines:
            fs = 96 * sc
            while text_w("Archivo Black", lines[0], fs) > W * 0.84 and fs > 40:
                fs *= 0.93
            ass.add(st, en, tag("Archivo Black", fs, W / 2, H * 0.47, extra="\\fad(150,0)") + esc(lines[0]), 6)
            for j, ln in enumerate(lines[1:]):
                ass.add(st + 0.15, en, tag("Inter Tight Medium", 40 * sc, W / 2, H * 0.47 + fs * 0.75 + j * 50 * sc,
                                           sp=2, extra="\\fad(150,0)") + esc(ln.upper()), 6)
        sfx.append(("transition_short.mp3", st, 0.4))


def faces_on_screen(seg, spec, src, W, H, t_src):
    """Output-frame x (0..1) of the faces visible in a full-frame 16:9 segment at source time t_src."""
    if seg.get("layout") == "sbs":
        return [0.25, 0.75]
    if seg.get("card") or seg.get("broll") or seg.get("layout", "full") != "full":
        return []
    path = find_clip(src, seg["clip"]); sw, sh_ = probe(path)
    z = float(seg.get("zoom", 1.0))
    vseg = {**seg, "start": seg["start"], "end": seg["end"]}
    cx = resolve_cx(vseg, path) if (z > 1 or sw / sh_ > W / H + 0.05) else 0.5
    cw = int(sw / z) // 2 * 2 if sw / sh_ <= W / H + 0.05 else int(sh_ * W / H / z) // 2 * 2
    x0 = min(max(cx * sw - cw / 2, 0), sw - cw)
    xs = faces_x(path, t_src, 3) + faces_x(path, t_src + 0.8, 3)  # what is really on screen right then
    xs += [tracked_x(path, t_src - 1.5, t_src + 1.5, side) for side in ("left", "right")]
    out = []
    for fx in xs:
        ox = (fx * sw - x0) / cw
        if -0.1 < ox < 1.1:
            out.append(ox)
    if z > 1.2 and seg.get("cx") in ("left", "right"):
        # tight single: the person fills the middle of the crop even when the detector misses a profile face;
        # keep the open side (the way they face, toward the other person) for overlays
        out += [0.32, 0.45, 0.55] if seg["cx"] == "left" else [0.45, 0.55, 0.68]
    return out


def place_stickers(sts, seginfo, spec, src, W, H):
    """x = "auto": put each group of floating elements in the widest gap away from the faces on screen."""
    groups = {}
    for stk in sts:
        if stk.get("x") == "auto":
            groups.setdefault(stk.get("group", id(stk)), []).append(stk)
    for g in groups.values():
        at = float(g[0]["at"])
        hit = next(((t0, d, sg) for t0, d, sg in seginfo if t0 <= at < t0 + d), None)
        faces = []
        if hit:
            t0, d, sg = hit
            faces = faces_on_screen(sg, spec, src, W, H, sg["start"] + (at - t0))
        n = len(g)
        hw = max(float(s.get("w", 0.10)) for s in g) / 2  # half width of the widest element in the group
        gap = max(0.13, 2 * hw + 0.01)  # faces get a wide berth: people lean, detections lag
        best, bs = None, -9
        for k in range(0, 60):
            x1 = 0.02 + hw + 0.015 * k
            xs = [x1 + gap * i for i in range(n)]
            if xs[-1] + hw > 0.985:
                break
            # bigger = the element's nearest edge is further from every face
            sc = min((min(abs(x - f) for f in faces) - hw if faces else 1.0) for x in xs)
            sc += 0.02 * (1 if 0.25 < sum(xs) / n < 0.75 else 0)  # slight preference for the open middle when tied
            if sc > bs:
                best, bs = xs, sc
        if best is None:
            best = [0.5] * n
        for stk, x in zip(g, best):
            stk["x"] = x


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec"); ap.add_argument("--src", required=True); ap.add_argument("--tx", required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--work", default=os.path.join(tempfile.gettempdir(), "podcast-work"))
    ap.add_argument("--draft", action="store_true", help="fast low-quality encode for review")
    ap.add_argument("--sheet", action="store_true", help="also write a 1 fps contact sheet next to the render")
    ap.add_argument("--reuse", action="store_true", help="keep segments already cut in the work dir (same spec): redo the final pass only")
    a = ap.parse_args()

    spec = json.load(open(a.spec, encoding="utf-8")); rid = spec["id"]
    global TXDIR
    TXDIR = a.tx
    fmt_ = spec.get("format", "short")
    W, H = (1080, 1920) if fmt_ == "short" else (1920, 1080)
    style = spec.get("captions", "lockup" if fmt_ == "short" else "none")
    default_y = {"full": 0.62, "letterbox": 0.5, "band": 0.5, "split": 0.5}.get(spec.get("layout", "full"), 0.6)
    cfg = {"cap_y": spec.get("cap_y", default_y if fmt_ == "short" else (1004 / 1080 if style == "v4" else 0.83)),
           "cap_x": spec.get("cap_x", 0.09), "cap_size": spec.get("cap_size", 66 if style == "v4" else 58),
           "cap_host": spec.get("cap_host", "L"), "host_box": spec.get("host_box", True),
           "cap_color": spec.get("cap_color", HIGHLIGHT), "cap_key": spec.get("cap_key", "mix")}
    global CACHE
    CACHE = os.path.abspath(os.path.join(a.work, "_cache"))  # shared by every chunk rendered into the same --work
    spec["_dir"] = os.path.dirname(os.path.abspath(a.spec))
    enc = ["-c:v", "libx264", "-preset", "ultrafast" if a.draft else "veryfast", "-crf", "26" if a.draft else "16",
           "-pix_fmt", "yuv420p"]
    work = os.path.abspath(os.path.join(a.work, rid)); os.makedirs(work, exist_ok=True)

    # expand segments: tightening (jump cuts) + alternating punch-ins
    segs = []
    gap = spec.get("tighten")
    jz = spec.get("jump_zoom")
    for seg in spec["segments"]:
        g = seg.get("tighten", gap)
        pieces = tighten(seg, a.tx, float(g), spec.get("drop_fillers", True), spec.get("master")) if (g and not seg.get("card") and seg.get("text") is None) else [seg]
        goff, gl = 0.0, [max(1, round((q["end"] - q["start"]) * FPS)) / FPS for q in pieces] if not seg.get("card") else [0]
        for k, p in enumerate(pieces):
            if jz and len(pieces) > 1 and "zoom" not in seg:
                p = {**p, "zoom": jz[k % len(jz)]}
            if k > 0:
                p.pop("chapter", None)
            if len(pieces) > 1:  # B-roll / panel video and push continue across the jump cuts; panels animate in once
                p = {**p, "_goff": round(goff, 4), "_gdur": round(sum(gl), 4)}
                goff += gl[k]
            segs.append(p)
    af_ = spec.get("auto_frame")
    if af_:  # one wide two-shot camera -> "multicam": tight on whoever talks, back to wide now and then
        tight = float(af_.get("zoom", 1.9 if fmt_ == "long" else 1.0))  # 4K two-shot: 2.0 = one person at native 1080p
        punch = float(af_.get("punch", 1.12))
        every = int(af_.get("wide_every", 4))
        mt = float(af_.get("min_turn", 0.4))  # shortest shot a speaker change may create
        split = []  # first cut every piece at speaker changes (midpoint of the gap between the two words)
        for p in segs:
            jp = os.path.join(a.tx, (spec.get("master") or p.get("clip", "")) + ".json")
            if p.get("card") or p.get("broll") or "cx" in p or p.get("layout") in ("split", "sbs", "frame", "frame2") or not os.path.exists(jp):
                split.append(p); continue
            ws = [w for sg in json.load(open(jp, encoding="utf-8")) for w in sg["w"]
                  if p["start"] - 0.05 <= w[0] < p["end"] - 0.05 and len(w) > 4 and w[4] in "LR"]
            cur = p["start"]
            for w0, w1 in zip(ws, ws[1:]):
                if w0[4] != w1[4]:
                    cut = round((w0[1] + w1[0]) / 2, 3)
                    if cut - cur > mt and p["end"] - cut > mt:
                        split.append({**p, "start": cur, "end": cut}); cur = cut
                        p = {k: v for k, v in p.items() if k != "chapter"}
            split.append({**p, "start": cur})
        segs = split
        last, turns = None, 0
        for k, p in enumerate(segs):
            if p.get("card") or p.get("broll") or "cx" in p or p.get("layout") in ("split", "sbs", "frame", "frame2"):
                continue
            who = speaker_of(a.tx, spec.get("master") or p["clip"], p["start"], p["end"])
            if who == "?" and fmt_ != "long":
                who = last or "R"  # vertical crop can't show both: stay on the last speaker
            if who != last:
                turns += 1
            if who == "?" or (fmt_ == "long" and every and who != last and turns % every == 0):
                p.update(cx=0.5, zoom=1.0)  # wide: both people (long-form) / centre (shorts)
            else:
                side = "left" if who == "L" else "right"
                tz = float(af_.get("zoom_" + side, tight))  # per-person framing (e.g. wider on someone facing a desk)
                z = tz * (punch if (who == last and k % 2) else 1.0)  # same speaker continues: alternate punch-in
                p.update(cx=side, zoom=round(z, 3))
                p.setdefault("cy", float(af_.get("cy", 0.36)))
            last = who
    if spec.get("endcard"):
        segs.append({"card": True, **spec["endcard"]})

    parts, caps, limits, t, chapters = [], [], [], 0.0, []
    cys = []; seginfo = []; meta = []
    keywords = [k.lower() for k in spec.get("keywords", [])]
    maxw = {"minimal": 4, "lockup": 5, "creator": 4, "pod": 6, "v4": 5}.get(style, 4)
    prev = None
    for seg in segs:  # v4 panels: a segment that continues the previous frame layout does not re-animate
        if seg.get("layout") in ("frame", "frame2") and prev is not None and "enter" not in seg and                 prev.get("layout") == seg["layout"] and prev.get("side") == seg.get("side") and                 (prev.get("panel") or {}).get("file") == (seg.get("panel") or {}).get("file") and not seg.get("_goff"):
            seg["enter"] = False
        prev = seg
    for i, seg in enumerate(segs):
        p = os.path.join(work, f"s{i:03d}.mov")
        if seg.get("chapter"):
            chapters.append((t, seg["chapter"]))
        if seg.get("card"):
            cfg["endcard"] = {**seg, "_at": t}
        dq_ = float(seg.get("dur", 2.0)) if seg.get("card") else max(1, round((seg["end"] - seg["start"]) * FPS)) / FPS
        ok_ = False
        if a.reuse and os.path.exists(p) and os.path.getsize(p) > 1000:  # only a complete segment of the right length
            r_ = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                capture_output=True, text=True).stdout.strip()
            ok_ = bool(r_) and r_ != "N/A" and abs(float(r_) - dq_) < 0.08
        if ok_:
            d = dq_
        else:
            d = cut_segment(seg, spec, a.src, a.tx, p, W, H, enc)
        parts.append(p); seginfo.append((t, d, seg))
        if not seg.get("card") and style != "none" and not seg.get("nocaps"):
            words = clip_words(a.tx, spec.get("master") or seg["clip"], seg["start"], seg["end"])
            if seg.get("text") is not None:
                words = align(words, seg["text"], d) if seg["text"] else []
            if words:
                words = apply_fixes(words, spec.get("fixes", {}))
                cu = spec.get("captions_until")  # long-form: captions over the cold open + intro only
                ww = [[max(w[0], 0) + t, min(w[1], d) + t, w[2]] for w in words]
                if style == "v4" and spec.get("drop_fillers", True):  # no um / uh on screen
                    ww = [w for w in ww if re.sub(r"[^\w]", "", w[2]).lower() not in FILLERS]
                for c in (v4_chunks(ww) if style == "v4" else chunk(ww, maxw)):
                    if cu is None or c[0][0] < float(cu):
                        caps.append(c); limits.append(min(t + d, float(cu)) if cu is not None else t + d)
                        cys.append(seg.get("cap_y", 0.88 if (seg.get("broll") or {}).get("panel") else None))
                        if style == "v4":  # position / size / width per layout (style guide s3)
                            br_ = seg.get("broll") or {}
                            s0 = seg["start"] + (c[0][0] - t); s1 = seg["start"] + (c[-1][1] - t)
                            who = speaker_of(a.tx, spec.get("master") or seg["clip"], s0, s1)
                            kind = "frame" if seg.get("layout") in ("frame", "frame2") else "broll" if (br_ and not br_.get("panel"))                                 else "wide" if float(seg.get("zoom", 1.0)) <= 1.05 and seg.get("layout", "full") == "full" else "talk"
                            ys = {"talk": cfg["cap_y"], "wide": cfg["cap_y"], "frame": spec.get("cap_y_frame", 1010 / 1080),
                                  "broll": spec.get("cap_y_broll", cfg["cap_y"])}
                            xs = {"wide": (600 if who == "L" else 1320) / 1920 if who in ("L", "R") else 0.5}
                            mw = {"talk": 1500, "broll": 1500, "frame": 1700, "wide": 880 if who in ("L", "R") else 1500}
                            meta.append({"y": seg.get("cap_y", ys[kind]), "x": seg.get("cap_x", xs.get(kind, 0.5)),
                                         "size": seg.get("cap_size", cfg["cap_size"]), "maxw": mw[kind], "who": who,
                                         "paper": bool(seg.get("cap_ink")) or (kind == "frame" and (seg.get("bg") or spec.get("bg", "paper")) == "paper")})
        t += d
        print(f"  cut {i + 1}/{len(segs)}", end="\r", flush=True)
    total = t
    print()

    ass = ASS(W, H); sfx = []
    if style == "v4":
        captions_v4(ass, caps, limits, keywords, cfg, meta)
    else:
        caption_events(ass, caps, limits, keywords, style, cfg, spec.get("accent", "#FFFFFF"), cys)
    panel_labels(ass, seginfo, spec, a.tx)
    build_overlays(ass, spec, total, cfg, sfx)
    for s in spec.get("sfx", []):  # manual hits: {"at": 3.2, "file": "whoosh_fast.mp3", "vol": 0.4}
        sfx.append((s["file"], float(s["at"]), float(s.get("vol", 0.4))))
    if spec.get("no_sfx"):
        sfx = []
    assp = os.path.join(work, "caps.ass"); ass.write(assp)
    open(os.path.join(work, "captions.txt"), "w", encoding="utf-8").write("\n".join(" ".join(w[2] for w in c) for c in caps))

    lst = os.path.join(work, "parts.txt")
    open(lst, "w", encoding="utf-8").write("".join("file '" + os.path.abspath(p).replace("\\", "/").replace("'", "'\\''") + "'\n" for p in parts))
    inputs = ["-f", "concat", "-safe", "0", "-i", lst]
    for f, _, _ in sfx:
        inputs += ["-i", os.path.join(SFX, f)]
    mus = spec.get("music")
    if mus:
        inputs += ["-stream_loop", "-1", "-i", os.path.abspath(mus["file"])]
    n = 1
    dn = spec.get("denoise", True)
    # filtergraph paths are relative to the work dir (ffmpeg runs there): no drive-letter / space escaping issues
    import shutil
    shutil.copytree(FONTS, os.path.join(work, "fonts"), dirs_exist_ok=True)
    sts = spec.get("stickers", [])
    fc = ""
    vin = "[0:v]"
    sfiles = [os.path.abspath(stk["file"] if os.path.isfile(stk["file"]) else os.path.join(ROOT, stk["file"])) for stk in sts]
    for j, stk in enumerate(sts):  # {"at": s, "file": "x.mov", "x": 0.8, "y": 0.3} centre position, output timeline
        inputs += (["-t", f"{float(stk['dur']):.3f}"] if stk.get("dur") else []) + ["-i", sfiles[j]]  # "dur": cut early
    place_stickers(sts, seginfo, spec, a.src, W, H)
    for j, stk in enumerate(sts):
        k = 1 + len(sfx) + (1 if mus else 0) + j
        at_ = float(stk["at"])
        if at_ >= total:
            continue
        ch = "format=rgba"
        if stk.get("w") and stk.get("x") != "auto" and (style == "v4" or stk.get("scale")) and stk.get("scale", True) is not False:
            tw_ = int(float(stk["w"]) * W) // 2 * 2  # v4: "w" = drawn width (fraction of the frame); v3 specs: placement hint
            if abs(probe(sfiles[j])[0] - tw_) > 4:
                ch += f",scale={tw_}:-2:flags=lanczos"
        dur = float(stk["dur"]) if stk.get("dur") else None
        fd = float(stk.get("fade", 0) or 0)
        if fd > 0:
            ch += f",fade=t=in:st=0:d={fd:.3f}:alpha=1"
            if dur:
                ch += f",fade=t=out:st={max(dur - fd, 0):.3f}:d={fd:.3f}:alpha=1"
        ch += ",scale=out_range=tv:out_color_matrix=bt709,format=yuva420p"
        fc += (f"[{k}:v]{ch},setpts=PTS-STARTPTS+{at_:.3f}/TB[sk{j}];"
               f"{vin}[sk{j}]overlay=x={float(stk.get('x', 0.8)) * W:.0f}-w/2:y={float(stk.get('y', 0.3)) * H:.0f}-h/2:eof_action=pass:format=auto[ov{j}];")
        vin = f"[ov{j}]"
    fc += f"{vin}ass=caps.ass:fontsdir=fonts[v];"
    fc += ("[0:a]highpass=f=70," + ("afftdn=nf=-28," if dn else "") +
           "acompressor=threshold=0.1:ratio=2.5:attack=15:release=200:makeup=1.5,"
           "loudnorm=I=-14:TP=-1.5:LRA=9[voice];")
    mix = []
    if mus:
        mi = n + len(sfx)
        fc += "[voice]asplit[vo1][vsc];"
        fc += (f"[{mi}:a]aresample=48000,volume={10 ** (float(mus.get('db', -24)) / 20):.4f},atrim=0:{total:.3f},"
               f"afade=t=out:st={max(total - 1.5, 0):.3f}:d=1.5[mraw];"
               f"[mraw][vsc]sidechaincompress=threshold=0.04:ratio=6:attack=30:release=500[mus];")
        mix += ["[vo1]", "[mus]"]
    else:
        mix += ["[voice]"]
    for j, (_, at, vol) in enumerate(sfx):
        ms = max(int(at * 1000), 0)
        fc += f"[{n + j}:a]aresample=48000,volume={vol},adelay={ms}|{ms}[x{j}];"; mix.append(f"[x{j}]")
    fc += "".join(mix) + f"amix=inputs={len(mix)}:normalize=0:duration=first,"
    fc += "loudnorm=I=-14:TP=-1.5:LRA=11,alimiter=limit=0.89:level=0[a]"
    os.makedirs(a.out, exist_ok=True)
    out = os.path.join(a.out, f"{rid}_{spec.get('slug', 'edit')}.mp4")
    out = os.path.abspath(out)
    sh(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "ultrafast" if a.draft else os.environ.get("PODCAST_FINAL_PRESET", "medium"), "-crf", "26" if a.draft else "18",
        "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
        "-t", f"{total:.3f}", out], cwd=work)
    # measured loudness trim: single-pass loudnorm drifts ~1 LU on short clips; land on -14 LUFS exactly
    r = subprocess.run(["ffmpeg", "-nostats", "-i", out, "-vn", "-af", "ebur128=framelog=quiet", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", r)
    if m and abs(float(m[-1]) + 14) > 0.3:
        g = -14 - float(m[-1]); tmp = out[:-4] + ".tmp.mp4"
        sh(["ffmpeg", "-y", "-v", "error", "-i", out, "-c:v", "copy", "-af", f"volume={g:.2f}dB,alimiter=limit=0.89:level=0",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", tmp])
        os.replace(tmp, out)
    if chapters:
        cp = out[:-4] + "_chapters.txt"
        lines = []
        for ct, title in chapters:
            m, s = divmod(int(ct), 60); h, m = divmod(m, 60)
            lines.append((f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}") + f" {title}")
        if not lines[0].startswith("00:00"):
            lines.insert(0, "00:00 Intro")
        open(cp, "w", encoding="utf-8").write("\n".join(lines) + "\n")
        print("chapters ->", cp)
    if a.sheet:
        step = max(total / 30, 1)
        sh(["ffmpeg", "-y", "-v", "error", "-i", out, "-vf",
            f"fps=1/{step:.2f},scale={270 if H > W else 480}:-1,tile=6x5", "-frames:v", "1", out[:-4] + "_sheet.jpg"])
        print("sheet ->", out[:-4] + "_sheet.jpg")
    print(f"{out}  {total:.1f}s  {len(segs)} cuts")


if __name__ == "__main__":
    main()

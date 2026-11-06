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
}


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
    if br:  # B-roll over the speaker's voice: picture from the B-roll file, audio (and captions) from the clip
        bpath = br["file"] if os.path.isfile(br["file"]) else os.path.join(ROOT, br["file"])
        bw, bhh = probe(bpath)
        still = bpath.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
        if still:
            inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{d:.3f}", "-i", bpath]
        else:
            inputs += ["-stream_loop", "-1", "-ss", f"{float(br.get('at', 0)):.3f}", "-t", f"{d:.3f}", "-i", bpath]
        panel = br.get("panel")  # "top": card/B-roll in the top half, the talker cropped in the bottom half
        side = panel in ("left", "right") and W > H  # 16:9 side card: card on that side, talker on the other
        if side:
            tw, th = int(W * float(br.get("frac", 0.42))) // 2 * 2, H
        else:
            tw, th = (W, int(W * 9 / 16) // 2 * 2) if (layout == "letterbox" and H > W) else (W, H // 2) if panel else (W, H)
        push = float(br.get("push", 0.06 if still else 0.03))  # slow push-in (Ken Burns); 0 = static
        n = max(int(d * FPS), 1)
        zp = (f"zoompan=z='1+{push}*on/{n}':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={tw}x{th}:fps={FPS}"
              if push > 0 else f"scale={tw}:{th}")
        fc = (f"[1:v]{crop_expr(bw, bhh, tw / th, 1.0, float(br.get('cx', 0.5)), float(br.get('cy', 0.5)))},"
              f"scale={tw * 2 if push > 0 else tw}:{th * 2 if push > 0 else th}:flags=lanczos,fps={FPS},{zp}{lk if not panel else ''}")
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
    nfr = max(1, round(d * FPS)); dq = nfr / FPS
    fc += f";[v]fps={FPS},tpad=stop_mode=clone:stop_duration=0.5,trim=end_frame={nfr},setpts=N/({FPS}*TB),setsar=1,format=yuv420p[vo]"
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
            "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
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
        n, gap = len(g), 0.13  # faces get a wide berth: people lean, detections lag
        best, bs = None, -1
        for k in range(0, 13):
            x1 = 0.09 + 0.065 * k
            xs = [x1 + gap * i for i in range(n)]
            if xs[-1] > 0.93:
                break
            sc = min((min(abs(x - f) for f in faces) if faces else 1.0) for x in xs)  # bigger = further from every face
            sc += 0.02 * (1 if 0.25 < sum(xs) / n < 0.75 else 0)  # slight preference for the open middle when tied
            if sc > bs:
                best, bs = xs, sc
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
    cfg = {"cap_y": spec.get("cap_y", default_y if fmt_ == "short" else 0.83), "cap_x": spec.get("cap_x", 0.09),
           "cap_size": spec.get("cap_size", 58)}
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
        for k, p in enumerate(pieces):
            if jz and len(pieces) > 1 and "zoom" not in seg:
                p = {**p, "zoom": jz[k % len(jz)]}
            if k > 0:
                p.pop("chapter", None)
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
            if p.get("card") or p.get("broll") or "cx" in p or p.get("layout") in ("split", "sbs") or not os.path.exists(jp):
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
            if p.get("card") or p.get("broll") or "cx" in p or p.get("layout") in ("split", "sbs"):
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
    cys = []; seginfo = []
    keywords = [k.lower() for k in spec.get("keywords", [])]
    maxw = {"minimal": 4, "lockup": 5, "creator": 4, "pod": 6}.get(style, 4)
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
                for c in chunk([[max(w[0], 0) + t, min(w[1], d) + t, w[2]] for w in words], maxw):
                    if cu is None or c[0][0] < float(cu):
                        caps.append(c); limits.append(min(t + d, float(cu)) if cu is not None else t + d)
                        cys.append(seg.get("cap_y", 0.88 if (seg.get("broll") or {}).get("panel") else None))
        t += d
        print(f"  cut {i + 1}/{len(segs)}", end="\r", flush=True)
    total = t
    print()

    ass = ASS(W, H); sfx = []
    caption_events(ass, caps, limits, keywords, style, cfg, spec.get("accent", "#FFFFFF"), cys)
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
    for j, stk in enumerate(sts):  # {"at": s, "file": "x.mov", "x": 0.8, "y": 0.3} centre position, output timeline
        inputs += ["-i", os.path.abspath(stk["file"] if os.path.isfile(stk["file"]) else os.path.join(ROOT, stk["file"]))]
    place_stickers(sts, seginfo, spec, a.src, W, H)
    for j, stk in enumerate(sts):
        k = 1 + len(sfx) + (1 if mus else 0) + j
        fc += (f"[{k}:v]format=rgba,setpts=PTS-STARTPTS+{float(stk['at']):.3f}/TB[sk{j}];"
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

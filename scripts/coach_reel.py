#!/usr/bin/env python3
"""Coach-show looks on top of scripts/podcast.py (additive: podcast.py itself is not changed).

Adds, measured from Nizam's coach references (see podcast-edit/references/reference-study.md, "Coach / triathlon"):
  layout  "card"     source as a sharp rounded card (default 4:3, 93% width) over a blurred copy of itself (ref cyc25).
                     A segment `broll` (another raw clip / photo) shows inside the card instead, voice continues.
  captions "bold"    heavy caps, 2-3 words, ONE accent word per chunk (keyword, else the strongest word),
                     soft shadow (+ outline with "cap_outline"). V1: orange under the card; V2: yellow, full frame.
  overlays (output-timeline seconds, top level of the spec):
    "progress": {"color": "#FF5A1F"}                       thin bar on the top edge that fills over the clip
    "headline": {"kicker": "IRONMAN · BIKE FIT", "text": "STOP SPRINTING OUT OF THE SWIM", "box": "SPRINTING",
                 "until": 4.5, "y": 0.06}                  mono kicker + heavy caps left-aligned, key word in an accent box
    "panels":   [{"at": 5, "dur": 4, "label": "THE RULE", "text": "AVOID SPIKES ALL DAY", "accent": "ALL DAY"},
                 {"at": 9, "dur": 5, "label": "WHAT A SPRINT DOES", "chart": "spike", "notes": ["▲ HEART RATE SPIKE"]}]
                 dark rounded panel with an accent top rule above the card; charts draw on left -> right.
                 chart presets: spike, flat_vs_zigzag, rise, drop, steady, build, intervals, or
                 "lines": [{"pts": [[0,0.7],[1,0.2]], "color": "#FF5A1F"}] (x 0-1 left->right, y 0 top -> 1 bottom)
usage: same as podcast.py
  python scripts/coach_reel.py <spec.json> --src <raw dir> --tx <tx dir> --out <dir> [--draft] [--sheet]
"""
import json, os, re, shutil, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import podcast as P  # noqa: E402

MONO = "Consolas"
MONO_FILE = "C:/Windows/Fonts/consolab.ttf"
STOP = set("""a an the and or but if so to of in on at for with from by as is are was were be been being it its it's this that
these those i you he she we they me him her us them my your his our their not no do does did have has had will would can
could should just very really then than there here what when where which who how why all any some more most much many
also too into out up down over about like get got go going gonna want okay yeah yes um uh know think thing things
because only even still well one that's what's doesn't don't isn't it's i'm you're we're they're let's give
often based basically gonna gotta kind sort right okay alright actually maybe little bit pretty lot every""".split())


# ----------------------------------------------------------------------------- card layout
def _mask(work, w, h, r):
    p = os.path.join(work, f"mask_{w}x{h}_{r}.png")
    if not os.path.exists(p):
        from PIL import Image, ImageDraw
        m = Image.new("L", (w, h), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], r, fill=255)
        m.save(p)
    return p


_orig_cut = P.cut_segment


def cut_segment(seg, spec, src, tx_src, out, W, H, enc):
    layout = seg.get("layout", spec.get("layout", "full"))
    if layout != "card" or seg.get("card"):
        if layout == "card":
            seg = {**seg, "layout": "full"}
        return _orig_cut(seg, spec, src, tx_src, out, W, H, enc)
    path = P.find_clip(src, seg["clip"])
    d = seg["end"] - seg["start"]
    z = float(seg.get("zoom", 1.0))
    look = seg.get("look", spec.get("look"))
    lk = ("," + P.LOOKS[look]) if look else ""
    aspect = float(spec.get("card_aspect", 4 / 3))
    cw = int(W * float(spec.get("card_w", 0.93))) // 2 * 2
    ch = int(cw / aspect) // 2 * 2
    top = int(H * float(spec.get("card_y", 0.525)) - ch / 2)
    inputs = ["-ss", f"{seg['start']:.3f}", "-t", f"{d:.3f}", "-i", path]
    br = seg.get("broll")
    if br:  # picture from another clip/photo inside the card, voice continues from the speaker
        bpath = br["file"] if os.path.isfile(br["file"]) else (P.find_clip(src, br["file"]) if not os.path.isabs(br["file"]) else br["file"])
        still = bpath.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
        inputs += (["-loop", "1", "-framerate", str(P.FPS), "-t", f"{d:.3f}", "-i", bpath] if still else
                   ["-ss", f"{float(br.get('at', 0)):.3f}", "-t", f"{d:.3f}", "-i", bpath])
        vin, vpath, vz = 1, bpath, float(br.get("zoom", 1.0))
        vcx, vcy = br.get("cx", 0.5), br.get("cy", 0.5)
    else:
        vin, vpath, vz, vcx, vcy = 0, path, z, seg.get("cx", 0.5), seg.get("cy", 0.5 if z <= 1 else 0.42)
    sw, sh_ = P.probe(vpath)
    if not isinstance(vcx, (int, float)):
        vcx = P.resolve_cx({**seg, "cx": vcx}, vpath) if not br else 0.5
    mask = _mask(os.path.dirname(out), cw, ch, int(cw * 0.035))
    mi = inputs.count("-i")
    inputs += ["-loop", "1", "-t", f"{d:.3f}", "-i", mask]
    fc = (f"[{vin}:v]split[a][b];[a]{P.crop_expr(sw, sh_, W / H, 1.0, 0.5, 0.5)},scale={W // 4}:{H // 4},"
          f"gblur=sigma=14,eq=brightness=-0.16:saturation=0.85{lk},scale={W}:{H},fps={P.FPS}[bg];"
          f"[b]{P.crop_expr(sw, sh_, aspect, vz, float(vcx), float(vcy))},scale={cw}:{ch}:flags=lanczos{lk},fps={P.FPS},format=rgba[fg0];"
          f"[{mi}:v]format=gray,scale={cw}:{ch},fps={P.FPS}[m];[fg0][m]alphamerge[fg];"
          f"[bg][fg]overlay=(W-w)/2:{top}:shortest=1[v]")
    nfr = max(1, round(d * P.FPS)); dq = nfr / P.FPS
    fc += f";[v]fps={P.FPS},tpad=stop_mode=clone:stop_duration=0.5,trim=end_frame={nfr},setpts=N/({P.FPS}*TB),setsar=1,format=yuv420p[vo]"
    af = f"aresample=48000,apad,atrim=0:{dq:.6f},afade=t=in:d=0.03,afade=t=out:st={max(dq - 0.04, 0):.3f}:d=0.04"
    P.sh(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", fc, "-map", "[vo]", "-map", "0:a:0",
          "-af", af, "-ac", "2", *enc, "-fps_mode", "passthrough", "-c:a", "pcm_s16le", out])
    return dq


# ----------------------------------------------------------------------------- bold captions
SPEC = {}
_orig_chunk = P.chunk


def chunk(words, maxw, maxdur=1.8):
    if SPEC.get("captions") == "bold":
        maxw = int(SPEC.get("cap_words", 3))
    return _orig_chunk(words, maxw, maxdur)


def _accent_idx(c, keywords):
    k = P.find_key(c, keywords)
    if k:
        return list(range(*k))
    best, bi = 0, None
    for i, w in enumerate(c):
        b = P.bare(w[2])
        if b in STOP or not b:
            continue
        score = len(b) + (6 if re.search(r"\d", b) else 0)
        if score > best:
            best, bi = score, i
    return [bi] if bi is not None and best >= 5 else []


_orig_caps = P.caption_events


def caption_events(ass, caps, limits, keywords, style, cfg, accent, ys=None, *rest, **kw):
    if style != "bold":
        return _orig_caps(ass, caps, limits, keywords, style, cfg, accent, ys, *rest, **kw)
    W, H = ass.W, ass.H
    x0 = W / 2
    size = float(SPEC.get("cap_size", 76))
    sp = float(SPEC.get("cap_spacing", 4))
    ol = float(SPEC.get("cap_outline", 0))
    font = SPEC.get("cap_font", "Archivo Black")
    for i, c in enumerate(caps):
        y0 = (ys[i] if ys and i < len(ys) and ys[i] is not None else cfg["cap_y"]) * H
        st = c[0][0]
        en = caps[i + 1][0][0] if i + 1 < len(caps) else c[-1][1] + 0.35
        en = min(en, c[-1][1] + 0.5, limits[i])
        acc = _accent_idx(c, keywords)
        parts = []
        for j, w in enumerate(c):
            t = P.esc(w[2].upper())
            col = P.ass_color(accent) if j in acc else "&HFFFFFF&"
            parts.append(f"{{\\c{col}}}{t}")
        plain = " ".join(w[2].upper() for w in c)
        fs = size
        while (aw(plain, fs, sp) if font == "Archivo Black" else P.text_w(font, plain, fs, sp)) > W * 0.90 and fs > 40:
            fs *= 0.93
        head = (f"{{\\an5\\pos({x0:.0f},{y0:.0f})\\fn{font}\\fs{fs:.0f}\\fsp{sp:.0f}\\bord{ol:.0f}\\3c&H000000&"
                f"\\shad4\\4c&H000000&\\4a&H60&\\blur0.8\\fscx88\\fscy88\\t(0,90,\\fscx100\\fscy100)}}")
        ass.add(st, en, head + " ".join(parts))


# ----------------------------------------------------------------------------- overlays
AK = 1000 / (1035 + 312)  # libass sizes Archivo Black by winAscent+winDescent: rendered width = measured * AK


def aw(text, fs, sp=0):
    return P.text_w("Archivo Black", text, fs) * AK + sp * max(len(text) - 1, 0)


def _rrect(x, y, w, h, r):
    k = r * 0.45
    return (f"m {x + r:.0f} {y:.0f} l {x + w - r:.0f} {y:.0f} b {x + w - k:.0f} {y:.0f} {x + w:.0f} {y + k:.0f} {x + w:.0f} {y + r:.0f} "
            f"l {x + w:.0f} {y + h - r:.0f} b {x + w:.0f} {y + h - k:.0f} {x + w - k:.0f} {y + h:.0f} {x + w - r:.0f} {y + h:.0f} "
            f"l {x + r:.0f} {y + h:.0f} b {x + k:.0f} {y + h:.0f} {x:.0f} {y + h - k:.0f} {x:.0f} {y + h - r:.0f} "
            f"l {x:.0f} {y + r:.0f} b {x:.0f} {y + k:.0f} {x + k:.0f} {y:.0f} {x + r:.0f} {y:.0f}")


def _draw(x0, y0, path, color, alpha="00", extra=""):
    return f"{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\c{P.ass_color(color)}\\1a&H{alpha}&{extra}}}{path}{{\\p0}}"


def _mono(size, x, y, color, an=7):
    return f"{{\\an{an}\\pos({x:.0f},{y:.0f})\\fn{MONO}\\b1\\fs{size:.0f}\\fsp2\\c{P.ass_color(color)}\\bord0\\shad0}}"


CHARTS = {
    "spike": [{"pts": [[0, .82], [.36, .8], [.44, .78], [.5, .08], [.56, .76], [.66, .8], [1, .79]], "color": "A"}],
    "flat_vs_zigzag": [{"pts": [[0, .12], [1, .12]], "color": "A"},
                       {"pts": [[0, .85], [.08, .4], [.16, .85], [.24, .45], [.32, .85], [.4, .35], [.48, .85], [.56, .3],
                                [.64, .85], [.72, .4], [.8, .85], [.88, .45], [1, .8]], "color": "#FFFFFF"}],
    "rise": [{"pts": [[0, .85], [.25, .7], [.5, .5], [.75, .3], [1, .1]], "color": "A"}],
    "drop": [{"pts": [[0, .15], [.3, .2], [.55, .45], [.8, .75], [1, .85]], "color": "A"}],
    "steady": [{"pts": [[0, .55], [.2, .5], [.4, .52], [.6, .49], [.8, .51], [1, .5]], "color": "A"}],
    "build": [{"pts": [[0, .85], [.2, .75], [.4, .62], [.6, .48], [.8, .36], [1, .25]], "color": "A"},
              {"pts": [[0, .9], [1, .9]], "color": "#777777"}],
    "intervals": [{"pts": [[0, .8], [.1, .8], [.1, .2], [.25, .2], [.25, .8], [.4, .8], [.4, .2], [.55, .2], [.55, .8],
                           [.7, .8], [.7, .2], [.85, .2], [.85, .8], [1, .8]], "color": "A"}],
}


def _stroke(pts, x, y, w, h):
    ab = [(x + px * w, y + py * h) for px, py in pts]
    seq = ab + ab[-2::-1]
    return "m " + " l ".join(f"{a:.0f} {b:.0f}" for a, b in seq)


_orig_over = P.build_overlays


def build_overlays(ass, spec, total, cfg, sfx, *rest, **kw):
    _orig_over(ass, spec, total, cfg, sfx, *rest, **kw)
    W, H = ass.W, ass.H
    acc = spec.get("accent", "#FF5A1F")
    pr = spec.get("progress")
    if pr:
        col = pr.get("color", acc)
        ass.add(0, total, _draw(0, 0, f"m 0 0 l {W} 0 l {W} 9 l 0 9", "#000000", "80"), 7)
        ass.add(0, total, _draw(0, 0, f"m 0 0 l {W} 0 l {W} 9 l 0 9", col,
                                extra=f"\\clip(0,0,1,20)\\t(0,{int(total * 1000)},\\clip(0,0,{W},20))"), 8)
    hl = spec.get("headline")
    if hl:
        until = min(float(hl.get("until", 4.0)), total)
        x = 0.06 * W
        y = float(hl.get("y", 0.075)) * H
        if hl.get("kicker"):
            ass.add(0.05, until, f"{{\\fad(120,0)}}" + _mono(30, x + 34, y, acc) + P.esc(hl["kicker"].upper()), 9)
            ass.add(0.05, until, _draw(0, 0, f"m {x:.0f} {y + 8:.0f} l {x + 18:.0f} {y + 8:.0f} l {x + 18:.0f} {y + 26:.0f} l {x:.0f} {y + 26:.0f}", acc), 9)
        words = hl["text"].upper().split()
        box = [b.upper() for b in (hl.get("box", "").split())]
        fs = float(hl.get("size", 96))
        maxw = W * 0.88
        lines, cur = [], []
        for w in words:
            if cur and aw(" ".join(cur + [w]), fs) > maxw:
                lines.append(cur); cur = []
            cur.append(w)
        lines.append(cur)
        while len(lines) > 4 and fs > 50:
            fs *= 0.9
            lines, cur = [], []
            for w in words:
                if cur and aw(" ".join(cur + [w]), fs) > maxw:
                    lines.append(cur); cur = []
                cur.append(w)
            lines.append(cur)
        ly = y + 60
        sp_w = aw(" ", fs)
        for li, ln in enumerate(lines):
            st = 0.08 + 0.09 * li
            cx = x
            for w in ln:
                ww = aw(w, fs)
                isbox = P.bare(w).upper() in box or w in box
                if isbox:
                    pad = fs * 0.12
                    ass.add(st, until, f"{{\\fad(100,0)}}" + _draw(0, 0, f"m {cx - pad:.0f} {ly + fs * 0.06:.0f} l {cx + ww + pad:.0f} {ly + fs * 0.06:.0f} "
                                                               f"l {cx + ww + pad:.0f} {ly + fs * 1.04:.0f} l {cx - pad:.0f} {ly + fs * 1.04:.0f}", acc), 9)
                ass.add(st, until, f"{{\\an7\\pos({cx:.0f},{ly:.0f})\\fnArchivo Black\\fs{fs:.0f}\\c&HFFFFFF&\\bord0"
                                   f"\\shad3\\4a&H70&\\fad(100,0)}}" + P.esc(w), 10)
                cx += ww + sp_w + (fs * 0.16 if isbox else 0)
            ly += fs * 1.02
        sfx.append(("whoosh_soft2.mp3", 0.0, 0.4))
    for pn in spec.get("panels", []):
        at, d = float(pn["at"]), float(pn.get("dur", 4))
        en = min(at + d, total)
        px, pw = 0.055 * W, 0.89 * W
        py = float(pn.get("y", 0.075)) * H
        has_chart = bool(pn.get("chart") or pn.get("lines"))
        ph = float(pn.get("h", 0.25 if has_chart else 0.17)) * H
        fade = "\\fad(160,120)"
        ass.add(at, en, _draw(0, 0, _rrect(px, py, pw, ph, 22), "#110F0F", "28", extra=fade), 9)
        ass.add(at, en, _draw(0, 0, _rrect(px, py, pw, 6, 3), acc, extra=fade + f"\\clip({px:.0f},0,{px + 1:.0f},{H})"
                                                                      f"\\t(0,300,\\clip({px:.0f},0,{px + pw:.0f},{H}))"), 10)
        lx, ly = px + 36, py + 34
        if pn.get("label"):
            ass.add(at + 0.05, en, _draw(0, 0, f"m {lx:.0f} {ly + 6:.0f} l {lx + 16:.0f} {ly + 6:.0f} l {lx + 16:.0f} {ly + 22:.0f} l {lx:.0f} {ly + 22:.0f}", acc, extra=fade), 11)
            ass.add(at + 0.05, en, "{" + fade + "}" + _mono(28, lx + 30, ly, acc) + P.esc(pn["label"].upper()), 11)
        cy = ly + 50
        if pn.get("text"):
            words = pn["text"].upper().split()
            accw = set((pn.get("accent") or "").upper().split())
            fs = float(pn.get("size", 74))
            maxw = pw - 72
            while True:
                lines, cur = [], []
                for w in words:
                    if cur and aw(" ".join(cur + [w]), fs) > maxw:
                        lines.append(cur); cur = []
                    cur.append(w)
                lines.append(cur)
                if len(lines) <= (2 if has_chart else 3) or fs < 44:
                    break
                fs *= 0.9
            for k, ln in enumerate(lines):
                txt = " ".join((f"{{\\c{P.ass_color(acc)}}}" if P.bare(w).upper() in accw or w in accw else "{\\c&HFFFFFF&}") + P.esc(w) for w in ln)
                ass.add(at + 0.12 + 0.08 * k, en, f"{{\\an7\\pos({lx:.0f},{cy:.0f})\\fnArchivo Black\\fs{fs:.0f}\\bord0\\shad0"
                                                  f"\\fad(140,120)\\fscx92\\fscy92\\t(0,140,\\fscx100\\fscy100)}}" + txt, 11)
                cy += fs * 1.05
        notes = pn.get("notes", [])
        if has_chart:
            lines = pn.get("lines") or CHARTS[pn["chart"]]
            gx, gw = lx, pw - 72
            gy = cy + (8 if pn.get("text") else 0) + (34 if notes[:1] and pn.get("note_top", True) else 0)
            gh = py + ph - gy - (54 if len(notes) > 1 else 30)
            if notes[:1] and pn.get("note_top", True):
                ass.add(at + 0.2, en, "{" + fade + "}" + _mono(26, lx + gw / 2, gy - 34, "#FFFFFF", an=8) + P.esc(notes[0]), 11)
            draw_t = int(float(pn.get("draw", 1.1)) * 1000)
            for k, ln in enumerate(lines):
                col = acc if ln.get("color", "A") == "A" else ln["color"]
                path = _stroke(ln["pts"], gx, gy, gw, gh)
                st = at + 0.25 + 0.35 * k
                ass.add(st, en, f"{{\\an7\\pos(0,0)\\p1\\1a&HFF&\\bord{ln.get('w', 3.5)}\\3c{P.ass_color(col)}\\shad0\\blur0.5"
                                f"\\clip({gx:.0f},0,{gx + 1:.0f},{H})\\t(0,{draw_t},\\clip({gx - 10:.0f},0,{gx + gw + 10:.0f},{H}))\\fad(0,120)}}"
                                f"{path}{{\\p0}}", 11)
            if len(notes) > 1:
                ass.add(at + 0.25 + draw_t / 1000, en, "{" + fade + "}" + _mono(24, gx + gw, py + ph - 40, "#D9D9D9", an=9) + P.esc(notes[1]), 11)
            ass.add(at + 0.05, en, _draw(0, 0, f"m {gx:.0f} {gy + gh + 6:.0f} l {gx + gw:.0f} {gy + gh + 6:.0f} l {gx + gw:.0f} {gy + gh + 8:.0f} l {gx:.0f} {gy + gh + 8:.0f}", "#FFFFFF", "C0", extra=fade), 10)
        elif notes:
            for k, n in enumerate(notes):
                ass.add(at + 0.3 + 0.25 * k, en, "{" + fade + "}" + _mono(30, lx, cy + 6 + k * 44, "#FFFFFF") + P.esc(n), 11)
        sfx.append(("whoosh_soft.mp3", at, 0.3))


# ----------------------------------------------------------------------------- run
def main():
    spec_path = sys.argv[1]
    SPEC.update(json.load(open(spec_path, encoding="utf-8")))
    P.cut_segment = cut_segment
    P.chunk = chunk
    P.caption_events = caption_events
    P.build_overlays = build_overlays
    P.FONT_FILES.setdefault("Consolas", MONO_FILE)
    # fonts for libass: podcast.py copies assets/fonts into <work>/<id>/fonts; add the mono font there too
    work = None
    for i, a in enumerate(sys.argv):
        if a == "--work" and i + 1 < len(sys.argv):
            work = sys.argv[i + 1]
    import tempfile
    wdir = os.path.join(work or os.path.join(tempfile.gettempdir(), "podcast-work"), SPEC["id"], "fonts")
    os.makedirs(wdir, exist_ok=True)
    if os.path.exists(MONO_FILE):
        shutil.copy(MONO_FILE, os.path.join(wdir, "consolab.ttf"))
    P.main()


if __name__ == "__main__":
    main()

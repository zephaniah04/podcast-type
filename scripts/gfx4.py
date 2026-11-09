#!/usr/bin/env python3
"""FUEL LAB packaging graphics for Carrie ep01 v4 (title sting, chapter cards + tags, hero punch cards, lower thirds,
headline overlays, outro, transition stingers, background plates).

Look + motion live in HTML/CSS/GSAP templates (projects/carrie-ep01/v4/gfx_src/: template.html, fuel.css, fuel.js);
each item is rendered frame-exact by HyperFrames (headless Chrome) to an RGBA PNG sequence in a C: work dir, then
encoded here:  opaque -> H.264 mp4 (yuv420p, BT.709, crf 14)   alpha -> QuickTime Animation (qtrle, argb) .mov cropped
to the element's union bounding box (same codec as scripts/fx.py)   plates -> png.

usage
  python scripts/gfx4.py                       # render everything in v4/gfx.json that changed
  python scripts/gfx4.py --from-plan           # (re)build v4/gfx.json from v4/edit_plan.json, then render
  python scripts/gfx4.py --only chap_04,hero_salt --force
  python scripts/gfx4.py --qa                  # + frames every 0.2 s -> contact sheets in %TEMP%/v4/gfx_test
gfx.json: {"episode": {...}, "items": [{"id", "kind", ...}]}; kinds: title chapter tag hero lt headline outro
transition plate (fields: see style_guide.md). A chapter item also renders its chapter_tag_NN.mov unless "tag": false.
Re-runs skip items whose JSON + template files are unchanged (signature in v4/gfx/_sig/). Writes v4/gfx/manifest.json.
"""
import argparse, glob, hashlib, json, os, re, shutil, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EP = os.path.join(ROOT, "projects", "carrie-ep01")
V4 = os.path.join(EP, "v4")
SRC = os.path.join(V4, "gfx_src")
OUT = os.path.join(V4, "gfx")
TMP = os.path.join(os.environ.get("LOCALAPPDATA", r"C:\Users\raika\AppData\Local"), "Temp", "v4")
WORK = os.path.join(TMP, "gfx_work")
BIG = os.path.join(TMP, "gfx_big")
TEST = os.path.join(TMP, "gfx_test")
FONTS = os.path.join(ROOT, "assets", "fonts")
GSAP = os.path.join(ROOT, "node_modules", "hyperframes", "dist", "vendor", "npm", "gsap@3.15.0", "dist", "gsap.min.js")
HF = os.path.join(ROOT, "node_modules", "hyperframes", "bin", "hyperframes.mjs")
FPS = 30
BIG_MB = 50
FONT_FILES = ["ArchivoBlack-Regular.ttf", "InterTight-Heavy.ttf", "InterTight-Medium.ttf", "InstrumentSerif-Italic.ttf",
              "SpaceMono-Regular.ttf", "SpaceMono-Bold.ttf"]
DUR = {"title": 4.5, "chapter": 3.0, "tag": 4.0, "lt": 4.5, "headline": 3.5, "outro": 6.0, "transition": 0.5, "plate": 0.1,
       "hero": {"punch": 2.6, "number": 2.8, "quote": 3.0, "myth": 3.0}}
ALPHA = {"tag", "lt", "headline", "transition"}
SFX = "assets/sfx/"


def dur_of(it):
    if it.get("dur"):
        return float(it["dur"])
    d = DUR[it["kind"]]
    return float(d.get(it.get("style", "punch"), 2.6) if isinstance(d, dict) else d)


def strip(prefix, s):
    return s[len(prefix):] if s.startswith(prefix) else s


def out_name(it):
    k, i = it["kind"], it["id"]
    if k == "title": return "title_sting.mp4"
    if k == "chapter": return f"chap_{int(it['n']):02d}.mp4"
    if k == "tag": return f"chapter_tag_{int(it['n']):02d}.mov"
    if k == "hero": return f"hero_{strip('hero_', i)}.mp4"
    if k == "lt": return f"lt_{strip('lt_', i)}.mov"
    if k == "headline": return f"hl_{strip('hl_', i)}.mov"
    if k == "outro": return "outro.mp4"
    if k == "transition": return f"tr_{it.get('variant', strip('tr_', i))}.mov"
    if k == "plate": return (i if i.startswith("bg_") else "bg_" + it.get("variant", i)) + ".png"
    raise SystemExit(f"unknown kind {k}")


def sfx_plan(it, d):
    """suggested SFX hits (seconds into the clip, file under assets/sfx, gain dB relative to the file)."""
    k, st = it["kind"], it.get("style", "punch")
    if k == "title":
        h = [(0.0, "whoosh_slow.mp3", -10), (0.28, "transition_short.mp3", -8), (0.72, "click.wav", -12), (1.06, "click.wav", -12),
             (1.8, "pop.mp3", -14), (d - 0.5, "whoosh_fast.mp3", -10)]
    elif k == "chapter":
        h = [(0.0, "whoosh_fast.mp3", -9), (0.12, "click.wav", -12), (0.3, "pop.mp3", -14), (d - 0.22, "whoosh_soft.mp3", -12)]
    elif k == "tag":
        h = [(0.0, "click.wav", -14), (d - 0.42, "whoosh_soft.mp3", -16)]
    elif k == "lt":
        h = [(0.05, "whoosh_soft2.mp3", -13), (0.2, "click.wav", -14)]
    elif k == "headline":
        h = [(0.0, "whoosh_soft.mp3", -12), (0.12, "click.wav", -13)]
    elif k == "hero" and st == "number":
        h = [(0.1, "whoosh_fast.mp3", -10), (0.95, "ding.mp3", -12)]
    elif k == "hero" and st == "myth":
        h = [(0.05, "whoosh_soft.mp3", -11), (float(it.get("strike_at", 0.95)), "click.wav", -10), (float(it.get("strike_at", 0.95)) + 0.3, "pop.mp3", -12)]
    elif k == "hero" and st == "quote":
        h = [(0.0, "whoosh_soft2.mp3", -12)]
    elif k == "hero":
        h = [(0.08, "whoosh_soft.mp3", -11), (0.1, "click.wav", -13)]
    elif k == "outro":
        h = [(0.3, "whoosh_slow.mp3", -14)]
    elif k == "transition":
        h = [(0.0, "whoosh_fast.mp3", -8)]
    else:
        h = []
    return [{"at": round(max(0.0, a), 2), "file": SFX + f, "gain_db": g} for a, f, g in h]


# ----------------------------------------------------------------------------------------------- spec
def default_spec():
    br = "projects/carrie-ep01/broll/"
    ch = [
        ("What I eat in a day", "a HYROX athlete's plate, audited", "NUTRITION", "chicken-rice.jpg", "EAT"),
        ("How much water you actually need", "thirst is only half the story", "HYDRATION", "office-bottle.jpg", "WATER"),
        ("ChatGPT was my dietitian", "supplements, vitamin D and guesswork", "SUPPLEMENTS", "supplements.jpg", "CHATGPT"),
        ("The salt problem", "white streaks, cramps, every single race", "SODIUM", "salt-pills.jpg", "SALT"),
        ("The 1 kg = 1 litre sweat test", "weigh yourself before and after", "HYDRATION", "digital-scale.jpg", "SWEAT"),
        ("Sodium, caffeine and only 2 gels", "race-day fuelling, rebuilt", "RACE DAY", "hyrox.jpg", "2 GELS"),
        ("Muscle without getting slower", "strength work for endurance athletes", "STRENGTH", "deadlift.jpg", "SLOWER"),
        ("Training fasted?", "what to eat before the gym", "TIMING", "banana-pb.jpg", "FASTED?"),
        ("Is the 30-minute window real?", "recovery timing, decoded", "RECOVERY", "milkshake.jpg", "REAL?"),
        ("What creatine actually does", "the most studied supplement there is", "SUPPLEMENTS", "supplement-powder.jpg", "CREATINE"),
        ("Why 50 g of protein is plenty", "per meal, not per day", "PROTEIN", "chicken-breast.jpg", "PLENTY"),
        ("Too tired to cook", "no-cook recovery dinners", "RECOVERY", "tuna-sandwich.jpg", "TIRED"),
        ("Real food vs multivitamins", "where the nutrients really come from", "MICRONUTRIENTS", "veg-market.jpg", "REAL"),
    ]
    items = [{"id": "title_sting", "kind": "title", "title": "Fuelling like an endurance athlete",
              "names": "Nizam × Carrie Mullin Innes", "role": "High-Performance Sports Dietitian · IOC Dip. Sports Nutrition",
              "photos": [br + "hyrox.jpg", br + "triathlon-swim.jpg", br + "electrolyte-tabs.jpg"]}]
    for n, (t, k, topic, ph, acc) in enumerate(ch, 1):
        items.append({"id": f"chap_{n:02d}", "kind": "chapter", "n": n, "total": len(ch), "title": t, "kicker": k, "topic": topic,
                      "photo": br + ph, "accent_word": acc, "placeholder": True})
    items += [
        {"id": "hero_salty", "kind": "hero", "style": "punch", "screen": "You're a salty sweater", "accent_word": "salty"},
        {"id": "hero_sodium", "kind": "hero", "style": "number", "screen": "1,000 mg of sodium per hour", "kicker": "CARRIE'S RACE TARGET"},
        {"id": "hero_litre", "kind": "hero", "style": "quote", "screen": "If you lose a kilo, that's a litre you didn't replace.", "accent_word": "litre"},
        {"id": "hero_window", "kind": "hero", "style": "myth", "myth": "The 30-minute window", "fact": "The whole day matters more", "accent_word": "day"},
        {"id": "lt_carrie", "kind": "lt", "name": "Carrie Mullin Innes", "role": "High-Performance Sports Dietitian · IOC Dip. Sports Nutrition", "label": "GUEST", "idx": "01"},
        {"id": "lt_nizam", "kind": "lt", "name": "Nizam", "role": "Training to become an endurance athlete", "label": "HOST", "idx": "02"},
        {"id": "hl_step1", "kind": "headline", "h3": "STEP 01", "h1": "Weigh yourself", "h2": "before and after the session", "pos": "tl"},
        {"id": "hl_rule", "kind": "headline", "h3": "THE RULE", "h1": "1 kg lost = 1 litre", "accent_word": "litre", "pos": "center"},
        {"id": "hl_why", "kind": "headline", "h3": "WHY IT MATTERS", "h1": "Cramps start with sodium", "accent_word": "sodium", "style": "ink", "pos": "left"},
        {"id": "outro", "kind": "outro", "title": "Fuelling like an endurance athlete", "photo": br + "triathlon-swim.jpg"},
        {"id": "tr_ink", "kind": "transition", "variant": "ink"},
        {"id": "tr_bars", "kind": "transition", "variant": "bars"},
        {"id": "tr_green", "kind": "transition", "variant": "green"},
        {"id": "tr_blocks", "kind": "transition", "variant": "blocks"},
        {"id": "bg_paper", "kind": "plate", "variant": "paper"},
        {"id": "bg_grid", "kind": "plate", "variant": "green"},
    ]
    return {"episode": {"title": "Fuelling like an endurance athlete", "ep": "01", "series": "FUEL LAB",
                        "host": {"name": "Nizam", "role": "Training to become an endurance athlete"},
                        "guest": {"name": "Carrie Mullin Innes", "role": "High-Performance Sports Dietitian · IOC Dip. Sports Nutrition"}},
            "items": items}


def slug(s, n=24):
    t = re.sub(r"[^a-z0-9]+", "_", str(s).lower()).strip("_")
    if len(t) > n: t = t[:n + 1].rsplit("_", 1)[0] if "_" in t[:n + 1] else t[:n]
    return t.strip("_") or "x"


def tc(sec):
    sec = int(round(float(sec))); return f"{sec // 3600:02d}:{sec % 3600 // 60:02d}:{sec % 60:02d}"


CH_PICK = {  # chapter n -> (topic chip, B-roll still for the card, accent word)
    1: ("NUTRITION", "lunch-boxes.jpg", "EAT"), 2: ("SUPPLEMENTS", "supplements.jpg", "DIETITIAN"),
    3: ("CRAMPS", "salt-pills.jpg", "FALL,"), 4: ("HYDRATION", "digital-scale.jpg", "LITRE"),
    5: ("RACE FUEL", "coffee.jpg", "CARBS?"), 6: ("STRENGTH", "deadlift.jpg", "SLOWER"),
    7: ("TIMING", "alarm-clock.jpg", "REAL?"), 8: ("SUPPLEMENTS", "fish-oil.jpg", "FAT?"),
    9: ("PROTEIN", "chicken-breast.jpg", "PLENTY"), 10: ("FUEL TIMING", "banana-pb.jpg", "EMPTY"),
    11: ("RECOVERY", "canned-tuna.jpg", "COOK?"), 12: ("RECOVERY", "protein-powder.jpg", "DINNER"),
    13: ("MUSCLE", "weightlifting.jpg", "MUSCLE"), 14: ("MICRONUTRIENTS", "multivitamin.jpg", "REAL FOOD?")}
BANNED_PHOTOS = {"sweaty-athlete.jpg", "fitness-race.jpg", "pain-spray.jpg", "cramp.jpg", "sports-drink.jpg", "energy-drink-cans.jpg", "finish-line.jpg"}  # likeness / brand logos
HERO_LABEL = {"number": "BY THE NUMBERS", "punch": "KEY POINT", "quote": "ON THE RECORD", "myth": "MYTH CHECK"}
OPS = ("=", "+", "->", "→", "≠", "/", "VS")


def auto_accent(screen):
    """operator present -> the words after the last operator; else the last non-small word."""
    w = str(screen).split()
    idx = [i for i, t in enumerate(w) if t.upper() in OPS]
    if idx:
        return " ".join(t for t in w[idx[-1] + 1:] if not re.match(r"^[\d.,:+-]+$", t)) or None
    small = {"a", "an", "the", "of", "to", "in", "on", "for", "and", "or", "is", "it", "at", "you", "i", "my", "me", "your", "that"}
    for t in reversed(w):
        if re.sub(r"[^a-z]", "", t.lower()) not in small: return t
    return None


_TX = {}


def speaker_at(f, t):
    """'N' (Nizam, left) / 'C' (Carrie, right) from the word-timed transcript."""
    name = {"A": "IMG_4342-001", "B": "IMG_4343-002"}.get(f)
    if not name: return None
    if name not in _TX:
        p = os.path.join(EP, "tx", name + ".json"); _TX[name] = []
        if os.path.exists(p):
            for seg in json.load(open(p, encoding="utf-8")):
                _TX[name] += [(w[0], w[4] if len(w) > 4 else None) for w in seg.get("w", [])]
    best = min(_TX[name], key=lambda x: abs(x[0] - float(t)), default=None)
    return {"L": "N", "R": "C"}.get(best[1]) if best else None


def from_plan(plan, base):
    """edit_plan.json -> gfx.json. Plan owns chapter title/kicker and hero screen/style (copied verbatim); everything
    else (title sting, LTs, headlines, outro, transitions, plates, hand-set fields on same-id items) is kept from base."""
    old = {it["id"]: it for it in base.get("items", [])}
    items = [it for it in base.get("items", []) if it["kind"] not in ("chapter", "hero")]
    chs = plan.get("chapters") or []
    for c in chs:
        n = int(c.get("n", len(items))); cid = f"chap_{n:02d}"; o = old.get(cid, {})
        if o.get("placeholder"): o = {}
        topic, ph, acc = CH_PICK.get(n, (None, None, None))
        it = {"id": cid, "kind": "chapter", "n": n, "total": len(chs), "title": c.get("title", f"Chapter {n}"), "kicker": c.get("kicker", "")}
        if isinstance(c.get("out_start_s"), (int, float)): it["tc"] = tc(c["out_start_s"])
        it["topic"] = o.get("topic") or topic or ""
        it["photo"] = o.get("photo") if o.get("photo") and not o.get("placeholder") else ("projects/carrie-ep01/broll/" + ph if ph else None)
        it["accent_word"] = o.get("accent_word") if o.get("accent_word") and not o.get("placeholder") else (acc or auto_accent(it["title"]))
        for k in ("bg", "tag", "tag_title", "photo_label"):
            if k in o: it[k] = o[k]
        items.append({k: v for k, v in it.items() if v not in (None, "")})
    for i, h in enumerate(plan.get("hero_lines") or []):
        screen = h.get("screen", ""); hid = h.get("id") or f"hero_{i + 1:02d}_{slug(screen, 18)}"
        o = old.get(hid, {}); st = h.get("style", "punch")
        it = {"id": hid, "kind": "hero", "style": st, "screen": screen, "chapter": h.get("chapter"), "plan_index": i,
              "f": h.get("f"), "t": h.get("t"), "label_top": f"CHAPTER {int(h.get('chapter') or 0):02d} — {HERO_LABEL.get(st, 'KEY POINT')}"}
        if st != "number": it["accent_word"] = h.get("accent_word") or o.get("accent_word") or auto_accent(screen)
        if st == "quote":
            who = h.get("who") or ("N" if re.match(r"^I", screen) else speaker_at(h.get("f"), h.get("t", 0)))
            it["who"] = who; it["by"] = "NIZAM" if who == "N" else "CARRIE MULLIN INNES · SPORTS DIETITIAN"
        for k in ("bg", "dur", "value", "unit", "myth", "fact", "accent_style", "size"):
            if h.get(k) is not None: it[k] = h[k]
            elif o.get(k) is not None: it[k] = o[k]
        items.append({k: v for k, v in it.items() if v is not None})
    ep = dict(base.get("episode", {}))
    if plan.get("title"): ep["title"] = plan["title"]
    for it in items:
        if it["kind"] in ("title", "outro") and plan.get("title"): it["title"] = plan["title"]
    order = {"title": 0, "chapter": 1, "outro": 2, "lt": 3, "hero": 4, "headline": 5, "transition": 6, "plate": 7}
    items.sort(key=lambda it: (order.get(it["kind"], 9), it.get("n", 0), it.get("plan_index", 0)))
    return {"episode": ep, "items": items}


def expand(spec):
    """chapter items also render their top-left tag."""
    out = []
    for it in spec["items"]:
        out.append(it)
        if it["kind"] == "chapter" and it.get("tag", True) is not False:
            out.append({"id": f"chapter_tag_{int(it['n']):02d}", "kind": "tag", "n": it["n"], "title": it.get("tag_title") or it["title"]})
    return out


# ----------------------------------------------------------------------------------------------- render
SECTION = {"chapter": "CHAPTER CARD", "tag": "CHAPTER TAG", "lt": "LOWER THIRD", "headline": "HEADLINE", "hero": "HERO cards",
           "title": "TITLE STING", "outro": "OUTRO", "transition": "TRANSITIONS", "plate": "PLATES"}


def template_hash(kind=None):
    """hash of template.html + fuel.css + the shared part of fuel.js + this kind's section only, so editing one
    kind's builder does not re-render every other kind."""
    h = hashlib.sha1()
    for f in ("template.html", "fuel.css"):
        h.update(open(os.path.join(SRC, f), "rb").read())
    js = open(os.path.join(SRC, "fuel.js"), encoding="utf-8").read()
    marks = [(m.start(), m.group(1)) for m in re.finditer(r"// -{20,} ([A-Za-z ]+?) \(", js)]
    tail = js.index("const B = {")
    if not marks or kind is None:
        h.update(js.encode("utf-8")); return h.hexdigest()
    h.update(js[:marks[0][0]].encode("utf-8")); h.update(js[tail:].encode("utf-8"))
    bounds = marks + [(tail, "END")]
    for (a, name), (b, _) in zip(bounds, bounds[1:]):
        if name.strip() == SECTION.get(kind):
            h.update(js[a:b].encode("utf-8"))
    return h.hexdigest()


def photos_of(it):
    ps = []
    for k in ("photo",):
        if it.get(k): ps.append(it[k])
    ps += list(it.get("photos") or [])
    return ps


def signature(it, th):
    s = json.dumps(it, sort_keys=True, ensure_ascii=False) + "|" + th
    for p in photos_of(it):
        ap = p if os.path.isabs(p) else os.path.join(ROOT, p)
        if os.path.exists(ap): s += f"|{p}:{os.path.getsize(ap)}"
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def grain_png(path):
    if os.path.exists(path): return
    import numpy as np
    r = np.random.default_rng(7); v = r.normal(0, 1, (256, 256))
    a = np.clip(np.abs(v) * 30, 0, 110).astype(np.uint8)
    rgb = np.where(v[..., None] > 0, 255, 0).astype(np.uint8).repeat(3, axis=2)
    Image.fromarray(np.dstack([rgb, a]), "RGBA").save(path)


def prep_work(it, d, wd):
    shutil.rmtree(wd, ignore_errors=True); os.makedirs(os.path.join(wd, "fonts")); os.makedirs(os.path.join(wd, "img"))
    for f in FONT_FILES: shutil.copy(os.path.join(FONTS, f), os.path.join(wd, "fonts", f))
    for f in ("fuel.css", "fuel.js"): shutil.copy(os.path.join(SRC, f), os.path.join(wd, f))
    shutil.copy(GSAP, os.path.join(wd, "gsap.min.js"))
    grain_png(os.path.join(WORK, "grain.png")); shutil.copy(os.path.join(WORK, "grain.png"), os.path.join(wd, "grain.png"))
    for p in photos_of(it):
        ap = p if os.path.isabs(p) else os.path.join(ROOT, p)
        if os.path.basename(ap) in BANNED_PHOTOS:
            raise SystemExit(f"{it['id']}: {os.path.basename(ap)} is banned (likeness / brand logo) - pick another photo")
        if os.path.exists(ap):
            im = Image.open(ap).convert("RGB"); im.thumbnail((1400, 1400)); im.save(os.path.join(wd, "img", os.path.basename(ap)), quality=92)
        else:
            print(f"  ! missing photo {p}", flush=True)
    data = dict(it)
    gfx = {"kind": it["kind"], "dur": d, "data": data}
    html = open(os.path.join(SRC, "template.html"), encoding="utf-8").read()
    html = html.replace("{{DUR}}", f"{d:g}").replace("{{GFX}}", json.dumps(gfx, ensure_ascii=False).replace("</", "<\\/"))
    open(os.path.join(wd, "index.html"), "w", encoding="utf-8").write(html)


def hf_render(wd, workers, alpha):
    """alpha kinds -> RGBA png sequence; opaque kinds -> HyperFrames mp4 (crf 10, ~3x faster than png capture)."""
    png = os.path.join(wd, "png"); shutil.rmtree(png, ignore_errors=True)
    if alpha:
        cmd = ["node", HF, "render", wd, "--format", "png-sequence", "-o", png, "--quiet", "--workers", str(workers), "--fps", str(FPS)]
    else:
        cmd = ["node", HF, "render", wd, "--format", "mp4", "--crf", "10", "-o", os.path.join(wd, "hf.mp4"), "--quiet", "--workers", str(workers), "--fps", str(FPS)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if not alpha and r.returncode == 0 and os.path.exists(os.path.join(wd, "hf.mp4")):
        return [os.path.join(wd, "hf.mp4")]
    frames = sorted(glob.glob(os.path.join(png, "*.png")))
    if r.returncode != 0 or not frames:
        open(os.path.join(wd, "render.log"), "w", encoding="utf-8").write(r.stdout + "\n" + r.stderr)
        raise RuntimeError(f"hyperframes render failed ({r.returncode}) in {wd}:\n{(r.stderr or r.stdout)[-1500:]}")
    return frames


def union_bbox(frames, pad=6):
    x0 = y0 = 10 ** 9; x1 = y1 = -1
    for f in frames:
        with Image.open(f) as im:
            b = im.getchannel("A").point(lambda v: 255 if v > 2 else 0).getbbox()
        if b:
            x0, y0, x1, y1 = min(x0, b[0]), min(y0, b[1]), max(x1, b[2]), max(y1, b[3])
    if x1 < 0: return (0, 0, 1920, 1080)
    x0, y0 = max(0, x0 - pad), max(0, y0 - pad); x1, y1 = min(1920, x1 + pad), min(1080, y1 + pad)
    w, h = (x1 - x0 + 1) // 2 * 2, (y1 - y0 + 1) // 2 * 2
    if x0 + w > 1920: x0 = 1920 - w
    if y0 + h > 1080: y0 = 1080 - h
    return (x0, y0, w, h)


GRAIN = {"ink": 5, "paper": 4, "green": 4}  # ffmpeg luma noise strength (temporal) per background


def grain_key(it):
    k = it["kind"]
    if k == "chapter": return it.get("bg") or ("green" if int(it.get("n", 1)) % 2 else "paper")
    if k == "hero": return it.get("bg") or {"number": "green", "quote": "paper"}.get(it.get("style"), "ink")
    if k == "outro": return "paper"
    return "ink"


def encode(it, frames, dst):
    k = it["kind"]; pat = os.path.join(os.path.dirname(frames[0]), "frame_%06d.png")
    if frames[0].endswith(".mp4"): pat = frames[0]
    if k == "plate":  # static film grain baked in
        import numpy as np
        a = np.asarray(Image.open(frames[0]).convert("RGB")).astype(np.float32)
        g = np.random.default_rng(11).normal(0, 5.5 if it.get("variant") == "paper" else 6.5, a.shape[:2])[..., None]
        Image.fromarray(np.clip(a + g, 0, 255).astype(np.uint8)).save(dst, optimize=True)
        return {"w": 1920, "h": 1080, "box": (0, 0, 1920, 1080)}
    if k in ALPHA:
        box = (0, 0, 1920, 1080) if k == "transition" else union_bbox(frames)
        x, y, w, h = box
        cmd = ["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", pat, "-vf", f"crop={w}:{h}:{x}:{y}",
               "-c:v", "qtrle", "-pix_fmt", "argb", dst]
    else:
        box = (0, 0, 1920, 1080); w, h = 1920, 1080
        cmd = ["ffmpeg", "-y", "-v", "error"] + ([] if pat.endswith(".mp4") else ["-framerate", str(FPS)]) + ["-i", pat, "-an",
               "-vf", f"noise=c0s={GRAIN.get(grain_key(it), 7)}:c0f=t+u,scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
               "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-threads", "4",
               "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-r", str(FPS), "-movflags", "+faststart", dst]
    for attempt in range(3):  # ffmpeg occasionally fails to start under heavy load (0xC0000142); retry
        if subprocess.run(cmd).returncode == 0: break
        time.sleep(3)
    else:
        raise RuntimeError("ffmpeg encode failed: " + dst)
    return {"w": w, "h": h, "box": box}


def render_item(job):
    it, th, workers = job
    d = dur_of(it); name = out_name(it); wd = os.path.join(WORK, os.path.splitext(name)[0])
    t0 = time.time()
    prep_work(it, d, wd)
    frames = hf_render(wd, workers, it["kind"] in ALPHA or it["kind"] == "plate")
    t1 = time.time(); dst = os.path.join(OUT, name)
    info = encode(it, frames, dst); info["t_hf"] = round(t1 - t0, 1); info["t_enc"] = round(time.time() - t1, 1)
    mb = os.path.getsize(dst) / 1e6
    if mb > BIG_MB:
        os.makedirs(BIG, exist_ok=True); big = os.path.join(BIG, name); shutil.move(dst, big); dst = big
    nfr = len(frames) if not frames[0].endswith(".mp4") else int(round(d * FPS))
    info.update({"file": dst, "frames": nfr, "secs": round(time.time() - t0, 1), "mb": round(mb, 2)})
    json.dump(info, open(os.path.join(OUT, "_sig", name + ".json"), "w"))
    open(os.path.join(OUT, "_sig", name + ".sig"), "w").write(signature(it, th))
    return it["id"], name, info


def manifest(items):
    rows = []
    for it in items:
        name = out_name(it); meta_p = os.path.join(OUT, "_sig", name + ".json")
        if not os.path.exists(meta_p): continue
        m = json.load(open(meta_p)); x, y, w, h = m["box"]; alpha = it["kind"] in ALPHA; d = dur_of(it)
        f = m["file"]; rel = os.path.relpath(f, ROOT).replace("\\", "/") if f.startswith(ROOT) else f
        hits = sfx_plan(it, d)
        row = {"file": rel, "id": it["id"], "kind": it["kind"] + (f":{it.get('style', 'punch')}" if it["kind"] == "hero" else ""),
               "w": m["w"], "h": m["h"], "dur": d if it["kind"] != "plate" else 0, "alpha": alpha,
               "place": {"x": round((x + w / 2) / 1920, 4), "y": round((y + h / 2) / 1080, 4), "w": round(w / 1920, 4)},
               "sfx_at": [s["at"] for s in hits], "sfx": [s["file"] for s in hits], "sfx_gain_db": [s["gain_db"] for s in hits]}
        if it["kind"] == "transition": row["cover"] = [0.2, 0.3]; row["cut_at"] = 0.25
        if it["kind"] == "chapter": row.update({"n": it["n"], "title": it.get("title"), "tag_file": f"projects/carrie-ep01/v4/gfx/chapter_tag_{int(it['n']):02d}.mov"})
        if it["kind"] == "hero": row["screen"] = it.get("screen") or f"{it.get('myth', '')} | {it.get('fact', '')}"
        rows.append(row)
    doc = {"generated": time.strftime("%Y-%m-%d %H:%M"), "canvas": [1920, 1080], "fps": FPS,
           "alpha_codec": "qtrle (QuickTime Animation), pix_fmt argb, straight alpha, cropped to the element bbox (transitions full frame)",
           "opaque_codec": "H.264 yuv420p BT.709 crf 14, no audio", "files": rows}
    json.dump(doc, open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    return doc


# ----------------------------------------------------------------------------------------------- QA
def backdrop():
    p = os.path.join(TEST, "backdrop.jpg")
    if not os.path.exists(p):
        src = r"I:\claude to edit\IMG_4342-001.MOV"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "1250", "-i", src, "-frames:v", "1", "-vf", "scale=1920:1080", p], check=False)
    return Image.open(p).convert("RGB") if os.path.exists(p) else Image.new("RGB", (1920, 1080), (90, 90, 90))


def qa(items, step=0.2):
    os.makedirs(TEST, exist_ok=True); bd = backdrop(); f = ImageFont.truetype(os.path.join(FONTS, "SpaceMono-Bold.ttf"), 15)
    tiles_all = []
    for it in items:
        name = out_name(it); wd = os.path.join(WORK, os.path.splitext(name)[0]); frames = sorted(glob.glob(os.path.join(wd, "png", "*.png")))
        if it["kind"] not in ALPHA and it["kind"] != "plate" and os.path.exists(os.path.join(OUT, name)):
            qd = os.path.join(wd, "qa"); shutil.rmtree(qd, ignore_errors=True); os.makedirs(qd)
            subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(OUT, name), "-vf", "scale=384:216", os.path.join(qd, "f_%04d.png")], check=False)
            frames = sorted(glob.glob(os.path.join(qd, "*.png")))
        if not frames: continue
        n = len(frames); idx = sorted(set([min(n - 1, int(round(t * FPS))) for t in [i * step for i in range(int(n / FPS / step) + 1)]] + [n - 1]))
        if it.get("_qa_light"): idx = idx[::2]
        tw, th_ = 320, 180; cols = 8; rows = (len(idx) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * tw, rows * (th_ + 20) + 26), (24, 24, 24)); d = ImageDraw.Draw(sheet)
        d.text((6, 4), f"{name}  {n} frames", font=f, fill=(255, 216, 77))
        for j, fi in enumerate(idx):
            im = Image.open(frames[fi]).convert("RGBA")
            base = bd.copy().convert("RGBA") if it["kind"] in ALPHA else Image.new("RGBA", (1920, 1080), (0, 0, 0, 255))
            if im.size != base.size: im = im.resize(base.size)
            base.alpha_composite(im); t = base.convert("RGB").resize((tw, th_), Image.LANCZOS)
            x, y = (j % cols) * tw, 26 + (j // cols) * (th_ + 20)
            sheet.paste(t, (x, y + 20)); d.text((x + 4, y + 2), f"{fi / FPS:.2f}s", font=f, fill=(230, 230, 230))
            if j == len(idx) // 2: tiles_all.append((name, t))
        sheet.save(os.path.join(TEST, f"qa_{os.path.splitext(name)[0]}.jpg"), quality=86)
    if tiles_all:  # overview: one mid frame per file
        cols = 6; tw, th_ = 384, 216; rows = (len(tiles_all) + cols - 1) // cols
        sh = Image.new("RGB", (cols * tw, rows * (th_ + 22)), (24, 24, 24)); d = ImageDraw.Draw(sh)
        for j, (nm, t) in enumerate(tiles_all):
            x, y = (j % cols) * tw, (j // cols) * (th_ + 22); sh.paste(t, (x, y + 22)); d.text((x + 4, y + 3), nm, font=f, fill=(255, 216, 77))
        sh.save(os.path.join(TEST, "sheet.jpg"), quality=86)
        print("sheet:", os.path.join(TEST, "sheet.jpg"))


# ----------------------------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default=os.path.join(V4, "gfx.json"))
    ap.add_argument("--plan", default=os.path.join(V4, "edit_plan.json"))
    ap.add_argument("--from-plan", action="store_true", help="rebuild gfx.json chapters/heroes from edit_plan.json")
    ap.add_argument("--only"); ap.add_argument("--kinds"); ap.add_argument("--force", action="store_true")
    ap.add_argument("-j", type=int, default=2, help="items rendered in parallel"); ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--qa", action="store_true"); ap.add_argument("--qa-only", action="store_true")
    ap.add_argument("--resign", action="store_true", help="mark the selected existing outputs as up to date (no render)")
    a = ap.parse_args()
    os.makedirs(os.path.join(OUT, "_sig"), exist_ok=True); os.makedirs(WORK, exist_ok=True)
    spec = json.load(open(a.spec, encoding="utf-8")) if os.path.exists(a.spec) else default_spec()
    if os.path.exists(a.plan) and (a.from_plan or not os.path.exists(a.spec) or any(it.get("placeholder") for it in spec["items"])):
        spec = from_plan(json.load(open(a.plan, encoding="utf-8")), spec); print("gfx.json rebuilt from edit_plan.json")
    json.dump(spec, open(a.spec, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    items = expand(spec)
    sel = [it for it in items if (not a.only or it["id"] in a.only.split(",") or out_name(it) in a.only.split(","))
           and (not a.kinds or it["kind"] in a.kinds.split(","))]
    if a.resign:
        for it in sel:
            name = out_name(it)
            if os.path.exists(os.path.join(OUT, "_sig", name + ".json")):
                open(os.path.join(OUT, "_sig", name + ".sig"), "w").write(signature(it, template_hash(it["kind"])))
        a.qa_only = True
    if not a.qa_only:
        jobs = []
        for it in sel:
            th = template_hash(it["kind"])
            name = out_name(it); sp = os.path.join(OUT, "_sig", name + ".sig"); meta = os.path.join(OUT, "_sig", name + ".json")
            have = os.path.exists(meta) and os.path.exists(json.load(open(meta))["file"])
            if not a.force and have and os.path.exists(sp) and open(sp).read() == signature(it, th):
                continue
            jobs.append((it, th, a.workers))
        print(f"{len(jobs)} to render, {len(sel) - len(jobs)} unchanged", flush=True)
        with ThreadPoolExecutor(a.j) as ex:
            for i, (iid, name, info) in enumerate(ex.map(render_item, jobs)):
                print(f"gfx {i + 1}/{len(jobs)} {name}  {info['w']}x{info['h']}  {info['frames']}f  {info['mb']} MB  {info['secs']} s (hf {info['t_hf']} / enc {info['t_enc']})", flush=True)
    doc = manifest(items); print(f"manifest: {len(doc['files'])} files -> {os.path.join(OUT, 'manifest.json')}")
    if a.qa or a.qa_only:
        qa(sel)


if __name__ == "__main__":
    main()

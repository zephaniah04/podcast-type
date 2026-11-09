#!/usr/bin/env python3
"""Carrie ep01 long-form v4 ("FUEL LAB"): the specialists' plans -> one render spec per chunk.

Inputs (projects/carrie-ep01/v4/):
  edit_plan.json   story editor: cold open, chapters (keep ranges), outro, hero lines, key facts
  broll_map.json   B-roll supervisor: phrase-anchored photos / videos (split | full | stack)
  info.json        infographic animator: phrase-anchored explainer graphics (full | panel)
  gfx/manifest.json + gfx.json   motion designer: chapter cards, hero punch cards, lower thirds, tags, stingers
Devices on the timeline (all pinned to the spoken words):
  frame   split-screen explainer: talker panel + B-roll / graphic panel (engine layout "frame")
  full    full-screen B-roll photo / video / graphic, voice + captions continue
  hero    full-screen kinetic punch card (screen text replaces the caption)
  frame2  both people framed side by side on quick back-and-forths
  stack   2-3 floating photo cards over the wide shot (fx.py photo cards)
  emoji / headline   small kinetic overlays on talking shots
Outputs: projects/carrie-ep01/long4/L4_*.json (+ v4/fx4.json rendered into v4/fx)
  python projects/carrie-ep01/build_long4.py [--no-render] [--only 03]
"""
import glob, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_shorts as B  # noqa: E402
import build_long2 as L2  # noqa: E402
P = B.P
ROOT = os.path.dirname(os.path.dirname(HERE))
V4 = os.path.join(HERE, "v4")
OUTJ = os.environ.get("V4OUTJ") or os.path.join(HERE, "long4"); os.makedirs(OUTJ, exist_ok=True)
PY = sys.executable
WS = L2.WS
NO_RENDER = "--no-render" in sys.argv
ONLY = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None

GAP = 0.5            # jump-cut every pause longer than this (talk segments)
OLD_ANGLE_END = 45.0  # file A: camera repositioned after this; Carrie is not in the shot before it
PAD = 1.0            # seconds of talking face between two layout devices
HEAD = 2.6           # no layout device in the first seconds of a chapter body (tag + names)
ACCENT, HIGHLIGHT = "#FF5A1F", "#FFD84D"
FIX4 = {**B.FIX, "protein shape": "protein shake", "someone for veggies": "some more veggies",
        "some of your race at lunch": "some of your rice at lunch", "iron one chat": "Ironman, ChatGPT", "gpd": "GPT"}
AF = {"zoom": 1.75, "zoom_right": 1.5, "punch": 1.0, "wide_every": 4, "cy": 0.40, "min_turn": 1.6}


def load(name, default=None):
    p = os.environ.get("V4PLAN") if name == "edit_plan.json" and os.environ.get("V4PLAN") else os.path.join(V4, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default


def exists(rel):
    return bool(rel) and os.path.exists(os.path.join(ROOT, rel))


def rel(p):
    return os.path.relpath(p, ROOT).replace(os.sep, "/") if os.path.isabs(p) else p.replace("\\", "/")


def dur_of(relpath):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                        os.path.join(ROOT, relpath)], capture_output=True, text=True).stdout.strip()
    try:
        return float(r)
    except ValueError:
        return 0.0


PLAN = load("edit_plan.json")
if not PLAN:
    raise SystemExit("v4/edit_plan.json missing (story editor)")
AVOID = {"fitness-race.jpg", "pain-spray.jpg", "cramp.jpg", "sweaty-athlete.jpg", "sports-drink.jpg", "energy-drink-cans.jpg"}  # logos / recognisable people
BRM = [b for b in load("broll_map.json", []) if exists(b.get("asset") or (b.get("assets") or [None])[0])
       and os.path.basename(b.get("asset") or "") not in AVOID]
for b in BRM:
    if b.get("assets"):
        b["assets"] = [a for a in b["assets"] if os.path.basename(a) not in AVOID]
INFO = [i for i in load("info.json", []) if exists(i.get("file"))]
GFXJ = load("gfx.json", {}) or {}
_man = load("gfx/manifest.json", {}) or {}
MAN = {rel(m["file"]): m for m in (_man.get("files", []) if isinstance(_man, dict) else _man) if isinstance(m, dict) and m.get("file")}
FX4 = {}  # v4 overlay elements rendered by scripts/fx.py into v4/fx


def gfx(name):
    """path of a motion-designer file (repo first, then the big-file folder on C:)"""
    for base in (os.path.join(V4, "gfx"), os.path.join(os.environ.get("TEMP", ""), "v4", "gfx_big")):
        p = os.path.join(base, name)
        if os.path.exists(p):
            return rel(p) if p.startswith(ROOT) else p.replace("\\", "/")
    return None


def place_of(path, default):
    m = MAN.get(path) or next((v for k, v in MAN.items() if k.endswith(os.path.basename(path or "?"))), None)
    return (m or {}).get("place") or default


def hero_file(h):
    """match a hero line to the designer's rendered punch card"""
    for it in (GFXJ.get("heroes") or GFXJ.get("hero") or GFXJ.get("items") or []):
        if isinstance(it, dict) and it.get("kind", "hero") == "hero" and (
                it.get("screen", "").strip().lower() == h["screen"].strip().lower()
                or (it.get("f") == h["f"] and abs(float(it.get("t", -9)) - float(h["t"])) < 0.5)):
            i_ = it.get("id") or ""
            f = gfx((i_ if i_.startswith("hero_") else f"hero_{i_}") + ".mp4") if i_ else None
            if f:
                return f
    return None


# ------------------------------------------------------------------------------------------ word helpers
def wi(f, t):
    """index of the word starting at (or right after) source time t"""
    w = WS[f]
    return min(range(len(w)), key=lambda i: abs(w[i][0] - t))


def cut_after(f, t, lim):
    """a clean picture cut at or after t: the next pause, else the next word end (<= lim)"""
    w = WS[f]
    for i in range(len(w) - 1):
        if w[i][1] >= t - 0.05:
            if w[i + 1][0] - w[i][1] > 0.18 or w[i][1] >= t + 0.6:
                return round(min(w[i][1] + 0.08, lim), 3)
    return round(min(t, lim), 3)


def talker(f, s, e):
    return L2.talker(f, s, e)


# ------------------------------------------------------------------------------------------ candidates
KEYS = {  # sparse 3D emoji on spoken keywords (the fx Nizam already has, reused when the clip exists)
 "banana": ("Banana", "banana"), "eggs": ("Egg", "eggs"), "rice": ("Cooked rice", "rice"), "water": ("Droplet", "water"),
 "salt": ("Salt", "salt"), "sodium": ("Salt", "sodium"), "cramp": ("Collision", "cramp"), "cramps": ("Collision", "cramps"),
 "caffeine": ("Hot beverage", "caffeine"), "carbs": ("Bread", "carbs"), "protein": ("Cut of meat", "protein"),
 "muscle": ("Flexed biceps", "muscle"), "bike": ("Bicycle", "bike"), "swim": ("Goggles", "swim"), "sleep": ("Zzz", "sleep"),
 "dinner": ("Fork and knife with plate", "dinner"), "breakfast": ("Pancakes", "breakfast"), "fruit": ("Grapes", "fruit"),
 "smoothie": ("Cup with straw", "smoothie"), "sandwich": ("Sandwich", "sandwich"), "tuna": ("Fish", "tuna"),
 "vitamin": ("Pill", "vitamin"), "creatine": ("Test tube", "creatine"), "energy": ("High voltage", "energy"),
 "recovery": ("Battery", "recovery"), "ironman": ("Person biking", "Ironman"), "calories": ("Fire", "calories"),
 "winter": ("Snowflake", "winter"), "blood": ("Drop of blood", "blood"), "race": ("Chequered flag", "race"),
}
KEY_MAX, KEY_SPACING = int(os.environ.get("V4EMOJI", "0")), 150.0  # style guide: no emoji in v4


def emo(emoji, label):
    fid = "e_" + "".join(ch if ch.isalnum() else "-" for ch in (emoji + "_" + label).lower()).strip("-")[:48]
    old = os.path.join(HERE, "fx", fid + ".mov")
    if os.path.exists(old):
        return f"projects/carrie-ep01/fx/{fid}.mov"
    FX4[fid] = {"id": fid, "kind": "emoji", "emoji": emoji, "label": label, "size": 300, "dur": 2.6}
    return f"projects/carrie-ep01/v4/fx/{fid}.mov"


def photo_card(asset, label, k):
    slug = os.path.splitext(os.path.basename(asset))[0]
    fid = "p4_" + slug[:30] + ("-" + "".join(ch if ch.isalnum() else "-" for ch in label.lower())[:16] if label else "")
    FX4[fid] = {"id": fid, "kind": "photo", "file": asset, "label": label, "w": 560, "dur": 3.8,
                "tilt": (-3.0, 2.2, -1.2)[k % 3]}
    return f"projects/carrie-ep01/v4/fx/{fid}.mov"


def in_ranges(ranges, f, s, e):
    return any(rf == f and rs + 0.15 <= s and e <= re_ - 0.12 for rf, rs, re_ in ranges)


def collect(ranges):
    cands = []  # (f, s, e, kind, payload, prio)
    for i in INFO:
        f, t = i["f"], float(i["t"])
        d = float(i.get("dur") or dur_of(i["file"]))
        s = round(t - 0.06, 3); e = round(s + d, 3)
        kind = "frame" if i.get("mode") == "panel" else "full"
        cands.append((f, s, e, kind, {"file": i["file"], "label": i.get("label", ""), "graphic": True, "id": i["id"]},
                      0 if i.get("prio", 2) == 1 else 2))
    for h in PLAN.get("hero_lines", []):
        hf = hero_file(h)
        if not hf:
            continue
        f, t = h["f"], float(h["t"])
        d = dur_of(hf) or 2.6
        cands.append((f, round(t - 0.04, 3), round(t - 0.04 + d, 3), "hero", {"file": hf, "screen": h["screen"]}, 1))
    for b in BRM:
        f, t = b["f"], float(b["t"])
        hold = float(b.get("hold", 3.5))
        s = round(t - 0.06, 3)
        e = cut_after(f, s + hold, s + hold + 1.2)
        pr = {1: 3, 2: 5, 3: 7}.get(int(b.get("prio", 2)), 5)
        treat = b.get("treat", "split")
        if treat == "stack":
            assets = [a for a in (b.get("assets") or [b.get("asset")]) if exists(a)][:3]
            if assets:  # v4 QA: floating cards over talk shots covered a face -> use a split panel instead
                cands.append((f, s, cut_after(f, s + 3.9, s + 5.1), "frame",
                              {"file": assets[0], "label": b.get("label", ""), "video": False}, pr + 1))
            continue
        kind = "full" if treat == "full" else "frame"
        cands.append((f, s, e, kind, {"file": b["asset"], "label": b.get("label", ""), "video": b.get("kind") == "video"}, pr))
    # quick back-and-forths -> both people framed side by side
    for f, ws in WS.items():
        turns = [i for i in range(1, len(ws)) if ws[i][3] in "LR" and ws[i - 1][3] in "LR" and ws[i][3] != ws[i - 1][3]]
        last = -99
        for a in range(len(turns)):
            s = ws[turns[a] - 1][0]
            if s - last < 30:
                continue
            for b2 in range(a + 2, len(turns)):
                e = ws[turns[b2] - 1][1]
                if e - s > 10:
                    break
                if e - s >= 4:
                    cands.append((f, round(s - 0.05, 3), round(e + 0.1, 3), "frame2", None, 8)); last = s
                    break
    return [c for c in cands if in_ranges(ranges, c[0], c[1], c[2])]


LAYOUT = ("frame", "full", "hero", "frame2")


def choose(cands, starts):
    """greedy by priority; devices never overlap (PAD of talking face between them); none in the first HEAD
    seconds of a chapter; two full-screen devices need a longer breath between them"""
    taken, ok = [], []
    for c in sorted(cands, key=lambda c: (c[5], c[1])):
        f, s, e, kind = c[0], c[1], c[2], c[3]
        if any(rf == f and rs - 0.5 <= s < rs + HEAD for rf, rs in starts):
            continue
        clash = False
        for (tf, ts, te, tk) in taken:
            pad = PAD + (1.5 if kind in ("full", "hero") and tk in ("full", "hero") else 0)
            if tf == f and not (e + pad <= ts or s >= te + pad):
                clash = True; break
        if not clash:
            taken.append((f, s, e, kind)); ok.append(c)
    return ok


# ------------------------------------------------------------------------------------------ spec builder
FIG = [0]


_LB = {}


def light_bottom(relpath):
    """True when the caption band (y 860-1080) of a graphic is light, sampled at 60 % of its length"""
    if relpath not in _LB:
        p = relpath if os.path.isabs(relpath) else os.path.join(ROOT, relpath)
        d = dur_of(relpath) or 2.0
        r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{d * 0.6:.2f}", "-i", p, "-frames:v", "1", "-vf",
                            "crop=1920:220:0:860,scale=96:11,format=gray", "-f", "rawvideo", "-"], capture_output=True)
        px = r.stdout
        _LB[relpath] = bool(px) and sum(px) / len(px) > 150
    return _LB[relpath]


def device_seg(c, clip):
    f, s, e, kind, pl = c[0], c[1], c[2], c[3], c[4]
    seg = {"clip": clip, "start": s, "end": e, "tighten": 0}
    if kind == "frame":
        who = talker(f, s, e)
        FIG[0] += 1
        seg.update(layout="frame", who=who, side="left" if who == "L" else "right",
                   bg="grid" if pl.get("graphic") else "paper",
                   panel={"file": pl["file"], "label": pl.get("label", "").upper(), "index": f"FIG.{FIG[0]:03d}",
                          "push": 0 if pl.get("graphic") else (0.03 if pl.get("video") else 0.05), "at": 0})
    elif kind == "full":
        FIG[0] += 1
        g = pl.get("graphic")
        seg["broll"] = {"file": pl["file"], "push": 0 if g else (0.03 if pl.get("video") else 0.07), "at": 0}
        if g and light_bottom(pl["file"]):
            seg["cap_ink"] = True  # light graphic: dark captions (white on paper was unreadable)
        if not g and pl.get("label"):
            seg["broll"].update(label=pl["label"].upper(), index=f"FIG.{FIG[0]:03d}")
    elif kind == "hero":
        seg["broll"] = {"file": pl["file"], "push": 0, "at": 0}
        seg["nocaps"] = True
    elif kind == "frame2":
        # v4 QA: frame2 panels sliced Carrie when her chair moved -> clean wide two-shot (both fully in frame)
        seg.update(zoom=1.0, cx=0.5, cy=0.5)
    return seg


def body_spec(cid, title, ranges, chosen, extra=None):
    """ranges: [(f, s, e)] in order; chosen: devices"""
    segs = []
    for f, rs, re_ in ranges:
        clip = B.FILES[f]
        cur = rs
        mine = sorted([c for c in chosen if c[0] == f and rs <= c[1] < re_ and c[3] in LAYOUT], key=lambda c: c[1])
        for c in mine:
            s, e = c[1], min(c[2], re_ - 0.05)
            if s < cur + 0.3 or e - s < 1.2:
                continue
            if s - cur > 0.3:
                segs.append({"clip": clip, "start": round(cur, 3), "end": round(s, 3)})
            segs.append(device_seg((c[0], s, e, c[3], c[4]), clip))
            cur = e
        if re_ - cur > 0.3:
            segs.append({"clip": clip, "start": round(cur, 3), "end": round(re_, 3)})
    # the first ~45 s of file A were shot from an older camera angle with Carrie out of frame: show them wide
    for sg in segs:
        if sg["clip"] == B.FILES["A"] and sg["start"] < OLD_ANGLE_END and not sg.get("layout") and not sg.get("broll"):
            sg.update(zoom=1.0, cx=0.5, cy=0.5)
    # output timeline (replicates the engine's tightening) to place overlays exactly
    t, pos = 0.0, []
    for sg in segs:
        g = sg.get("tighten", GAP)
        pieces = P.tighten(sg, B.TX, float(g), True) if g else [sg]
        for p in pieces:
            d = round((p["end"] - p["start"]) * 30) / 30
            k = sg.get("layout") or ("hero" if sg.get("nocaps") else "full" if sg.get("broll") else "talk")
            pos.append((sg["clip"], p["start"], p["end"], t, k))
            t += d
    stickers, sfx = [], []

    def out_at(clip, ts, kinds=("talk",)):
        hit = next((p for p in pos if p[0] == clip and p[1] - 0.05 <= ts < p[2]), None)
        if not hit or hit[4] not in kinds:
            return None
        return round(hit[3] + max(ts - hit[1], 0), 3)

    # stacks: floating photo cards over the talk shot
    for c in sorted([c for c in chosen if c[3] == "stack"], key=lambda c: c[1]):
        at = out_at(B.FILES[c[0]], c[1] + 0.1)
        if at is None:
            continue
        for k, a in enumerate(c[4]["assets"]):
            stickers.append({"at": round(at + 0.28 * k, 3), "file": photo_card(a, c[4]["label"] if k == 0 else "", k),
                             "x": "auto", "y": 0.42, "w": 0.28, "group": f"s{at}"})
        sfx.append({"at": at, "file": "whoosh_soft.mp3", "vol": 0.22})
    # emoji on spoken keywords (sparse)
    used = {}
    for p in pos:
        if p[4] != "talk":
            continue
        f = "A" if p[0] == B.FILES["A"] else "B"
        for w in WS[f]:
            if not (p[1] + 0.3 <= w[0] < p[2] - 1.0) or w[2] not in KEYS:
                continue
            e_, l_ = KEYS[w[2]]
            last = used.setdefault(w[2], [])
            if len(last) >= KEY_MAX or any(abs(lt - w[0]) < KEY_SPACING for lt in last):
                continue
            at = round(p[3] + w[0] - p[1], 3)
            if any(abs(s_["at"] - at) < 6 for s_ in stickers):
                continue
            last.append(w[0])
            stickers.append({"at": at, "file": emo(e_, l_), "x": "auto", "y": 0.30, "w": 0.16, "group": f"e{at}"})
            sfx.append({"at": at, "file": "pop.mp3", "vol": 0.14})
    # whoosh into every device, click on panels
    for k, p in enumerate(pos):
        if p[4] in ("frame", "full", "hero", "frame2") and (k == 0 or pos[k - 1][4] != p[4] or pos[k - 1][1] != p[1]):
            if k and pos[k - 1][4] == p[4]:
                continue
            sfx.append({"at": round(p[3], 2), "file": "whoosh_fast.mp3" if p[4] == "hero" else "whoosh_soft.mp3", "vol": 0.22})
    spec = {"_piece": True, "id": cid, "slug": "v4", "format": "long", "title": title, "topic": "long-form part",
            "auto_frame": AF, "tighten": GAP, "captions": "v4", "fixes": FIX4, "accent": ACCENT,
            "segments": segs, "stickers": stickers, "sfx": sfx}
    if extra:
        extra(spec, pos)
    counts = {k: sum(1 for p in pos if p[4] == k) for k in ("talk", "frame", "full", "hero", "frame2")}
    counts["stack"] = len({s_["group"] for s_ in stickers if s_.get("group", "").startswith("s")})
    counts["emoji"] = sum(1 for s_ in stickers if s_.get("group", "").startswith("e"))
    return spec, t, counts


def chapter_extra(ci, n_total):
    def add(spec, pos):
        tag = gfx(f"chapter_tag_{ci:02d}.mov")
        if tag:
            pl = place_of(tag, {"x": 0.2, "y": 0.09, "w": 0.34})
            spec["stickers"].insert(0, {"at": 0.25, "file": tag, "x": pl["x"], "y": pl["y"], "w": pl["w"]})
        if ci == 1:  # names on the first chapter, when each person first speaks
            for who, lt in (("R", "lt_carrie.mov"), ("L", "lt_nizam.mov")):
                f = gfx(lt)
                p0 = next((p for p in pos if p[4] == "talk" and p[3] > 2.0 and
                           not (p[0] == B.FILES["A"] and p[1] < OLD_ANGLE_END) and
                           talker("A" if p[0] == B.FILES["A"] else "B", p[1], p[2]) == who), None)
                if f and p0:
                    pl = place_of(f, {"x": 0.22, "y": 0.70, "w": 0.36})
                    spec["stickers"].append({"at": round(p0[3] + 0.4, 2), "file": f, "x": pl["x"], "y": pl["y"], "w": pl["w"]})
                    spec["sfx"].append({"at": round(p0[3] + 0.4, 2), "file": "click.wav", "vol": 0.3})
    return add


def main():
    ch = PLAN["chapters"]
    allr = [(k["f"], float(k["start"]), float(k["end"])) for c in ch for k in c["keep"]]
    allr += [(b["f"], float(b["start"]), float(b["end"])) for b in PLAN.get("cold_open", []) + PLAN.get("outro", [])]
    starts = [(c["keep"][0]["f"], float(c["keep"][0]["start"])) for c in ch]
    chosen = choose(collect(allr), starts)
    specs, tot, allc = [], 0.0, {}
    for c in ch:
        ci = int(c["n"])
        ranges = [(k["f"], float(k["start"]), float(k["end"])) for k in c["keep"]]
        mine = [x for x in chosen if in_ranges(ranges, x[0], x[1], x[2])]
        sp, t, cnt = body_spec(f"L4_{ci:02d}", f"v4 chapter {ci}: {c['title']}", ranges, mine, chapter_extra(ci, len(ch)))
        specs.append(sp); tot += t
        for k, v in cnt.items():
            allc[k] = allc.get(k, 0) + v
        print(f"ch{ci:02d} {t / 60:5.1f} min {c['title'][:34]:34s}", cnt)
    # cold open: beats as they are (tight), devices that fall inside a beat
    co = [(b["f"], float(b["start"]), float(b["end"])) for b in PLAN["cold_open"]]
    sp, t, cnt = body_spec("L4_00", "v4 cold open", co, [x for x in chosen if in_ranges(co, x[0], x[1], x[2]) and x[3] != "frame2"])
    sp["tighten"] = 0.3
    specs.append(sp); tot += t
    print(f"cold open {t:.1f} s", cnt)
    ou = [(b["f"], float(b["start"]), float(b["end"])) for b in PLAN.get("outro", [])]
    if ou:
        sp, t, cnt = body_spec("L4_99", "v4 outro", ou, [])
        specs.append(sp); tot += t
        print(f"outro {t:.1f} s")
    print(f"TOTAL talk+devices {tot / 60:.1f} min (+ cards);", allc)
    ev = sum(v for k, v in allc.items() if k != "talk")
    print(f"~{ev / (tot / 60):.1f} visual devices per minute")
    json.dump({"accent": ACCENT, "fx": list(FX4.values())}, open(os.path.join(V4, "fx4.json"), "w", encoding="utf-8"), indent=1)
    if not NO_RENDER and FX4:
        subprocess.run([PY, os.path.join(ROOT, "scripts", "fx.py"), os.path.join(V4, "fx4.json"), "--out", os.path.join(V4, "fx"), "-j", "6"], check=True)
    for sp in specs:
        if ONLY and not sp["id"].endswith(ONLY):
            continue
        sp["stickers"] = [s for s in sp["stickers"] if os.path.exists(s["file"] if os.path.isabs(s["file"]) else os.path.join(ROOT, s["file"]))]
        json.dump(sp, open(os.path.join(OUTJ, sp["id"] + ".json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build + render the FUEL LAB explainer graphics (HyperFrames HTML+GSAP -> mp4).

  python projects/carrie-ep01/v4/info_src/build.py                 # validate anchors + render everything
  python projects/carrie-ep01/v4/info_src/build.py --batch 1       # one batch
  python projects/carrie-ep01/v4/info_src/build.py --only i_vitd_max,r_sweat
  python projects/carrie-ep01/v4/info_src/build.py --check         # anchors + keep ranges only, no render
  options: --jobs N (parallel renders, default 2), --no-render (just write html), --sheet-only

Work dir (html project, raw renders, QA frames) is C:/Users/raika/AppData/Local/Temp/v4/info_test/.
Finals: projects/carrie-ep01/v4/info/<id>.mp4 (H.264 yuv420p 30 fps, no audio) + v4/info.json (merged, sorted by file, t).
"""
import json, os, shutil, subprocess, sys, concurrent.futures as cf
args = sys.argv[1:]
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
V4 = os.path.dirname(HERE)
EP = os.path.dirname(V4)
ROOT = os.path.dirname(os.path.dirname(EP))
sys.path.insert(0, EP); sys.path.insert(0, HERE)
os.chdir(ROOT)
import build_long2 as L2  # noqa: E402
import graphics  # noqa: E402

WORK = r"C:/Users/raika/AppData/Local/Temp/v4/info_test"
PROJ = os.path.join(WORK, "proj")
RAW = os.path.join(WORK, "raw")
FR = os.path.join(WORK, "frames")
OUT = os.path.join(V4, "info")
HF = os.path.join(ROOT, "node_modules", "hyperframes", "bin", "hyperframes.mjs")
GSAP = os.path.join(ROOT, "node_modules", "hyperframes", "dist", "vendor", "npm", "gsap@3.15.0", "dist", "gsap.min.js")
FONTS = ["ArchivoBlack-Regular.ttf", "InterTight-Heavy.ttf", "InterTight-Medium.ttf", "InstrumentSerif-Italic.ttf",
         "SpaceMono-Regular.ttf", "SpaceMono-Bold.ttf"]
SIZE = {"full": (1920, 1080), "panel": (840, 780)}



def opt(name, default=None):
    return args[args.index(name) + 1] if name in args else default


def mmss(t):
    return f"{int(t // 60):02d}:{t % 60:04.1f}"


def keep_info(f, t, dur):
    plan = json.load(open(os.path.join(V4, "edit_plan.json"), encoding="utf-8"))
    for c in plan["chapters"]:
        for k in c["keep"]:
            if k["f"] == f and k["start"] - 0.05 <= t <= k["end"]:
                return c["n"], c["title"], (t + dur <= k["end"] + 1.5)
    return None, None, False


def resolve(gr):
    i, n = L2.find(gr["f"], gr["at_hint"], gr["phrase"])
    t = round(L2.WS[gr["f"]][i][0], 2)
    ch, title, fits = keep_info(gr["f"], t, gr["dur"])
    return t, ch, title, fits


def page(gr, idx):
    w, h = SIZE[gr["mode"]]
    spec = {"id": gr["id"], "mode": gr["mode"], "dur": gr["dur"], "kind": gr["kind"], "bg": gr["bg"], "tag": gr["tag"],
            "idx": idx, "data": gr["data"]}
    css = open(os.path.join(HERE, "engine.css"), encoding="utf-8").read()
    return f"""<!doctype html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width={w}, height={h}">
<title>{gr['id']}</title>
<script src="gsap.min.js"></script>
<style>
{css}
</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-width="{w}" data-height="{h}" data-duration="{gr['dur']}"></div>
<script>window.SPEC = {json.dumps(spec, ensure_ascii=False)};</script>
<script src="engine.js"></script>
</body></html>
"""


def photos(gr):
    out = []
    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "photo" and isinstance(v, str):
                    out.append(v)
                else:
                    walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(gr["data"])
    return out


def setup(sel, idxmap):
    os.makedirs(os.path.join(PROJ, "fonts"), exist_ok=True)
    os.makedirs(os.path.join(PROJ, "img"), exist_ok=True)
    for d in (RAW, FR, OUT):
        os.makedirs(d, exist_ok=True)
    shutil.copy(os.path.join(HERE, "engine.js"), PROJ)
    shutil.copy(os.path.join(HERE, "grain.png"), PROJ)
    shutil.copy(GSAP, PROJ)
    for f in FONTS:
        shutil.copy(os.path.join(ROOT, "assets", "fonts", f), os.path.join(PROJ, "fonts", f))
    for gr in sel:
        for p in photos(gr):
            src = os.path.join(EP, "broll", p + ".jpg")
            if not os.path.exists(src):
                raise SystemExit(f"missing photo {src}")
            shutil.copy(src, os.path.join(PROJ, "img", p + ".jpg"))
        open(os.path.join(PROJ, gr["id"] + ".html"), "w", encoding="utf-8").write(page(gr, idxmap[gr["id"]]))


def render(gr):
    raw = os.path.join(RAW, gr["id"] + ".mp4")
    cmd = ["node", HF, "render", PROJ, "-c", gr["id"] + ".html", "-o", raw, "--quality", "delivery", "--quiet", "--workers", "3"]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode or not os.path.exists(raw):
        return gr["id"], "RENDER FAIL: " + (r.stderr or r.stdout)[-800:]
    w, h = SIZE[gr["mode"]]
    out = os.path.join(OUT, gr["id"] + ".mp4")
    r2 = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-an", "-vf", f"scale={w}:{h},fps=30,format=yuv420p",
                         "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-movflags", "+faststart", out], capture_output=True, text=True)
    if r2.returncode:
        return gr["id"], "FFMPEG FAIL: " + r2.stderr[-400:]
    # QA frames: mid-entrance, settled, just before exit
    for tag, tt in (("a", 0.9), ("b", gr["dur"] - 0.55)):
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{tt:.2f}", "-i", out, "-frames:v", "1", "-q:v", "3",
                        os.path.join(FR, f"{gr['id']}_{tag}.jpg")], capture_output=True)
    return gr["id"], "ok"


def sheet(ids, path, cols=4, cw=480):
    from PIL import Image, ImageDraw
    tiles = []
    for i in ids:
        p = os.path.join(FR, f"{i}_b.jpg")
        if os.path.exists(p):
            im = Image.open(p).convert("RGB")
            im.thumbnail((cw, int(cw * 0.95)))
            tiles.append((i, im))
    if not tiles:
        return
    ch = max(t[1].height for t in tiles) + 26
    rows = (len(tiles) + cols - 1) // cols
    S = Image.new("RGB", (cols * (cw + 8) + 8, rows * (ch + 8) + 8), (40, 40, 40))
    d = ImageDraw.Draw(S)
    for k, (i, im) in enumerate(tiles):
        x, y = 8 + (k % cols) * (cw + 8), 8 + (k // cols) * (ch + 8)
        S.paste(im, (x, y + 24))
        d.text((x + 4, y + 4), i, fill=(255, 216, 77))
    S.save(path, quality=82)
    print("sheet", path)


def main():
    allg = graphics.G
    rows = []
    bad = []
    for gr in allg:
        try:
            t, ch, title, fits = resolve(gr)
        except SystemExit as e:
            bad.append((gr["id"], str(e))); continue
        rows.append((gr, t, ch, title, fits))
    for b in bad:
        print("ANCHOR FAIL", *b)
    rows.sort(key=lambda r: (r[0]["f"], r[1]))
    idxmap = {r[0]["id"]: f"{k + 1:02d} / {len(rows):02d}" for k, r in enumerate(rows)}
    prev = None
    for gr, t, ch, title, fits in rows:
        warn = []
        if ch is None: warn.append("NOT IN KEEP")
        elif not fits: warn.append("runs past keep end")
        if prev is not None and prev[0]["kind"] == gr["kind"]: warn.append(f"same kind as {prev[0]['id']}")
        if prev is not None and prev[0]["f"] == gr["f"] and t - prev[1] < prev[0]["dur"] + 1.0: warn.append(f"overlaps {prev[0]['id']}")
        if "--check" in args or warn:
            print(f"{gr['id']:18s} {gr['f']} {mmss(t)} b{gr['batch']} {gr['kind']:9s} {gr['mode']:5s} ch{ch} {' | '.join(warn)}")
        prev = (gr, t)
    if bad or "--check" in args:
        return
    sel = rows
    if opt("--batch"):
        bs = {int(x) for x in opt("--batch").split(",")}
        sel = [r for r in rows if r[0]["batch"] in bs]
    if opt("--only"):
        ids = set(opt("--only").split(","))
        sel = [r for r in rows if r[0]["id"] in ids]
    setup([r[0] for r in sel], idxmap)
    if "--no-render" in args:
        return
    results = {}
    if "--sheet-only" not in args:
        with cf.ThreadPoolExecutor(int(opt("--jobs", 2))) as ex:
            for gid, st in ex.map(render, [r[0] for r in sel]):
                results[gid] = st
                print(gid, st[:300])
    # merge into info.json
    jpath = os.path.join(V4, "info.json")
    cur = {e["id"]: e for e in json.load(open(jpath, encoding="utf-8"))} if os.path.exists(jpath) else {}
    for gr, t, ch, title, fits in rows:
        fp = os.path.join(OUT, gr["id"] + ".mp4")
        if not os.path.exists(fp) or results.get(gr["id"], "ok") != "ok":
            continue
        cur[gr["id"]] = {"id": gr["id"], "f": gr["f"], "t": t, "at": mmss(t), "phrase": gr["phrase"], "mode": gr["mode"],
                         "dur": gr["dur"], "file": f"projects/carrie-ep01/v4/info/{gr['id']}.mp4", "kind": gr["kind"],
                         "chapter_hint": f"{ch} {title}" if ch else "", "prio": gr["prio"],
                         "research": gr["kind"] == "research" or gr["tag"].startswith("THE SCIENCE")}
    out = sorted(cur.values(), key=lambda e: (e["f"], e["t"]))
    json.dump(out, open(jpath, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("info.json:", len(out), "entries")
    tag = opt("--batch", "sel").replace(",", "-")
    sheet([r[0]["id"] for r in sel], os.path.join(WORK, f"sheet_b{tag}.jpg"))
    sheet([e["id"] for e in out], os.path.join(WORK, "sheet.jpg"), cols=6, cw=400)


if __name__ == "__main__":
    main()

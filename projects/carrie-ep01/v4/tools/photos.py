#!/usr/bin/env python3
"""Keyless photo B-roll for v4 (Openverse + Wikimedia Commons via scripts/find_broll.py), picked by eye.

  python photos.py search plan.json [--only a,b]   # plan = {"slug": ["query one", "query two"]}: candidates + thumbs
  python photos.py sheets plan.json --out NAME      # numbered contact sheets (8 slugs per sheet)
  python photos.py get picks.json                  # {"slug": idx | ["other-slug", idx]} -> broll/<slug>.jpg + credits
Only CC0 / PD / CC BY / CC BY-SA (NC / ND dropped), width >= 1000 px. Never overwrites an existing broll/<slug>.jpg;
credits.json is appended to (existing records kept). Work files: C:/Users/raika/AppData/Local/Temp/v4/cand.
"""
import argparse, json, os, re, subprocess, sys, time
from PIL import Image, ImageDraw, ImageFont

ROOT = "I:/podcast-type"
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import find_broll as FB  # noqa: E402

EP = os.path.join(ROOT, "projects/carrie-ep01")
BR = os.path.join(EP, "broll")
WORK = "C:/Users/raika/AppData/Local/Temp/v4/cand"
os.makedirs(WORK, exist_ok=True)
BAD = re.compile(r"(^|[-/ ])(nc|nd)([-/ ]|$)", re.I)


def curl(url, out, t=60):
    r = subprocess.run(["curl", "-sSL", "--max-time", str(t), "-A", FB.UA, "-o", out, "-w", "%{http_code}", url],
                       capture_output=True, text=True)
    ok = r.stdout.strip()[-3:] == "200" and os.path.exists(out) and os.path.getsize(out) > 2000
    if not ok and os.path.exists(out):
        os.remove(out)
    return ok


def thumb_url(c):
    u = c["url"].split("?")[0]
    m = re.match(r"(https://upload\.wikimedia\.org/wikipedia/commons)/(\w)/(\w\w)/(.+)$", u)
    if m:
        name = m.group(4)
        ext = ".jpg" if name.lower().endswith((".tif", ".tiff", ".webp")) else ""
        return f"{m.group(1)}/thumb/{m.group(2)}/{m.group(3)}/{name}/330px-{name}{ext}"
    m = re.match(r"(https://(?:live|farm\d+)\.staticflickr\.com/\d+/\d+_[0-9a-f]+)(?:_\w)?\.jpg$", u)
    if m:
        return m.group(1) + "_n.jpg"
    if c["source"] == "openverse":
        return f"https://api.openverse.org/v1/images/{c['id']}/thumb/"
    return u


def search_slug(slug, queries):
    seen, out = set(), []
    calls = [("ov", queries[0])] + [("cm", q) for q in queries]
    for kind, q in calls:
        try:
            res = list(FB.openverse(q, 8)) if kind == "ov" else list(FB.commons(q, 8, "photo"))
        except Exception as e:
            print("  !", kind, q, e); res = []
        time.sleep(2.2)
        for c in res:
            lic = c.get("license", "") or ""
            if not c.get("url") or not FB.OK_LIC.search(lic) or BAD.search(lic):
                continue
            if c["w"] and c["w"] < 1000:
                continue
            if c["url"].lower().split("?")[0].endswith((".svg", ".gif", ".tif", ".tiff", ".pdf", ".djvu")):
                continue
            key = c["url"].split("?")[0]
            if key in seen:
                continue
            seen.add(key); out.append(c)
    # landscape first, then by size
    out.sort(key=lambda c: (0 if (c["w"] or 1) >= (c["h"] or 1) * 1.15 else 1, -(c["w"] or 0)))
    return out[:10]


def cmd_search(plan, only):
    for slug, qs in plan.items():
        if only and slug not in only:
            continue
        cp = os.path.join(WORK, slug + ".json")
        if os.path.exists(cp):
            continue
        cs = search_slug(slug, qs)
        json.dump(cs, open(cp, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        for i, c in enumerate(cs):
            tp = os.path.join(WORK, f"{slug}_{i}.jpg")
            if not os.path.exists(tp) and not curl(thumb_url(c), tp, 40):
                time.sleep(3); curl(thumb_url(c), tp, 40)
            time.sleep(0.3)
        print(" ", slug, len(cs), flush=True)


def cmd_sheets(slugs, name):
    fb = ImageFont.truetype(os.path.join(ROOT, "assets/fonts/InterTight-Heavy.ttf"), 18)
    fm = ImageFont.truetype(os.path.join(ROOT, "assets/fonts/InterTight-Medium.ttf"), 13)
    TW, TH, per, rows = 230, 155, 10, 8
    for k in range(0, len(slugs), rows):
        chunk = slugs[k:k + rows]
        sh = Image.new("RGB", (150 + per * TW, len(chunk) * (TH + 22)), (18, 18, 18)); d = ImageDraw.Draw(sh)
        for r, s in enumerate(chunk):
            y = r * (TH + 22)
            d.text((4, y + 6), s[:15], font=fb, fill=(255, 200, 60))
            cp = os.path.join(WORK, s + ".json")
            cs = json.load(open(cp, encoding="utf-8")) if os.path.exists(cp) else []
            for i, c in enumerate(cs[:per]):
                x = 150 + i * TW
                tp = os.path.join(WORK, f"{s}_{i}.jpg")
                if os.path.exists(tp):
                    try:
                        im = Image.open(tp).convert("RGB"); im.thumbnail((TW - 4, TH)); sh.paste(im, (x, y))
                    except Exception:
                        pass
                d.rectangle([x, y, x + 24, y + 22], fill=(0, 0, 0)); d.text((x + 5, y + 1), str(i), font=fb, fill=(255, 255, 255))
                d.text((x + 2, y + TH + 3), f"{c['w']}x{c['h']} {c['license'][:12]}", font=fm, fill=(190, 190, 190))
        out = os.path.join(WORK, f"sheet_{name}_{k // rows:02d}.jpg"); sh.save(out, quality=82); print(out, chunk)


def save_credits(cpath, credits):
    """atomic write with retries (another process may hold the file open for a moment)"""
    tmp = cpath + ".v4tmp"
    for k in range(10):
        try:
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(credits, fh, indent=1, ensure_ascii=False)
            os.replace(tmp, cpath)
            return
        except OSError:
            time.sleep(1.5)
    raise SystemExit("could not write credits.json")


def cmd_get(picks):
    cpath = os.path.join(BR, "credits.json")
    credits = json.load(open(cpath, encoding="utf-8"))
    for slug, idx in picks.items():
        src = slug
        if isinstance(idx, list):
            src, idx = idx
        dst = os.path.join(BR, slug + ".jpg")
        c = json.load(open(os.path.join(WORK, src + ".json"), encoding="utf-8"))[idx]
        if os.path.exists(dst):
            if any(x.get("file") == f"broll/{slug}.jpg" for x in credits):
                print("exists, kept:", slug); continue
            im = Image.open(dst)  # file landed but its credit write failed earlier: log it now
            rec = {"file": f"broll/{slug}.jpg", "source": c["source"], "title": c["title"], "author": c.get("author", ""),
                   "license": c["license"], "page": c.get("page", ""), "url": c["url"], "added": "v4"}
            credits.append(rec); save_credits(cpath, credits); print("credited", slug); continue
        raw = os.path.join(WORK, f"_dl_{slug}")
        ok = curl(c["url"], raw, 180)
        if not ok:
            time.sleep(5); ok = curl(c["url"], raw, 180)
        if not ok:
            print("FAILED", slug, c["url"]); continue
        try:
            im = Image.open(raw); im.load()
            im = im.convert("RGB")
        except Exception as e:
            print("BAD IMAGE", slug, e); os.remove(raw); continue
        if im.width > 2600:
            im = im.resize((2600, round(im.height * 2600 / im.width)), Image.LANCZOS)
        im.save(dst, quality=90); os.remove(raw)
        rec = {"file": f"broll/{slug}.jpg", "source": c["source"], "title": c["title"], "author": c.get("author", ""),
               "license": c["license"], "page": c.get("page", ""), "url": c["url"], "added": "v4"}
        credits = [x for x in credits if x.get("file") != rec["file"]] + [rec]
        save_credits(cpath, credits)
        print("got", slug, im.size, c["license"], flush=True)
        time.sleep(1.5)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("file")
    ap.add_argument("--only", default=""); ap.add_argument("--out", default="s")
    a = ap.parse_args()
    data = json.load(open(a.file, encoding="utf-8"))
    if a.cmd == "search":
        cmd_search(data, set(x for x in a.only.split(",") if x))
    elif a.cmd == "sheets":
        sl = [s for s in data if not a.only or s in a.only.split(",")]
        cmd_sheets(sl, a.out)
    elif a.cmd == "get":
        cmd_get(data)

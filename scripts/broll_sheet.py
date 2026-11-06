#!/usr/bin/env python3
"""Pick B-roll by eye: for every slug, search keyless sources (Openverse + Wikimedia Commons photos), download
small thumbnails and lay them out as numbered contact sheets. Then fetch the chosen ones with --get.

usage:
  python scripts/broll_sheet.py plan.json --ep projects/<ep>            # search + thumbnails + sheets
  python scripts/broll_sheet.py plan.json --ep projects/<ep> --get picks.json   # {"slug": index, ...} -> broll/<slug>.jpg
plan.json: {"slug": ["query one", "query two"], ...}
Only CC0 / PD / CC BY / CC BY-SA (NC / ND dropped). Credits land in <ep>/broll/credits.json.
"""
import argparse, concurrent.futures as cf, json, os, re, subprocess, sys, time, urllib.parse
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import find_broll as FB  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TW, TH = 300, 200


def thumb_url(c):
    u = c["url"].split("?")[0]
    m = re.match(r"(https://upload\.wikimedia\.org/wikipedia/commons)/(\w)/(\w\w)/(.+)$", u)
    if m:
        name = m.group(4)
        return f"{m.group(1)}/thumb/{m.group(2)}/{m.group(3)}/{name}/330px-{name}" + (".jpg" if name.lower().endswith((".tif", ".tiff")) else "")
    if c["source"] == "openverse":
        return f"https://api.openverse.org/v1/images/{c['id']}/thumb/"
    return u


def curl(url, out, t=40):
    r = subprocess.run(["curl", "-sSL", "--max-time", str(t), "-A", FB.UA, "-o", out, "-w", "%{http_code}", url],
                       capture_output=True, text=True)
    ok = r.stdout.strip() == "200" and os.path.exists(out) and os.path.getsize(out) > 2000
    if not ok and os.path.exists(out):
        os.remove(out)  # never keep an error page as an image
    return ok


def search(queries, n=8):
    seen, out = set(), []
    for q in queries:
        ov = list(FB.openverse(q, n)); time.sleep(2.5)
        cm = list(FB.commons(q, n, "photo")); time.sleep(2.5)
        for c in ov + cm:
            lic = c.get("license", "") or ""
            if not c.get("url") or not FB.OK_LIC.search(lic) or re.search(r"(^|[-/ ])(nc|nd)([-/ ]|$)", lic, re.I):
                continue
            if c["w"] and c["h"] and (min(c["w"], c["h"]) < 1000 or c["h"] > c["w"] * 1.1):
                continue  # need landscape, big enough for a 1920x1080 push-in
            key = c["url"].split("?")[0]
            if key in seen:
                continue
            seen.add(key); out.append(c)
    return out[:n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan"); ap.add_argument("--ep", required=True); ap.add_argument("--get")
    ap.add_argument("--only"); ap.add_argument("--sheets", action="store_true", help="reuse saved candidates, only thumbs + sheets")
    a = ap.parse_args()
    plan = json.load(open(a.plan, encoding="utf-8"))
    cand_dir = os.path.join(a.ep, "broll", "_cand"); os.makedirs(cand_dir, exist_ok=True)
    if a.get:
        picks = json.load(open(a.get, encoding="utf-8"))
        cpath = os.path.join(a.ep, "broll", "credits.json")
        credits = json.load(open(cpath, encoding="utf-8")) if os.path.exists(cpath) else []
        for slug, idx in picks.items():
            src_slug = slug
            if isinstance(idx, list):  # ["other-slug", index]: reuse another beat's candidate
                src_slug, idx = idx
            if os.path.exists(os.path.join(a.ep, "broll", slug + ".jpg")):
                continue
            cs = json.load(open(os.path.join(cand_dir, src_slug + ".json"), encoding="utf-8"))
            c = cs[idx]
            time.sleep(1.5)
            dst = os.path.join(a.ep, "broll", slug + ".jpg"); raw = dst + ".dl"
            if not curl(c["url"], raw, 120):
                print("FAILED", slug, c["url"]); continue
            im = Image.open(raw).convert("RGB")
            if im.width > 2600:
                im = im.resize((2600, int(im.height * 2600 / im.width)), Image.LANCZOS)
            im.save(dst, quality=92); os.remove(raw)
            rec = {"file": f"broll/{slug}.jpg", "source": c["source"], "title": c["title"], "author": c.get("author", ""),
                   "license": c["license"], "page": c.get("page", ""), "url": c["url"]}
            credits = [x for x in credits if x.get("file") != rec["file"]] + [rec]
            print("got", slug, im.size, c["license"])
        json.dump(credits, open(cpath, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        return
    slugs = [s for s in plan if not a.only or s in a.only.split(",")]
    res = {}
    for s in slugs:  # one at a time: the free APIs rate-limit parallel searches
        cp = os.path.join(cand_dir, s + ".json")
        if a.sheets and os.path.exists(cp):
            res[s] = json.load(open(cp, encoding="utf-8")); continue
        res[s] = search(plan[s]); print(" ", s, len(res[s]), flush=True)
    jobs = []
    for s, cs in res.items():
        json.dump(cs, open(os.path.join(cand_dir, s + ".json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        for i, c in enumerate(cs):
            jobs.append((thumb_url(c), os.path.join(cand_dir, f"{s}_{i}.jpg")))
    for j in jobs:  # gently: upload.wikimedia.org throttles bursts
        if not os.path.exists(j[1]) and not curl(j[0], j[1]):
            time.sleep(4); curl(j[0], j[1])
    f = ImageFont.truetype(os.path.join(ROOT, "assets/fonts/InterTight-Heavy.ttf"), 22)
    per = 6
    for k in range(0, len(slugs), per):
        rows = slugs[k:k + per]
        sheet = Image.new("RGB", (8 * TW + 180, len(rows) * (TH + 8)), (20, 20, 20))
        d = ImageDraw.Draw(sheet)
        for r, s in enumerate(rows):
            y = r * (TH + 8)
            d.text((6, y + 8), s, font=f, fill=(255, 200, 60))
            for i in range(8):
                p = os.path.join(cand_dir, f"{s}_{i}.jpg")
                if not os.path.exists(p):
                    continue
                try:
                    im = Image.open(p).convert("RGB"); im.thumbnail((TW, TH))
                except Exception:
                    continue
                x = 180 + i * TW
                sheet.paste(im, (x + (TW - im.width) // 2, y + (TH - im.height) // 2))
                d.rectangle([x, y, x + 30, y + 28], fill=(0, 0, 0)); d.text((x + 6, y + 2), str(i), font=f, fill=(255, 255, 255))
        out = os.path.join(cand_dir, f"_sheet_{k // per:02d}.jpg")
        sheet.save(out, quality=85); print("sheet", out, rows)
    print({s: len(c) for s, c in res.items()})


if __name__ == "__main__":
    main()

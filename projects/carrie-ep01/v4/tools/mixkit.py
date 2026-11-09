#!/usr/bin/env python3
"""Keyless Mixkit video B-roll (Mixkit Stock Video Free License only: free for commercial use, no attribution needed).

  python mixkit.py search "query one" "query two" ...      # listing pages -> candidates + thumbnails
  python mixkit.py sheets q1 q2 ... --out NAME              # numbered contact sheet of already-searched queries
  python mixkit.py get <id> <slug> [--ss 2] [--dur 10]      # licence check, 1080/720 download, trim <=12 s, x264 crf 20, no audio
Work files live in C:/Users/raika/AppData/Local/Temp/v4/mixkit; clips land in projects/carrie-ep01/broll_video/<slug>.mp4
and every clip is logged in broll_video/credits.json. Page requests are spaced out (2 s).
"""
import argparse, json, os, re, subprocess, sys, time, html
from PIL import Image, ImageDraw, ImageFont

ROOT = "I:/podcast-type"
EP = os.path.join(ROOT, "projects/carrie-ep01")
OUT = os.path.join(EP, "broll_video")
WORK = "C:/Users/raika/AppData/Local/Temp/v4/mixkit"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
os.makedirs(WORK, exist_ok=True); os.makedirs(OUT, exist_ok=True)


def curl(url, out=None, t=60):
    cmd = ["curl", "-sSL", "--max-time", str(t), "-A", UA, "-w", "%{http_code}", "-o", out or os.devnull, url]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout.strip()[-3:]


def qslug(q):
    return re.sub(r"[^a-z0-9]+", "-", q.lower()).strip("-")


def search(q):
    path = os.path.join(WORK, "q_" + qslug(q) + ".json")
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    page = os.path.join(WORK, "q_" + qslug(q) + ".html")
    code = curl(f"https://mixkit.co/free-stock-video/discover/{qslug(q)}/", page)
    time.sleep(2)
    if code != "200":
        print("  !", q, code); return []
    t = open(page, encoding="utf-8", errors="ignore").read()
    items, seen = [], set()
    for m in re.finditer(r'href="/free-stock-video/([a-z0-9-]+)-(\d+)/"', t):
        slug, vid = m.group(1), m.group(2)
        if vid in seen:
            continue
        seen.add(vid)
        th = re.search(r'https://assets\.mixkit\.co/[^"\s]*?/' + vid + r'[^"\s]*?thumb[^"\s]*?\.jpg', t)
        items.append({"id": vid, "title": slug.replace("-", " "), "page": f"https://mixkit.co/free-stock-video/{slug}-{vid}/",
                      "thumb": th.group(0) if th else f"https://assets.mixkit.co/videos/{vid}/{vid}-thumb-360-0.jpg"})
    items = items[:16]
    json.dump(items, open(path, "w", encoding="utf-8"), indent=1)
    for it in items:
        tp = os.path.join(WORK, f"t_{it['id']}.jpg")
        if not os.path.exists(tp):
            if curl(it["thumb"], tp, 30) != "200" and os.path.exists(tp):
                os.remove(tp)
            time.sleep(0.15)
    print(" ", q, len(items), flush=True)
    return items


def sheet(qs, name):
    fb = ImageFont.truetype(os.path.join(ROOT, "assets/fonts/InterTight-Heavy.ttf"), 18)
    fm = ImageFont.truetype(os.path.join(ROOT, "assets/fonts/InterTight-Medium.ttf"), 13)
    TW, TH, per = 240, 135, 10
    sh = Image.new("RGB", (160 + per * TW, len(qs) * (TH + 24)), (18, 18, 18)); d = ImageDraw.Draw(sh)
    for r, q in enumerate(qs):
        items = search(q)
        y = r * (TH + 24)
        d.text((4, y + 6), q[:16], font=fb, fill=(255, 200, 60))
        for i, it in enumerate(items[:per]):
            tp = os.path.join(WORK, f"t_{it['id']}.jpg")
            x = 160 + i * TW
            if os.path.exists(tp):
                try:
                    im = Image.open(tp).convert("RGB"); im.thumbnail((TW - 4, TH)); sh.paste(im, (x, y))
                except Exception:
                    pass
            d.rectangle([x, y, x + 70, y + 20], fill=(0, 0, 0)); d.text((x + 3, y + 1), f"{i}:{it['id']}", font=fb, fill=(255, 255, 255))
            d.text((x + 2, y + TH + 2), it["title"][:30], font=fm, fill=(190, 190, 190))
    out = os.path.join(WORK, f"sheet_{name}.jpg"); sh.save(out, quality=82); print(out)


def item_meta(vid):
    page = None
    for fn in os.listdir(WORK):
        if fn.startswith("q_") and fn.endswith(".json"):
            for it in json.load(open(os.path.join(WORK, fn), encoding="utf-8")):
                if it["id"] == vid:
                    page = it["page"]; break
        if page:
            break
    if not page:
        sys.exit(f"unknown id {vid}: search for it first")
    hp = os.path.join(WORK, f"item_{vid}.html")
    if not os.path.exists(hp):
        curl(page, hp); time.sleep(2)
    t = open(hp, encoding="utf-8", errors="ignore").read()
    lic = re.search(r'"license":"([^"]+)"', t)
    cu = re.search(r'"contentUrl":"([^"]+\.mp4)"', t)
    nm = re.search(r'"@type":"VideoObject","name":"([^"]+)"', t) or re.search(r'<title>([^<|]+)', t)
    return {"page": page, "license": lic.group(1) if lic else "", "content": cu.group(1) if cu else "",
            "title": html.unescape(nm.group(1)).strip() if nm else ""}


def get(vid, slug, ss, dur):
    dst = os.path.join(OUT, slug + ".mp4")
    if os.path.exists(dst):
        sys.exit(f"exists: {dst}")
    m = item_meta(vid)
    if not m["license"].endswith("#videoFree"):
        sys.exit(f"not Mixkit Free License ({m['license']}): {m['page']}")
    srcs = []
    if m["content"]:
        srcs = [re.sub(r"-(360|720)\.mp4$", "-1080.mp4", m["content"]), m["content"]]
    srcs += [f"https://assets.mixkit.co/videos/{vid}/{vid}-1080.mp4", f"https://assets.mixkit.co/videos/{vid}/{vid}-720.mp4"]
    raw = os.path.join(WORK, f"raw_{vid}.mp4"); used = None
    for u in srcs:
        if os.path.exists(raw) and os.path.getsize(raw) > 100000:
            used = u; break
        if curl(u, raw, 300) == "200" and os.path.getsize(raw) > 100000:
            used = u; break
    if not used:
        sys.exit(f"download failed {vid}")
    pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", raw],
                                   capture_output=True, text=True).stdout or "{}")
    full = float(pr.get("format", {}).get("duration", 0) or 0)
    dur = min(dur, 12.0, max(full - ss, 1.0))
    vf = "scale='if(gt(ih,1080),-2,iw)':'if(gt(ih,1080),1080,ih)',fps=30,format=yuv420p"
    for crf in (20, 23, 26):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(ss), "-i", raw, "-t", f"{dur:.2f}", "-vf", vf, "-an",
                        "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-movflags", "+faststart", dst], check=True)
        if os.path.getsize(dst) <= 15e6:
            break
    pr2 = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration",
                                     "-of", "json", dst], capture_output=True, text=True).stdout or "{}")
    st = (pr2.get("streams") or [{}])[0]
    rec = {"file": f"broll_video/{slug}.mp4", "source": "mixkit", "title": m["title"], "author": "Mixkit (Envato)",
           "license": "Mixkit Stock Video Free License (free for commercial use, no attribution required)",
           "page": m["page"], "url": used, "id": vid, "trim": [ss, round(dur, 2)], "width": st.get("width"), "height": st.get("height"),
           "duration": round(float(pr2.get("format", {}).get("duration", 0) or 0), 2), "fetched": time.strftime("%Y-%m-%d")}
    cp = os.path.join(OUT, "credits.json")
    cr = json.load(open(cp, encoding="utf-8")) if os.path.exists(cp) else []
    cr = [c for c in cr if c.get("file") != rec["file"]] + [rec]
    json.dump(cr, open(cp, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    os.remove(raw)
    print(f"got {slug} {st.get('width')}x{st.get('height')} {rec['duration']}s {os.path.getsize(dst) / 1e6:.1f} MB  <- {m['title']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("args", nargs="*")
    ap.add_argument("--out", default="x"); ap.add_argument("--ss", type=float, default=1.0); ap.add_argument("--dur", type=float, default=10.0)
    a = ap.parse_args()
    if a.cmd == "search":
        for q in a.args:
            search(q)
    elif a.cmd == "sheets":
        sheet(a.args, a.out)
    elif a.cmd == "get":
        get(a.args[0], a.args[1], a.ss, a.dur)

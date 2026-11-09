"""Write the B-roll credits list for the v4 episode: every credited photo/video whose file is referenced by the
final specs (long4/*.json) or by the graphics sources (v4/gfx.json, v4/info.json, v4/info_src, v4/gfx_src).
usage: python credits_list.py <out.txt>"""
import glob, json, os, sys

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # projects/carrie-ep01
blob = []
for pat in ("long4/L4_*.json", "v4/gfx.json", "v4/info.json", "v4/info_src/**/*.*", "v4/gfx_src/**/*.*"):
    for p in glob.glob(os.path.join(HERE, pat), recursive=True):
        if os.path.isfile(p) and os.path.getsize(p) < 5_000_000 and p.endswith((".json", ".html", ".js", ".css", ".txt", ".md")):
            blob.append(open(p, encoding="utf-8", errors="ignore").read())
blob = "\n".join(blob)

creds = []
for f in ("broll/credits.json", "broll_video/credits.json"):
    creds += json.load(open(os.path.join(HERE, f), encoding="utf-8"))
used, seen = [], set()
for c in creds:
    b = os.path.basename(c["file"])
    if b in blob and b not in seen:
        seen.add(b); used.append(c)

need = [c for c in used if "BY" in c.get("license", "").upper()]
free = [c for c in used if c not in need]
L = ["B-ROLL CREDITS — Fuelling Like an Endurance Athlete (Nizam x Carrie Mullin Innes)", "",
     "Attribution required (paste into the YouTube description):"]
for c in sorted(need, key=lambda c: c["title"].lower()):
    L.append(f'- "{c["title"]}" by {c.get("author") or "unknown"}, {c["license"]} — {c.get("page", "")}')
L += ["", "No attribution required (listed for the record):"]
for c in sorted(free, key=lambda c: (c.get("source", ""), c["title"].lower())):
    L.append(f'- {c["title"]} — {c.get("author") or c.get("source")}, {c.get("license", "")} — {c.get("page", "")}')
open(sys.argv[1], "w", encoding="utf-8").write("\n".join(L) + "\n")
print(len(used), "used;", len(need), "need attribution ->", sys.argv[1])

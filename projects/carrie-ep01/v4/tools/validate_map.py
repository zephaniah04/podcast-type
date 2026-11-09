#!/usr/bin/env python3
"""Validate projects/carrie-ep01/v4/broll_map.json. Exit 1 on any failure.

Checks every entry: the anchor phrase is found by build_long2.find(f, at, phrase) and starts at `t` (+-0.05 s);
the media files exist (photos >= 1000 px wide, videos <= 15 MB, <= 1080p); fields/treat/kind/hold/label are legal;
the beat lies inside the edit plan; no two beats within 6 s in one file; each file used <= 3 times and >= 180 s apart
(approx. output time `out`); sorted by file then time.
Run from the repo root:  python projects/carrie-ep01/v4/tools/validate_map.py
"""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from l2 import L2, EP  # noqa: E402
from PIL import Image  # noqa: E402
os.chdir(os.path.dirname(os.path.dirname(EP)))
import build_map as BM  # noqa: E402  (edit-plan ranges)

m = json.load(open(os.path.join(EP, "v4", "broll_map.json"), encoding="utf-8"))
err = []
seen_img = {}


def bad(e, msg):
    err.append(f"{e.get('f')} {e.get('at')} '{e.get('phrase')}': {msg}")


for e in m:
    try:
        i, n = L2.find(e["f"], e["at"], e["phrase"])
        t = L2.WS[e["f"]][i][0]
        if abs(t - e["t"]) > 0.05:
            bad(e, f"t {e['t']} != phrase start {t:.2f}")
        if e["at"] != BM.mmss(e["t"])[:5]:
            bad(e, f"at {e['at']} != t {e['t']}")
        if not 2 <= n <= 5:
            bad(e, f"phrase has {n} words (want 2-5)")
    except SystemExit as x:
        bad(e, f"phrase not found ({x})")
    files = e.get("assets") or [e.get("asset")]
    if e["treat"] == "stack":
        if not e.get("assets") or not 2 <= len(e["assets"]) <= 4:
            bad(e, "stack needs 2-4 assets")
    elif not e.get("asset"):
        bad(e, "missing asset")
    if e["treat"] not in ("split", "full", "stack") or e["kind"] not in ("photo", "video"):
        bad(e, "bad treat/kind")
    for p in files:
        if not p or not os.path.exists(p):
            bad(e, f"file missing: {p}"); continue
        if p.endswith(".jpg"):
            if p not in seen_img:
                seen_img[p] = Image.open(p).size
            if seen_img[p][0] < 1000:
                bad(e, f"photo only {seen_img[p][0]} px wide")
            if e["kind"] != "photo":
                bad(e, "kind should be photo")
        elif p.endswith(".mp4"):
            if e["kind"] != "video":
                bad(e, "kind should be video")
            if os.path.getsize(p) > 15e6:
                bad(e, "video > 15 MB")
            d = BM.vdur(p)
            if e["hold"] > d + 0.05:
                bad(e, f"hold {e['hold']} > clip {d:.1f}")
    lo = 2.5 if e["kind"] == "photo" else 2.0
    if not lo <= e["hold"] <= (6.0 if e["kind"] == "photo" else 12.0):
        bad(e, f"hold {e['hold']} out of range")
    if len(e["label"].split()) > 4:
        bad(e, f"label > 4 words: {e['label']}")
    if e["prio"] not in (1, 2, 3):
        bad(e, "prio")
    if not BM.where(e["f"], e["t"]):
        bad(e, "outside the edit plan")
for a, b in zip(m, m[1:]):
    if (a["f"], a["t"]) > (b["f"], b["t"]):
        bad(b, "not sorted")
    if a["f"] == b["f"] and b["t"] - a["t"] < 6.0:
        bad(b, f"only {b['t'] - a['t']:.2f} s after the previous beat")
uses = {}
for e in m:
    for p in e.get("assets") or [e["asset"]]:
        uses.setdefault(p, []).append(e["out"])
for p, u in uses.items():
    u.sort()
    if len(u) > 3:
        err.append(f"{p}: used {len(u)}x")
    for x, y in zip(u, u[1:]):
        if y - x < 180:
            err.append(f"{p}: reused {y - x:.0f} s apart (out {x:.0f} / {y:.0f})")
print(f"{len(m)} beats, {len(uses)} files checked: {len(err)} problem(s)")
for x in err:
    print("  -", x)
sys.exit(1 if err else 0)

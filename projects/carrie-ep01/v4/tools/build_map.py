#!/usr/bin/env python3
"""Resolve v4/tools/beats.py into projects/carrie-ep01/v4/broll_map.json (+ broll_map.md).

Run from the repo root:  python projects/carrie-ep01/v4/tools/build_map.py
- every phrase is located with build_long2.find() (exact word match within +-25 s); t = first word's start
- only beats inside edit_plan.json keep / cold_open / outro ranges are mapped
- the best AVAILABLE asset is used (primary, else alt; stacks keep the photos that exist), so re-running after
  new downloads upgrades the map in place
- greedy by priority: never two beats within 6 s (same file), each file used <= 3 times and >= 180 s apart
  (approximate output time from the edit plan)
"""
import json, os, subprocess, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
os.chdir(ROOT)
EP = "projects/carrie-ep01"
sys.path.insert(0, EP)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from l2 import L2  # noqa: E402  (build_long2, robust import)
from beats import BEATS  # noqa: E402

SPACING, REUSE_N, REUSE_GAP = 6.0, 3, 180.0
FLEN = {"A": 2351.0, "B": 3151.0}


def plan_ranges():
    d = json.load(open(f"{EP}/v4/edit_plan.json", encoding="utf-8"))
    rng = []  # (f, start, end, out_start, ratio, chapter)
    for c in d["chapters"]:
        o = c["out_start_s"]
        for k in c["keep"]:
            dur = k["end"] - k["start"]
            ratio = (k.get("est_s") or dur) / dur if dur else 1
            rng.append((k["f"], k["start"], k["end"], o, ratio, c["n"]))
            o += k.get("est_s") or dur
    o = 0.0
    for s in d["cold_open"]:
        rng.append((s["f"], s["start"], s["end"], o, 1.0, 0)); o += s.get("est_s") or (s["end"] - s["start"])
    o = d.get("outro_out_start_s", 3800)
    for s in d["outro"]:
        rng.append((s["f"], s["start"], s["end"], o, 1.0, 99)); o += s["end"] - s["start"]
    return rng


RANGES = plan_ranges()


def where(f, t):
    """(out_time, chapter, seconds left in the contiguous kept stretch) or None. Prefers chapter keeps over the cold open."""
    hits = [r for r in RANGES if r[0] == f and r[1] - 0.05 <= t < r[2]]
    if not hits:
        return None
    hits.sort(key=lambda r: (r[5] == 0, r[1]))
    r = hits[0]
    end = r[2]
    while True:  # extend through back-to-back keeps
        nxt = [q for q in RANGES if q[0] == f and q[5] == r[5] and abs(q[1] - end) < 0.6 and q[2] > end]
        if not nxt:
            break
        end = nxt[0][2]
    return r[3] + (t - r[1]) * r[4], r[5], end - t


def path_of(a):
    kind, slug = a.split(":", 1)
    return (f"{EP}/broll/{slug}.jpg", "photo") if kind == "p" else (f"{EP}/broll_video/{slug}.mp4", "video")


_dur = {}


def vdur(p):
    if p not in _dur:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True)
        _dur[p] = float(r.stdout.strip() or 0)
    return _dur[p]


def mmss(t):
    return f"{int(t // 60):02d}:{t % 60:05.2f}"


def main():
    uses = {}  # file -> [out times]
    placed, skipped, missing = [], [], []

    def free(p, out):
        u = uses.get(p, [])
        return len(u) < REUSE_N and all(abs(out - x) >= REUSE_GAP for x in u)

    cands = []
    for b in BEATS:
        try:
            i, n = L2.find(b["f"], b["at"], b["phrase"])
        except SystemExit as e:
            skipped.append((b, f"PHRASE NOT FOUND: {e}")); continue
        t = round(L2.WS[b["f"]][i][0], 2)
        w = where(b["f"], t)
        if not w:
            skipped.append((b, "outside the edit plan")); continue
        if w[2] < 2.5:
            skipped.append((b, f"only {w[2]:.1f} s before a cut")); continue
        cands.append((b, t, w))
    cands.sort(key=lambda c: (c[0]["prio"], c[0]["f"], c[1]))
    for b, t, (out, ch, left) in cands:
        if any(p["f"] == b["f"] and abs(p["t"] - t) < SPACING for p in placed):
            skipped.append((b, "within 6 s of a higher-priority beat")); continue
        options = []
        prim = b["asset"]
        if isinstance(prim, list):
            have = [a for a in prim if os.path.exists(path_of(a)[0])]
            if len(have) >= 2:
                options.append(("stack", have))
            elif len(have) == 1:
                options.append(("single", have[0]))
        elif os.path.exists(path_of(prim)[0]):
            options.append(("single", prim))
        if b.get("alt") and os.path.exists(path_of(b["alt"])[0]):
            options.append(("single", b["alt"]))
        chosen = None
        for kind, a in options:
            files = [path_of(x)[0] for x in (a if kind == "stack" else [a])]
            if all(free(p, out) for p in files):
                chosen = (kind, a, files); break
        if not chosen:
            (missing if not options else skipped).append((b, "no media yet" if not options else "reuse limit (3x / 3 min)"))
            continue
        kind, a, files = chosen
        for p in files:
            uses.setdefault(p, []).append(out)
        e = {"f": b["f"], "t": t, "at": mmss(t)[:5], "phrase": b["phrase"]}
        if kind == "stack":
            e.update(assets=files, kind="photo", treat="stack")
        else:
            p, k = path_of(a)
            e.update(asset=p, kind=k, treat=("split" if b["treat"] == "stack" else b["treat"]) if k == "photo" else "full")
        hold = b["hold"]
        if e["kind"] == "video":
            hold = min(max(hold, 3.0), vdur(e["asset"]))
        hold = round(min(hold, left), 2)
        e.update(label=b["label"], hold=hold, prio=b["prio"], why=b["why"], out=round(out, 1), ch=ch)
        if e.get("asset") and a != b["asset"]:
            e["why"] += " (fallback photo)"
        placed.append(e)
    placed.sort(key=lambda e: (e["f"], e["t"]))
    json.dump(placed, open(f"{EP}/v4/broll_map.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    json.dump([dict(b, reason=r) for b, r in missing], open(f"{EP}/v4/tools/pending.json", "w", encoding="utf-8"), indent=1)
    write_md(placed, skipped, missing)
    print(f"placed {len(placed)}  missing-media {len(missing)}  skipped {len(skipped)}")
    for b, r in skipped:
        if r.startswith("PHRASE") or r.startswith("reuse"):
            print("  !", b["f"], b["at"], b["phrase"], "->", r)


def write_md(placed, skipped, missing):
    cred = {c["file"]: c for c in json.load(open(f"{EP}/broll/credits.json", encoding="utf-8"))}
    new = {k for k, c in cred.items() if c.get("added") == "v4"}
    files = [x for e in placed for x in (e.get("assets") or [e["asset"]])]
    photos = {x for x in files if x.endswith(".jpg")}
    rel = lambda p: p.replace(f"{EP}/", "")
    n_new = len([p for p in photos if rel(p) in new])
    vids = {x for x in files if x.endswith(".mp4")}
    by = lambda k: sum(1 for e in placed if e["treat"] == k)
    L = ["# v4 B-roll map", "",
         f"- beats placed: **{len(placed)}** (A {sum(e['f'] == 'A' for e in placed)}, B {sum(e['f'] == 'B' for e in placed)})"
         f" — prio 1: {sum(e['prio'] == 1 for e in placed)}, prio 2: {sum(e['prio'] == 2 for e in placed)}, prio 3: {sum(e['prio'] == 3 for e in placed)}",
         f"- treat: split {by('split')}, full {by('full')}, stack {by('stack')}",
         f"- unique photos used: {len(photos)} ({len(photos) - n_new} existing, {n_new} new in v4); photo placements: {sum(f.endswith('.jpg') for f in files)}",
         f"- videos used: {len(vids)} unique, {sum(f.endswith('.mp4') for f in files)} placements",
         "- only beats inside edit_plan.json keep / cold_open / outro ranges; never two beats within 6 s; each file <= 3x and >= 3 min apart (approx. output time)",
         "- `out` = approximate output time (s) from the edit plan, `ch` = chapter (0 = cold open, 99 = outro)", "",
         "## Beats still waiting for media", ""]
    for b, r in sorted(missing, key=lambda x: (x[0]["f"], x[0]["at"])):
        a = b["asset"] if isinstance(b["asset"], str) else " + ".join(b["asset"])
        L.append(f"- {b['f']} {b['at']} \"{b['phrase']}\" -> {a} ({b['label']}, prio {b['prio']})")
    L += ["", "## Beats skipped", ""]
    for b, r in sorted(skipped, key=lambda x: (x[0]["f"], x[0]["at"])):
        L.append(f"- {b['f']} {b['at']} \"{b['phrase']}\": {r}")
    open(f"{EP}/v4/broll_map.md", "w", encoding="utf-8").write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()

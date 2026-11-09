#!/usr/bin/env python3
"""Explore the Carrie ep01 word timings.
  wordview.py dump A 01:07 06:04      -> words with start times (new line on gaps > 0.6 s or speaker change)
  wordview.py est  A 01:07 06:04      -> tightened-duration estimate (word durations + gaps capped at 0.35 s)
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
TX = os.path.join(ROOT, "projects", "carrie-ep01", "tx")
FILES = {"A": "IMG_4342-001", "B": "IMG_4343-002"}
_W = {}


def words(f):
    if f not in _W:
        d = json.load(open(os.path.join(TX, FILES[f] + ".json"), encoding="utf-8"))
        _W[f] = [(x[0], x[1], x[2].strip(), x[4] if len(x) > 4 else "?") for s in d for x in s["w"] if x[2].strip()]
    return _W[f]


def sec(t):
    if isinstance(t, (int, float)):
        return float(t)
    m, s = t.split(":"); return int(m) * 60 + float(s)


def mmss(t):
    return f"{int(t // 60):02d}:{t % 60:04.1f}"


def est(f, a, b):
    ws = [x for x in words(f) if x[0] >= a - 1e-6 and x[1] <= b + 1e-6]
    t = 0.0
    for i, x in enumerate(ws):
        t += x[1] - x[0]
        if i:
            t += min(max(x[0] - ws[i - 1][1], 0.0), 0.35)
    return t


def dump(f, a, b):
    ws = [x for x in words(f) if a <= x[0] <= b]
    line, prev = [], None
    for x in ws:
        if prev is not None and (x[0] - prev[1] > 0.6 or x[3] != prev[3]):
            print(" ".join(line)); line = []
        if not line:
            line.append(f"[{mmss(x[0])} {x[3]}]")
        line.append(x[2])
        prev = x
    if line:
        print(" ".join(line))


if __name__ == "__main__":
    cmd, f, a, b = sys.argv[1], sys.argv[2], sec(sys.argv[3]), sec(sys.argv[4])
    if cmd == "dump":
        dump(f, a, b)
    print(f"# est {f} {mmss(a)}-{mmss(b)}: {est(f, a, b):.1f} s")

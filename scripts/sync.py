#!/usr/bin/env python3
"""Find how far apart multicam recordings started, from their audio (every phone/camera hears the room).

usage:
  python3 scripts/sync.py projects/ep01/raw/camA.MOV projects/ep01/raw/camB.MOV [more cams...] [--dur 600]

The FIRST file is the master (best mic: its audio and transcript drive the edit). For every other file prints
its delay = how many seconds later it started than the master (negative = it started earlier), plus a
confidence score, and the JSON to paste into the spec:

  "master": "camA", "sync": {"camB": 2.507}

In a spec all segment times are then master times; camB is read at (time - 2.507).
Confidence < 3 means the match is weak (very different mics, music, or no overlap in the first --dur seconds):
check by eye on a clap / hard consonant, or raise --dur.
"""
import argparse, json, os, subprocess, sys
import numpy as np

SR = 8000      # decode rate
ENV = 400      # envelope rate (2.5 ms resolution)


def envelope(path, start, dur):
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(start), "-t", str(dur), "-i", path, "-map", "0:a:0",
                          "-ac", "1", "-ar", str(SR), "-af", "highpass=f=150,lowpass=f=3500", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    x = np.abs(np.frombuffer(pcm, np.float32))
    k = SR // ENV
    x = x[: len(x) // k * k].reshape(-1, k).mean(1)          # rectified + decimated loudness curve
    x = np.log1p(x * 1000.0)                                  # compress so loud laughs don't dominate
    x -= np.convolve(x, np.ones(ENV) / ENV, mode="same")      # remove slow level drift (1 s)
    return (x - x.mean()) / (x.std() + 1e-9)


def find_delay(a, b):
    n = 1 << int(np.ceil(np.log2(len(a) + len(b))))
    c = np.fft.irfft(np.fft.rfft(a, n) * np.conj(np.fft.rfft(b, n)), n)
    c = np.concatenate([c[-(len(b) - 1):], c[: len(a)]])      # lags -(len(b)-1) .. len(a)-1
    lags = np.arange(-(len(b) - 1), len(a))
    i = int(np.argmax(c))
    # confidence: peak vs. the best peak at least 0.5 s away
    mask = np.abs(lags - lags[i]) > ENV // 2
    second = c[mask].max() if mask.any() else 0
    conf = float(c[i] / (abs(second) + 1e-9))
    # parabolic refinement of the peak
    if 0 < i < len(c) - 1:
        y0, y1, y2 = c[i - 1], c[i], c[i + 1]
        frac = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2 + 1e-12)
    else:
        frac = 0.0
    return (lags[i] + frac) / ENV, conf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--dur", type=float, default=600, help="seconds of audio to compare (from the start)")
    ap.add_argument("--start", type=float, default=0)
    a = ap.parse_args()
    if len(a.files) < 2:
        sys.exit("give the master file first, then one or more other cameras")
    name = lambda p: os.path.splitext(os.path.basename(p))[0]
    m = envelope(a.files[0], a.start, a.dur)
    out = {}
    for f in a.files[1:]:
        d, conf = find_delay(m, envelope(f, a.start, a.dur))
        out[name(f)] = round(d, 3)
        flag = "" if conf >= 3 else "   <- weak match, verify"
        print(f"{name(f)}: starts {d:+.3f} s vs {name(a.files[0])} (confidence {conf:.1f}){flag}")
    print(json.dumps({"master": name(a.files[0]), "sync": out}))


if __name__ == "__main__":
    main()

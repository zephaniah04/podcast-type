#!/usr/bin/env python3
"""Label who speaks each word by VOICE PITCH (one mixed mic track, a male and a female voice).

Mouth-motion labels fail when a speaker faces away from the camera (a dietitian at her monitor). Pitch doesn't care
where anyone looks. Per word: median F0 of its voiced frames (autocorrelation, 70-400 Hz). The two voices form two
clusters; the threshold is the valley between them (or --split Hz). Labels are smoothed over each Whisper segment and
written into tx/<clip>.json word field [4] ("L" = --low side, "R" = --high side) + tx/<clip>_speakers.txt.

usage: python scripts/pitch_speakers.py "<video>" --tx <tx dir> --low Nizam --high Carrie --low-side L
"""
import argparse, json, os, subprocess
import numpy as np

SR = 16000


def f0_track(x, hop=0.01, win=0.04, fmin=70, fmax=400):
    n, h = int(win * SR), int(hop * SR)
    lo, hi = int(SR / fmax), int(SR / fmin)
    nfr = max(0, (len(x) - n) // h)
    out = np.zeros(nfr, np.float32)
    # frame matrix (strided), energy gate, normalised autocorrelation via FFT
    idx = np.arange(n)[None, :] + h * np.arange(nfr)[:, None]
    for s in range(0, nfr, 4000):
        fr = x[idx[s:s + 4000]].astype(np.float32)
        fr -= fr.mean(1, keepdims=True)
        e = (fr ** 2).sum(1)
        F = np.fft.rfft(fr, 2 * n)
        ac = np.fft.irfft(F * np.conj(F))[:, :n]
        ac /= np.maximum(ac[:, :1], 1e-9)
        seg = ac[:, lo:hi]
        k = seg.argmax(1); pk = seg.max(1)
        f = SR / (k + lo)
        ok = (pk > 0.45) & (e > np.percentile(e, 30) if len(e) > 10 else e > 0)
        out[s:s + len(fr)] = np.where(ok, f, 0)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("--tx", required=True)
    ap.add_argument("--low", default="LOW"); ap.add_argument("--high", default="HIGH")
    ap.add_argument("--low-side", default="L", choices=["L", "R"])
    ap.add_argument("--win", type=float, default=1.2, help="smoothing half-window in seconds")
    ap.add_argument("--split", type=float, default=None, help="Hz between the two voices (default: auto valley)")
    a = ap.parse_args()
    name = os.path.splitext(os.path.basename(a.video))[0]
    jp = os.path.join(a.tx, name + ".json")
    d = json.load(open(jp, encoding="utf-8"))
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", a.video, "-map", "0:a:0", "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
    f0 = f0_track(x)
    # per word median F0
    wf = []
    for sg in d:
        for w in sg["w"]:
            a0, a1 = int(w[0] * 100), int(w[1] * 100) + 1
            v = f0[a0:a1]; v = v[v > 0]
            wf.append(float(np.median(v)) if len(v) >= 3 else 0.0)
    # time smoothing: a word's pitch = median pitch of voiced words within +-win s (voices overlap word by word)
    tw = np.array([w[0] for sg in d for w in sg["w"]]); fw = np.array(wf)
    sw = []
    for i in range(len(fw)):
        m = (np.abs(tw - tw[i]) <= a.win) & (fw > 0)
        sw.append(float(np.median(fw[m])) if m.any() else 0.0)
    wf = sw
    allf = np.array([f for f in wf if f > 0])
    if a.split:
        thr = a.split
    else:  # valley of the log-F0 histogram between the two modes
        h, edges = np.histogram(np.log(allf), bins=60, range=(np.log(70), np.log(400)))
        hs = np.convolve(h, np.ones(5) / 5, "same")
        c = (edges[:-1] + edges[1:]) / 2
        p1 = int(np.argmax(hs)); hs2 = hs.copy(); hs2[max(0, p1 - 8):p1 + 9] = 0; p2 = int(np.argmax(hs2))
        lo_, hi_ = sorted((p1, p2))
        v = lo_ + int(np.argmin(hs[lo_:hi_ + 1]))
        thr = float(np.exp(c[v]))
    print(f"{name}: voiced words {len(allf)}/{len(wf)}, F0 p10/50/90 = {np.percentile(allf, [10, 50, 90]).round(0)}, split {thr:.0f} Hz")
    hs_ = "L" if a.low_side == "R" else "R"
    k = 0; lines = []
    for sg in d:
        labs = []
        for w in sg["w"]:
            f = wf[k]; k += 1
            labs.append(None if f <= 0 else (a.low_side if f < thr else hs_))
        # smooth: unlabelled / isolated words take the majority of their neighbours (window 5)
        sm = []
        for i in range(len(labs)):
            win = [l for l in labs[max(0, i - 2):i + 3] if l]
            sm.append(max(set(win), key=win.count) if win else (labs[i] or "?"))
        for w, l in zip(sg["w"], sm):
            if len(w) > 4:
                w[4] = l
            else:
                while len(w) < 4:
                    w.append(0)
                w.append(l)
        # transcript lines split at speaker changes
        cur, st, words = None, None, []
        for w, l in zip(sg["w"], sm):
            if l != cur and words:
                lines.append((st, prev_end, cur, " ".join(words))); words = []
            if not words:
                st = w[0]
            cur = l; words.append(w[2].strip()); prev_end = w[1]
        if words:
            lines.append((st, prev_end, cur, " ".join(words)))
    json.dump(d, open(jp, "w", encoding="utf-8"))
    nm = {a.low_side: a.low.upper(), hs_: a.high.upper(), "?": "?"}
    fmt = lambda t: f"{int(t // 60):02d}:{t % 60:04.1f}"
    out = os.path.join(a.tx, name + "_speakers.txt")
    with open(out, "w", encoding="utf-8") as f:
        for st, en, l, txt in lines:
            f.write(f"[{fmt(st)} - {fmt(en)}] {nm.get(l, '?')}: {txt}\n")
    print("->", out)


if __name__ == "__main__":
    main()

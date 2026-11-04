#!/usr/bin/env python3
"""Who is speaking, word by word, in a two-person wide shot (LEFT person vs RIGHT person).

usage:
  python scripts/speakers.py projects/ep01/raw/IMG_4342.MOV --tx projects/ep01/tx --left Nizam --right Carrie

Method (auto):
  1. audio  - if the two mics are on separate stereo channels, the louder channel per word wins (most reliable).
  2. video  - otherwise, mouth/jaw motion inside each person's face box (frame differencing at 6 fps): the side
              that moves more during a sentence is the speaker. Decided per transcript segment, then per word.
Writes back into tx/<clip>.json: every word gets a 5th field "L"/"R"/"?", every segment "spk".
Writes tx/<clip>_speakers.txt:  "[12:03.4 - 12:09.9] CARRIE: ..."  (read this to pick Q -> A moments).
Prints how sure it is; spot-check a few turns before trusting it for a whole episode.
"""
import argparse, json, os, subprocess, sys
import numpy as np


def fmt(t):
    m, s = divmod(max(t, 0), 60); h, m = divmod(int(m), 60)
    return f"{h}:{m:02d}:{s:04.1f}" if h else f"{m:02d}:{s:04.1f}"


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,channels",
                          "-of", "json", path], capture_output=True, text=True, check=True).stdout
    st = json.loads(out)["streams"]
    v = next(s for s in st if s["codec_type"] == "video"); a = next((s for s in st if s["codec_type"] == "audio"), {})
    return v["width"], v["height"], a.get("channels", 1)


# ------------------------------------------------------------------ audio
def audio_labels(path, segs, sr=16000):
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-map", "0:a:0", "-ac", "2", "-ar", str(sr),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(pcm, np.float32).reshape(-1, 2)
    L, R = x[:, 0], x[:, 1]
    if np.corrcoef(L[::50], R[::50])[0, 1] > 0.97:
        return None, 0.0  # both channels carry the same mix
    db = lambda v: 10 * np.log10(np.mean(v.astype(np.float64) ** 2) + 1e-12)
    labs, sure = [], 0
    for sg in segs:
        lw = []
        for w in sg["w"]:
            a, b = int(w[0] * sr), max(int(w[1] * sr), int(w[0] * sr) + 160)
            d = db(L[a:b]) - db(R[a:b])
            lw.append("L" if d > 3 else "R" if d < -3 else "?")
        sure += sum(l != "?" for l in lw)
        labs.append(lw)
    n = sum(len(sg["w"]) for sg in segs) or 1
    return labs, sure / n


# ------------------------------------------------------------------ video
def face_boxes(path, W, H, dur):
    """Median face box (x, y, w, h in 0..1) for the left and the right person."""
    import cv2
    casc = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml"))
    prof = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, "haarcascade_profileface.xml"))
    sw = 960; shh = int(sw * H / W) // 2 * 2
    left, right = [], []
    for t in np.linspace(dur * 0.05, dur * 0.95, 15):
        p = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", path, "-frames:v", "1",
                            "-vf", f"scale={sw}:{shh}", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True)
        if len(p.stdout) != sw * shh:
            continue
        img = np.frombuffer(p.stdout, np.uint8).reshape(shh, sw)
        fs = list(casc.detectMultiScale(img, 1.1, 5, minSize=(sw // 30, sw // 30)))
        fs += list(prof.detectMultiScale(img, 1.1, 5, minSize=(sw // 30, sw // 30)))
        fs += [(sw - x - w, y, w, h) for x, y, w, h in prof.detectMultiScale(img[:, ::-1].copy(), 1.1, 5, minSize=(sw // 30, sw // 30))]
        for x, y, w, h in fs:
            (left if x + w / 2 < sw / 2 else right).append((x / sw, y / shh, w / sw, h / shh))
    pick = lambda b: tuple(np.median(np.array(b), 0)) if b else None
    return pick(left), pick(right)


def mouth_motion(path, W, H, boxes, fps=6):
    """Per-frame motion energy in the lower face (mouth/jaw) of each person. Returns times, mL, mR."""
    sw = 640; shh = int(sw * H / W) // 2 * 2
    rois = []
    for (x, y, w, h) in boxes:
        x0, x1 = int((x - 0.1 * w) * sw), int((x + 1.1 * w) * sw)
        y0, y1 = int((y + 0.55 * h) * shh), int((y + 1.25 * h) * shh)
        rois.append((max(x0, 0), max(y0, 0), min(x1, sw), min(y1, shh)))
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-vf", f"fps={fps},scale={sw}:{shh}", "-f", "rawvideo",
                             "-pix_fmt", "gray", "-"], stdout=subprocess.PIPE)
    n = sw * shh; prev = None; mL, mR = [], []
    while True:
        buf = proc.stdout.read(n)
        if len(buf) < n:
            break
        f = np.frombuffer(buf, np.uint8).reshape(shh, sw).astype(np.int16)
        if prev is None:
            mL.append(0.0); mR.append(0.0)
        else:
            d = np.abs(f - prev)
            for out, (x0, y0, x1, y1) in zip((mL, mR), rois):
                out.append(float(d[y0:y1, x0:x1].mean()))
        prev = f
    proc.wait()
    mL, mR = np.array(mL), np.array(mR)
    # people move differently: normalise each side by its own typical level
    mL /= np.median(mL[mL > 0]) + 1e-6; mR /= np.median(mR[mR > 0]) + 1e-6
    return np.arange(len(mL)) / fps, mL, mR


def video_labels(segs, t, mL, mR):
    labs, sure = [], 0
    for sg in segs:
        sel = (t >= sg["s"]) & (t <= sg["e"])
        if sel.sum() < 2:
            lab = "?"
        else:
            a, b = mL[sel].mean(), mR[sel].mean()
            lab = "L" if a > b * 1.15 else "R" if b > a * 1.15 else "?"
        sure += lab != "?"
        labs.append([lab] * len(sg["w"]))
    return labs, sure / max(len(segs), 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("--tx", required=True)
    ap.add_argument("--left", default="LEFT"); ap.add_argument("--right", default="RIGHT")
    ap.add_argument("--method", default="auto", choices=["auto", "audio", "video"])
    a = ap.parse_args()
    clip = os.path.splitext(os.path.basename(a.video))[0]
    jp = os.path.join(a.tx, clip + ".json")
    segs = json.load(open(jp, encoding="utf-8"))
    W, H, ch = probe(a.video)
    labs, how, sure = None, "", 0.0
    if a.method in ("auto", "audio") and ch >= 2:
        labs, sure = audio_labels(a.video, segs)
        how = "audio channels"
        if labs is not None and a.method == "auto" and sure < 0.5:
            labs = None  # channels too similar to decide most words
    if labs is None:
        dur = max(sg["e"] for sg in segs)
        bl, br = face_boxes(a.video, W, H, dur)
        if not bl or not br:
            sys.exit("could not find a face on both sides of the frame; pass --method audio or label by hand")
        t, mL, mR = mouth_motion(a.video, W, H, (bl, br))
        labs, sure = video_labels(segs, t, mL, mR)
        how = "mouth motion"
    names = {"L": a.left.upper(), "R": a.right.upper(), "?": "?"}
    lines = []
    for sg, lw in zip(segs, labs):
        for w, l in zip(sg["w"], lw):
            w[4:] = [l]
        vals = [l for l in lw if l != "?"]
        sg["spk"] = max(set(vals), key=vals.count) if vals else "?"
        lines.append(f"[{fmt(sg['s'])} - {fmt(sg['e'])}] {names[sg['spk']]}: {sg['text']}")
    json.dump(segs, open(jp, "w", encoding="utf-8"), ensure_ascii=False)
    open(os.path.join(a.tx, clip + "_speakers.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    share = {k: sum(sg["spk"] == k for sg in segs) for k in "LR?"}
    print(f"{clip}: method={how}, decided {sure:.0%}; segments {names['L']}={share['L']} {names['R']}={share['R']} unsure={share['?']}")


if __name__ == "__main__":
    main()

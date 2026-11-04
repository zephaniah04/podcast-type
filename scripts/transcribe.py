#!/usr/bin/env python3
"""Transcribe raw podcast clips with word timings (faster-whisper, CPU).

For every input file writes, into --out:
  <clip>.json  [{"s": start, "e": end, "text": "...", "w": [[start, end, word, prob], ...]}, ...]
  <clip>.txt   one line per segment: "[mm:ss.s - mm:ss.s] text"  (this is what Claude reads to pick moments)

usage:
  python3 scripts/transcribe.py projects/ep01/raw/*.mp4 --out projects/ep01/tx [--model small] [--lang en]

Notes
- Hinglish: leave --lang unset (auto) or use --lang hi with --task transcribe; fix spellings later with "fixes" in the spec.
- Long episodes: the model streams, so a 2 h file is fine; budget ~0.3-0.5x real time for "small" on 8 CPU cores.
- Re-running skips clips that already have a .json (use --force to redo).
"""
import argparse, json, os, sys, time


def fmt(t):
    m, s = divmod(max(t, 0), 60)
    h, m = divmod(int(m), 60)
    return f"{h}:{m:02d}:{s:04.1f}" if h else f"{m:02d}:{s:04.1f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="small", help="tiny|base|small|medium|large-v3 (bigger = better, slower)")
    ap.add_argument("--lang", default=None, help="force language code, e.g. en / hi")
    ap.add_argument("--prompt", default=None, help="names and jargon to spell right, e.g. 'Bijen, HYROX, VO2 max'")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    from faster_whisper import WhisperModel
    os.makedirs(a.out, exist_ok=True)
    model = None
    for f in a.files:
        clip = os.path.splitext(os.path.basename(f))[0]
        jpath = os.path.join(a.out, clip + ".json")
        if os.path.exists(jpath) and not a.force:
            print(f"skip {clip} (exists)"); continue
        if model is None:
            model = WhisperModel(a.model, device="cpu", compute_type="int8")
        t0 = time.time()
        # decode with ffmpeg ourselves (16 kHz mono float) - avoids PyAV version issues and reads any container
        import subprocess, numpy as np
        pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-map", "0:a:0", "-ac", "1", "-ar", "16000",
                              "-f", "f32le", "-"], capture_output=True, check=True).stdout
        audio = np.frombuffer(pcm, np.float32)
        segs, info = model.transcribe(audio, language=a.lang, word_timestamps=True, vad_filter=True,
                                      initial_prompt=a.prompt, condition_on_previous_text=False)
        out, lines = [], []
        for s in segs:
            words = [[round(w.start, 3), round(w.end, 3), w.word.strip(), round(w.probability, 3)]
                     for w in (s.words or []) if w.word.strip()]
            if not words:
                continue
            out.append({"s": round(s.start, 3), "e": round(s.end, 3), "text": s.text.strip(), "w": words})
            lines.append(f"[{fmt(s.start)} - {fmt(s.end)}] {s.text.strip()}")
        json.dump(out, open(jpath, "w", encoding="utf-8"), ensure_ascii=False)
        open(os.path.join(a.out, clip + ".txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
        print(f"{clip}: {len(out)} segments, lang={info.language}, {info.duration:.0f}s audio in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    sys.exit(main())

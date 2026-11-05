#!/usr/bin/env python3
"""Client tracker: one table of every video made from an episode (topic, type, length, where it came from).

usage:
  python3 scripts/report.py projects/<ep> [--exports exports/<show>/<ep>]

Reads every spec in projects/<ep>/clips/*.json and projects/<ep>/long/*.json (add "title" and "topic" to each
spec), measures rendered files in --exports when they exist (else estimates from the spec), and writes
  projects/<ep>/deliverables.md   (paste/share with the client)
  projects/<ep>/deliverables.csv  (open in Excel / Google Sheets)
"""
import argparse, csv, glob, json, os, subprocess


def mmss(t):
    t = int(round(t)); h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def rendered_dur(path):
    if not path or not os.path.exists(path):
        return None
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                       capture_output=True, text=True).stdout.strip()
    return float(r) if r else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ep"); ap.add_argument("--exports", default=None)
    a = ap.parse_args()
    specs = sorted(glob.glob(os.path.join(a.ep, "long", "*.json"))) + sorted(glob.glob(os.path.join(a.ep, "clips", "*.json")))
    rows = []
    for p in specs:
        sp = json.load(open(p, encoding="utf-8"))
        if sp.get("_piece"):  # internal render chunk of a long-form, not a deliverable
            continue
        segs = [s for s in sp.get("segments", []) if not s.get("card")]
        est = sum(s["end"] - s["start"] for s in segs) + sum(float(s.get("dur", 0)) for s in sp.get("segments", []) if s.get("card"))
        est += float(sp.get("endcard", {}).get("dur", 0)) if sp.get("endcard") else 0
        out = os.path.join(a.exports, f"{sp['id']}_{sp.get('slug', 'edit')}.mp4") if a.exports else None
        real = rendered_dur(out)
        long_ = sp.get("format") == "long"
        src = sp.get("source") or ", ".join(f"{mmss(s['start'])}-{mmss(s['end'])}" for s in segs[:4]) + (" ..." if len(segs) > 4 else "")
        rows.append({
            "ID": sp["id"],
            "Type": "Long-form (YouTube)" if long_ else "Reel / Short",
            "Title": sp.get("title", sp.get("slug", "")),
            "Topic": sp.get("topic", ""),
            "Look": sp.get("look_name", sp.get("captions", "")),
            "Length": mmss(real if real else est),
            "Seconds": round(real if real else est, 1),
            "Source (raw timecodes)": src if not long_ else f"{len(segs)} segments",
            "B-roll": sp.get("broll_count", sum(1 for s in segs if s.get("broll"))),
            "Status": "Rendered" if real else "Planned",
            "File": os.path.basename(out) if real else "",
        })
    if not rows:
        raise SystemExit(f"no specs in {a.ep}/clips or {a.ep}/long")
    cols = list(rows[0])
    with open(os.path.join(a.ep, "deliverables.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    shorts = [r for r in rows if r["Type"] != "Long-form (YouTube)"]; longs = [r for r in rows if r not in shorts]
    md = [f"# Deliverables: {os.path.basename(os.path.normpath(a.ep))}", "",
          f"**{len(longs)} long-form** ({mmss(sum(r['Seconds'] for r in longs))} total) and "
          f"**{len(shorts)} shorts** ({mmss(sum(r['Seconds'] for r in shorts))} total). "
          f"Rendered {sum(r['Status'] == 'Rendered' for r in rows)} / {len(rows)}.", "",
          "| " + " | ".join(c for c in cols if c != "Seconds") + " |",
          "|" + "---|" * (len(cols) - 1)]
    for r in rows:
        md.append("| " + " | ".join(str(r[c]) for c in cols if c != "Seconds") + " |")
    open(os.path.join(a.ep, "deliverables.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()

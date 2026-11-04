#!/usr/bin/env python3
"""Download one B-roll file (video or photo) into an episode's broll/ folder and log where it came from.

Typical use: Claude searches with the Pexels MCP tools (pexels_search_videos / pexels_search_photos),
picks a result, then downloads the right rendition here:

  python3 scripts/fetch_broll.py "<direct file url>" --ep projects/ep01 --name runner-sunrise \
      --source pexels --id 857195 --author "Jane Doe" --page "https://www.pexels.com/video/..."

Picks the extension from the URL, writes projects/<ep>/broll/<name>.<ext>, and appends a line to
projects/<ep>/broll/credits.json (source, id, author, page, license note, file). Media files stay git-ignored;
credits.json is committed so every clip used is traceable.
"""
import argparse, json, os, re, subprocess, sys, time

LICENSES = {
    "pexels": "Pexels License: free to use, no attribution required (credit appreciated)",
    "pixabay": "Pixabay Content License: free to use, no attribution required",
    "unsplash": "Unsplash License: free to use, no attribution required",
    "openverse": "Creative Commons: check the license field; CC BY / BY-SA need a credit line",
    "drive": "Client's own footage",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--ep", required=True, help="episode folder, e.g. projects/ep01")
    ap.add_argument("--name", required=True, help="short slug, e.g. runner-sunrise")
    ap.add_argument("--source", default="pexels", choices=sorted(LICENSES))
    ap.add_argument("--id", default="")
    ap.add_argument("--author", default="")
    ap.add_argument("--page", default="", help="human page URL of the asset")
    a = ap.parse_args()

    out_dir = os.path.join(a.ep, "broll"); os.makedirs(out_dir, exist_ok=True)
    ext = os.path.splitext(re.sub(r"[?#].*$", "", a.url))[1].lower() or ".mp4"
    name = re.sub(r"[^\w-]+", "-", a.name).strip("-")
    path = os.path.join(out_dir, name + ext)
    r = subprocess.run(["curl", "-sSfL", "--retry", "3", "-o", path, a.url])
    if r.returncode or not os.path.exists(path) or not os.path.getsize(path):
        if os.path.exists(path):
            os.remove(path)
        sys.exit(f"download failed: {a.url} (HTTP 429 = that host is rate-limiting; try another rendition/source)")
    info = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height:format=duration",
                           "-of", "json", path], capture_output=True, text=True).stdout
    meta = json.loads(info or "{}")
    st = (meta.get("streams") or [{}])[0]
    rec = {"file": os.path.basename(path), "source": a.source, "id": a.id, "author": a.author, "page": a.page,
           "url": a.url, "license": LICENSES[a.source], "width": st.get("width"), "height": st.get("height"),
           "duration": float(meta.get("format", {}).get("duration", 0) or 0), "fetched": time.strftime("%Y-%m-%d")}
    cpath = os.path.join(out_dir, "credits.json")
    credits = json.load(open(cpath)) if os.path.exists(cpath) else []
    credits = [c for c in credits if c.get("file") != rec["file"]] + [rec]
    json.dump(credits, open(cpath, "w"), indent=1)
    print(f"{path}  {rec['width']}x{rec['height']}  {rec['duration']:.1f}s")


if __name__ == "__main__":
    main()

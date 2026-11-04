#!/usr/bin/env python3
"""Search free B-roll WITHOUT any API key: Openverse (photos), Wikimedia Commons (photos + video),
Internet Archive (video). Prints ranked candidates with a direct download URL and license, and saves them
to JSON so Claude can pick, then download with scripts/fetch_broll.py.

usage:
  python scripts/find_broll.py "athlete drinking water" --kind photo --orient portrait --n 8 --out projects/ep01/broll/_search.json
  python scripts/find_broll.py "marathon runners" --kind video

--kind photo|video|any   --orient portrait|landscape|any   --min 1080 (shortest side, px)
Licenses: only commercial-friendly results (CC0, Public Domain, CC BY, CC BY-SA). BY / BY-SA need a credit line
(fetch_broll.py records it in credits.json; put credits in the video description).
If a host rate-limits (HTTP 429), wait a minute or try another source; on a home connection this is rare.
"""
import argparse, json, os, re, subprocess, sys, urllib.parse

UA = "podcast-type-broll/0.2 (video editing; contact via repo)"
OK_LIC = re.compile(r"(cc0|pdm|public ?domain|^by$|^by-sa$|cc[- ]by(-sa)?|creativecommons\.org/(licenses/by(-sa)?|publicdomain))", re.I)


def get_json(url):
    r = subprocess.run(["curl", "-sS", "--max-time", "30", "-A", UA, url], capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except Exception:
        print(f"  ! {urllib.parse.urlparse(url).netloc}: no JSON ({r.stdout[:80].strip() or r.stderr.strip()})", file=sys.stderr)
        return None


def openverse(q, n):
    d = get_json("https://api.openverse.org/v1/images/?" + urllib.parse.urlencode(
        {"q": q, "page_size": min(n * 3, 50), "license_type": "commercial", "size": "large"}))
    for r in (d or {}).get("results", []):
        yield {"source": "openverse", "kind": "photo", "title": r.get("title", ""), "url": r.get("url"),
               "page": r.get("foreign_landing_url"), "author": r.get("creator", ""),
               "license": f"CC {r.get('license', '').upper()} {r.get('license_version', '')}".strip(),
               "w": r.get("width") or 0, "h": r.get("height") or 0, "id": r.get("id")}


def commons(q, n, kind):
    ft = {"photo": "filetype:bitmap", "video": "filetype:video", "any": ""}[kind]
    d = get_json("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "format": "json", "generator": "search", "gsrsearch": f"{q} {ft}".strip(),
        "gsrnamespace": 6, "gsrlimit": min(n * 3, 40), "prop": "imageinfo",
        "iiprop": "url|size|extmetadata|mime", "iiextmetadatafilter": "LicenseShortName|Artist"}))
    for p in ((d or {}).get("query", {}).get("pages", {}) or {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        md = ii.get("extmetadata", {})
        yield {"source": "wikimedia", "kind": "video" if ii.get("mime", "").startswith("video") else "photo",
               "title": p.get("title", "").replace("File:", ""), "url": ii.get("url"), "page": ii.get("descriptionurl"),
               "author": re.sub("<[^>]+>", "", md.get("Artist", {}).get("value", ""))[:80],
               "license": md.get("LicenseShortName", {}).get("value", ""), "w": ii.get("width") or 0,
               "h": ii.get("height") or 0, "id": p.get("pageid")}


def archive(q, n):
    d = get_json("https://archive.org/advancedsearch.php?" + urllib.parse.urlencode({
        "q": f"({q}) AND mediatype:movies AND (licenseurl:*creativecommons* OR licenseurl:*publicdomain*)",
        "fl[]": ["identifier", "title", "licenseurl", "creator"], "rows": min(n * 2, 20), "output": "json"}, doseq=True))
    for doc in (d or {}).get("response", {}).get("docs", [])[:n]:
        ident = doc["identifier"]
        meta = get_json(f"https://archive.org/metadata/{ident}") or {}
        files = [f for f in meta.get("files", []) if f.get("name", "").lower().endswith((".mp4", ".mov", ".webm"))]
        if not files:
            continue
        f = max(files, key=lambda f: int(f.get("size", 0) or 0) if int(f.get("size", 0) or 0) < 400e6 else 0)
        yield {"source": "archive", "kind": "video", "title": doc.get("title", ""), "page": f"https://archive.org/details/{ident}",
               "url": f"https://archive.org/download/{ident}/{urllib.parse.quote(f['name'])}",
               "author": doc.get("creator", "") if isinstance(doc.get("creator"), str) else "",
               "license": doc.get("licenseurl", ""), "w": int(f.get("width", 0) or 0), "h": int(f.get("height", 0) or 0), "id": ident}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query"); ap.add_argument("--kind", default="any", choices=["photo", "video", "any"])
    ap.add_argument("--orient", default="any", choices=["portrait", "landscape", "any"])
    ap.add_argument("--min", type=int, default=1080); ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    found = []
    if a.kind in ("photo", "any"):
        found += list(openverse(a.query, a.n))
    found += list(commons(a.query, a.n, a.kind))
    if a.kind in ("video", "any"):
        found += list(archive(a.query, max(a.n // 2, 3)))
    keep = []
    for c in found:
        lic = c.get("license", "") or ""
        if not c.get("url") or not OK_LIC.search(lic) or re.search(r"(^|[-/ ])(nc|nd)([-/ ]|$)", lic, re.I):
            continue  # NC = no commercial use, ND = no edits/crops: never usable in our videos
        w, h = c["w"], c["h"]
        if w and h:
            if min(w, h) < a.min:
                continue
            if a.orient == "portrait" and w > h * 1.05 and c["kind"] == "photo" and w / h > 1.8:
                continue  # very wide photos crop badly to 9:16
            if a.orient == "landscape" and h > w:
                continue
        c["score"] = (2 if c["kind"] == "video" else 1) + min(w * h / 8e6, 2) if w and h else 1
        keep.append(c)
    keep.sort(key=lambda c: -c["score"])
    keep = keep[: a.n]
    for i, c in enumerate(keep, 1):
        print(f"{i:2d}. [{c['source']}/{c['kind']}] {c['title'][:60]}  {c['w']}x{c['h']}  {c['license']}\n    {c['url']}")
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        json.dump({"query": a.query, "results": keep}, open(a.out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    if not keep:
        print("no usable results (try simpler nouns: 'runner', 'water bottle', 'pasta')", file=sys.stderr)


if __name__ == "__main__":
    main()

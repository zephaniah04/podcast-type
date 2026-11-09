# Engine status (scripts/podcast.py v4) — engine engineer

Status 2026-11-07: **(1) captions v4, (2) layouts frame / frame2, (3) full-person guard: WORKING** (draft renders
checked frame by frame on C:). Also working: full-screen B-roll label/index, video panels, sticker `dur`/`fade`/`w`,
camera push / pull / punch / pan / drift (first pass, see limits). Full key reference: `.claude/skills/podcast-edit/references/spec.md`, section "v4".

Run exactly like v3 (`PODCAST_HWDEC=cuda`, `--work` on C:). Every chunk rendered into the same `--work` shares
`<work>/_cache/` (head detections, panel masks): keep one --work base for all chunks.

## Top-level keys
`"captions": "v4"` · `cap_size` (design px of the guest base word, default 66 = style guide; all caption sizes scale
with it) · `cap_y` (bottom of the line, default 1004/1080) · `cap_y_frame` (1010/1080) · `cap_y_broll` · `cap_key`
(`mix` default | `serif` | `none`) · `cap_host` ("L" = Nizam gets the INK box) · `host_box` (true) · `keywords` ·
`fixes` · `drop_fillers` · `bg` (default plate for frame layouts: `paper` | `grid` | `blur` | a png path) ·
`gfx_dir` (where bg_paper.png / bg_grid.png live; default finds `projects/carrie-ep01/v4/gfx/`) · `guard` (true) ·
`zmax` (2.3) · `people` / `avoid` (body model overrides, defaults = this room).

## Example segments
```json
{"clip": "IMG_4342-001", "start": 87.5, "end": 97.6, "cx": "left", "zoom": 1.8}
{"clip": "IMG_4342-001", "start": 97.6, "end": 110.7, "layout": "frame", "who": "L", "bg": "paper",
 "panel": {"file": "projects/carrie-ep01/broll/guacamole-toast.jpg", "push": 0.05, "label": "Eggs + guac", "index": "07 — FIG."}}
{"clip": "IMG_4342-001", "start": 121.2, "end": 128.0, "layout": "frame", "who": "L", "bg": "grid",
 "panel": {"file": "projects/carrie-ep01/broll_video/x.mp4", "at": 5, "push": 0.03, "label": "Granola", "index": "08"}}
{"clip": "IMG_4342-001", "start": 110.7, "end": 121.2, "layout": "frame2", "bg": "grid"}
{"clip": "IMG_4342-001", "start": 128.0, "end": 134.0, "broll": {"file": "projects/carrie-ep01/broll/plain-yogurt.jpg", "push": 0.05, "label": "Greek yogurt", "index": "09"}}
{"clip": "IMG_4343-002", "start": 302.0, "end": 310.0, "cx": "left", "zoom": 1.8,
 "cam": {"move": "push", "from": 1.0, "to": 1.08}, "punch": [{"at": 4.0, "to": 1.12, "dur": 0.25}]}
```
stickers: `{"at": 12.0, "file": "projects/carrie-ep01/v4/gfx/x.mov", "x": 0.5, "y": 0.5, "w": 1.0, "dur": 2.0, "fade": 0.2}`
(`w` scales the overlay to that fraction of 1920 only when the file is > 4 px off; overlays work over every layout).

## Rules you can rely on
- Captions: style guide s3 (one line, 2-5 words / 30 chars, blur-to-sharp build, connective words small PAPER, one
  keyword: numbers/data HIGHLIGHT (host: ACCENT), contrast words serif italic; Nizam's chunks on an INK box).
  Position by layout: single talker / full-screen B-roll x 960 y 1004 max 1500; wide two-shot (zoom 1.0) under the
  speaker (x 600 / 1320, max 880); frame layouts y 1010 max 1700. Long chunks shrink to one line. No um/uh, no dashes.
- frame: talker panel = `who` (default: who talks most), sits on `side` (default Nizam left, Carrie right).
  Panels slide 60 px + fade in (8 f, 2nd panel +3 f) unless the previous segment is the same layout + side + panel
  file, or `"enter": false`. Tightened pieces of one segment continue the panel video and push (no restart).
- Guard log per chunk: `<work>/<id>/guard.log` (every zoom/cx/cy change it made).

## Known limits
- Carrie's panel/close shot can show her desk monitor (spreadsheet) when she types: the guard avoids the monitor only
  when the person rules still hold (always on Nizam's side when he sits back, not when he leans in).
- When Nizam leans toward the monitor, a 1.8 zoom single on him keeps Carrie out by putting him right of centre.
- Panel exit is a cut (no 5 f exit animation).
- Camera moves use zoompan on a 2x supersampled crop (sub-pixel smooth) and cost ~2x a static segment to cut.

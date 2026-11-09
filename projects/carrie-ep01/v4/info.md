# v4 explainer graphics ("FUEL LAB" info cards)

Re-render everything (from repo root `I:\podcast-type`):

```
/c/Users/raika/AppData/Local/Programs/Python/Python313/python.exe projects/carrie-ep01/v4/info_src/build.py --jobs 3
```

Options: `--batch 1,2` (one or more batches), `--only i_vitd_max,r_sweat`, `--check` (validate anchors + keep ranges, no render),
`--no-render` (write the HTML only), `--jobs N` (parallel HyperFrames renders; 3 is safe, 4 sometimes fails to start a renderer).

- Source: `v4/info_src/graphics.py` (one entry per graphic: anchor, mode, kind, data), `engine.js` (one GSAP renderer per kind,
  HyperFrames seek-safe paused timeline), `engine.css` (fonts/tokens), `grain.png`, `build.py` (anchors via
  `build_long2.find`, keep-range check against `edit_plan.json`, HTML project + HyperFrames render, ffmpeg encode, QA frames,
  contact sheets, `info.json` merge).
- Work dir (HTML project, raw renders, QA frames, contact sheets): `C:\Users\raika\AppData\Local\Temp\v4\info_test\`.
- Output: `v4/info/<id>.mp4` (H.264, yuv420p, 30 fps, no audio; full = 1920x1080, panel = 840x780) and `v4/info.json`
  (sorted by file, t). `t` = start of the first anchor word in the raw file; every anchor sits inside a `chapters[].keep` range.
- Each graphic: opaque background, fast in (header rule draws, elements stagger in) / calm hold with a slow 3.5 % push /
  fast out over the last 0.36 s back to the bare background. Full-screen cards keep the bottom 230 px empty for captions.
- `research: true` entries are the "THE SCIENCE" cards; each names its source on the card. Numbers on the other cards are
  Carrie's (or Nizam's own); bars marked "relative" / "not measured" are qualitative.

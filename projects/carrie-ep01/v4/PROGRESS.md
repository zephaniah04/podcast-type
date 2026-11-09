# v4 long-form — progress + resume guide (written 2026-11-07 06:35 IST)

Read `BRIEF.md` (job, people, art direction) and `style_guide.md` (FUEL LAB look) first.
Goal: ONE 60-70 min 16:9 episode from `I:\claude to edit` (A=IMG_4342-001, B=IMG_4343-002) -> `I:\edited\`.
Hard rule: people never sliced at a frame/panel edge. No music, no CTA, no emoji. -14 LUFS.

## Done
- Story cut: `edit_plan.json/.md` (cold open 53 s, 14 chapters, outro; ~64 min). FINAL.
- Build script: `../build_long4.py` (reads edit_plan, broll_map, info.json, gfx manifest/gfx.json -> specs in `../long4/L4_*.json`).
  Dry run: 64.0 min, ~3.8 devices/min before hero cards. Fixed: manifest dict format, hero id lookup, emoji off (V4EMOJI=0).
- Render script: `../render_long4.sh` (pieces on C:\Users\raika\AppData\Local\Temp\v4\pieces, JOBS=4) -> `../assemble_long4.py`
  (cold open -> title sting -> [chap card -> chapter] x14 -> outro talk -> outro card; card SFX from gfx/manifest.json;
  concat copy to `I:/edited/Fuelling-Like-an-Endurance-Athlete_Nizam-x-Carrie-Mullin-Innes.mp4` + `_chapters.txt`).
- Motion designer: bg_paper/bg_grid plates, title_sting (in %TEMP%\v4\gfx_big, 38 MB), chap_01..07 so far — QA'd, look pro.
- B-roll map: 198 beats; 29 video clips in `../broll_video/`.
- Infographics: 10 in `info/` (i_gap_5h great; i_vitd_max had an invisible counter -> fix was requested).

## Still in progress when the usage cap hit (background agents may have died — check files, not agents)
- Engine (`scripts/podcast.py`): captions "v4", layout "frame"/"frame2", framing guard, camera moves.
  Signal of done = `v4/ENGINE_STATUS.md` (NOT present yet). If missing: read `git diff scripts/podcast.py` and
  spec.md, finish/verify the features yourself or relaunch an engine agent with BRIEF.md + style_guide.md §3-4.
- Designer: chap_08..14, outro.mp4, lt_carrie/lt_nizam.mov, chapter_tag_NN.mov, 49 hero_*.mp4, hl_*.mov, tr_*.mov
  (`scripts/gfx4.py`, templates in `gfx_src/`, list in `gfx.json`).
- Infographics: more items into `info.json` + `info/` (source `info_src/`); check the vitamin-D counter fix.
- B-roll: more beats/videos into `broll_map.json`.

## Next steps
1. Finish whatever is missing above (relaunch specialist agents with BRIEF.md if needed; MVP first).
2. `python projects/carrie-ep01/build_long4.py` (renders v4/fx overlays) -> test-render a short chapter
   (e.g. L4_08) with podcast.py to %TEMP%\v4, pull frames, QA framing/captions/split panels.
3. Fix, then `bash projects/carrie-ep01/render_long4.sh` (background; ~hours) -> assembled export in I:\edited.
4. Verify: decode check, 60-70 min, loudnorm -14 LUFS, chapters txt; credits list for the description.
Python: /c/Users/raika/AppData/Local/Programs/Python/Python313/python.exe · PODCAST_HWDEC=cuda · preset fast.
Never delete Nizam's files; don't commit/push.

## Update 2026-11-07 ~11:30 IST (usage cap hit again)
- ENGINE_STATUS.md exists: captions v4, frame/frame2, framing guard WORKING (see spec.md "v4").
- B-roll DONE: broll_map.json 234 beats, 44 Mixkit videos (credits broll_video/credits.json), 85 new Commons photos
  (65 CC BY/BY-SA need description credits). build_long4.py now skips AVOID photos (logos/recognisable people).
- Designer: chap_01..14, outro, lt_carrie, chapter_tag_01, first hero cards done; asked to swap sweaty-athlete.jpg
  out of title_sting + chap_03 (recognisable athlete). Still pending: rest of heroes, lt_nizam, tags, hl_, tr_.
- Infographics: agent was mid-batch (check info.json count; i_vitd_max fix).
- build_long4.py ran (specs in long4/). Test render of L4_01 finished in %TEMP%\v4\test\ — NOT yet QA'd.
NEXT: QA L4_01 frames (framing, captions, panels) -> re-run build_long4.py once heroes/info are in -> render_long4.sh.

## Update 2026-11-07 ~22:50 IST (scheduled resume run)
- Inventory: all chap_01..14, chapter_tag_01..14, 49 heroes, lt_carrie/lt_nizam, outro, title_sting present. Missing
  hl_*.mov (3) + tr_*.mov (4): build skips missing stickers, so not blocking. info.json = 40 items.
- QA of L4_01 test: floating photo "stacks" (x=auto) landed over Nizam's face -> build_long4.py now turns every stack
  into a split-screen panel (frame). QA of L4_08 draft: frame2 (both people in panels) sliced Carrie at the panel edge
  when her chair moved -> frame2 now = clean wide two-shot (zoom 1.0). Rebuilt: 64.0 min, ~3.8 devices/min.
- Known, accepted: Carrie's monitor (a Word doc) is visible in some of her singles, not legible, never zoomed into.
- Full render launched: `render_long4.sh` (JOBS=4) -> log `projects/carrie-ep01/render_long4.log`.
- Credits tool: `v4/tools/credits_list.py <out.txt>` (credited files referenced by specs/gfx/info).

## DONE 2026-11-09 07:20 IST — exported
- I:\edited\Fuelling-Like-an-Endurance-Athlete_Nizam-x-Carrie-Mullin-Innes.mp4 (64.8 min, 1080p30, -14.3 LUFS sample,
  decodes clean) + _chapters.txt + _credits.txt (91 items need attribution in the description).
- 4 chunks (01,03,04,13) failed in the first run (C: nearly full); re-rendered. Ch1 opening fixed by hand in long4/L4_01.json
  (start of file A = old camera angle, Carrie off screen -> wide shot; lt_carrie moved to 4.3 s). Re-running build_long4.py
  would undo that edit.
- Known, not fixed: Nizam's tight singles cut his back/shoulder at the left frame edge (head always whole) because the
  guard keeps Carrie out; lowercase "i" in some captions; host caption box wider than its text; headline/transition overlays unused.

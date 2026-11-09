# FUEL LAB — v4 style guide (Carrie ep01, 16:9 long-form)

Editorial brutalism + kinetic type. Big type, hard edges, grid, index numbers, registration marks, film grain.
Fast in (6-10 f) · calm hold with a slow push (2-4 %) · faster out (4-6 f). All px at 1920x1080, 30 fps.
Reference measurements: `references/studies/ig4-6_notes.md`. Renderer: `scripts/gfx4.py` (HTML/GSAP templates in
`v4/gfx_src/`, rendered by HyperFrames). Files + placement: `v4/gfx/manifest.json`.

## 1. Tokens
| token | hex | use |
|---|---|---|
| INK | `#0D0D0D` | punch-card bg, slabs on video, body type on paper |
| PAPER | `#EFEBE3` | paper plate, name slabs, light type (PAPER-2 `#E2DDD2` = shade / ghost card) |
| ACCENT | `#FF5A1F` | one word per frame on INK/PAPER, chips, rules, strike bars |
| HIGHLIGHT | `#FFD84D` | numbers, caption keyword on video, accent word on GREEN |
| TRACK GREEN | `#1F6B45` (+ deep `#154D31` vignette) | grid plate, number cards |
| GRID LINE | `#2E8A5C` (rendered `rgba(58,160,106,.55)` 2 px) | 60 px grid on green |
| WHITE | `#FFFFFF` | type on green/ink |
Max 2 accent colours per frame (ACCENT+HIGHLIGHT). On GREEN the accent word is HIGHLIGHT (orange-on-green fails contrast).
Grid: 96 px outer margins, 12 cols x 144 px; background grid 60 px cells (32 x 18, lines at x,y = 0,60,120…).
Grain: luma noise added at encode (`noise=c0s=6-7:c0f=t+u`), static on the PNG plates.

## 2. Type scale (fonts in `assets/fonts/`)
| role | font file / libass name | size px | case / tracking | leading |
|---|---|---|---|---|
| D1 display (chapter title, sting) | ArchivoBlack-Regular / `Archivo Black` | 150-210 (auto-fit) | CAPS, -2 % | 0.88-0.90 |
| D2 hero punch | Archivo Black | 120-170 | CAPS, -2 % | 0.90 |
| H1 headline slab | Archivo Black | 104 (64 min) | CAPS, -2 % | 0.98 |
| Outline numerals | Archivo Black, 3 px stroke, no fill | 900-1020 | -5 % | 0.78 |
| H2 kicker / contrast word | InstrumentSerif-Italic / `Instrument Serif Italic` | 52-72 (quotes 104) | sentence case, -1 % | 1.04 |
| Names, UI heavy | InterTight-Heavy / `Inter Tight Heavy` | 50-66 | as written | 1.0 |
| Body / roles | InterTight-Medium / `Inter Tight Medium` | 28-36 | sentence case | 1.15 |
| H3 meta / index / timecode | SpaceMono-Bold / `Space Mono` + `\b1` (Regular for secondary) | 16-24 | CAPS, +12-14 % | 1.0 |
Glyph note: Inter Tight and Instrument Serif have NO `→ ≠`; Archivo Black and Space Mono do. In captions write "to"/"not".

## 3. Captions — SUPERSEDED 2026-11-09 by Nizam's review

> **Current rules: `.claude/skills/podcast-edit/references/fuel-lab-longform.md` section 4** — one font, one size, one
> baseline, no host box, no blur, light outline, keyword = colour only and rare. The text below is the original v4
> design, kept for history only. Section 5/7 motion: graphics no longer push/zoom/drift/shake while holding.
 (engine, libass, PlayRes 1920x1080) — the most-seen element
Model: word-by-word BUILD inside a chunk, size contrast (small connective words, one keyword), no boxes for the
guest, a box for the host (ig4 rule: interviewer and guest look different).

**Chunking** 2-5 words, <= 30 chars, ONE line. Break at punctuation or a pause > 0.35 s. Max one keyword per chunk.
Event start = first word start; event end = min(next chunk start, last word end + 0.6 s); if the gap to the next chunk
< 0.25 s, extend to it (no flicker). Hard cut between chunks (no fade-out).

**Styles** (ASS colours are &HAABBGGRR; alpha 00 = opaque)
```
Style: CapGuest,Inter Tight Heavy,66,&H00FFFFFF,&H00FFFFFF,&H590D0D0D,&H800D0D0D,0,0,0,0,100,100,-1,0,1,3,0,2,0,0,0,1
Style: CapHost, Inter Tight Heavy,62,&H00FFFFFF,&H00FFFFFF,&H1A0D0D0D,&H1A0D0D0D,0,0,0,0,100,100,-1,0,3,14,0,2,0,0,0,1
```
- Guest (Carrie): white 66 px, soft dark halo = Outline 3 in INK at 65 % + `\blur3` on the event. No box.
- Host (Nizam): same type 62 px on an INK 90 % box (BorderStyle 3, Outline 14 = padding). The box may show at
  full chunk width from the first word; that is fine (ig4 does the same).
- Connective words (a an the of to in on for and or but is it I you my we that this with at be so): `{\fnInter Tight Medium\fs52}` colour PAPER `&H00E3EBEF&`.
- Keyword, data type (numbers, units, foods, body parts, products): `{\fs88\c&H004DD8FF&}` = HIGHLIGHT (host: ACCENT `&H001F5AFF&`).
- Keyword, contrast type (why, actually, problem, never, real, enough, emotions): `{\fnInstrument Serif Italic\fs100}` white, no colour.
- Numbers are always keywords. Story editor's `accent_word` wins when present.

**Word build** (t = word start relative to event start, ms). All words of the chunk are laid out from frame 0
(invisible) so nothing reflows:
```
normal : {\alpha&HFF&\blur6\t(t,t+100,\alpha&H00&\blur3)}word
keyword: {\alpha&HFF&\blur14\t(t,t+200,\alpha&H00&\blur3)}KEYWORD
```
(6-frame blur-to-sharp for the keyword, 3 frames for the rest; said words stay lit until the chunk ends.)

**Position** (`\an2\pos(x,y)` = bottom centre of the line)
| layout | x | y | max width |
|---|---|---|---|
| single talker full frame / full-screen B-roll | 960 | 1004 | 1500 |
| wide two-shot | 600 under Nizam / 1320 under Carrie | 1004 | 880 |
| split screen (panels 80-860) | 960 | 1010 (zone 860-1080) | 1700 |
| over a hero/chapter card | no captions (cards are full-screen statements) | | |
Shrink `\fs` proportionally if a chunk exceeds max width. Never over the face; never above y 900 on talking shots.

## 4. Split-screen frame (agreed geometry)
Canvas 1920x1080 on `gfx/bg_paper.png` or `gfx/bg_grid.png` (grain, 60 px grid, corner registration marks at
(48,48)…(1872,1032), edge ticks every 60 px, two 15 px mono labels in the top margin at y 34).
Panels 840x780 at (80,80) and (1000,80), radius 24, no stroke; drop shadow `0 20 50 rgba(0,0,0,.28)` on paper only.
Panel index label: Space Mono Bold 20 px, +12 % tracking, 24 px inside the panel's top-left, on a chip
(PAPER on GREEN plate / INK-on-PAPER chip), text like `02 — FIG.`. Caption pill on the graphic panel: Inter Tight
Heavy 30 px caps, INK on HIGHLIGHT, padding 10/18, radius 999, 24 px from the panel's bottom-left.
Panels enter: slide 60 px + fade, 8 f expo-out, second panel 3 f later; exit 5 f power3-in. Caption band 860-1080 free.

## 5. Packaging pieces (all in `v4/gfx/`, see manifest for place + SFX)
| piece | file | dur | look | motion |
|---|---|---|---|---|
| Title sting | `title_sting.mp4` | 4.5 s | INK + faint grid, giant outlined "01" (ACCENT 30 %), 3 polaroids at z -240, title 3 lines one big word per line ("FUELLING *like an* / ENDURANCE / ATHLETE", small words in serif italic ACCENT), ACCENT rule, names Inter Tight Heavy 50, role mono 21 | ACCENT scan line 0.0, slams at 0.28 / 0.72 / 1.06 (scale 1.55→1 + blur 26→0, or mask-rise + tracking collapse), photos drop with each slam, 3D camera push (rotY -9°→+1.6°, z -220→+80), exit 4.0-4.45 push-through (scale 1.35 + blur), ends on clean INK |
| Chapter card | `chap_NN.mp4` | 3.0 s | alternating GREEN (odd) / PAPER (even) grid; H3 meta row "CHAPTER 04 / 14" + rule + topic chip + TC; outlined index numeral 960 px at z -460; polaroid + ghost card at z -170; H1 title auto-fit <= 196 px, max 3 lines, left at x 96, accent word ACCENT/HIGHLIGHT; ACCENT bar + H2 kicker serif 66; footer mono + 14-segment progress ticks | camera rotY -7°→-0.4°, rotX 4°→0.5°, z -150→+60; rule draws 0.02; numeral slides+deblurs 0.03; title lines mask-rise 0.10 (+2 f stagger); photo drops 0.27 (back-out); kicker blur-in 0.34; exit from 2.77, clean by 2.97 (hard cut out is clean) |
| Chapter tag | `chapter_tag_NN.mov` (alpha) | 4.0 s | top-left at (96,64): ACCENT 62x54 chip "04" + INK 88 % bar, dash + title Inter Tight Heavy 25 caps +5 % | chip spins in, bar wipes, title types (<= 0.55 s), out at 3.58 (untype, collapse, chip out) |
| Lower third | `lt_carrie.mov`, `lt_nizam.mov` (alpha) | 4.5 s | bottom-left, bottom edge y 832: chips "GUEST·01"/"HOST·02", PAPER slab with ACCENT edge + name Archivo Black 62, INK strip role Inter Tight Medium 29, tiny reg mark | chips pop, slab wipes L→R, name rises, role words blur in (45 ms stagger), drift 6 px, out 4.0 (R→L wipes) |
| Hero card | `hero_<id>.mp4` | punch 2.6 / number 2.8 / quote 3.0 / myth 3.0 | punch: INK, white Archivo caps, accent word ACCENT + giant outline echo; number: GREEN, numerals HIGHLIGHT rolling odometer + vertical motion blur, words white smaller, units Inter Tight Heavy; quote: PAPER, ACCENT serif quote mark 620 px, Archivo caps INK, attribution mono; myth: INK, chip MYTH CHECK struck → FACT (HIGHLIGHT), statement caps | words blur/scale in 2-3 f apart, slow push 4.5 %, exit last 5 f (scale 1.1 + blur 12 → black) |
| Headline (H1/H2/H3) | `hl_<id>.mov` (alpha) | 3.5 s | H3 ACCENT mono chip / H1 PAPER (or INK / ACCENT) slab Archivo 104 / H2 serif 52 on INK 78 % slab; pos tl (96,96), left, center, bl | chip wipe, slabs wipe (2 f stagger), text mask-rise, H2 blur-in, out last 0.45 s |
| Transition | `tr_ink/bars/green/blocks.mov` (alpha, full frame) | 0.5 s | INK panel + ACCENT edges / 6 ACCENT-INK bars / GREEN grid panel with HIGHLIGHT edges / 8 INK-ACCENT columns | fully covers 0.20-0.30 s → put the cut at 0.25 s |
| Outro | `outro.mp4` | 6.0 s | PAPER, "Thanks for" serif 150 + "WATCHING." Archivo 196, rule, HOST / GUEST columns, episode title mono, polaroid | calm: fades from INK 0.5 s, slow rises, slow camera drift, fade to INK last 0.9 s. No CTA, no logo |

## 6. Transitions + SFX map (assets/sfx, gains relative to the file; voice is -14 LUFS, SFX sit ~10-14 dB under)
| moment | sfx | gain |
|---|---|---|
| title slams | whoosh_slow @0, transition_short @0.28, click @0.72/1.06, pop @1.8 | -8…-14 dB |
| chapter card in | whoosh_fast @0, click @0.12, pop @0.3 (photo) | -9…-14 |
| chapter tag / headline / LT | click or whoosh_soft(2) @0-0.2 | -12…-16 |
| hero punch / quote | whoosh_soft @0.08 + click @0.1 / whoosh_soft2 @0 | -11…-13 |
| hero number land | whoosh_fast @0.1, ding @0.95 | -10/-12 |
| myth strike / fact | click @0.95, pop @1.25 | -10/-12 |
| transition stinger | whoosh_fast @0 (peak at the cover) | -8 |
| B-roll hard cut on a noun | none or click -18 (sparingly: max 1 SFX per 3 s) | |
Cut rules: B-roll / card every 2-3 s in explainer stretches; talking-head holds max 8-10 s undressed; hard cuts on
word onsets; use a stinger max once per 2-3 min (chapter boundaries, topic jumps), never two in a row.

## 7. Motion curves
Entrances expo.out 0.3-0.55 s (back.out(1.3) for photos/chips) · stagger 2-3 f · exits power3.in 0.12-0.25 s ·
camera sine.inOut over the hold · blur-to-sharp 14-26 px → 0 · counters power3.out 0.85 s with vertical blur 26 px → 0 ·
holds always carry a 2-4 % push or drift; nothing is static except the PNG plates.

## 8. Do / don't
Do: one idea per card; numbers in HIGHLIGHT; one accent word; left-aligned editorial titles on chapters, centred on
punches; mono for anything that is a label/index/timecode; keep 96 px margins and the caption band empty on overlays.
Don't: gradients on type, bevels, glows, emoji, drop-shadowed white text on paper, more than 2 accent colours,
captions on top of cards, overlays over a face, logos/CTAs, rounded "pill" captions for the guest.

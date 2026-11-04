---
name: podcast-edit
description: Edit raw podcast footage into finished videos - vertical clips (Reels / Shorts / TikTok) in three measured house looks (letterbox lockup, creator hyper-edit, clean minimal) and full 16:9 YouTube episodes with a cold open, jump-cut tightening and chapters. Claude picks the moments from Whisper transcripts, cuts on word boundaries, writes the JSON spec and renders with scripts/podcast.py. Use when Nizam drops raw podcast clips, asks for podcast reels/shorts, a long-form episode edit, a cold open, captions on podcast footage, or says "/podcast-edit".
---

# /podcast-edit — raw podcast footage -> finished clips and episodes

Built from a measured study of 5 references (3 Instagram podcast reels + 2 long-form YouTube episodes),
see `references/reference-study.md`. Learn their grammar; never reuse their footage, music, logos or show names.

**Engine:** `scripts/podcast.py` (ffmpeg + libass, deterministic, no browser). **Transcripts:** `scripts/transcribe.py`
(faster-whisper word timings). **Spec format:** `references/spec.md`. **Long-form structure:** `references/longform.md`.
**Which device when (zoom, split, B&W, stamps... decided by what is said):** `references/edit-decisions.md` — read it before writing any spec.
**Starter specs:** `examples/`.

Heavier motion graphics (text behind the head, 3D phone mockups, glossy buttons with real depth, animated charts)
go through **HyperFrames** (`/hyperframes`, `hyperframes-registry`, `media-use` for cutouts) layered on top of an
engine render — only when the beat earns it.

## 0. Before the first edit of a new show (once)

Ask for anything missing from this list, in one message, then save answers to `brand-kit/<show>/BRAND.md`:
1. Show name, host + guest names and how to write their handles/roles (lower thirds).
2. Camera setup: how many cameras, which file is which (wide / host / guest), are they already synced?
   Separate mic tracks per speaker? (decides multicam switching, see section 3)
3. Language (English / Hinglish / Hindi) and words Whisper will get wrong (names, brands, jargon).
4. Look: pick a default clip look (A / B / C below) + accent colour + logo PNG (transparent) + CTA text
   ("Comment LINK", "Full episode on YouTube", "Follow for part 2").
5. Music: **Nizam adds music himself in his editing app.** Render voice + SFX only (no `music` key) unless he asks.
6. Targets: clips per episode, clip length (default 30-60 s), long-form yes/no.

## 1. Ingest

```bash
mkdir -p projects/<ep>/raw projects/<ep>/tx          # raw/ is git-ignored
# raw clips usually come as a Google Drive link: pull them with the Google Drive connector
# (search/download the files) into projects/<ep>/raw/. If a file is too big for the connector,
# ask Nizam to share it as "anyone with the link" and download it directly.
python3 scripts/transcribe.py projects/<ep>/raw/* --out projects/<ep>/tx --model small --prompt "<names, jargon>"
```
- Use `--model medium` for Hinglish or noisy rooms (slower, much better). `--lang hi` only for mostly-Hindi speech.
- Check sync if multicam: the same sentence should have the same timestamp in every camera's `.txt`.
  If not, measure the offset (first shared sentence) and use `start2` / per-clip offsets in the spec.
- `ffprobe` every file: resolution, fps, rotation, audio channels (two channels can mean two lav mics).

## 2. Find the moments (this is the editor's job — do it properly)

Read every `tx/<clip>.txt` in full. Score candidate moments; a clip must have ALL of:
- **Hook in the first 1.5 s**: a bold claim, a number, a contrarian line, or a question the viewer wants answered.
  Start mid-thought if needed ("A friend is not someone who tells you what you want to hear").
- **One idea, closed loop**: setup -> turn -> payoff. Cut the clip on the payoff line, not after it.
- **Stands alone**: no "as I said earlier", no unexplained "he/that".
Good sources: Q -> A pairs (host question + guest's sharpest answer), lists ("three things..."), stories with a
twist, numbers/proof, disagreements. Write a shortlist (time range, hook line, why it works, suggested look)
in `projects/<ep>/moments.md` and show it to Nizam before rendering if more than 3 clips.

**Tightening rules (all formats):**
- Cut on word boundaries from the transcript, pad 0.1 s. Remove dead air > 0.35 s (clips) / > 0.6 s (long-form),
  "um/uh", false starts, repeated phrases, "you know"/"like" chains.
- You may re-order lines inside a clip if the meaning holds (question after the answer is a classic hook).
- Never cut a word in half; never change what someone meant.

## 3. Pick shots (multicam logic) — full rules in references/edit-decisions.md

- Speaker on camera: show whoever is talking. Cut to the listener for reactions (laugh, nod, shock) <= 1.5 s.
- With separate mic tracks: the louder track is the speaker; switch only after >= 1.2 s of the new speaker.
- One wide camera only: fake two cameras with alternating `zoom` 1.0 / 1.2-1.3 every 3-6 s (cuts on sentence ends)
  and `cx` to follow the speaker (`"auto"` = largest face, `"left"`/`"right"` in a two-shot).
- Wide two-shot = the "breath" shot: use it on topic changes and as cutaway, max once per ~15 s.

## 4. The three clip looks (vertical 1080x1920, -14 LUFS, 30 fps)

| | **A. Letterbox lockup** (ref ig3) | **B. Creator hyper-edit** (ref ig2) | **C. Clean minimal** (ref ig1) |
|---|---|---|---|
| Use for | quotes, wisdom, emotional lines | how-to, frameworks, numbers, founder/creator talk | calm deep talk, long answers, YouTube Shorts |
| `layout` | `letterbox` (16:9 band on black; first seg `"open": true`) | mix: `full` punch-ins, `band` (blur-fill), `split` intro | `full` (or `letterbox`) |
| `captions` | `lockup`: tiny grotesk builds word by word; keyword -> HUGE heavy sans + italic serif connectors | `creator`: left stack, bold lines; keyword -> HUGE | `minimal`: small geometric sans, 2-4 words, swap, no animation |
| Cuts | 1-3 per clip, slow; wide two-shot as cutaway | every 0.8-6 s (median 1.7 s, ~22 cuts/min) | host Q -> hard cut -> guest A, ~1 cut / 7 s |
| Extras | headline in the top black (`hook`), logo sting end (`endcard.logo`) | `names` typed on, `counters`, `stamps`, `stacks`, `look: "bw"` for "before" beats | none |
| Keywords | 1 per 4-6 s, the word that carries the meaning | 1 per 3-5 s, numbers and nouns | none |
| End | 1-1.5 s logo sting on black/gradient | "COMMENT 'LINK'" card | hard out / follow card |

Caption rules for every look: never over the face or mouth, max 2 lines, keep spoken wording (fix spelling via
`fixes`), one accent colour at most, no em dashes on screen.

## 5. Write the spec and render

Copy the closest file from `examples/` to `projects/<ep>/clips/<id>.json`, fill segments from the transcript.
```bash
python3 scripts/podcast.py projects/<ep>/clips/C01.json --src projects/<ep>/raw --tx projects/<ep>/tx \
    --out exports/<show>/<ep> --draft --sheet      # review render (fast) + contact sheet
python3 scripts/podcast.py ... (same, without --draft)                 # final
```

## 5b. B-roll

When (see `references/edit-decisions.md`): a named place / person / event / object, the start of a story,
"imagine..." or anything the speaker describes visually. Not on emotional peaks or punchlines (stay on the face).
2-4 s each, max ~1 per 10 s in clips, slow push-in, voice continues underneath.

Sources, in order:
1. **Nizam's Drive `B-roll library`** (Google Drive connector): own footage beats stock.
2. **Pexels MCP** (`pexels_search_videos` / `pexels_search_photos`; needs `PEXELS_API_KEY` in the environment).
   Search with concrete nouns + mood ("runner sunrise track slow motion"), `orientation: portrait` for clips,
   `landscape` for long-form; pick a rendition >= output size (1080 wide / 1920 wide), avoid watermarks/logos/faces
   that look like real public figures.
3. Openverse (keyless photos, check CC license).
Download with `scripts/fetch_broll.py <url> --ep projects/<ep> --name <slug> --source pexels --id <id> --author <name> --page <url>`
(writes `broll/credits.json`), then add `"broll": {"file": ...}` to the segment.

## 6. QA — LOOK before you hand anything over

1. Read the `_sheet.jpg`. Then pull full-size frames at every keyword lockup, overlay and cut
   (`ffmpeg -ss <t> -i out.mp4 -frames:v 1 f.png`) and Read them. Check: face framed (not cut by crop),
   captions off the face, nothing overflows the frame, lockups readable, no caption on a card.
2. Read `work/<id>/captions.txt` against the audio transcript: spelling of names, Hinglish kept as spoken.
3. Loudness: the engine trims to -14 LUFS integrated; confirm with
   `ffmpeg -nostats -i out.mp4 -af ebur128=peak=true -f null - 2>&1 | tail -12` (I ~ -14, true peak < -1).
4. First frame: would it stop a scroll with the sound off? If not, fix the hook (re-order, headline, punch-in).
5. Send Nizam the render + 1-line "why this moment" for each clip. Delivered without music: leave voice at
   -14 LUFS and tell him to sit music around -20 to -24 dB under the voice in his app.

## Long-form episodes (16:9, 1920x1080)

Follow `references/longform.md` (cold-open trailer -> sting -> intro -> chapters). Engine: `"format": "long"`,
`"tighten": 0.6`, `"jump_zoom": [1.0, 1.12]` on single-camera stretches, `"chapter"` on the first segment of each
chapter (writes `_chapters.txt` for the YouTube description). Render 20-30 min sections separately, then concat.

## Don'ts
- Don't render before reading the full transcript. Don't pick a moment for its first line alone.
- Don't cover faces with captions or crop through a head. Don't leave a punch-in on a soft source (> 1.3x on 1080p).
- Don't stack more than 2 overlays at once. No idle wobble, no random emoji, no stock "subscribe" animations.
- Never commit raw footage or renders (git-ignored). Never use reference footage, music or logos.

## Learnings
- 2026-11-04: v1. Engine verified on reference stand-in footage: letterbox band-open, lockups, creator stack,
  split, band blur-fill, B&W look, counters, stamps, stacks, end card, jump-cut tightening, chapters, -14 LUFS.
  `alimiter` auto-levels by default in ffmpeg 6 — always `level=0`. OpenCV 5 has no Haar cascades — pin 4.12.

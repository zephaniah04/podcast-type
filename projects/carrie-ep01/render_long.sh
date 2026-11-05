#!/usr/bin/env bash
# Waits for the shorts batch, then renders long cards + 7 long pieces (2 at a time), then assembles L01-L03.
cd /i/podcast-type
PY=/c/Users/raika/AppData/Local/Programs/Python/Python313/python.exe
export PODCAST_HWDEC=cuda PY
until grep -q ALL-SHORTS-DONE projects/carrie-ep01/render_shorts.log 2>/dev/null; do sleep 30; done
$PY scripts/cards.py projects/carrie-ep01/cards_long.json --out projects/carrie-ep01/cards | tail -1
rl() { k=$1; ls exports/carrie/ep01/long_pieces/L_${k}_*.mp4 >/dev/null 2>&1 && { echo "skip $k"; return; }
  $PY scripts/podcast.py projects/carrie-ep01/long/L_$k.json --src "I:/claude to edit" --tx projects/carrie-ep01/tx \
     --out exports/carrie/ep01/long_pieces --work "$TEMP/podcast-work-long" 2>&1 | tail -2; }
export -f rl
printf "P3\nP1\nP2\nP4\nCO1\nCO2\nCO3\n" | xargs -P 2 -I{} bash -c 'rl {}'
$PY projects/carrie-ep01/assemble_long.py
echo ALL-LONG-DONE

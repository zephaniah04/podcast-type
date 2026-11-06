#!/usr/bin/env bash
# v2 long-form: render cold open + 4 body chunks in parallel, then join into one episode.
cd /i/podcast-type
PY=/c/Users/raika/AppData/Local/Programs/Python/Python313/python.exe
export PODCAST_HWDEC=cuda PODCAST_FINAL_PRESET=${PODCAST_FINAL_PRESET:-fast} PY
rl() { k=$1; ls exports/carrie/ep01/long2_pieces/L2_${k}_*.mp4 >/dev/null 2>&1 && { echo "skip $k"; return; }
  $PY scripts/podcast.py projects/carrie-ep01/long2/L2_$k.json --src "I:/claude to edit" --tx projects/carrie-ep01/tx \
     --out exports/carrie/ep01/long2_pieces --work "$TEMP/podcast-work-l2" 2>&1 | grep -v "^  cut" | tail -3; }
export -f rl
printf "P3\nP1\nP2\nP4\nCO1\n" | xargs -P ${JOBS:-4} -I{} bash -c 'rl {}'
$PY projects/carrie-ep01/assemble_long2.py
echo ALL-LONG2-DONE

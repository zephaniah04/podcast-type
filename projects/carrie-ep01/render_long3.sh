#!/usr/bin/env bash
# v3 long-form: cold open + one chunk per chapter, 4 in parallel (longest first), then join into one episode.
cd /i/podcast-type
PY=/c/Users/raika/AppData/Local/Programs/Python/Python313/python.exe
export PODCAST_HWDEC=cuda PODCAST_FINAL_PRESET=${PODCAST_FINAL_PRESET:-fast} PY
OUTD=exports/carrie/ep01/long3_pieces
rl() { k=$1; ls $OUTD/L3_${k}_*.mp4 >/dev/null 2>&1 && { echo "skip $k"; return; }
  $PY scripts/podcast.py projects/carrie-ep01/long3/L3_$k.json --src "I:/claude to edit" --tx projects/carrie-ep01/tx \
     --out $OUTD --work "$TEMP/podcast-work-l3" 2>&1 | grep -v "^  cut" | tail -2
  ls $OUTD/L3_${k}_*.mp4 >/dev/null 2>&1 && rm -rf "$TEMP/podcast-work-l3/L3_$k"; echo "done $k"; }
export -f rl; export OUTD
printf "14\n11\n13\n04\n05\n12\n01\n15\n06\n07\n17\n16\n08\n03\n09\n02\n10\n00\n" | xargs -P ${JOBS:-4} -I{} bash -c 'rl {}'
$PY projects/carrie-ep01/assemble_long3.py
echo ALL-LONG3-DONE

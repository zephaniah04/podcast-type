#!/bin/bash
# final renders, 2 at a time, skips finished files. Log: projects/calvin-ep01/render.log
cd /i/podcast-type
PY=/c/Users/raika/AppData/Local/Programs/Python/Python313/python.exe
OUT=exports/calvin/ep01; mkdir -p $OUT
one() { id=$(basename "$1" .json); if ls $OUT/${id}_*.mp4 >/dev/null 2>&1; then echo "skip $id"; return; fi
  "$PY" scripts/coach_reel.py "$1" --src "H:/Nizam Blr/calvin" --tx projects/calvin-ep01/tx --out $OUT --work "C:/Users/raika/AppData/Local/Temp/calvin-work" > /tmp/r_$id.log 2>&1 \
   && echo "done $id $(date +%T)" || { echo "FAIL $id"; tail -5 /tmp/r_$id.log; }; }
export -f one; export PY OUT
ls projects/calvin-ep01/clips/*.json | xargs -P 2 -I{} bash -c 'one {}'
echo ALL FINISHED $(date +%T)

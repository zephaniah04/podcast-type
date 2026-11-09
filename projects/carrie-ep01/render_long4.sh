#!/usr/bin/env bash
# v4 long-form: every chunk (cold open, chapters, outro) rendered JOBS at a time (longest first) on C:, then joined
# into I:/edited by assemble_long4.py. Re-runs skip finished pieces (delete a piece to re-render it).
cd /i/podcast-type
PY=/c/Users/raika/AppData/Local/Programs/Python/Python313/python.exe
export PODCAST_HWDEC=cuda PODCAST_FINAL_PRESET=${PODCAST_FINAL_PRESET:-fast} PY
T=$(cygpath -m "$TEMP")/v4; OUTD=$T/pieces; WORK=$T/work; mkdir -p "$OUTD" "$WORK"
export OUTD WORK
rl() { k=$1; ls $OUTD/L4_${k}_*.mp4 >/dev/null 2>&1 && { echo "skip $k"; return; }
  s=$(date +%s)
  $PY scripts/podcast.py projects/carrie-ep01/long4/L4_$k.json --src "I:/claude to edit" --tx projects/carrie-ep01/tx \
     --out "$OUTD" --work "$WORK" > "$WORK/L4_$k.log" 2>&1
  if ls $OUTD/L4_${k}_*.mp4 >/dev/null 2>&1; then rm -rf "$WORK/L4_$k"; echo "done $k $(( $(date +%s) - s ))s"; else echo "FAIL $k (see $WORK/L4_$k.log)"; fi; }
export -f rl
# longest chunks first so the parallel slots stay busy
ORDER=$($PY -c "
import json,glob,os
fs=glob.glob('projects/carrie-ep01/long4/L4_*.json')
d=lambda f:sum(s['end']-s['start'] for s in json.load(open(f,encoding='utf-8'))['segments'])
print(' '.join(os.path.basename(f)[3:5] for f in sorted(fs,key=d,reverse=True)))")
echo "order: $ORDER"
printf "%s\n" $ORDER | xargs -P ${JOBS:-4} -I{} bash -c 'rl {}'
echo ALL-PIECES-DONE
[ -z "$NO_ASSEMBLE" ] && $PY projects/carrie-ep01/assemble_long4.py --pieces "$OUTD" && echo ALL-LONG4-DONE

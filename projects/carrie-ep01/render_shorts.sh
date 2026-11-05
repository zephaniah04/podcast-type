#!/usr/bin/env bash
# Final renders of C01-C25, two at a time, skipping ones already in exports/carrie/ep01.
cd /i/podcast-type
PY=/c/Users/raika/AppData/Local/Programs/Python/Python313/python.exe
export PODCAST_HWDEC=cuda
render() {
  id=$1
  ls exports/carrie/ep01/${id}_*.mp4 >/dev/null 2>&1 && { echo "skip $id"; return; }
  $PY scripts/podcast.py projects/carrie-ep01/clips/$id.json --src "I:/claude to edit" --tx projects/carrie-ep01/tx \
      --out exports/carrie/ep01 --sheet --work "$TEMP/podcast-work-final" 2>&1 | tail -1
}
export -f render; export PY
for i in $(seq -w 1 25); do echo C$i; done | xargs -P ${JOBS:-2} -I{} bash -c 'render {}'
echo ALL-SHORTS-DONE

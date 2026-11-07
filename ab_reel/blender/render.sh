#!/bin/bash
# Render every 3D shot (EEVEE on CPU via Mesa) and encode each PNG sequence to mp4.
#   ./render.sh            all shots          ./render.sh num1 ball   just those
cd "$(dirname "$0")"
export LIBGL_ALWAYS_SOFTWARE=1 TAA=${TAA:-16}
for s in ${@:-avg ducks y2007 y2011 y2015 trophy}; do
  t0=$(date +%s)
  python3 shots.py $s > log_$s.txt 2>&1 || { echo "$s FAILED"; tail -5 log_$s.txt; continue; }
  ffmpeg -v error -y -framerate 30 -i renders/$s/%04d.png -vf scale=1080:1920:flags=lanczos -c:v libx264 -crf 14 -pix_fmt yuv420p renders/$s.mp4
  touch renders/$s.done; echo "$s done in $(( $(date +%s) - t0 ))s"
done

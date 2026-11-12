#!/bin/bash
# full-HD renders of every 3D shot, then encode each PNG sequence to a ProRes-quality mp4
cd "$(dirname "$0")"
for s in speed score98 date logo; do
  t0=$(date +%s)
  python3 shots3d.py $s --res 1920x1080 > log_full_$s.txt 2>&1
  ffmpeg -v error -y -framerate 30 -i renders/$s/%04d.png -c:v libx264 -crf 12 -preset slow -pix_fmt yuv420p renders/$s.mp4
  echo "$s done in $(( $(date +%s) - t0 ))s"
done

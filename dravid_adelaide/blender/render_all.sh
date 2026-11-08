#!/bin/bash
# Vertical 3D shots -> 1080x1920 mp4s (rendered at RES, default 720x1280, upscaled)
cd "$(dirname "$0")"
for s in ${@:-s556 s196 s72}; do
  rm -rf renders/$s
  TAA=${TAA:-16} python3 shots.py $s --res ${RES:-720x1280} > log_$s.txt 2>&1
  ffmpeg -v error -y -framerate 30 -i renders/$s/%04d.png -vf scale=1080:1920:flags=lanczos -c:v libx264 -crf 14 -pix_fmt yuv420p renders/$s.mp4
  echo "$s done"
done
echo RENDER3D_DONE

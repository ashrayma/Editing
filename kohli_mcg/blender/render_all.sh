#!/bin/bash
# 3D shots -> PNG sequences -> 1080p mp4s.
# Draft (default): RES=1600x900 TAA=12, upscaled.  Final: RES=1920x1080 TAA=32 ./render_all.sh
cd "$(dirname "$0")"
for s in ${@:-ball score314 eight28 days1020 hero82 logo}; do
  t0=$(date +%s)
  rm -rf renders/$s
  TAA=${TAA:-12} python3 shots3d.py $s --res ${RES:-1600x900} > log_full_$s.txt 2>&1
  ffmpeg -v error -y -framerate 30 -i renders/$s/%04d.png -vf scale=1920:1080:flags=lanczos -c:v libx264 -crf 12 -preset slow -pix_fmt yuv420p renders/$s.mp4
  echo "$s done in $(( $(date +%s) - t0 ))s"
done
echo RENDER3D_DONE

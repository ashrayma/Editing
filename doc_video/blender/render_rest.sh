#!/bin/bash
# finish the speed gauge at full quality, the rest at 1440x810 / 24 samples (upscaled in the edit)
cd "$(dirname "$0")"
n=$(ls renders/speed | wc -l)
python3 shots3d.py speed --frames $((n+1))-105 --res 1920x1080 > log_full_speed.txt 2>&1
for s in score98 date logo; do TAA=24 python3 shots3d.py $s --res 1440x810 > log_full_$s.txt 2>&1; done
for s in speed score98 date logo; do
  ffmpeg -v error -y -framerate 30 -i renders/$s/%04d.png -vf "scale=1920:1080:flags=lanczos" -c:v libx264 -crf 12 -preset slow -pix_fmt yuv420p renders/$s.mp4
done
echo ALLDONE

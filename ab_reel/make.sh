#!/bin/bash
# composition -> HyperFrames render (1080x1920, 30 fps) -> soundtrack -> mux at -14 LUFS
set -e
cd "$(dirname "$0")"
python3 reel.py
python3 soundtrack.py
( cd hf && npx --prefix ../../doc_video hyperframes render -o ../out/video_silent.mp4 -q delivery -w ${WORKERS:-4} )
for v in reel:soundtrack music_sfx:music_sfx_only; do
  ffmpeg -v error -y -i out/video_silent.mp4 -i out/${v##*:}.wav -map 0:v -map 1:a -c:v copy \
    -af "loudnorm=I=-14:TP=-1.5:LRA=11" -ar 48000 -c:a aac -b:a 256k -shortest -movflags +faststart \
    out/ABdeVilliers_${v%%:*}.mp4
done
ffprobe -v error -show_entries format=duration,size -of csv=p=0 out/ABdeVilliers_reel.mp4

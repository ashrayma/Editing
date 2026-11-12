#!/bin/bash
# Full pipeline: composition -> HyperFrames render (1080p30) -> soundtrack -> final mux at -14 LUFS
set -e
cd "$(dirname "$0")"
python3 gen.py
python3 soundtrack.py
( cd hf_main && npx hyperframes render -o ../out/video_silent.mp4 -q delivery -w 4 )
ffmpeg -v error -y -i out/video_silent.mp4 -i out/soundtrack.wav -map 0:v -map 1:a -c:v copy \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11" -ar 48000 -c:a aac -b:a 256k -shortest -movflags +faststart \
  out/Centurion2003_The98.mp4
ffprobe -v error -show_entries format=duration,size -of csv=p=0 out/Centurion2003_The98.mp4
echo FILM_DONE

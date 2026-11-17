#!/bin/bash
# Full pipeline: clean VO -> composition -> soundtrack -> HyperFrames render (1080p30) -> mux at -14 LUFS
#   ./make.sh            delivery quality
#   ./make.sh draft      fast check render
set -e
cd "$(dirname "$0")"
Q=${1:-delivery}
python3 build_vo.py
python3 cut_clips.py
python3 gen.py
python3 soundtrack.py
( cd hf && npx hyperframes render -o ../out/silent.mp4 -q "$Q" -w 3 --quiet )
ffmpeg -v error -y -i out/silent.mp4 -i out/soundtrack.wav -map 0:v -map 1:a -c:v copy \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11" -ar 48000 -c:a aac -b:a 256k -shortest -movflags +faststart \
  out/Karun303.mp4
ffprobe -v error -show_entries format=duration,size -of csv=p=0 out/Karun303.mp4
echo FILM_DONE

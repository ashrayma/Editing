#!/bin/bash
# reel.py -> HyperFrames render -> mux with the soundtrack at -14 LUFS
set -e
cd "$(dirname "$0")"
python3 reel.py
( cd reel && npx hyperframes render -o ../out/silent.mp4 -q delivery -w 4 )
ffmpeg -v error -y -i out/silent.mp4 -i out/soundtrack.wav -map 0:v -map 1:a -c:v copy \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11" -ar 48000 -c:a aac -b:a 256k -shortest -movflags +faststart out/DearRajat.mp4
echo DONE

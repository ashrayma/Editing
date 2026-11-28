#!/bin/bash
# clean VO -> reel composition + soundtrack -> HyperFrames render (1080x1920) -> mux at -14 LUFS
set -e
cd "$(dirname "$0")"
python3 build_vo.py
python3 reel.py
( cd reel && npx hyperframes render -o ../out/silent.mp4 -q delivery -w 3 --quiet )
mkdir -p final
ffmpeg -v error -y -i out/silent.mp4 -i out/soundtrack.wav -map 0:v -map 1:a -c:v copy \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11" -ar 48000 -c:a aac -b:a 256k -shortest -movflags +faststart final/AndersonStillBowling.mp4
echo DONE

#!/bin/bash
# Full pipeline: composition -> HyperFrames render (1080p30) -> soundtrack -> final mux at -14 LUFS.
#   ./make_film.sh            uses whatever narration is in out/ (scratch_vo.py or build_vo.py)
# 3D shots must exist first: blender/render_all.sh (draft) or RES=1920x1080 TAA=32 blender/render_all.sh (final)
set -e
cd "$(dirname "$0")"
[ -f out/vo_timeline.json ] || python3 scratch_vo.py
python3 gen.py
python3 soundtrack.py
( cd hf_main && ../../doc_video/node_modules/.bin/hyperframes render -o ../out/video_silent.mp4 -q delivery -w ${WORKERS:-4} --quiet )
ffmpeg -v error -y -i out/video_silent.mp4 -i out/soundtrack.wav -map 0:v -map 1:a -c:v copy \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11" -ar 48000 -c:a aac -b:a 256k -shortest -movflags +faststart \
  out/31for4.mp4
ffprobe -v error -show_entries format=duration,size -of csv=p=0 out/31for4.mp4
echo FILM_DONE

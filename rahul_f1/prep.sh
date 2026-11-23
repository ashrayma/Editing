#!/bin/bash
# 1080x1920 versions of the supplied clips: landscape/square video large in the middle over a blurred, darkened copy.
set -e
cd "$(dirname "$0")"
vert() {  # in start dur out [crop]
  local crop=${5:-"iw:ih:0:0"}
  ffmpeg -nostdin -v error -y -ss "$2" -t "$3" -i "$1" -filter_complex \
   "[0:v]crop=$crop,split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:2,eq=brightness=-0.18[bg];\
    [b]scale=1080:-2:flags=lanczos,unsharp=5:5:0.8[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2-80,fps=30,format=yuv420p" \
   -an -c:v libx264 -crf 17 -preset medium "$4"
}
# Rahul, Cricbuzz/ANI press conference (Lord's, July 2025): video area only, credits kept
vert src/interview.mp4 50.85 8.85 assets/interview.mp4 "1080:608:0:866"
ffmpeg -nostdin -v error -y -ss 50.85 -t 8.85 -i src/interview.mp4 -vn -ac 1 -ar 44100 assets/interview_audio.wav
# F1 onboard (2011 Renault V8)
vert src/f1.mp4 2 8 assets/f1_hook.mp4
vert src/f1.mp4 30 6 assets/f1_fast.mp4
ffmpeg -nostdin -v error -y -ss 2 -t 8 -i src/f1.mp4 -vn -ac 1 -ar 44100 assets/f1_hook_audio.wav
ffmpeg -nostdin -v error -y -ss 30 -t 6 -i src/f1.mp4 -vn -ac 1 -ar 44100 assets/f1_fast_audio.wav
echo PREP_DONE

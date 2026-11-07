#!/bin/bash
# For each 3D shot: <shot>.len (seconds) and <shot>_last.png (held frame) next to renders/<shot>.mp4.
# A shot still rendering gets a placeholder clip from the frames done so far (for layout previews only).
cd "$(dirname "$0")/renders"
for s in seven stumps trophies n91 goat logo; do
  if [ ! -f $s.mp4 ] || [ "$1" = "--placeholders" -a ! -f $s.done ]; then
    if ls $s/*.png >/dev/null 2>&1; then
      ffmpeg -v error -y -framerate 30 -pattern_type glob -i "$s/*.png" -vf "scale=1080:1920,tpad=stop_mode=clone:stop_duration=1" -c:v libx264 -crf 18 -pix_fmt yuv420p $s.mp4
    else
      ffmpeg -v error -y -f lavfi -i color=c=0x030304:s=1080x1920:d=1.4:r=30 -c:v libx264 -pix_fmt yuv420p $s.mp4
    fi
  fi
  ffprobe -v error -show_entries format=duration -of csv=p=0 $s.mp4 > $s.len
  ffmpeg -v error -y -sseof -0.05 -i $s.mp4 -frames:v 1 -update 1 ${s}_last.png
done
ls

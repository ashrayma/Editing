#!/bin/bash
# Sharpen everything for the long-form: highlight clips (fast model, every frame) + photos (full model).
# Waits for the voiceover transcription to finish so the two don't fight over the CPU.
cd "$(dirname "$0")"
SR=/tmp/claude-0/-home-user-Editing/f9639e0c-d650-5d7c-847c-d36184625aa6/scratchpad/sr
until grep -q TRANSCRIBE_DONE vo/transcribe.log 2>/dev/null && ! pgrep -f faster_whisper >/dev/null; do sleep 20; done
# name start end  (seconds in src/hl_303.mp4) — see src_clips.md
while read name a b; do
  [ -z "$name" ] && continue
  mkdir -p clips/$name/in
  [ -f clips/$name/done ] && continue
  ffmpeg -nostdin -loglevel error -y -ss $a -to $b -i src/hl_303.mp4 -vf "crop=440:248:100:52" clips/$name/in/%04d.png
  python3 fast_sr.py $SR/realesr-general-x4v3.pth clips/$name/in clips/$name/up > /dev/null < /dev/null && touch clips/$name/done
  echo "clip $name done"
done <<'LIST'
drop34 43.0 47.5
broad 123.0 127.0
hundred 150.0 154.5
dressing100 155.0 158.0
dressing100b 164.5 167.5
dressing150 239.0 243.0
bat150 245.5 248.5
crowd 303.0 307.0
walk381 395.0 398.5
shot300 452.0 456.5
kohli300 459.0 461.8
arms300 462.0 468.3
hug300 468.5 471.2
armclose 471.5 474.2
walkoff 474.5 477.6
LIST
# photos under 1600 px wide: full Real-ESRGAN x4plus
for f in assets/*.jpg assets/*.gif; do
  n=$(basename "${f%.*}")
  [ -f up/$n.png ] && continue
  w=$(python3 -c "from PIL import Image; print(Image.open('$f').width)")
  if [ "$w" -lt 1600 ]; then
    python3 -c "from PIL import Image; Image.open('$f').convert('RGB').save('up/_in_$n.png')"
    python3 ../doc_video/thumb/esrgan.py $SR/RealESRGAN_x4plus.pth up/_in_$n.png up/$n.png > /dev/null 2>&1 < /dev/null && rm up/_in_$n.png
    echo "photo $n done"
  fi
done
echo UPSCALE_ALL_DONE

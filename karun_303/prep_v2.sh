#!/bin/bash
# New highlight close-ups (upscaled) + subject cutouts for the depth-text style.
cd "$(dirname "$0")"
SR=/tmp/claude-0/-home-user-Editing/f9639e0c-d650-5d7c-847c-d36184625aa6/scratchpad/sr
while read name a b; do
  [ -z "$name" ] && continue
  [ -f clips/$name/done ] && continue
  mkdir -p clips/$name/in
  ffmpeg -nostdin -loglevel error -y -ss $a -to $b -i src/hl_303.mp4 -vf "crop=440:248:100:52" clips/$name/in/%04d.png
  python3 fast_sr.py $SR/realesr-general-x4v3.pth clips/$name/in clips/$name/up > /dev/null < /dev/null && touch clips/$name/done
  echo "clip $name done"
done <<'LIST'
closeA 83.6 85.4
sweep 75.6 78.2
closeB 185.0 186.9
closeC 325.2 326.9
closeD 405.9 408.0
LIST
python3 - <<'PY'
import os, numpy as np
from PIL import Image, ImageFilter
from rembg import new_session, remove
sess = new_session("isnet-general-use")
os.makedirs("cut", exist_ok=True)
for n in ["karun_303_chennai_2016", "karun_2025_portrait_fence", "karun_vidarbha_hundred", "karun_oval_fifty_2025",
          "sehwag_triple_bat_helmet", "karun_northants_hundred"]:
    src = f"up/{n}.png" if os.path.exists(f"up/{n}.png") else [f"assets/{f}" for f in os.listdir("assets") if f.startswith(n)][0]
    im = Image.open(src).convert("RGB")
    k = 1400 / max(im.size)
    small = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    m = remove(small, session=sess, only_mask=True).resize(im.size, Image.LANCZOS)
    out = im.convert("RGBA"); out.putalpha(m)
    out.save(f"cut/{n}.png"); print("cut", n, flush=True)
PY
echo PREP_V2_DONE

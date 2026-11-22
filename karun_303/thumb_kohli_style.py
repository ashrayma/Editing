#!/usr/bin/env python3
"""Karun thumbnail in the 'Kohli Cried' (82*) formula, 1920x1080:
faded tricolour background; Karun NOW (the frowning close-up) small and black-and-white, printed into the flag on
the left; Karun 2016 (helmet raised after the 303*) big and in full colour on the right, lit by the flag;
FORGOTTEN (big grunge white) + 303* on the red brush stroke, bottom-left; UNTOLD STORIES #5 badge top-right;
bottom-right corner left clear for YouTube's length badge.

    python3 thumb_kohli_style.py -> out/Karun_303_thumb_kohli_style.png / .jpg / _small.png
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "virat_82"))
sys.path.insert(0, os.path.join(ROOT, "virat_story"))
sys.path.insert(0, os.path.join(ROOT, "doc_video", "thumb"))
import thumb_82_v2 as k  # noqa: E402  (double exposure, flag light, edge glow, dust, bloom, unify)
import thumb_goat_v2 as g  # noqa: E402  (flag background, grunge text, brush box, edge fade)
import thumb_wc2003 as tw  # noqa: E402
from thumb_wc2003 import ANTON, H, W, fade_bottom, finish, place, regrade  # noqa: E402

tw.HERE = os.path.join(HERE, "out")
Y = (255, 222, 89)


def badge(base, text, right, top):
    f = ImageFont.truetype(ANTON, 44)
    d = ImageDraw.Draw(base)
    l, t, r, b = d.textbbox((0, 0), text, font=f)
    bw, bh = r - l + 64, b - t + 30
    x0 = right - bw
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    dl.rectangle((x0, top, right, top + bh), fill=(14, 14, 18, 205))
    dl.rectangle((x0, top, x0 + 11, top + bh), fill=Y + (255,))
    dl.text((x0 + 34 - l, top + 15 - t), text, font=f, fill=(255, 255, 255, 240))
    base.alpha_composite(lay)


def main():
    g.CHAKRA = (905, 455, 95)                      # in the gap between the two Karuns
    base = g.flag_background()

    # LEFT - Karun now: the frowning close-up, black-and-white, printed into the flag
    now = Image.open(os.path.join(HERE, "cut", "karun_now_face.png")).convert("RGBA")
    now = now.crop((0, 0, 1500, int(now.height * 0.62)))              # head and shoulders
    s = 760 / now.height
    now = now.resize((int(now.width * s), 760), Image.LANCZOS)
    now = regrade(now, color=0.0, contrast=1.3, bright=1.05, sharpen=(1.0, 60, 1))
    now = g.edge_fade(fade_bottom(now, 470, 740), left=30, right=40)
    base = k.double_exposure(base, now, max(0, 420 - now.width // 2), 20, strength=0.9)

    # RIGHT - Karun 2016: helmet raised after the 303*, big, full colour, lit by the flag
    cel = Image.open(os.path.join(HERE, "cut", "helmet_raised_2016.png")).convert("RGBA")
    cel = cel.crop((0, 0, cel.width, int(cel.height * 0.74)))
    s = 1420 / cel.height
    cel = cel.resize((int(cel.width * s), 1420), Image.LANCZOS)
    cel = regrade(cel, color=1.08, contrast=1.12, bright=1.05, sharpen=(1.0, 60, 1))
    cel = k.flag_light(cel)
    cel = fade_bottom(cel, 880, 1000)
    cx, cy = 1450 - cel.width // 2, 125
    k.edge_glow(base, cel, cx, cy, (255, 170, 80), spread=40, k=0.45)
    place(base, cel, cx, cy, wrap=0.5, rim_color=(255, 190, 110), rim_side=-1, rim_k=0.5, shadow=0.85)

    # text block, bottom-left only
    g.grunge_text(base, "FORGOTTEN", 60, 575, 150)
    g.brush_box(base, (60, 775, 640, 1040))
    g.grunge_text(base, "303*", 110, 765, 245, shadow=False)

    badge(base, "UNTOLD STORIES #5", W - 40, 40)

    k.dust(base)
    base = k.bloom(base)
    base = k.unify(base)
    finish(base, "Karun_303_thumb_kohli_style")


if __name__ == "__main__":
    main()

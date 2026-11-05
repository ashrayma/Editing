#!/usr/bin/env python3
"""1920x1080 thumbnail, v2: "Virat Kohli's 82*: The Night That Became Cricket History | MCG 2022".

Gritty tricolour style (shared with the Ordinary Boy to GOAT v2 thumbnail): textured saffron / white
(Ashoka Chakra) / green background; Virat waving to the MCG after the win, faded, on the left; the six off
Haris Rauf huge on the right (helmet, gloves, bat); THE NIGHT / 82* on a red brush block / MCG 2022.

    python3 thumb_82_v2.py  ->  thumb_82_v2.png / .jpg / _small.png
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "virat_story"))
sys.path.insert(0, os.path.join(HERE, "..", "doc_video", "thumb"))
import thumb_goat_v2 as g  # noqa: E402  (flag background, duotone, grunge text, brush box)
import thumb_wc2003 as tw  # noqa: E402
from thumb_wc2003 import W, fade_bottom, finish, load_cut, place, regrade  # noqa: E402

tw.HERE = HERE


def main():
    g.CHAKRA = (765, 520, 110)  # in the gap between the two Viratas
    base = g.flag_background()

    # LEFT - after the win: Virat waving to the MCG, faded, centred over the headline
    wv = load_cut("cut_wave.png", 760)
    wv = g.duotone(regrade(wv, contrast=1.2), opacity=0.7)
    wv = g.edge_fade(fade_bottom(wv, 430, 700), left=40, right=40)
    base.alpha_composite(wv, (500 - wv.width // 2, 30))

    # RIGHT - the six off Rauf: helmet, gloves and bat, huge
    sx = Image.open(os.path.join(HERE, "cut_six.png")).convert("RGBA").crop((900, 0, 2824, 2000))
    s = 1150 / sx.height
    sx = sx.resize((int(sx.width * s), 1150), Image.LANCZOS)
    sx = regrade(sx, color=1.1, contrast=1.15, bright=1.04, sharpen=(1.0, 60, 1))
    sx = tw.directional_light(sx, "left", (255, 210, 160), 0.35)
    sx = g.edge_fade(fade_bottom(sx, 820, 1120), left=90)
    place(base, sx, W - sx.width + 60, -40, wrap=0.3, rim_color=(255, 190, 120), rim_side=-1, rim_k=0.45, shadow=0.8)

    # text block, bottom left
    g.grunge_text(base, "THE NIGHT", 60, 560, 160)
    g.brush_box(base, (60, 770, 580, 1040))
    g.grunge_text(base, "82*", 120, 760, 245, shadow=False)
    g.grunge_text(base, "MCG", 630, 775, 125)
    g.grunge_text(base, "2022", 630, 900, 125, fill=(255, 222, 89))
    finish(base, "thumb_82_v2")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""1920x1080 thumbnail: "Virat Kohli's 82: The Night That Became Cricket History | MCG 2022".

Real MCG night (post-win photo, blurred + bloomed) behind; Virat's roar large on the left; the six off
Haris Rauf on the right; a giant 82* set behind both players; "THE NIGHT" + VS PAKISTAN · MCG 2022 banner.
Cut-outs come from Real-ESRGAN 4x upscales; compositing helpers are shared with the World Cup 2003 thumbnail.

    python3 thumb_82.py  ->  thumb_82.png / .jpg / _small.png
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "doc_video", "thumb"))
import thumb_wc2003 as tw  # noqa: E402
from thumb_wc2003 import ANTON, H, W, arr, fade_bottom, finish, img, load_cut, place, radial, regrade, shadow_text  # noqa: E402

Y = (255, 222, 89)  # brand #FFDE59
tw.HERE = HERE


def background():
    """The MCG on the night (post-win photo): cover-crop, blur, cool grade, floodlight bloom, vignette."""
    im = Image.open(os.path.join(HERE, "bg_mcg.jpg")).convert("RGB")
    s = W / im.width
    im = im.resize((W, int(im.height * s)), Image.LANCZOS).crop((0, 0, W, H))
    im = im.filter(ImageFilter.GaussianBlur(7))
    a = arr(im)
    lum = a.mean(-1, keepdims=True)
    bloom = arr(img(np.clip((lum - 170) * 3, 0, 255)[..., 0], "L").filter(ImageFilter.GaussianBlur(30)))[..., None] / 255
    a = lum + (a - lum) * 0.8
    a = a * np.array([0.8, 0.9, 1.08], np.float32) * 0.5
    a += bloom * np.array([255, 240, 215], np.float32) * 0.9
    a += radial(960, 470, 700, 500, 1.8)[..., None] * np.array(Y, np.float32) * 0.18   # warm glow behind 82*
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = 1 - 0.75 * np.clip(((xx - W / 2) / (W * 0.6)) ** 2 + ((yy - H * 0.42) / (H * 0.78)) ** 2, 0, 1)
    return img(a * v[..., None]).convert("RGBA")


def big_number(base, txt, cx, top, size):
    """Giant yellow number with dark extrusion and glow, drawn before the players so they overlap it."""
    f = ImageFont.truetype(ANTON, size)
    l, t, r, b = f.getbbox(txt)
    x = int(cx - (r - l) / 2 - l)
    glow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).text((x, top - t), txt, font=f, fill=Y + (150,))
    base.alpha_composite(glow.filter(ImageFilter.GaussianBlur(40)))
    ext = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ext)
    for k in range(14, 0, -1):
        d.text((x + k, top - t + k), txt, font=f, fill=(120, 90, 10, 255))
    base.alpha_composite(ext)
    ImageDraw.Draw(base).text((x, top - t), txt, font=f, fill=Y, stroke_width=3, stroke_fill=(40, 30, 4))


def banner(base, txt, cx, top, size=60):
    f = ImageFont.truetype(ANTON, size)
    track = 4
    w = sum(f.getlength(c) for c in txt) + track * (len(txt) - 1)
    l, t, r, b = f.getbbox(txt)
    pw, ph = 34, 14
    box = (int(cx - w / 2 - pw), top, int(cx + w / 2 + pw), top + (b - t) + 2 * ph)
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle((box[0] + 8, box[1] + 10, box[2] + 8, box[3] + 10), fill=(0, 0, 0, 200))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(base)
    d.rectangle(box, fill=Y + (255,))
    x = box[0] + pw - l
    for c in txt:
        d.text((x, top + ph - t), c, font=f, fill=(14, 12, 6))
        x += f.getlength(c) + track


def main():
    base = background()
    big_number(base, "82*", 980, 40, 470)

    # RIGHT - the six off Rauf, a step back
    sx = load_cut("cut_six.png", 1000)
    sx = regrade(sx, color=1.05, contrast=1.08, bright=0.95, sharpen=(1.0, 60, 1))
    sx = tw.directional_light(sx, "left", (255, 225, 160), 0.5)
    sx = fade_bottom(sx, 700, 960)
    place(base, sx, 1500 - sx.width // 2, 70, rim_color=(170, 210, 255), rim_side=-1, rim_k=0.45, shadow=0.6)

    # LEFT - the roar, hero
    ro = load_cut("cut_roar.png", 1080)
    ro = regrade(ro, color=1.1, contrast=1.1, bright=1.06, sharpen=(1.0, 60, 1))
    ro = tw.directional_light(ro, "right", (255, 215, 140), 0.55)
    ro = fade_bottom(ro, 780, 1060)
    place(base, ro, 560 - ro.width // 2, 20, wrap=0.4, rim_color=Y, rim_side=1, rim_k=0.5, shadow=0.75)

    tw.floor(base, 700)
    shadow_text(base, "THE NIGHT", 150, 980, 800, (255, 255, 255), stroke=5, tracking=4)
    banner(base, "VS PAKISTAN  ·  MCG 2022", 980, 970, 58)
    finish(base, "thumb_82")


if __name__ == "__main__":
    main()

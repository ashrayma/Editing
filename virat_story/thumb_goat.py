#!/usr/bin/env python3
"""1920x1080 thumbnail: "From an Ordinary Boy to the GOAT: The Virat Kohli Story".

Before -> after split: young Virat (2008-era headshot) cool and muted on the left, today's Virat arms
raised in warm floodlight on the right, "ORDINARY BOY -> THE GOAT" across the bottom.
Cut-outs come from Real-ESRGAN 4x upscales (doc_video/thumb/esrgan.py); compositing helpers
(place, regrade, fade_bottom, shadow_text...) are shared with the World Cup 2003 thumbnail.

    python3 thumb_goat.py  ->  thumb_goat.png / .jpg / _small.png
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "doc_video", "thumb"))
import thumb_wc2003 as tw  # noqa: E402
from thumb_wc2003 import (ANTON, H, W, arr, fade_bottom, finish, img, load_cut, place,  # noqa: E402,F401
                          radial, regrade, shadow_text)

Y = (255, 222, 89)  # brand #FFDE59
rng = np.random.default_rng(18)
tw.HERE = HERE      # load_cut / finish read and write next to this script


def background():
    """Cool, flat 'ordinary' left half; warm floodlit 'glory' right half, with beams and bokeh."""
    a = np.zeros((H, W, 3), np.float32) + np.array([8, 9, 13], np.float32)
    for cx, cy, rx, ry, col, k in [(380, 420, 820, 700, (70, 85, 105), 0.55),        # dull steel left
                                   (1500, 380, 950, 820, (235, 150, 40), 0.95),       # gold right
                                   (1560, -60, 700, 460, (255, 225, 150), 0.8),
                                   (960, 1100, 900, 300, (20, 20, 25), 0.3)]:
        a += radial(cx, cy, rx, ry, 1.8)[..., None] * np.array(col, np.float32) * k

    beams = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(beams)
    fx, fy = 1560, -80
    for ang in (62, 74, 88, 102, 116):
        t = np.radians(ang)
        for spread, val in [(0.06, 30), (0.025, 42)]:
            d.polygon([(fx, fy), (fx + 2400 * np.cos(t - spread), fy + 2400 * np.sin(t - spread)),
                       (fx + 2400 * np.cos(t + spread), fy + 2400 * np.sin(t + spread))], fill=val)
    beams = arr(beams.filter(ImageFilter.GaussianBlur(24))) / 255
    beams *= np.clip(1 - np.linspace(0, 1, H) * 1.05, 0, 1)[:, None]
    beams *= np.clip((np.arange(W) - 820) / 400, 0, 1)[None, :]     # beams only on the GOAT side
    a += beams[..., None] * np.array([255, 235, 200], np.float32)

    bok = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(bok)
    for _ in range(120):
        x = rng.uniform(900, W)
        y = rng.normal(160, 90)
        r = rng.uniform(6, 22)
        c = np.array([255, 205, 120]) * rng.uniform(0.25, 0.7)
        d.ellipse((x - r, y - r, x + r, y + r), fill=tuple(int(v) for v in c))
    bok = bok.filter(ImageFilter.GaussianBlur(5))
    a += arr(bok) + arr(bok.filter(ImageFilter.GaussianBlur(40))) * 1.1

    # gold dust drifting on the right
    dust = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(dust)
    for _ in range(260):
        x, y = rng.uniform(1000, W), rng.uniform(0, H * 0.8)
        r = rng.uniform(1, 3.2)
        d.ellipse((x - r, y - r, x + r, y + r), fill=int(rng.uniform(80, 220)))
    a += arr(dust.filter(ImageFilter.GaussianBlur(0.8)))[..., None] / 255 * np.array([255, 215, 140], np.float32)

    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = 1 - 0.7 * np.clip(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H * 0.4) / (H * 0.8)) ** 2, 0, 1)
    return img(a * v[..., None]).convert("RGBA")


def arrow(base, cx, cy, size=120):
    """Bold yellow chevron arrow with a soft glow."""
    pts = [(-size, -size * 0.32), (size * 0.15, -size * 0.32), (size * 0.15, -size * 0.75),
           (size, 0), (size * 0.15, size * 0.75), (size * 0.15, size * 0.32), (-size, size * 0.32)]
    pts = [(cx + x, cy + y) for x, y in pts]
    glow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).polygon(pts, fill=Y + (200,))
    base.alpha_composite(glow.filter(ImageFilter.GaussianBlur(22)))
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).polygon([(x + 8, y + 10) for x, y in pts], fill=(0, 0, 0, 200))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
    ImageDraw.Draw(base).polygon(pts, fill=Y + (255,), outline=(20, 16, 4, 255))


def tag(base, txt, x, y, fg, bg):
    f = ImageFont.truetype(ANTON, 46)
    l, t, r, b = f.getbbox(txt)
    w, h = r - l + 44, b - t + 22
    d = ImageDraw.Draw(base)
    d.rectangle((x, y, x + w, y + h), fill=bg)
    d.text((x + 22 - l, y + 11 - t), txt, font=f, fill=fg)


def main():
    base = background()

    # LEFT - the ordinary boy: muted, cool, a step back
    yb = load_cut("cut_young.png", 860)
    yb = regrade(yb, color=0.7, contrast=1.08, bright=0.98, sharpen=(1.0, 60, 1), tint=(150, 170, 200), tint_k=0.12)
    yb = fade_bottom(yb, 620, 840)
    place(base, yb, 430 - yb.width // 2, 60, rim_color=(190, 210, 235), rim_side=1, rim_k=0.35, shadow=0.6)

    # RIGHT - the GOAT: arms raised, warm key from the floodlights
    gt = load_cut("cut_goat.png", 1130)
    gt = regrade(gt, color=1.12, contrast=1.1, bright=1.04, sharpen=(1.0, 60, 1))
    gt = tw.directional_light(gt, "right", (255, 190, 90), 0.6)
    gt = fade_bottom(gt, 820, 1100)
    place(base, gt, 1420 - gt.width // 2, -40, wrap=0.4, rim_color=Y, rim_side=1, rim_k=0.55, shadow=0.7)

    # bottom band
    tw.floor(base, 640)
    arrow(base, 905, 925, 95)
    shadow_text(base, "ORDINARY", 112, 430, 805, (255, 255, 255), stroke=4, tracking=2)
    shadow_text(base, "BOY", 112, 430, 930, (255, 255, 255), stroke=4, tracking=2)
    shadow_text(base, "THE GOAT", 240, 1450, 800, Y, stroke=6, tracking=4)

    tag(base, "2008", 60, 60, (255, 255, 255), (40, 44, 52, 235))
    tag(base, "TODAY", W - 210, 60, (15, 12, 4), Y + (255,))
    finish(base, "thumb_goat")


if __name__ == "__main__":
    main()

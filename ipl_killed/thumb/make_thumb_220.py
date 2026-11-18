#!/usr/bin/env python3
"""Thumbnail B for 'IPL is dying': frustrated Bumrah left, huge '220' right, 'IS NORMAL NOW?' below.
python3 make_thumb_220.py -> out/IPL_is_dying_thumbnail_B_220.jpg"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from scipy import ndimage as nd

from make_thumb import ANTON, HERE, INK, LOGO, W, H, Y, cover

RED = (229, 52, 52)


def background():
    bg = cover(Image.open(os.path.join(HERE, "up", "stadium.png")).convert("RGB"), W, H, 0.5, 0.30)
    bg = bg.filter(ImageFilter.GaussianBlur(9))                       # floodlights become soft bokeh
    a = np.asarray(bg, np.float32)
    a = a * np.array([0.62, 0.70, 0.95])                               # navy night
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W * 0.5) / (W * 0.62)) ** 2 + ((yy - H * 0.45) / (H * 0.75)) ** 2)
    edge = np.clip((r - 0.55) / 0.6, 0, 1)[..., None]
    a = a * (1 - 0.55 * edge) + np.array([150, 18, 22]) * 0.55 * edge  # red danger tint at the edges
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


def glow_edge(layer, radius=14, color=(255, 222, 89), strength=0.38):
    a = np.asarray(layer.split()[3], np.float32) / 255
    g = np.clip(nd.gaussian_filter(a, radius) - a * 0.6, 0, 1) * strength * 2.2   # a rim just outside the edge
    out = Image.new("RGBA", layer.size, color + (0,))
    out.putalpha(Image.fromarray(np.clip(g * 255, 0, 255).astype(np.uint8)))
    return out


def outlined(base, xy, text, font, fill, stroke, sw, anchor="mm", shadow=True):
    if shadow:
        sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((xy[0], xy[1] + 10), text, font=font, fill=(0, 0, 0, 200), anchor=anchor,
                                stroke_width=sw, stroke_fill=(0, 0, 0, 200))
        base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    ImageDraw.Draw(base).text(xy, text, font=font, fill=fill, anchor=anchor, stroke_width=sw, stroke_fill=stroke)


def main():
    base = background()

    # Bumrah: waist up, left half, head near the top
    b = Image.open(os.path.join(HERE, "cut", "bumrah.png"))
    b = b.crop((0, 0, b.width, int(b.height * 0.74)))
    bh = 790
    b = b.resize((round(b.width * bh / b.height), bh), Image.LANCZOS)
    b = ImageEnhance.Contrast(b).enhance(1.06)
    bx, by = 330 - b.width // 2, H - bh + 70
    gl = glow_edge(b)
    pad = 60
    glc = Image.new("RGBA", (b.width + 2 * pad, b.height + 2 * pad), (0, 0, 0, 0))
    glc.alpha_composite(gl, (pad, pad))
    base.alpha_composite(glc.filter(ImageFilter.GaussianBlur(4)), (bx - pad, by - pad))
    base.alpha_composite(b, (bx, by))

    # 220 + IS NORMAL NOW?
    cx = 935
    f1 = ImageFont.truetype(ANTON, 330)                                # cap height ~ 40% of the frame
    outlined(base, (cx, 300), "220", f1, Y, INK, 7)
    f2 = ImageFont.truetype(ANTON, 84)
    outlined(base, (cx, 548), "IS NORMAL NOW?", f2, (255, 255, 255), INK, 4)

    # small red up-arrow beside 220
    d = ImageDraw.Draw(base)
    l, t, r, bt = d.textbbox((cx, 300), "220", font=f1, anchor="mm")
    ax, ay = r + 40, t + 10
    arrow = [(ax, ay), (ax + 34, ay + 46), (ax + 13, ay + 46), (ax + 13, ay + 120), (ax - 13, ay + 120),
             (ax - 13, ay + 46), (ax - 34, ay + 46)]
    d.polygon(arrow, fill=RED, outline=INK)

    logo = Image.open(LOGO).convert("RGBA")
    logo = logo.resize((140, round(logo.height * 140 / logo.width)), Image.LANCZOS)
    base.alpha_composite(logo, (W - 140 - 24, 22))

    out = os.path.join(HERE, "out", "IPL_is_dying_thumbnail_B_220.jpg")
    base.convert("RGB").save(out, quality=93)
    base.convert("RGB").resize((168, 94), Image.LANCZOS).save(os.path.join(HERE, "out", "b220_tiny.png"))
    print(out, os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    main()

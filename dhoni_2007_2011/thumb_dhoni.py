#!/usr/bin/env python3
"""1920x1080 thumbnail: Dhoni's plan from the 2007 T20 World Cup to the 2011 World Cup.

Diagonal split: 2007 (cool, steel-blue, Johannesburg crowd) roar on the left; 2011 (warm gold, Wankhede crowd)
winning-six follow-through on the right; giant ghost years behind each; a glowing crack down the split;
"2007 = 2011?" across the bottom with the "=" in brand yellow and the "?" in red.
Cut-outs come from Real-ESRGAN 4x upscales; compositing helpers are shared with the other thumbnails.

    python3 thumb_dhoni.py  ->  thumb_dhoni.png / .jpg / _small.png
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "doc_video", "thumb"))
import thumb_wc2003 as tw  # noqa: E402
from thumb_wc2003 import ANTON, H, W, arr, fade_bottom, finish, img, place, radial, regrade  # noqa: E402

tw.HERE = HERE
Y = (255, 222, 89)
RED = (226, 38, 38)
rng = np.random.default_rng(711)
TOP_X, BOT_X = 1050, 870  # split line from (TOP_X, 0) to (BOT_X, H)


def split_mask(soft=3):
    """1 on the 2011 (right) side of the diagonal."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    line = TOP_X + (BOT_X - TOP_X) * yy / H
    return np.clip((xx - line) / soft + 0.5, 0, 1)


def crowd(name, tint, dark):
    im = Image.open(os.path.join(HERE, name)).convert("RGB")
    s = max(W / im.width, H / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    im = im.crop(((im.width - W) // 2, 0, (im.width - W) // 2 + W, H)).filter(ImageFilter.GaussianBlur(16))
    a = arr(im)
    lum = a.mean(-1, keepdims=True)
    return (lum * 0.55 + a * 0.45) * np.array(tint, np.float32) * dark


def background():
    left = crowd("bg_2007.jpg", (0.72, 0.85, 1.05), 0.42)
    right = crowd("bg_2011.jpg", (1.12, 0.92, 0.62), 0.48)
    left += radial(480, 380, 760, 640, 1.8)[..., None] * np.array([70, 110, 170], np.float32) * 0.55
    right += radial(1460, 300, 820, 700, 1.8)[..., None] * np.array([255, 170, 60], np.float32) * 0.6
    right += radial(1560, -80, 600, 420, 1.6)[..., None] * np.array([255, 230, 170], np.float32) * 0.55
    m = split_mask()[..., None]
    a = left * (1 - m) + right * m
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = 1 - 0.7 * np.clip(((xx - W / 2) / (W * 0.6)) ** 2 + ((yy - H * 0.42) / (H * 0.78)) ** 2, 0, 1)
    return img(a * v[..., None]).convert("RGBA")


def ghost_year(base, txt, cx, top, size, color, alpha):
    f = ImageFont.truetype(ANTON, size)
    l, t, r, b = f.getbbox(txt)
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((cx - (r - l) / 2 - l, top - t), txt, font=f, fill=color + (alpha,))
    base.alpha_composite(layer)


def crack(base):
    """Bright, slightly jagged seam with glow along the split, plus a few hairline fractures."""
    pts = []
    for i, y in enumerate(np.linspace(-10, H + 10, 34)):
        x = TOP_X + (BOT_X - TOP_X) * y / H + (rng.normal(0, 7) if 0 < i < 33 else 0)
        pts.append((x, y))
    glow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(glow)
    d.line(pts, fill=(255, 220, 140, 255), width=26)
    base.alpha_composite(glow.filter(ImageFilter.GaussianBlur(26)))
    core = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(core)
    d.line(pts, fill=(255, 248, 225, 255), width=5)
    for _ in range(9):
        i = rng.integers(3, 30)
        x, y = pts[i]
        for _ in range(3):
            nx, ny = x + rng.normal(0, 40), y + rng.uniform(15, 55) * rng.choice([-1, 1])
            d.line((x, y, nx, ny), fill=(255, 240, 210, 170), width=2)
            x, y = nx, ny
    base.alpha_composite(core.filter(ImageFilter.GaussianBlur(0.8)))


def headline(base, top=820, size=215):
    """2007 = 2011? on a dark band: '=' as two bold brand-yellow bars with glow, '?' red."""
    tw.floor(base, 620)
    f = ImageFont.truetype(ANTON, size)
    eq_w, gap = 150, 46
    parts = [("2007", (230, 238, 255)), ("=", Y), ("2011", (255, 214, 140)), ("?", RED)]
    widths = [eq_w if t == "=" else f.getlength(t) for t, _ in parts]
    widths[0] += gap
    widths[1] += gap
    x0 = (W - sum(widths)) / 2
    l, t, r, b = f.getbbox("2007")
    cap_mid = top + (b - t) / 2

    def draw(target, dx, dy, fill, stroke=0, glow_only=False):
        d = ImageDraw.Draw(target)
        xx = x0
        for (txt, col), w in zip(parts, widths):
            c = fill or col
            if txt == "=":
                bh, sep = 34, 30
                for yb in (cap_mid - sep / 2 - bh, cap_mid + sep / 2):
                    d.rectangle((xx + dx, yb + dy, xx + eq_w + dx, yb + bh + dy), fill=c,
                                outline=(10, 10, 14) if stroke else None, width=stroke)
            elif not glow_only or txt == "?":
                d.text((xx + dx, top - t + dy), txt, font=f, fill=c, stroke_width=stroke, stroke_fill=(10, 10, 14))
            xx += w

    sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw(sh, 8, 12, (0, 0, 0, 235), stroke=8)
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    glow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw(glow, 0, 0, None, glow_only=True)
    base.alpha_composite(glow.filter(ImageFilter.GaussianBlur(26)))
    draw(base, 0, 0, None, stroke=5)


def main():
    base = background()
    ghost_year(base, "2007", 470, 30, 400, (150, 185, 235), 60)
    ghost_year(base, "2011", 1470, 30, 400, (255, 200, 110), 70)

    # LEFT - 2007: the roar after the T20 World Cup win, cool light
    d7 = Image.open(os.path.join(HERE, "cut_2007.png")).convert("RGBA")
    d7 = d7.crop((0, 0, d7.width, int(d7.height * 0.72)))  # head to knees: big enough to read
    d7 = d7.resize((int(d7.width * 1060 / d7.height), 1060), Image.LANCZOS)
    d7 = regrade(d7, color=1.0, contrast=1.1, bright=1.04, sharpen=(1.0, 60, 1), tint=(170, 200, 240), tint_k=0.1)
    d7 = fade_bottom(d7, 640, 1000)
    place(base, d7, 470 - d7.width // 2, 10, wrap=0.45, rim_color=(170, 210, 255), rim_side=1, rim_k=0.5,
          shadow=0.75)

    # RIGHT - 2011: the winning six, warm floodlight
    d11 = Image.open(os.path.join(HERE, "cut_2011.png")).convert("RGBA")
    d11 = d11.crop((0, 0, d11.width, int(d11.height * 0.6)))  # bat to thigh
    d11 = d11.resize((int(d11.width * 1110 / d11.height), 1110), Image.LANCZOS)
    d11 = regrade(d11, color=1.1, contrast=1.12, bright=1.04, sharpen=(1.0, 60, 1))
    d11 = tw.directional_light(d11, "right", (255, 200, 110), 0.55)
    d11 = fade_bottom(d11, 680, 1060)
    place(base, d11, 1440 - d11.width // 2, -10, wrap=0.45, rim_color=(255, 200, 110), rim_side=1, rim_k=0.55,
          shadow=0.75)

    crack(base)
    headline(base)
    finish(base, "thumb_dhoni")


if __name__ == "__main__":
    main()

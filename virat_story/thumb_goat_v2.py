#!/usr/bin/env python3
"""1920x1080 thumbnail, v2: "From an Ordinary Boy to the GOAT: The Virat Kohli Story".

Gritty tricolour look: textured saffron / white (Ashoka Chakra) / green background, young Virat
faded and centred on the left,
a huge intense close-up on the right, and distressed ORDINARY BOY / TO / GOAT (on a red brush block).

    python3 thumb_goat_v2.py  ->  thumb_goat_v2.png / .jpg / _small.png
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "doc_video", "thumb"))
import thumb_wc2003 as tw  # noqa: E402
from thumb_wc2003 import ANTON, H, W, arr, fade_bottom, finish, img, load_cut, place, regrade  # noqa: E402

tw.HERE = HERE
RED = (214, 26, 34)
CHAKRA = (1110, 520, 150)  # centre x, y, radius; callers may move it into their layout's gap
rng = np.random.default_rng(2008)


def noise(scale, octaves=3):
    """Smooth multi-octave noise in [0, 1], W x H."""
    out = np.zeros((H, W), np.float32)
    amp = 1.0
    for o in range(octaves):
        s = max(2, int(scale / (2 ** o)))
        n = rng.random((H // s + 2, W // s + 2)).astype(np.float32)
        out += amp * arr(img(n * 255, "L").resize((W, H), Image.BICUBIC)) / 255
        amp *= 0.5
    out -= out.min()
    return out / out.max()


def flag_background():
    a = np.zeros((H, W, 3), np.float32)
    band = H / 3
    a[: int(band)] = (255, 153, 51)
    a[int(band): int(2 * band)] = (236, 232, 222)
    a[int(2 * band):] = (19, 136, 8)
    # soft band edges, like cloth
    a = arr(img(a).filter(ImageFilter.GaussianBlur(10)))
    # Ashoka Chakra, behind the centre
    ch = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ch)
    cx, cy, r = CHAKRA
    navy = (0, 0, 128, 255)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=navy, width=16)
    d.ellipse((cx - 30, cy - 30, cx + 30, cy + 30), fill=navy)
    for k in range(24):
        t = 2 * np.pi * k / 24
        d.line((cx, cy, cx + (r - 8) * np.cos(t), cy + (r - 8) * np.sin(t)), fill=navy, width=7)
    chm = arr(ch)
    al = chm[..., 3:4] / 255 * 0.85
    a = a * (1 - al) + chm[..., :3] * al
    # grunge: blotches, grain, scratches, then crush it down to a dark, moody flag
    blot = noise(220)[..., None]
    a *= 0.7 + 0.45 * blot
    grain = rng.normal(0, 1, (H, W, 1)).astype(np.float32)
    a += grain * 10
    scr = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(scr)
    for _ in range(140):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        ln, ang = rng.uniform(40, 260), rng.uniform(-0.4, 0.4) + np.pi / 2 * rng.integers(0, 2)
        sd.line((x, y, x + ln * np.cos(ang), y + ln * np.sin(ang)), fill=int(rng.uniform(40, 120)), width=1)
    a -= arr(scr)[..., None] * 0.5
    lum = a.mean(-1, keepdims=True)
    a = (lum + (a - lum) * 0.95) * 0.68
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = 1 - 0.75 * np.clip(((xx - W / 2) / (W * 0.58)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2, 0, 1)
    a *= v[..., None]
    # darker, smoky left side for the collage and text
    smoke = np.clip(1 - xx / 1100, 0, 1) ** 1.2 * (0.35 + 0.4 * noise(160))
    a *= (1 - smoke * 0.75)[..., None]
    return img(a).convert("RGBA")


def duotone(im, dark=(18, 22, 30), light=(200, 205, 215), opacity=0.55):
    """Faded monochrome for the memory collage."""
    a = arr(im)
    lum = (a[..., :3].mean(-1, keepdims=True) / 255)
    rgb = np.array(dark, np.float32) + (np.array(light, np.float32) - np.array(dark, np.float32)) * lum
    out = np.dstack([rgb, a[..., 3:4] * opacity])
    return img(out, "RGBA")


def edge_fade(im, left=0, right=0, top=0):
    a = arr(im.getchannel("A"))
    w, h = im.size
    xs, ys = np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32)
    if left:
        a *= np.clip(xs / left, 0, 1)[None, :]
    if right:
        a *= np.clip((w - xs) / right, 0, 1)[None, :]
    if top:
        a *= np.clip(ys / top, 0, 1)[:, None]
    out = im.copy()
    out.putalpha(img(a, "L"))
    return out


def grunge_mask(mask, strength=0.12):
    """Knock fine speckles and light scuffs out of a text/box mask."""
    m = arr(mask) / 255
    n = noise(5, 2)
    holes = np.clip((n - (1 - strength)) / 0.06, 0, 1)
    fine = rng.random((H, W)).astype(np.float32) > 0.992
    m *= (1 - holes * 0.55) * (1 - fine * 0.7)
    return img(m * 255, "L")


def grunge_text(base, txt, x, y, size, fill=(255, 255, 255), shadow=True):
    f = ImageFont.truetype(ANTON, size)
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).text((x, y), txt, font=f, fill=255)
    if shadow:
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sh.putalpha(mask.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.85)))
        base.alpha_composite(sh, (8, 12))
    m = grunge_mask(mask)
    layer = Image.new("RGBA", (W, H), fill + (0,))
    layer.putalpha(m)
    base.alpha_composite(layer)
    return f.getbbox(txt)


def brush_box(base, box, color=RED):
    """Red block with torn, brushed edges."""
    x0, y0, x1, y1 = box
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    pts = []
    for x in np.linspace(x0, x1, 40):
        pts.append((x + rng.normal(0, 4), y0 + rng.normal(0, 9)))
    for y in np.linspace(y0, y1, 14):
        pts.append((x1 + rng.normal(0, 14), y))
    for x in np.linspace(x1, x0, 40):
        pts.append((x + rng.normal(0, 4), y1 + rng.normal(0, 9)))
    for y in np.linspace(y1, y0, 14):
        pts.append((x0 + rng.normal(0, 14), y))
    d.polygon(pts, fill=255)
    for _ in range(18):  # dry-brush streaks off the ends
        yy = rng.uniform(y0 + 10, y1 - 10)
        ln = rng.uniform(20, 70)
        d.line((x1, yy, x1 + ln, yy + rng.normal(0, 2)), fill=255, width=int(rng.uniform(3, 9)))
        yy = rng.uniform(y0 + 10, y1 - 10)
        d.line((x0, yy, x0 - rng.uniform(15, 50), yy), fill=255, width=int(rng.uniform(3, 8)))
    m = grunge_mask(m.filter(ImageFilter.GaussianBlur(1)), 0.1)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh.putalpha(m.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.8)))
    base.alpha_composite(sh, (10, 14))
    layer = Image.new("RGBA", (W, H), color + (0,))
    layer.putalpha(m)
    base.alpha_composite(layer)


def main():
    base = flag_background()

    # LEFT - the start: young Virat, faded, centred over the headline
    yb = load_cut("cut_young.png", 760)
    yb = yb.crop((int(yb.width * 0.12), 0, int(yb.width * 0.88), yb.height))
    yb = duotone(regrade(yb, contrast=1.2), opacity=0.7)
    yb = edge_fade(fade_bottom(yb, 450, 700), left=60, right=60)
    base.alpha_composite(yb, (560 - yb.width // 2, 0))

    # RIGHT - the GOAT, huge and intense
    fc = load_cut("cut_face.png", 1180)
    fc = regrade(fc, color=1.0, contrast=1.22, bright=1.0, sharpen=(1.0, 70, 1))
    fc = tw.directional_light(fc, "left", (255, 210, 160), 0.35)
    fc = edge_fade(fc, left=80)
    place(base, fc, W - fc.width + 120, -60, wrap=0.3, rim_color=(255, 190, 120), rim_side=-1, rim_k=0.4, shadow=0.8)

    # text block, bottom left
    grunge_text(base, "ORDINARY BOY", 60, 590, 150)
    grunge_text(base, "TO", 64, 790, 200)
    brush_box(base, (300, 770, 900, 1035))
    grunge_text(base, "GOAT", 360, 755, 250, shadow=False)
    finish(base, "thumb_goat_v2")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""YouTube thumbnail: "EVERYONE KNEW?" (Sandpaper -> Sabr long-form).

Split like the Dhoni 2007 = 2011? thumbnail: Khawaja (warm light) left, Lehmann (cold light) right, a glowing
crack down the middle with a small tilted yellow sandpaper piece on it, red SANDPAPERGATE tag top-left and
EVERYONE KNEW? bottom-centre (kept clear of the duration badge, bottom-right).
Faces come from Real-ESRGAN 4x upscales of frames in the reference reel.

    python3 thumb_everyone_knew.py  ->  thumb_everyone_knew.png / .jpg (1920x1080), _1280.jpg, _small.png
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "doc_video", "thumb"))
sys.path.insert(0, os.path.join(ROOT, "dhoni_2007_2011"))
import thumb_wc2003 as tw  # noqa: E402
import thumb_dhoni as dh  # noqa: E402
from thumb_wc2003 import ANTON, H, W, arr, fade_bottom, img, place, radial, regrade  # noqa: E402

Y, RED, WHITE = (255, 222, 89), (226, 38, 38), (255, 255, 255)
rng = np.random.default_rng(2018)
dh.TOP_X, dh.BOT_X = 1000, 920   # split line, nearly vertical


def background():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    left = np.zeros((H, W, 3), np.float32) + np.array([18, 10, 6], np.float32)
    left += radial(480, 380, 900, 760, 1.6)[..., None] * np.array([230, 130, 40], np.float32) * 0.55
    left += radial(200, -60, 600, 420, 1.6)[..., None] * np.array([255, 190, 110], np.float32) * 0.35
    right = np.zeros((H, W, 3), np.float32) + np.array([6, 10, 18], np.float32)
    right += radial(1460, 380, 900, 760, 1.6)[..., None] * np.array([60, 110, 170], np.float32) * 0.6
    right += radial(1760, -60, 600, 420, 1.6)[..., None] * np.array([170, 200, 235], np.float32) * 0.3
    m = dh.split_mask()[..., None]
    a = left * (1 - m) + right * m
    a += rng.normal(0, 3.5, (H, W, 1)).astype(np.float32)
    v = 1 - 0.65 * np.clip(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H * 0.42) / (H * 0.8)) ** 2, 0, 1)
    return img(a * v[..., None]).convert("RGBA")


def sandpaper(w=190, h=140, angle=-14):
    """A torn, gritty yellow sandpaper scrap."""
    m = Image.new("L", (w + 40, h + 40), 0)
    d = ImageDraw.Draw(m)
    pts = []
    for x in np.linspace(20, w + 20, 14):
        pts.append((x, 20 + rng.normal(0, 3)))
    for y in np.linspace(20, h + 20, 10):
        pts.append((w + 20 + rng.normal(0, 6), y))   # torn right edge
    for x in np.linspace(w + 20, 20, 14):
        pts.append((x, h + 20 + rng.normal(0, 3)))
    for y in np.linspace(h + 20, 20, 10):
        pts.append((20 + rng.normal(0, 1.5), y))
    d.polygon(pts, fill=255)
    a = np.zeros((h + 40, w + 40, 3), np.float32) + np.array([248, 205, 40], np.float32)
    grit = rng.normal(0, 1, (h + 40, w + 40)).astype(np.float32)
    a += grit[..., None] * 26
    a *= (0.88 + 0.12 * np.linspace(1, 0.8, h + 40))[:, None, None]
    paper = img(a).convert("RGBA")
    paper.putalpha(m)
    paper = paper.rotate(angle, expand=True, resample=Image.BICUBIC)
    pad = 80
    out = Image.new("RGBA", (paper.width + 2 * pad, paper.height + 2 * pad), (0, 0, 0, 0))
    ga = Image.new("L", out.size, 0)
    ga.paste(paper.getchannel("A"), (pad, pad))
    glow = Image.new("RGBA", out.size, Y + (0,))
    glow.putalpha(ga.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(28)).point(lambda v: int(v * 0.8)))
    out.alpha_composite(glow)
    sh = Image.new("RGBA", paper.size, (0, 0, 0, 0))
    sh.putalpha(paper.getchannel("A").filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.7)))
    out.alpha_composite(sh, (pad + 10, pad + 16))
    out.alpha_composite(paper, (pad, pad))
    return out


def tag(base, txt, x, y):
    f = ImageFont.truetype(ANTON, 54)
    track = 5
    w = sum(f.getlength(c) for c in txt) + track * (len(txt) - 1)
    l, t, r, b = f.getbbox(txt)
    box = (x, y, int(x + w + 52), y + (b - t) + 30)
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle((box[0] + 6, box[1] + 8, box[2] + 6, box[3] + 8), fill=(0, 0, 0, 190))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
    d = ImageDraw.Draw(base)
    d.rectangle(box, fill=RED + (255,))
    xx = x + 26 - l
    for c in txt:
        d.text((xx, y + 15 - t), c, font=f, fill=WHITE)
        xx += f.getlength(c) + track


def headline(base, top=845, size=205):
    tw.floor(base, 640)
    f = ImageFont.truetype(ANTON, size)
    parts = [("EVERYONE ", WHITE), ("KNEW", Y), ("?", RED)]
    widths = [f.getlength(t) for t, _ in parts]
    x0 = (W - sum(widths)) / 2 - 40           # nudged left: duration badge sits bottom-right
    l, t, r, b = f.getbbox("EVERYONE")
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
    glow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    x = x0
    for (txt, col), w in zip(parts, widths):
        ImageDraw.Draw(sh).text((x + 8, top - t + 12), txt, font=f, fill=(0, 0, 0, 235), stroke_width=8,
                                stroke_fill=(0, 0, 0, 235))
        if col != WHITE:
            ImageDraw.Draw(glow).text((x, top - t), txt, font=f, fill=col + (160,))
        x += w
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    base.alpha_composite(glow.filter(ImageFilter.GaussianBlur(24)))
    d = ImageDraw.Draw(base)
    x = x0
    for (txt, col), w in zip(parts, widths):
        d.text((x, top - t), txt, font=f, fill=col, stroke_width=5, stroke_fill=(10, 10, 14))
        x += w
    return x0, x


def main():
    base = background()

    # LEFT - Khawaja, serious, to camera; warm key
    k = Image.open(os.path.join(HERE, "cut_khawaja.png")).convert("RGBA")
    k = k.crop((0, 0, k.width, int(k.height * 0.6)))       # head and chin, above the reel's captions
    k = k.resize((int(k.width * 760 / k.height), 760), Image.LANCZOS)
    k = regrade(k, color=1.05, contrast=1.12, bright=1.06, sharpen=(1.0, 60, 1))
    k = tw.directional_light(k, "left", (255, 190, 110), 0.55)
    k = fade_bottom(k, 600, 760)
    kx, ky = 470 - k.width // 2, 40
    place(base, k, kx, ky, wrap=0.4, rim_color=(255, 190, 110), rim_side=-1, rim_k=0.5, shadow=0.7)
    base = dh.face_light(base, k, kx, ky, (470, 400), 240, 0.12)

    # RIGHT - Lehmann, arms crossed, sunglasses; cold key
    lm = Image.open(os.path.join(HERE, "cut_lehmann.png")).convert("RGBA")
    lm = lm.resize((int(lm.width * 1000 / lm.height), 1000), Image.LANCZOS)
    lm = regrade(lm, color=0.85, contrast=1.12, bright=1.0, sharpen=(1.0, 60, 1), tint=(150, 180, 220), tint_k=0.12)
    lm = tw.directional_light(lm, "right", (170, 200, 240), 0.5)
    lm = fade_bottom(lm, 640, 960)
    lx, ly = 1450 - lm.width // 2, 0
    place(base, lm, lx, ly, wrap=0.4, rim_color=(160, 200, 255), rim_side=1, rim_k=0.5, shadow=0.7)

    dh.crack(base)
    sp = sandpaper()
    base.alpha_composite(sp, (960 - sp.width // 2, 610 - sp.height // 2))
    tag(base, "SANDPAPERGATE", 50, 46)
    headline(base)
    tw.HERE = HERE
    tw.finish(base, "thumb_everyone_knew")
    Image.open(os.path.join(HERE, "thumb_everyone_knew.png")).resize((1280, 720), Image.LANCZOS).save(
        os.path.join(HERE, "thumb_everyone_knew_1280.jpg"), quality=94)
    Image.open(os.path.join(HERE, "thumb_everyone_knew.png")).resize((160, 90), Image.LANCZOS).save(
        os.path.join(HERE, "thumb_everyone_knew_160.png"))


if __name__ == "__main__":
    main()

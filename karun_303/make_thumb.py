#!/usr/bin/env python3
"""Final thumbnail for '303* to Dropped': warm 2016 celebration (left 40%) -> cold close-up now (right 60%),
303* (yellow box) -> FORGOTTEN (red box), white arrow between.   python3 make_thumb.py -> out/Karun_303_thumbnail.jpg"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ANTON = os.path.join(ROOT, "doc_video", "thumb", "fonts", "Anton-Regular.woff")
W, H = 1280, 720
SPLIT = 500                                   # left panel ~40%
Y, INK, RED = (255, 222, 89), (14, 14, 16), (222, 32, 38)


def cover(im, w, h, fx=0.5, fy=0.5):
    s = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x, y = int((im.width - w) * fx), int((im.height - h) * fy)
    return im.crop((x, y, x + w, y + h))


def grade(im, mul, add=0, sat=1.0, gamma=1.0):
    a = np.asarray(im, np.float32) / 255
    g = a.mean(2, keepdims=True)
    a = g + (a - g) * sat
    a = np.clip(a, 0, 1) ** gamma
    return Image.fromarray(np.clip((a * np.array(mul) + add) * 255, 0, 255).astype(np.uint8))


def vignette(im, k=0.55, cx=0.5, cy=0.45):
    a = np.asarray(im, np.float32)
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    r = ((xx / w - cx) / 0.7) ** 2 + ((yy / h - cy) / 0.75) ** 2
    return Image.fromarray(np.clip(a * np.clip(1 - k * r, 0.25, 1)[..., None], 0, 255).astype(np.uint8))


def boxed(base, xy, text, size, bg, fg, pad=(22, 12)):
    f = ImageFont.truetype(ANTON, size)
    d = ImageDraw.Draw(base)
    l, t, r, b = d.textbbox((0, 0), text, font=f)
    bw, bh = r - l + 2 * pad[0], b - t + 2 * pad[1]
    box = Image.new("RGBA", (bw, bh), bg + (255,))
    ImageDraw.Draw(box).text((pad[0] - l, pad[1] - t), text, font=f, fill=fg)
    sh = Image.new("RGBA", (bw + 60, bh + 60), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle((30, 30, 30 + bw, 30 + bh), fill=(0, 0, 0, 190))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)), (xy[0] - 22, xy[1] - 18))
    base.alpha_composite(box, xy)
    return (xy[0], xy[1], xy[0] + bw, xy[1] + bh)


def main():
    # right: Karun now, big close-up, cold
    r = Image.open(os.path.join(HERE, "up", "karun_dejected_2025_close.png")).convert("RGB")
    r = cover(r, W - SPLIT + 120, H, 0.5, 0.10)
    r = grade(r, (0.80, 0.90, 1.08), 0.0, sat=0.35, gamma=1.08)
    r = vignette(r, 0.6, 0.45, 0.4)
    # left: 2016, bat raised after the 303*, warm golden
    l = Image.open(os.path.join(HERE, "up", "karun_303_chennai_2016.png")).convert("RGB")
    l = cover(l, SPLIT + 120, H, 0.12, 0.0)
    l = grade(l, (1.18, 1.0, 0.66), 0.04, sat=1.1, gamma=0.92)
    l = vignette(l, 0.35, 0.45, 0.45)
    shifted = Image.new("RGB", l.size)
    shifted.paste(l, (0, 70))
    fill = l.crop((0, 0, l.width, 40)).resize((l.width, 150)).filter(ImageFilter.GaussianBlur(18))
    under = shifted.copy()
    under.paste(fill, (0, 0))
    fm = np.clip((np.arange(l.height) - 80) / 60, 0, 1)[:, None] * np.ones((1, l.width))   # feathered join
    l = Image.composite(shifted, under, Image.fromarray((fm * 255).astype(np.uint8)))

    base = Image.new("RGBA", (W, H))
    base.paste(r, (SPLIT - 120, 0))
    # soft diagonal blend between the two panels
    mask = np.zeros((H, SPLIT + 120), np.float32)
    xx = np.arange(SPLIT + 120)[None, :]
    yy = np.arange(H)[:, None]
    edge = SPLIT + 40 - (yy - H / 2) * 0.12
    mask = np.clip((edge - xx) / 40 + 0.5, 0, 1)
    lm = Image.fromarray((mask * 255).astype(np.uint8))
    base.paste(l, (0, 0), lm)
    # glowing crack on the seam
    seam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ds = ImageDraw.Draw(seam)
    rng = np.random.default_rng(5)
    pts = []
    for y in range(-10, H + 30, 30):
        x = SPLIT + 40 - (y - H / 2) * 0.12 + rng.uniform(-9, 9)
        pts.append((x, y))
    ds.line(pts, fill=(255, 244, 220, 255), width=4)
    base.alpha_composite(seam.filter(ImageFilter.GaussianBlur(9)))
    base.alpha_composite(seam.filter(ImageFilter.GaussianBlur(3)))
    base.alpha_composite(seam)

    # 303*  ->  FORGOTTEN
    b1 = boxed(base, (34, 34), "303*", 150, Y, INK)
    b2 = boxed(base, (812, 40), "FORGOTTEN", 92, RED, (255, 255, 255), pad=(20, 12))
    d = ImageDraw.Draw(base)
    y = (b1[1] + b1[3]) // 2 + 8
    x0, x1 = b1[2] + 26, b2[0] - 22
    arrow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    da = ImageDraw.Draw(arrow)
    da.line([(x0, y), (x1 - 30, y + 4)], fill=(255, 255, 255, 255), width=10)
    da.polygon([(x1, y + 4), (x1 - 42, y - 22), (x1 - 42, y + 30)], fill=(255, 255, 255, 255))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh.alpha_composite(arrow, (4, 6))
    shm = np.asarray(sh, np.float32)
    shm[..., :3] = 0
    base.alpha_composite(Image.fromarray(shm.astype(np.uint8)).filter(ImageFilter.GaussianBlur(5)))
    base.alpha_composite(arrow)

    # UNTOLD STORIES #5, small, 60% white
    f = ImageFont.truetype(ANTON, 34)
    tag = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(tag).text((W - 28, H - 24), "UNTOLD STORIES #5", font=f, fill=(255, 255, 255, 155), anchor="rs")
    base.alpha_composite(tag)

    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    out = os.path.join(HERE, "out", "Karun_303_thumbnail.jpg")
    base.convert("RGB").save(out, quality=93)
    base.convert("RGB").resize((168, 94), Image.LANCZOS).save(os.path.join(HERE, "out", "thumb_tiny.png"))
    print(out, os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    main()

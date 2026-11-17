#!/usr/bin/env python3
"""Thumbnail: 'IPL is dying' (IPL Ko Kisne Maara?) - crime scene. python3 make_thumb.py -> out/thumb.jpg"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ANTON = os.path.join(ROOT, "doc_video", "thumb", "fonts", "Anton-Regular.woff")
LOGO = os.path.join(ROOT, "kohli_countdown", "assets", "logo.png")
W, H = 1280, 720
Y = (255, 222, 89)
INK = (14, 14, 16)


def cover(im, w, h, fx=0.5, fy=0.5):
    s = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x = int((im.width - w) * fx)
    y = int((im.height - h) * fy)
    return im.crop((x, y, x + w, y + h))


def background():
    bg = cover(Image.open(os.path.join(HERE, "up", "stadium.png")).convert("RGB"), W, H, 0.5, 0.42)
    bg = bg.filter(ImageFilter.GaussianBlur(2.2))
    bg = ImageEnhance.Color(bg).enhance(0.75)
    a = np.asarray(bg, np.float32)
    a = a * np.array([0.92, 0.98, 1.08])                      # a little cooler: night / crime-scene mood
    yy, xx = np.mgrid[0:H, 0:W]
    vig = 1 - 0.38 * (((xx - W * 0.6) / (W * 0.75)) ** 2 + ((yy - H * 0.5) / (H * 0.8)) ** 2)
    a = a * np.clip(vig, 0.55, 1)[..., None] * 1.05
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


def shadow(layer, blur=18, off=(0, 10), alpha=0.65):
    a = np.asarray(layer.split()[3], np.float32) * alpha
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    sh.putalpha(Image.fromarray(a.astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur)))
    out = Image.new("RGBA", (layer.width + abs(off[0]), layer.height + abs(off[1])), (0, 0, 0, 0))
    out.alpha_composite(sh, (max(0, off[0]), max(0, off[1])))
    return out


def chalk_outline(layer, gap=16, width=7):
    """Rough white chalk line around a cut-out, like a crime-scene body outline."""
    a = np.asarray(layer.split()[3]) > 100
    pad = gap + width + 4
    a = np.pad(a, pad)
    outer = nd.binary_dilation(a, iterations=gap + width)
    inner = nd.binary_dilation(a, iterations=gap)
    ring = (outer & ~inner).astype(np.float32)
    rng = np.random.default_rng(3)
    ring *= (rng.random(ring.shape) > 0.22)                 # chalk texture
    ring = nd.gaussian_filter(ring, 0.8)
    out = Image.new("RGBA", (a.shape[1], a.shape[0]), (245, 245, 240, 0))
    out.putalpha(Image.fromarray(np.clip(ring * 330, 0, 235).astype(np.uint8)))
    return out, pad


def tape(length, thick, text, angle):
    t = Image.new("RGBA", (length, thick), Y + (255,))
    d = ImageDraw.Draw(t)
    d.rectangle((0, 0, length, 5), fill=(30, 30, 30, 255))
    d.rectangle((0, thick - 6, length, thick), fill=(30, 30, 30, 255))
    f = ImageFont.truetype(ANTON, int(thick * 0.58))
    x = 18
    while x < length:
        d.text((x, thick / 2), text, font=f, fill=INK, anchor="lm")
        x += int(d.textlength(text, font=f)) + 46
    # slight crumple: brightness bands
    a = np.asarray(t, np.float32)
    band = 1 - 0.07 * np.sin(np.linspace(0, 23, length))[None, :, None]
    a[..., :3] *= band
    t = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    return t.rotate(angle, expand=True, resample=Image.BICUBIC)


def text_block(base):
    d = ImageDraw.Draw(base)
    f1 = ImageFont.truetype(ANTON, 132)
    # line 1 "WHO" white, line 2 "KILLED IT?" with KILLED in a yellow box
    x0, y0 = 600, 26
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ds = ImageDraw.Draw(sh)
    for dx, dy in [(0, 6)]:
        ds.text((x0 + dx, y0 + dy), "WHO", font=f1, fill=(0, 0, 0, 200))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    d.text((x0, y0), "WHO", font=f1, fill=(255, 255, 255))
    wk = d.textlength("KILLED", font=f1)
    y1 = y0 + 150
    pad = 16
    box = Image.new("RGBA", (int(wk + 2 * pad), 160), Y + (255,))
    base.alpha_composite(shadow(box, 10, (0, 8), 0.55), (x0 - pad, y1 + 4))
    base.alpha_composite(box, (x0 - pad, y1 + 4))
    d.text((x0, y1 - 6), "KILLED", font=f1, fill=INK)
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((x0 + wk + 34, y1 - 6 + 6), "IT?", font=f1, fill=(0, 0, 0, 200))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    d.text((x0 + wk + 34, y1 - 6), "IT?", font=f1, fill=(255, 255, 255))


def main():
    base = background()

    # trophy: the "body", tilted as if knocked over, chalk outline around it
    tr = Image.open(os.path.join(HERE, "cut", "trophy.png"))
    th = 370
    tr = tr.resize((round(tr.width * th / tr.height), th), Image.LANCZOS)
    tr = ImageEnhance.Contrast(tr).enhance(1.08)
    tr = tr.rotate(-14, expand=True, resample=Image.BICUBIC)
    tx, ty = 1060 - tr.width // 2, 730 - tr.height
    ch, pad = chalk_outline(tr)
    base.alpha_composite(ch, (tx - pad, ty - pad))
    base.alpha_composite(shadow(tr, 16, (10, 14), 0.7), (tx, ty))
    base.alpha_composite(tr, (tx, ty))

    # Kohli: the witness, looking up at the question
    k = Image.open(os.path.join(HERE, "cut", "kohli.png"))
    k = k.crop(k.getbbox())
    kh = 760
    k = k.resize((round(k.width * kh / k.height), kh), Image.LANCZOS)
    k = ImageEnhance.Contrast(k).enhance(1.06)
    kx, ky = 250 - k.width // 2, H - kh + 70
    # rim light so he doesn't look pasted on
    rim = Image.new("RGBA", k.size, (255, 236, 170, 0))
    ra = np.asarray(k.split()[3], np.float32)
    edge = np.clip(ra - nd.uniform_filter(ra, 9), 0, 255) * 1.6
    rim.putalpha(Image.fromarray(np.clip(edge, 0, 160).astype(np.uint8)))
    base.alpha_composite(shadow(k, 34, (6, 0), 0.3), (kx, ky))
    base.alpha_composite(k, (kx, ky))
    base.alpha_composite(rim, (kx, ky))

    # police tape across the scene, in front of the trophy
    t1 = tape(1100, 56, "CRIME SCENE  •  DO NOT CROSS", 9)
    base.alpha_composite(shadow(t1, 8, (0, 6), 0.5), (520, 520))
    base.alpha_composite(t1, (520, 520))

    text_block(base)

    logo = Image.open(LOGO).convert("RGBA")
    logo = logo.resize((150, round(logo.height * 150 / logo.width)), Image.LANCZOS)
    base.alpha_composite(logo, (W - 150 - 26, 22))

    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    base.convert("RGB").save(os.path.join(HERE, "out", "thumb.jpg"), quality=94)
    base.convert("RGB").resize((320, 180), Image.LANCZOS).save(os.path.join(HERE, "out", "thumb_small.jpg"), quality=90)


if __name__ == "__main__":
    main()

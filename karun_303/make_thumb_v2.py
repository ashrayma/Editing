#!/usr/bin/env python3
"""Karun '303* -> FORGOTTEN' thumbnail, v2: real 303* celebration (warm gold, rays, confetti) vs a tight 2025
face (cold teal, rim light, haze), glowing jagged crack, tilted 3D text, curved arrow, branded badge.
python3 make_thumb_v2.py -> out/Karun_303_thumbnail_v2.jpg"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ANTON = os.path.join(ROOT, "doc_video", "thumb", "fonts", "Anton-Regular.woff")
STADIUM = os.path.join(ROOT, "ipl_killed", "thumb", "up", "stadium.png")
W, H = 1280, 720
Y, INK, RED = (255, 222, 89), (14, 14, 16), (222, 32, 38)
rng = np.random.default_rng(11)


def cover(im, w, h, fx=0.5, fy=0.5):
    s = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x, y = int((im.width - w) * fx), int((im.height - h) * fy)
    return im.crop((x, y, x + w, y + h))


def crack_x(y):
    """Jagged seam position at row y (about 40% across, leaning slightly)."""
    base = 505 - (y - H / 2) * 0.10
    return base + 14 * math.sin(y / 23.0) + 9 * math.sin(y / 7.3 + 1.0)


def background():
    bg = cover(Image.open(STADIUM).convert("RGB"), W, H, 0.5, 0.3).filter(ImageFilter.GaussianBlur(10))
    a = np.asarray(bg, np.float32) / 255
    lum = a.mean(2, keepdims=True)
    warm = np.clip(lum * np.array([1.55, 1.05, 0.45]) * 1.15 + np.array([0.10, 0.05, 0.0]), 0, 1)
    cold = np.clip(lum * np.array([0.35, 0.62, 0.80]) * 0.85, 0, 1)
    xx = np.arange(W)[None, :]
    seam = np.array([crack_x(y) for y in range(H)])[:, None]
    left = (xx < seam).astype(np.float32)[..., None]
    out = warm * left + cold * (1 - left)
    yy, xg = np.mgrid[0:H, 0:W]
    # light rays fanning from behind the celebrating Karun (left)
    ang = np.arctan2(yy - 120, xg - 250)
    rays = (0.5 + 0.5 * np.cos(ang * 18)) ** 6 * np.exp(-((xg - 250) ** 2 + (yy - 120) ** 2) / (2 * 380 ** 2))
    out += (rays * left[..., 0])[..., None] * np.array([1.0, 0.75, 0.3]) * 0.55
    # heavy vignette on the cold side, soft on the warm side
    r = ((xg - 880) / 520) ** 2 + ((yy - 320) / 420) ** 2
    out *= np.clip(1 - 0.75 * r, 0.15, 1)[..., None] * (1 - left) + np.clip(1 - 0.25 * (((xg - 250) / 500) ** 2 + ((yy - 300) / 450) ** 2), 0.5, 1)[..., None] * left
    return Image.fromarray(np.clip(out * 255, 0, 255).astype(np.uint8)).convert("RGBA"), left[..., 0]


def tone(im, mul, sat, contrast=1.2, sharpen=110):
    a = im.split()[3]
    rgb = im.convert("RGB")
    x = np.asarray(rgb, np.float32) / 255
    g = x.mean(2, keepdims=True)
    x = np.clip(g + (x - g) * sat, 0, 1) * np.array(mul)
    rgb = Image.fromarray(np.clip(x * 255, 0, 255).astype(np.uint8))
    rgb = ImageEnhance.Contrast(rgb).enhance(contrast)
    if sharpen:
        rgb = rgb.filter(ImageFilter.UnsharpMask(radius=2.0, percent=sharpen, threshold=3))
    out = rgb.convert("RGBA")
    out.putalpha(a)
    return out


def place_person(base, im, x, y, rim, rim_glow, shadow_off):
    full = Image.new("L", (W, H), 0)
    full.paste(im.split()[3], (x, y))
    fa = np.asarray(full, np.float32) / 255
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh.putalpha(Image.fromarray((fa * 190).astype(np.uint8)).filter(ImageFilter.GaussianBlur(22)))
    shifted = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shifted.alpha_composite(sh, shadow_off)
    base.alpha_composite(shifted)
    ring = np.clip(nd.binary_dilation(fa > 0.5, iterations=4).astype(np.float32) - fa, 0, 1)
    glow = Image.new("RGBA", (W, H), rim_glow + (0,))
    glow.putalpha(Image.fromarray(np.clip(nd.gaussian_filter(ring, 14) * 520, 0, 170).astype(np.uint8)))
    base.alpha_composite(glow)
    line = Image.new("RGBA", (W, H), rim + (0,))
    line.putalpha(Image.fromarray(np.clip(nd.gaussian_filter(ring, 1.1) * 255, 0, 220).astype(np.uint8)))
    base.alpha_composite(line)
    base.alpha_composite(im, (x, y))


def confetti(base, left_mask):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for _ in range(70):
        x, y = rng.uniform(0, 470), rng.uniform(0, H)
        if left_mask[int(min(y, H - 1)), int(min(x, W - 1))] < 0.5:
            continue
        w, h = rng.uniform(5, 11), rng.uniform(3, 6)
        col = [(255, 214, 90), (255, 236, 160), (255, 170, 60)][rng.integers(0, 3)]
        piece = Image.new("RGBA", (int(w * 2), int(w * 2)), (0, 0, 0, 0))
        ImageDraw.Draw(piece).rectangle((w / 2, w - h / 2, w * 1.5, w + h / 2), fill=col + (int(rng.uniform(140, 230)),))
        piece = piece.rotate(rng.uniform(0, 180), resample=Image.BICUBIC)
        lay.alpha_composite(piece, (int(x), int(y)))
    base.alpha_composite(lay.filter(ImageFilter.GaussianBlur(0.6)))


def haze(base, left_mask):
    lay = np.zeros((H, W), np.float32)
    for _ in range(140):                                          # thin dark-blue rain streaks
        x, y, l = rng.uniform(480, W), rng.uniform(-40, H), rng.uniform(30, 70)
        xs = np.linspace(x, x - l * 0.25, 30).astype(int)
        ys = np.linspace(y, y + l, 30).astype(int)
        ok = (xs >= 0) & (xs < W) & (ys >= 0) & (ys < H)
        lay[ys[ok], xs[ok]] = rng.uniform(0.25, 0.55)
    smoke = nd.gaussian_filter(rng.random((H // 8, W // 8)).astype(np.float32), 3)
    smoke = np.kron(smoke, np.ones((8, 8)))[:H, :W]
    smoke = np.clip((smoke - smoke.mean()) * 6 + 0.25, 0, 0.5)
    a = (nd.gaussian_filter(lay, 0.6) * 0.8 + smoke * 0.45) * (1 - left_mask)
    lay_img = Image.new("RGBA", (W, H), (150, 190, 215, 0))
    lay_img.putalpha(Image.fromarray(np.clip(a * 255, 0, 160).astype(np.uint8)))
    base.alpha_composite(lay_img)


def crack(base):
    pts = [(crack_x(y), y) for y in range(-20, H + 21, 6)]
    for col, dx in (((255, 140, 30), -5), ((70, 170, 255), 5)):
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(lay).line([(x + dx, y) for x, y in pts], fill=col + (255,), width=8)
        base.alpha_composite(lay.filter(ImageFilter.GaussianBlur(14)))
        base.alpha_composite(lay.filter(ImageFilter.GaussianBlur(4)))
    core = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(core).line(pts, fill=(255, 250, 235, 255), width=3)
    base.alpha_composite(core)
    sp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sp)
    for _ in range(26):
        y = rng.uniform(0, H)
        x = crack_x(y) + rng.normal(0, 16)
        r = rng.uniform(1.5, 3.5)
        ds.ellipse((x - r, y - r, x + r, y + r), fill=(255, 220, 150, int(rng.uniform(150, 255))))
    base.alpha_composite(sp.filter(ImageFilter.GaussianBlur(0.8)))


def tilted_box(text, size, bg, fg, angle, pad=(24, 12), distress=False):
    f = ImageFont.truetype(ANTON, size)
    tmp = ImageDraw.Draw(Image.new("L", (1, 1)))
    l, t, r, b = tmp.textbbox((0, 0), text, font=f)
    bw, bh = r - l + 2 * pad[0], b - t + 2 * pad[1]
    box = Image.new("RGBA", (bw, bh), bg + (255,))
    ImageDraw.Draw(box).text((pad[0] - l, pad[1] - t), text, font=f, fill=fg + (255,))
    if distress:                                                  # worn, half-faded: 'forgotten'
        a = np.asarray(box, np.float32)
        n = nd.gaussian_filter(rng.random((bh, bw)).astype(np.float32), 1.2)
        n2 = nd.gaussian_filter(rng.random((bh, bw)).astype(np.float32), 6)
        wear = np.clip((n - 0.55) * 7, 0, 1) * 0.85 + np.clip((n2 - 0.52) * 10, 0, 1) * 0.35
        fade = np.linspace(1.0, 0.72, bw)[None, :]
        a[..., 3] *= np.clip(1 - wear, 0.05, 1) * fade
        box = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    return box.rotate(angle, expand=True, resample=Image.BICUBIC)


def drop(base, im, xy, off=(9, 11), blur=6, alpha=0.85, glow=None):
    a = np.asarray(im.split()[3], np.float32)
    if glow:
        g = Image.new("RGBA", im.size, glow + (0,))
        g.putalpha(Image.fromarray((a * 0.8).astype(np.uint8)).filter(ImageFilter.GaussianBlur(18)))
        pad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        pad.alpha_composite(g, xy)
        base.alpha_composite(pad)
    s = Image.new("RGBA", im.size, (0, 0, 0, 0))
    s.putalpha(Image.fromarray((a * alpha).astype(np.uint8)))
    pad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pad.alpha_composite(s, (xy[0] + off[0], xy[1] + off[1]))
    base.alpha_composite(pad.filter(ImageFilter.GaussianBlur(blur)))
    base.alpha_composite(im, xy)


def curved_arrow(base, p0, p1, bulge=-70):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 + bulge
    ts = np.linspace(0, 1, 60)
    pts = [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * mx + t ** 2 * p1[0],
            (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * my + t ** 2 * p1[1]) for t in ts]
    d.line(pts[:-6], fill=(255, 255, 255, 255), width=12, joint="curve")
    (ax, ay), (bx, by) = pts[-9], pts[-1]
    v = np.array([bx - ax, by - ay]); v /= np.linalg.norm(v)
    n = np.array([-v[1], v[0]]); tip = np.array([bx, by])
    d.polygon([tuple(tip + v * 6), tuple(tip - v * 44 + n * 30), tuple(tip - v * 44 - n * 30)], fill=(255, 255, 255, 255))
    base.alpha_composite(lay.filter(ImageFilter.GaussianBlur(12)))
    base.alpha_composite(lay)


def badge(base, text, right, bottom):
    f = ImageFont.truetype(ANTON, 30)
    d = ImageDraw.Draw(base)
    l, t, r, b = d.textbbox((0, 0), text, font=f)
    bw, bh = r - l + 44, b - t + 22
    x0, y0 = right - bw, bottom - bh
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    dl.rectangle((x0, y0, right, bottom), fill=(14, 14, 18, 200))
    dl.rectangle((x0, y0, x0 + 8, bottom), fill=Y + (255,))
    dl.text((x0 + 24 - l, y0 + 11 - t), text, font=f, fill=(255, 255, 255, 235))
    base.alpha_composite(lay)


def main():
    base, left = background()
    confetti(base, left)
    haze(base, left)

    # right: Karun now, tight on the face, cold teal, blue rim light
    now = Image.open(os.path.join(HERE, "cut", "karun_now_face.png"))
    nh = 1060
    now = now.resize((round(now.width * nh / now.height), nh), Image.LANCZOS)
    now = tone(now, (0.72, 0.92, 1.02), 0.40, 1.18, sharpen=60)
    place_person(base, now, 400, -60, (170, 215, 255), (60, 140, 255), (-18, 8))

    # left: the 303* moment, warm gold
    cel = Image.open(os.path.join(HERE, "cut", "celebrate_303.png"))
    cel = cel.crop((470, 0, 1300, 992))                 # body and both raised arms, not the empty frame edges
    ch = 640
    cel = cel.resize((round(cel.width * ch / cel.height), ch), Image.LANCZOS)
    cel = tone(cel, (1.22, 0.92, 0.58), 0.45, 1.12, sharpen=40)
    place_person(base, cel, 250 - cel.width // 2, H - ch + 30, (255, 236, 190), (255, 190, 60), (18, 8))

    crack(base)

    # 303*  (-5 deg, 3D shadow, yellow glow)  ->  FORGOTTEN (+4 deg, distressed)
    b1 = tilted_box("303*", 170, Y, INK, 5)
    drop(base, b1, (26, 18), glow=(255, 215, 80))
    b2 = tilted_box("FORGOTTEN", 96, RED, (255, 255, 255), -4, distress=True)
    drop(base, b2, (W - b2.width - 34, 28), off=(7, 9))
    curved_arrow(base, (26 + b1.width + 6, 110), (W - b2.width - 44, 96), bulge=-60)

    badge(base, "UNTOLD STORIES #5", W - 24, H - 22)

    out = os.path.join(HERE, "out", "Karun_303_thumbnail_v2.jpg")
    base.convert("RGB").save(out, quality=93)
    base.convert("RGB").resize((168, 94), Image.LANCZOS).save(os.path.join(HERE, "out", "thumb_v2_tiny.png"))
    print(out, os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    main()

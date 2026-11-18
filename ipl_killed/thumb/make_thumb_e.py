#!/usr/bin/env python3
"""Thumbnail E for 'IPL is dying' (reference-style 'downfall' look, our own build):
fan on his phone in blue light (left), an evidence screen of empty stands with a red chart crashing (centre),
worried Kohli (right), huge two-tone 'WHO KILLED IPL?' across the bottom.   python3 make_thumb_e.py"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from scipy import ndimage as nd

from make_thumb import ANTON, HERE, INK, LOGO, W, H, Y, cover
from make_thumb_220 import soft_shadow
from make_thumb_cd import down_tag, ipl_badge

RED = (232, 30, 36)


def room():
    a = np.zeros((H, W, 3), np.float32) + np.array([11, 11, 14])
    yy, xx = np.mgrid[0:H, 0:W]
    for x0 in (0, W):                                                    # red light bleeding in from both edges
        d = np.abs(xx - x0) / 160
        a += np.exp(-d ** 2)[..., None] * np.array([150, 10, 14])
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


def screen(base, box):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    im = cover(Image.open(os.path.join(HERE, "up", "empty_seats.png")).convert("L"), w, h, 0.5, 0.4).convert("RGB")
    a = np.asarray(im, np.float32) * 0.55
    a[::5] *= 0.55                                                       # scanlines
    # red area chart crashing down to the right
    xs = np.linspace(0, w, 11)
    ys = np.array([0.30, 0.22, 0.34, 0.26, 0.40, 0.35, 0.52, 0.48, 0.66, 0.74, 0.86]) * h
    curve = np.interp(np.arange(w), xs, ys)
    yy = np.arange(h)[:, None]
    fill = (yy > curve[None, :]).astype(np.float32)
    a = a * (1 - 0.72 * fill[..., None]) + np.array(RED) * 0.72 * fill[..., None]
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    pts = list(zip(xs, ys))
    d.line(pts, fill=(255, 80, 80, 255), width=7, joint="curve")
    (ax, ay), (bx, by) = pts[-2], pts[-1]
    v = np.array([bx - ax, by - ay]); v /= np.linalg.norm(v)
    nrm = np.array([-v[1], v[0]]); tip = np.array([bx - 6, by])
    d.polygon([tuple(tip + v * 8), tuple(tip - v * 46 + nrm * 30), tuple(tip - v * 46 - nrm * 30)], fill=(255, 80, 80, 255))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), 14, fill=255)
    img.putalpha(mask)
    full = Image.new("L", base.size, 0)
    full.paste(mask, (x0, y0))
    base.alpha_composite(soft_shadow(full, (0, 14), 26, 0.8))
    base.alpha_composite(img, (x0, y0))
    ImageDraw.Draw(base).rounded_rectangle(box, 14, outline=(60, 60, 66, 255), width=3)


def fan(base):
    f = Image.open(os.path.join(HERE, "cut", "fan_phone.png"))
    f = f.crop((int(f.width * 0.30), 0, int(f.width * 0.80), int(f.height * 0.86)))
    fh = 540
    f = f.resize((round(f.width * fh / f.height), fh), Image.LANCZOS)
    a = f.split()[3]
    g = np.asarray(f.convert("L"), np.float32)[..., None] * np.array([0.42, 0.46, 0.62])   # cold, dim
    # blue phone glow on the face and hands (the phone sits left-centre of this crop)
    yy, xx = np.mgrid[0:f.height, 0:f.width]
    glow = np.exp(-(((xx - f.width * 0.22) / (f.width * 0.32)) ** 2 + ((yy - f.height * 0.42) / (f.height * 0.38)) ** 2))
    g += glow[..., None] * np.array([40, 70, 230]) * 0.75
    f = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).convert("RGBA")
    f.putalpha(a)
    f = f.transpose(Image.FLIP_LEFT_RIGHT)                               # face turned toward the screen
    x, y = -40, H - fh - 70
    full = Image.new("L", base.size, 0)
    full.paste(a.transpose(Image.FLIP_LEFT_RIGHT), (x, y))
    base.alpha_composite(soft_shadow(full, (16, 6), 18, 0.7))
    base.alpha_composite(f, (x, y))


def kohli(base):
    k = Image.open(os.path.join(HERE, "cut", "kohli.png"))
    k = k.crop(k.getbbox())
    kh = 800
    k = k.resize((round(k.width * kh / k.height), kh), Image.LANCZOS)
    a = k.split()[3]
    rgb = ImageEnhance.Contrast(k.convert("RGB")).enhance(1.12).filter(ImageFilter.UnsharpMask(radius=2, percent=70, threshold=2))
    k = rgb.convert("RGBA")
    k.putalpha(a)
    x, y = W - k.width + 70, H - kh + 40
    full = Image.new("L", base.size, 0)
    full.paste(a, (x, y))
    base.alpha_composite(soft_shadow(full, (-20, 6), 22, 0.75))
    fa = np.asarray(full, np.float32) / 255
    ring = nd.gaussian_filter(np.clip(nd.binary_dilation(fa > 0.5, iterations=4).astype(np.float32) - fa, 0, 1), 1.2)
    rl = Image.new("RGBA", base.size, (255, 120, 110, 0))
    rl.putalpha(Image.fromarray(np.clip(ring * 255, 0, 200).astype(np.uint8)))
    base.alpha_composite(rl)
    base.alpha_composite(k, (x, y))


def gradient_text(base, xy, txt, font, top, bot, stroke=6):
    m = Image.new("L", base.size, 0)
    ImageDraw.Draw(m).text(xy, txt, font=font, fill=255, anchor="ls")
    ma = np.asarray(m, np.float32) / 255
    base.alpha_composite(soft_shadow(m, (8, 10), 6, 0.9))
    ol = nd.binary_dilation(ma > 0.5, iterations=stroke).astype(np.float32)
    o = Image.new("RGBA", base.size, INK + (0,))
    o.putalpha(Image.fromarray((nd.gaussian_filter(ol, 0.8) * 255).astype(np.uint8)))
    base.alpha_composite(o)
    ys = np.nonzero(ma.max(1) > 0.5)[0]
    t = np.clip((np.arange(H) - ys.min()) / max(1, ys.max() - ys.min()), 0, 1)
    col = np.array(top) * (1 - t[:, None]) + np.array(bot) * t[:, None]
    fill = np.zeros((H, W, 4), np.float32)
    fill[..., :3] = col[:, None, :]
    fill[..., 3] = ma * 255
    base.alpha_composite(Image.fromarray(fill.astype(np.uint8)))
    return m.getbbox()


def graph_bg(base):
    """Full-frame background: faint empty stands, a translucent red area chart crashing to the right, glowing line."""
    st = cover(Image.open(os.path.join(HERE, "up", "empty_seats.png")).convert("L"), W, H, 0.5, 0.4)
    st = np.asarray(st.filter(ImageFilter.GaussianBlur(3)), np.float32)[..., None] * np.array([0.20, 0.20, 0.24])
    a = np.asarray(base, np.float32)[..., :3] * 0.6 + st
    xs = np.linspace(-20, 1000, 11)
    ys = np.array([0.24, 0.17, 0.28, 0.22, 0.36, 0.32, 0.47, 0.43, 0.58, 0.64, 0.74]) * H
    curve = np.interp(np.arange(W), xs, ys)
    yy = np.arange(H)[:, None]
    fill = (yy > curve[None, :]).astype(np.float32)
    fade = np.clip((yy - curve[None, :]) / 230, 0, 1)                # strongest just under the line, gone by the text
    alpha = fill * 0.40 * (1 - fade) * (np.arange(W)[None, :] < 1000)
    a = a * (1 - alpha[..., None]) + np.array(RED) * alpha[..., None]
    a[::4] *= 0.86                                                     # faint scanlines
    band = np.clip((yy - 470) / 140, 0, 1)[..., None] if False else np.clip((np.arange(H)[:, None] - 470) / 140, 0, 1)[..., None]
    a *= 1 - 0.55 * band                                               # dark band under the headline
    out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    pts = list(zip(xs, ys))
    d.line(pts, fill=(255, 70, 70, 255), width=11, joint="curve")
    for p in pts[2:9:2]:
        d.ellipse((p[0] - 10, p[1] - 10, p[0] + 10, p[1] + 10), fill=(255, 230, 230, 255), outline=(255, 70, 70, 255), width=5)
    (ax, ay), (bx, by) = pts[-2], pts[-1]
    v = np.array([bx - ax, by - ay]); v /= np.linalg.norm(v)
    nrm = np.array([-v[1], v[0]]); tip = np.array([bx, by])
    d.polygon([tuple(tip + v * 10), tuple(tip - v * 54 + nrm * 36), tuple(tip - v * 54 - nrm * 36)], fill=(255, 70, 70, 255))
    halo = lay.filter(ImageFilter.GaussianBlur(20))
    out.alpha_composite(halo)
    out.alpha_composite(halo)
    out.alpha_composite(lay)
    return out


def main():
    base = graph_bg(room())
    ipl_badge(base, cx=110, cy=120, d=150)
    w1 = down_tag(base, 216, 84, "VIEWERS")
    down_tag(base, 216 + w1 + 20, 84, "TRP")
    kohli(base)
    f = ImageFont.truetype(ANTON, 150)
    l, t, r, b = gradient_text(base, (34, 690), "WHO KILLED", f, (255, 255, 255), (150, 150, 158))
    gradient_text(base, (r + 26, 690), "IPL?", f, (255, 70, 60), (170, 10, 14))
    logo = Image.open(LOGO).convert("RGBA")
    logo = logo.resize((130, round(logo.height * 130 / logo.width)), Image.LANCZOS)
    base.alpha_composite(logo, (W - 130 - 22, 20))
    out = os.path.join(HERE, "out", "IPL_is_dying_thumbnail_E_downfall.jpg")
    base.convert("RGB").save(out, quality=93)
    base.convert("RGB").resize((168, 94), Image.LANCZOS).save(out.replace(".jpg", "_tiny.png"))
    print(out, os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    main()

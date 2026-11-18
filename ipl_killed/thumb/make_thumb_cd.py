#!/usr/bin/env python3
"""Thumbnails C and D for 'IPL is dying': worried Kohli left, WHO KILLED / IPL? right, a red line behind.
C = falling graph, D = heartbeat (ECG) that flatlines.   python3 make_thumb_cd.py"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from scipy import ndimage as nd

from make_thumb import ANTON, HERE, INK, LOGO, W, H, Y, cover
from make_thumb_220 import RED, big_number, outlined, soft_shadow


def background():
    bg = cover(Image.open(os.path.join(HERE, "up", "stadium.png")).convert("RGB"), W, H, 0.5, 0.35)
    bg = bg.filter(ImageFilter.GaussianBlur(12))
    a = np.asarray(bg, np.float32) * np.array([0.42, 0.30, 0.36])          # dark, red-leaning
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W * 0.55) / (W * 0.6)) ** 2 + ((yy - H * 0.5) / (H * 0.7)) ** 2)
    edge = np.clip((r - 0.35) / 0.8, 0, 1)[..., None]
    a = a * (1 - 0.5 * edge) + np.array([120, 12, 18]) * 0.5 * edge        # red tint toward the edges
    a *= np.clip(1 - 0.5 * r ** 2 * 0.6, 0.45, 1)[..., None]              # vignette
    # faint chart grid
    g = np.zeros((H, W), np.float32)
    g[::72, :] = 1
    g[:, ::72] = 1
    a += nd.gaussian_filter(g, 0.6)[..., None] * np.array([60, 30, 34]) * 0.35
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


def glow_line(base, pts, width=12, color=(235, 45, 45), glow=22, dots=None, arrow=False):
    """Red line with a soft glow; optional bright dots at chart points."""
    lay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.line(pts, fill=color + (255,), width=width, joint="curve")
    if arrow:                                       # arrowhead on the last segment
        (x0, y0), (x1, y1) = pts[-2], pts[-1]
        v = np.array([x1 - x0, y1 - y0], float)
        v /= np.linalg.norm(v)
        nrm = np.array([-v[1], v[0]])
        tip = np.array([x1, y1])
        d.polygon([tuple(tip + v * 10), tuple(tip - v * 52 + nrm * 34), tuple(tip - v * 52 - nrm * 34)], fill=color + (255,))
    for p in dots or []:
        d.ellipse((p[0] - 11, p[1] - 11, p[0] + 11, p[1] + 11), fill=(255, 230, 230, 255), outline=color + (255,), width=5)
    halo = lay.filter(ImageFilter.GaussianBlur(glow))
    base.alpha_composite(halo)
    base.alpha_composite(halo)
    base.alpha_composite(lay)


def kohli(base):
    k = Image.open(os.path.join(HERE, "cut", "kohli.png"))
    k = k.crop(k.getbbox())
    kh = 780
    k = k.resize((round(k.width * kh / k.height), kh), Image.LANCZOS)
    a = k.split()[3]
    rgb = ImageEnhance.Contrast(k.convert("RGB")).enhance(1.12).filter(ImageFilter.UnsharpMask(radius=2, percent=70, threshold=2))
    k = rgb.convert("RGBA")
    k.putalpha(a)
    kx, ky = 255 - k.width // 2, H - kh + 60
    full = Image.new("L", (W, H), 0)
    full.paste(a, (kx, ky))
    base.alpha_composite(soft_shadow(full, (22, 6), 20, 0.7))
    fa = np.asarray(full, np.float32) / 255
    ring = nd.gaussian_filter(np.clip(nd.binary_dilation(fa > 0.5, iterations=4).astype(np.float32) - fa, 0, 1), 1.2)
    rl = Image.new("RGBA", (W, H), (255, 236, 210, 0))
    rl.putalpha(Image.fromarray(np.clip(ring * 255, 0, 210).astype(np.uint8)))
    base.alpha_composite(rl)
    base.alpha_composite(k, (kx, ky))


def headline(base, cx=900):
    f1 = ImageFont.truetype(ANTON, 128)
    outlined(base, (cx, 150), "WHO KILLED", f1, (255, 255, 255), INK, 5)
    big_number(base, "IPL?", cx, 395, 300)


def finish(base, name):
    logo = Image.open(LOGO).convert("RGBA")
    logo = logo.resize((140, round(logo.height * 140 / logo.width)), Image.LANCZOS)
    base.alpha_composite(logo, (W - 140 - 24, 22))
    out = os.path.join(HERE, "out", name)
    base.convert("RGB").save(out, quality=93)
    base.convert("RGB").resize((168, 94), Image.LANCZOS).save(out.replace(".jpg", "_tiny.png"))
    print(out, os.path.getsize(out) // 1024, "KB")


def thumb_c():
    base = background()
    # falling graph: rises a little, peaks, then crashes to the bottom right
    pts = [(-20, 300), (150, 250), (300, 180), (420, 230), (560, 200), (700, 330), (820, 300), (960, 470), (1090, 560),
           (1215, 650)]
    glow_line(base, pts, dots=pts[2:9:2], arrow=True)
    kohli(base)
    headline(base)
    finish(base, "IPL_is_dying_thumbnail_C_graph.jpg")


def thumb_d():
    base = background()
    # heartbeat: regular beats on the left, weaker, then a flat line on the right
    y0 = 560
    pts = [(-20, y0)]
    x = 0
    for amp in [1.0, 0.95, 0.75, 0.5, 0.28]:
        pts += [(x + 40, y0), (x + 60, y0 - 26 * amp), (x + 80, y0), (x + 96, y0 + 30 * amp), (x + 112, y0 - 190 * amp),
                (x + 130, y0 + 70 * amp), (x + 148, y0), (x + 190, y0 - 34 * amp), (x + 220, y0)]
        x += 210
    pts += [(1300, y0)]
    glow_line(base, pts, width=11)
    kohli(base)
    headline(base)
    finish(base, "IPL_is_dying_thumbnail_D_flatline.jpg")


if __name__ == "__main__":
    thumb_c()
    thumb_d()

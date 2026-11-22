#!/usr/bin/env python3
"""Karun thumbnail v3: one face, one number (the Bumrah '220' structure).
Huge yellow 303* + red grunge FORGOTTEN on the left, the frowning 2025 close-up big on the right, dark navy.
python3 make_thumb_v3.py -> out/Karun_303_thumbnail_v3.jpg"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage as nd

import make_thumb_v2 as V

W, H, Y, INK, RED = V.W, V.H, V.Y, V.INK, V.RED


def background():
    yy, xx = np.mgrid[0:H, 0:W]
    a = np.zeros((H, W, 3), np.float32) + np.array([10, 16, 34])                       # dark navy
    glow = np.exp(-(((xx - 960) / 300) ** 2 + ((yy - 250) / 260) ** 2))[..., None]     # soft blue glow behind his head
    a += glow * np.array([40, 95, 170])
    r = ((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2
    a *= np.clip(1 - 0.45 * r, 0.45, 1)[..., None]                                    # light vignette
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


def huge_number(base, txt, x, y_base, size):
    """Bright yellow, no box, thick dark outline, drop shadow (left-aligned at x, baseline y_base)."""
    f = ImageFont.truetype(V.ANTON, size)
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).text((x, y_base), txt, font=f, fill=255, anchor="ls")
    ma = np.asarray(m, np.float32) / 255
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh.putalpha(Image.fromarray((ma * 230).astype(np.uint8)))
    pad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pad.alpha_composite(sh, (10, 14))
    base.alpha_composite(pad.filter(ImageFilter.GaussianBlur(10)))
    ol = nd.gaussian_filter(nd.binary_dilation(ma > 0.5, iterations=9).astype(np.float32), 0.8)
    o = Image.new("RGBA", (W, H), INK + (0,))
    o.putalpha(Image.fromarray((ol * 255).astype(np.uint8)))
    base.alpha_composite(o)
    ys = np.nonzero(ma.max(1) > 0.5)[0]
    t = np.clip((np.arange(H) - ys.min()) / max(1, ys.max() - ys.min()), 0, 1)[:, None]
    col = np.array([255, 232, 110]) * (1 - t) + np.array([255, 196, 40]) * t        # bright yellow, a touch deeper low
    fill = np.zeros((H, W, 4), np.float32)
    fill[..., :3] = col[:, None, :] * np.ones((1, W, 1))
    fill[..., 3] = ma * 255
    base.alpha_composite(Image.fromarray(fill.astype(np.uint8)))
    return m.getbbox()


def main():
    base = background()
    # the frowning 2025 close-up, right half, nothing overlapping it
    now = Image.open(os.path.join(V.HERE, "cut", "karun_now_face.png"))
    nh = 1060
    now = now.resize((round(now.width * nh / now.height), nh), Image.LANCZOS)
    now = V.tone(now, (0.78, 0.94, 1.04), 0.45, 1.18, sharpen=60)
    V.place_person(base, now, 525, -60, (170, 215, 255), (60, 140, 255), (-18, 8))

    l, t, r, b = huge_number(base, "303*", 44, 370, 290)
    fb = V.tilted_box("FORGOTTEN", 92, RED, (255, 255, 255), -3, distress=True)
    V.drop(base, fb, (52, b + 40), off=(7, 9))
    V.badge(base, "UNTOLD STORIES #5", W - 24, H - 22)

    out = os.path.join(V.HERE, "out", "Karun_303_thumbnail_v3.jpg")
    base.convert("RGB").save(out, quality=93)
    base.convert("RGB").resize((168, 94), Image.LANCZOS).save(os.path.join(V.HERE, "out", "thumb_v3_tiny.png"))
    print(out, os.path.getsize(out) // 1024, "KB", "303* box", (l, t, r, b))


if __name__ == "__main__":
    main()

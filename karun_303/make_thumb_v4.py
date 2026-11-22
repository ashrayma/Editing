#!/usr/bin/env python3
"""Karun thumbnail v4, 'Then vs Now': 2016 head-and-shoulders (left, warm glow), the frowning 2025 close-up
(right, cold glow), 303* top-left in empty space, FORGOTTEN lower middle, one dark navy background, natural skin.
python3 make_thumb_v4.py -> out/Karun_303_thumbnail_v4_then_now.jpg"""
import os

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

import make_thumb_v2 as V
import make_thumb_v3 as T

W, H, RED = V.W, V.H, V.RED


def background():
    yy, xx = np.mgrid[0:H, 0:W]
    a = np.zeros((H, W, 3), np.float32) + np.array([10, 16, 34])
    warm = np.exp(-(((xx - 250) / 260) ** 2 + ((yy - 430) / 260) ** 2))[..., None]
    cold = np.exp(-(((xx - 930) / 320) ** 2 + ((yy - 260) / 280) ** 2))[..., None]
    a += warm * np.array([170, 90, 30]) + cold * np.array([40, 95, 170])
    r = ((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2
    a *= np.clip(1 - 0.45 * r, 0.45, 1)[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


def natural(im, contrast=1.10, sharpen=50):
    """Natural skin tones: a little contrast and clarity, no colour filter."""
    a = im.split()[3]
    rgb = ImageEnhance.Contrast(im.convert("RGB")).enhance(contrast)
    rgb = ImageEnhance.Color(rgb).enhance(1.02)
    if sharpen:
        rgb = rgb.filter(ImageFilter.UnsharpMask(radius=2.0, percent=sharpen, threshold=3))
    out = rgb.convert("RGBA")
    out.putalpha(a)
    return out


def main():
    base = background()

    # THEN: 2016, head and shoulders (the raised arm stays on his own side)
    then = Image.open(os.path.join(V.HERE, "cut", "helmet_raised_2016.png"))
    then = then.crop((0, 0, then.width, 1180))                           # helmet held high, down to the chest
    tw = 430
    then = then.resize((tw, round(then.height * tw / then.width)), Image.LANCZOS)
    then = natural(then)
    a = np.asarray(then.split()[3], np.float32) / 255
    yy = np.linspace(0, 1, then.height)[:, None]
    a *= np.clip((1 - yy) / 0.18, 0, 1)                                  # soft fade at the cut-off bottom
    then.putalpha(Image.fromarray((a * 255).astype(np.uint8)))
    V.place_person(base, then, 30, H - then.height + 10, (255, 230, 200), (255, 150, 60), (14, 6))

    # NOW: the frowning close-up, in front, same as the single-face version
    now = Image.open(os.path.join(V.HERE, "cut", "karun_now_face.png"))
    nh = 1060
    now = now.resize((round(now.width * nh / now.height), nh), Image.LANCZOS)
    now = natural(now, 1.15, 60)
    V.place_person(base, now, 545, -60, (170, 215, 255), (60, 140, 255), (-18, 8))

    # 303* in the empty top-left, FORGOTTEN lower middle
    T.huge_number(base, "303*", 36, 168, 150)
    fb = V.tilted_box("FORGOTTEN", 76, RED, (255, 255, 255), -3, distress=True)
    V.drop(base, fb, (440, 548), off=(7, 9))
    V.badge(base, "UNTOLD STORIES #5", W - 24, H - 22)

    out = os.path.join(V.HERE, "out", "Karun_303_thumbnail_v4_then_now.jpg")
    base.convert("RGB").save(out, quality=93)
    base.convert("RGB").resize((168, 94), Image.LANCZOS).save(out.replace(".jpg", "_tiny.png"))
    print(out, os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    main()

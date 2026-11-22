#!/usr/bin/env python3
"""Karun thumbnail in the 'Kohli Cried' (82*) formula, 1920x1080:
faded tricolour background; Karun NOW (the frowning close-up) small and black-and-white, printed into the flag on
the left; Karun 2016 (helmet raised after the 303*) big and in full colour on the right, lit by the flag;
FORGOTTEN (big grunge white) + 303* on the red brush stroke, bottom-left; UNTOLD STORIES #5 badge top-right;
bottom-right corner left clear for YouTube's length badge.

    python3 thumb_kohli_style.py -> out/Karun_303_thumb_kohli_style.png / .jpg / _small.png
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "virat_82"))
sys.path.insert(0, os.path.join(ROOT, "virat_story"))
sys.path.insert(0, os.path.join(ROOT, "doc_video", "thumb"))
import thumb_82_v2 as k  # noqa: E402  (double exposure, flag light, edge glow, dust, bloom, unify)
import thumb_goat_v2 as g  # noqa: E402  (flag background, grunge text, brush box, edge fade)
import thumb_wc2003 as tw  # noqa: E402
from thumb_wc2003 import ANTON, H, W, fade_bottom, finish, place, regrade  # noqa: E402

tw.HERE = os.path.join(HERE, "out")
Y = (255, 222, 89)


def badge(base, text, right, top):
    f = ImageFont.truetype(ANTON, 44)
    d = ImageDraw.Draw(base)
    l, t, r, b = d.textbbox((0, 0), text, font=f)
    bw, bh = r - l + 64, b - t + 30
    x0 = right - bw
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    dl.rectangle((x0, top, right, top + bh), fill=(14, 14, 18, 205))
    dl.rectangle((x0, top, x0 + 11, top + bh), fill=Y + (255,))
    dl.text((x0 + 34 - l, top + 15 - t), text, font=f, fill=(255, 255, 255, 240))
    base.alpha_composite(lay)


def badge_left(base, text, left, top):
    f = ImageFont.truetype(ANTON, 44)
    d = ImageDraw.Draw(base)
    l, t, r, b = d.textbbox((0, 0), text, font=f)
    bw, bh = r - l + 64, b - t + 30
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    dl.rectangle((left, top, left + bw, top + bh), fill=(14, 14, 18, 205))
    dl.rectangle((left, top, left + 11, top + bh), fill=Y + (255,))
    dl.text((left + 34 - l, top + 15 - t), text, font=f, fill=(255, 255, 255, 240))
    base.alpha_composite(lay)


def light_dust(base, n=40):
    rng = np.random.default_rng(303)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(n):
        x, y, r = rng.uniform(0, W), rng.uniform(0, H * 0.8), rng.uniform(0.8, 1.8)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 215, 160, int(rng.uniform(40, 110))))
    base.alpha_composite(layer)


def clean_grade(im):
    a = np.asarray(im.convert("RGB"), np.float32)
    a = 255 * (0.5 + 0.5 * np.tanh((a / 255 - 0.5) * 1.5) / np.tanh(0.75))
    a = a * 0.97 + np.array([3, 5, 10], np.float32)
    a += np.random.default_rng(1).normal(0, 2.0, (H, W, 1)).astype(np.float32)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def main_final():
    """Text bottom-left (as in the original); sharp colour celebration above it; big sharp B&W face right."""
    g.CHAKRA = (735, 470, 80)
    base = g.flag_background()

    # RIGHT - Karun now: colour, centred in the right half, face level with the flag's middle band,
    # lit by the flag itself (no white border)
    now = Image.open(os.path.join(HERE, "cut", "karun_now_face.png")).convert("RGBA")
    now = now.crop((0, 0, 1700, int(now.height * 0.72)))
    s = 900 / now.height
    now = now.resize((int(now.width * s), 900), Image.LANCZOS)
    now = regrade(now, color=0.95, contrast=1.15, bright=1.02, sharpen=(2, 110, 2))
    now = k.flag_light(now)
    now = fade_bottom(now, 700, 900)
    nx, ny = 1350 - now.width // 2, 40
    place(base, now, nx, ny, wrap=0.55, rim_color=(255, 175, 90), rim_side=-1, rim_k=0.22, shadow=0.6)

    # LEFT - Karun 2016: helmet raised, sharp, full colour, above the text
    cel = Image.open(os.path.join(HERE, "cut", "helmet_raised_2016.png")).convert("RGBA")
    cel = cel.crop((0, 0, cel.width, 1240))
    s = 600 / cel.height
    cel = cel.resize((int(cel.width * s), 600), Image.LANCZOS)
    cel = regrade(cel, color=1.08, contrast=1.14, bright=1.05, sharpen=(2, 120, 2))
    cel = k.flag_light(cel)
    cel = fade_bottom(cel, 470, 595)
    cx, cy = 330 - cel.width // 2, 10
    k.edge_glow(base, cel, cx, cy, (255, 170, 80), spread=34, k=0.45)
    place(base, cel, cx, cy, wrap=0.5, rim_color=(255, 190, 110), rim_side=1, rim_k=0.5, shadow=0.85)

    # text block, bottom-left (same place as the original)
    g.grunge_text(base, "FORGOTTEN", 60, 575, 150)
    g.brush_box(base, (60, 775, 640, 1040))
    g.grunge_text(base, "303*", 110, 765, 245, shadow=False)
    badge_left(base, "UNTOLD STORIES #5", 640, 40)

    light_dust(base)
    base = k.bloom(base, k=0.12)
    tw.grade_and_grain = clean_grade
    base = k.unify(base)
    finish(base, "Karun_303_thumb_kohli_style_final")


def main():
    import sys as _s
    if "--final" in _s.argv:
        return main_final()
    swapped = "--swap" in _s.argv
    g.CHAKRA = (1060, 470, 95) if swapped else (905, 455, 95)
    base = g.flag_background()

    # Karun now: the frowning close-up, black-and-white, printed into the flag
    now = Image.open(os.path.join(HERE, "cut", "karun_now_face.png")).convert("RGBA")
    now = now.crop((0, 0, 1500, int(now.height * 0.62)))
    s = 760 / now.height
    now = now.resize((int(now.width * s), 760), Image.LANCZOS)
    nx = min(W - now.width, 1520 - now.width // 2) if swapped else max(0, 420 - now.width // 2)
    if swapped:
        # a sharp black-and-white cut-out sitting on the flag (not printed into it)
        now = regrade(now, color=0.0, contrast=1.22, bright=1.04, sharpen=(2, 120, 2))
        now = fade_bottom(now, 520, 740)
        k.edge_glow(base, now, nx, -10, (255, 235, 205), spread=34, k=0.38)
        place(base, now, nx, -10, wrap=0.35, rim_color=(255, 205, 150), rim_side=-1, rim_k=0.45, shadow=0.7)
    else:
        now = regrade(now, color=0.0, contrast=1.3, bright=1.05, sharpen=(1.0, 60, 1))
        now = g.edge_fade(fade_bottom(now, 470, 740), left=40, right=30)
        base = k.double_exposure(base, now, nx, 20, strength=0.9)

    # Karun 2016: helmet raised after the 303*, big, full colour, lit by the flag
    cel = Image.open(os.path.join(HERE, "cut", "helmet_raised_2016.png")).convert("RGBA")
    cel = cel.crop((0, 0, cel.width, int(cel.height * 0.74)))
    s = 1420 / cel.height
    cel = cel.resize((int(cel.width * s), 1420), Image.LANCZOS)
    cel = regrade(cel, color=1.08, contrast=1.14, bright=1.05, sharpen=(2, 120, 2) if swapped else (1.0, 60, 1))
    cel = k.flag_light(cel)
    cel = fade_bottom(cel, 880, 1000)
    cx, cy = ((500 if swapped else 1450) - cel.width // 2), 125
    k.edge_glow(base, cel, cx, cy, (255, 170, 80), spread=40, k=0.45)
    place(base, cel, cx, cy, wrap=0.5, rim_color=(255, 190, 110), rim_side=1 if swapped else -1, rim_k=0.5, shadow=0.85)

    if swapped:
        # text bottom-right, kept clear of the very corner where YouTube's length badge sits
        g.grunge_text(base, "FORGOTTEN", 1180, 560, 150)
        g.brush_box(base, (1180, 760, 1760, 990))
        g.grunge_text(base, "303*", 1230, 745, 230, shadow=False)
        badge_left(base, "UNTOLD STORIES #5", 40, 40)
        name = "Karun_303_thumb_kohli_style_swapped"
    else:
        g.grunge_text(base, "FORGOTTEN", 60, 575, 150)
        g.brush_box(base, (60, 775, 640, 1040))
        g.grunge_text(base, "303*", 110, 765, 245, shadow=False)
        badge(base, "UNTOLD STORIES #5", W - 40, 40)
        name = "Karun_303_thumb_kohli_style"

    if swapped:
        light_dust(base)                                   # far fewer, fainter specks
        base = k.bloom(base, k=0.12)
        tw.grade_and_grain = clean_grade                   # less grain, keeps the faces crisp
    else:
        k.dust(base)
        base = k.bloom(base)
    base = k.unify(base)
    finish(base, name)


if __name__ == "__main__":
    main()

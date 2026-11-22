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


def inset(base, cx, cy, d, label="2016"):
    """Circular 'then' photo: Karun with the bat in Chennai 2016, thin yellow ring, tiny year tag."""
    im = Image.open(os.path.join(V.HERE, "up", "karun_303_chennai_2016.png")).convert("RGB")
    # square crop on his face and the raised bat
    im = im.crop((820, 120, 820 + 1080, 1200)).resize((d, d), Image.LANCZOS)
    im = V.tone(im.convert("RGBA"), (1.06, 1.0, 0.9), 1.05, 1.08, sharpen=50)
    m = Image.new("L", (d, d), 0)
    ImageDraw.Draw(m).ellipse((0, 0, d - 1, d - 1), fill=255)
    disc = Image.new("RGBA", (d + 16, d + 16), (0, 0, 0, 0))
    ImageDraw.Draw(disc).ellipse((0, 0, d + 15, d + 15), fill=Y + (255,))
    disc.paste(im, (8, 8), m)
    V.drop(base, disc, (cx - disc.width // 2, cy - disc.height // 2), off=(6, 8), blur=8, alpha=0.7)
    f = ImageFont.truetype(V.ANTON, 30)
    dd = ImageDraw.Draw(base)
    l, t, r, b = dd.textbbox((0, 0), label, font=f)
    tw, th = r - l + 20, b - t + 10
    tx, ty = cx + d // 2 - tw + 14, cy + d // 2 - th + 6
    dd.rounded_rectangle((tx, ty, tx + tw, ty + th), 6, fill=Y + (255,))
    dd.text((tx + 10 - l, ty + 5 - t), label, font=f, fill=INK)


def memory(base, cx, bottom, h, opacity=0.78):
    """The 2016 300-celebration (arms up), warm sepia and slightly faded: the 'then' behind the number."""
    cel = Image.open(os.path.join(V.HERE, "cut", "helmet_raised_2016.png"))
    cel = cel.crop((0, 0, cel.width, int(cel.height * 0.60)))        # helmet raised high, down to the waist
    cel = cel.resize((round(cel.width * h / cel.height), h), Image.LANCZOS)
    cel = V.tone(cel, (1.12, 0.98, 0.78), 0.6, 1.1, sharpen=40)
    a = np.asarray(cel.split()[3], np.float32) / 255
    yy = np.linspace(0, 1, cel.height)[:, None]
    a = a * np.clip((1 - yy) / 0.45, 0, 1) ** 0.8 * opacity          # fades out toward the bottom
    xx = np.linspace(0, 1, cel.width)[None, :]

    cel.putalpha(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)))
    x, y = cx - cel.width // 2, bottom - h
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gm = Image.new("L", (W, H), 0)
    gm.paste(cel.split()[3], (x, y))
    g = Image.new("RGBA", (W, H), (255, 170, 60, 0))
    g.putalpha(gm.filter(ImageFilter.GaussianBlur(30)).point(lambda v: int(v * 0.55)))
    base.alpha_composite(g)
    base.alpha_composite(cel, (x, y))


def main():
    base = background()
    # the frowning 2025 close-up, right half, nothing overlapping it
    now = Image.open(os.path.join(V.HERE, "cut", "karun_now_face.png"))
    nh = 1060
    now = now.resize((round(now.width * nh / now.height), nh), Image.LANCZOS)
    now = V.tone(now, (0.78, 0.94, 1.04), 0.45, 1.18, sharpen=60)
    import sys
    if "--memory" in sys.argv:
        memory(base, 300, 520, 530, opacity=1.0)
    V.place_person(base, now, 525, -60, (170, 215, 255), (60, 140, 255), (-18, 8))

    if "--memory" in sys.argv:
        l, t, r, b = huge_number(base, "303*", 44, 585, 240)
    else:
        l, t, r, b = huge_number(base, "303*", 44, 370, 290)
    fb = V.tilted_box("FORGOTTEN", 92 if "--memory" not in sys.argv else 72, RED, (255, 255, 255), -3, distress=True)
    V.drop(base, fb, (52, b + (40 if "--memory" not in sys.argv else 14)), off=(7, 9))
    V.badge(base, "UNTOLD STORIES #5", W - 24, H - 22)
    name = "Karun_303_thumbnail_v3.jpg"
    if "--inset" in sys.argv:
        inset(base, 560, b + 40 + fb.height // 2, 138)
        name = "Karun_303_thumbnail_v3_inset.jpg"
    if "--memory" in sys.argv:
        name = "Karun_303_thumbnail_v3_memory.jpg"

    out = os.path.join(V.HERE, "out", name)
    base.convert("RGB").save(out, quality=93)
    base.convert("RGB").resize((168, 94), Image.LANCZOS).save(out.replace(".jpg", "_tiny.png"))
    print(out, os.path.getsize(out) // 1024, "KB", "303* box", (l, t, r, b))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""YouTube thumbnails (1280x720) for "Centurion 2003: The 98" - three variants for YouTube's Test & Compare.

What works in this niche (cricket history/documentary): one or two big, emotional faces; a face-off for
rivalries; one striking number; 2-3 huge words max; high contrast on a dark ground; brand colour as accent.
Everything must read at phone size (~320 px wide), so check the *_small.png previews.
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
W, H = 1280, 720
Y = (254, 222, 92)
BLACK_F = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
XB_F = "/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf"


def font(path, size):
    return ImageFont.truetype(path, size)


def background(src, dim=0.6, blur=14, tint=(20, 16, 6)):
    im = Image.open(os.path.join(ROOT, src)).convert("RGB")
    s = max(W / im.width, H / im.height) * 1.05
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x, y = (im.width - W) // 2, (im.height - H) // 2
    im = im.crop((x, y, x + W, y + H)).filter(ImageFilter.GaussianBlur(blur))
    im = Image.blend(im, Image.new("RGB", (W, H), tint), dim)
    # vignette
    yy, xx = np.mgrid[0:H, 0:W]
    v = 1 - 0.75 * np.clip(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2, 0, 1)
    arr = np.array(im).astype(float) * v[..., None]
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA")


def subject(cut, height, sharpen=True):
    im = Image.open(os.path.join(HERE, cut)).convert("RGBA")
    bbox = im.getchannel("A").point(lambda a: 255 if a > 20 else 0).getbbox()
    im = im.crop(bbox)
    s = height / im.height
    im = im.resize((int(im.width * s), height), Image.LANCZOS)
    if sharpen:
        rgb = im.convert("RGB").filter(ImageFilter.UnsharpMask(2, 90, 2))
        rgb = ImageEnhance.Contrast(ImageEnhance.Color(rgb).enhance(1.15)).enhance(1.12)
        rgb.putalpha(im.getchannel("A"))
        im = rgb
    return im


def rim(im, color=Y, spread=18, strength=0.85):
    """Brand-yellow glow behind a cut-out so it pops off the dark ground."""
    a = im.getchannel("A").filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(spread))
    glow = Image.new("RGBA", im.size, color + (0,))
    glow.putalpha(a.point(lambda v: int(v * strength)))
    return glow


def place(base, im, x, y, glow=True):
    if glow:
        g = rim(im)
        base.alpha_composite(g, (x, y))
    base.alpha_composite(im, (x, y))


def gold_text(txt, size, depth=14):
    """Gold gradient face + dark-gold extrusion + soft shadow, as an RGBA image."""
    f = font(BLACK_F, size)
    l, t, r, b = f.getbbox(txt)
    w, h = r - l + depth + 40, b - t + depth + 40
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(out)
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((20 - l + 10, 20 - t + depth + 12), txt, font=f, fill=(0, 0, 0, 200))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    for k in range(depth, 0, -1):
        d.text((20 - l, 20 - t + k), txt, font=f, fill=(110, 76, 12, 255))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).text((20 - l, 20 - t), txt, font=f, fill=255)
    grad = np.zeros((h, w, 3))
    stops = [(0.0, (255, 246, 196)), (0.35, Y), (0.7, (200, 150, 30)), (1.0, (255, 228, 140))]
    ys = np.linspace(0, 1, h)
    for c in range(3):
        grad[..., c] = np.interp(ys, [s for s, _ in stops], [col[c] for _, col in stops])[:, None]
    face = Image.fromarray(grad.astype(np.uint8)).convert("RGBA")
    face.putalpha(mask)
    out.alpha_composite(face)
    return out


def label(txt, size, fg=(255, 255, 255), bg=None, pad=(26, 12), stroke=0):
    f = font(BLACK_F, size)
    l, t, r, b = f.getbbox(txt, stroke_width=stroke)
    w, h = r - l + 2 * pad[0], b - t + 2 * pad[1]
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if bg:
        d.rounded_rectangle((0, 0, w - 1, h - 1), radius=min(18, h // 3), fill=bg)
    d.text((pad[0] - l, pad[1] - t), txt, font=f, fill=fg, stroke_width=stroke, stroke_fill=(0, 0, 0))
    return im


def logo(base, x, y, width=190):
    lg = Image.open(os.path.join(ROOT, "..", "kohli_countdown", "assets", "logo.png")).convert("RGBA")
    lg = lg.resize((width, int(lg.height * width / lg.width)), Image.LANCZOS)
    base.alpha_composite(lg, (x, y))


def save(img, name):
    rgb = img.convert("RGB")
    rgb.save(os.path.join(HERE, name + ".png"))
    rgb.save(os.path.join(HERE, name + ".jpg"), quality=95)
    rgb.resize((320, 180), Image.LANCZOS).save(os.path.join(HERE, name + "_small.png"))


def thumb_a():
    """Face-off + giant gold 98 + 2 RUNS SHORT."""
    img = background("assets/ai/ai_stadium.png", dim=0.62)
    s = subject("cut_faceoff_tight.png", 640)
    place(img, s, -40, H - s.height + 8)
    n = gold_text("98", 300, depth=14)
    img.alpha_composite(n, (W - n.width - 20, 70))
    t = label("2 RUNS SHORT", 58, fg=(18, 18, 20), bg=Y + (255,))
    img.alpha_composite(t, (W - t.width - 40, 430))
    tag = label("SACHIN vs SHOAIB · 2003", 30, fg=(255, 255, 255), bg=(0, 0, 0, 170), pad=(18, 9))
    img.alpha_composite(tag, (W - tag.width - 40, 540))
    save(img, "thumb_A_faceoff_98")


def thumb_b():
    """Shoaib in delivery + 161.3 km/h + vs SACHIN."""
    img = background("assets/ai/ai_ball.png", dim=0.5, blur=6)
    s = subject("cut_shoaib_bowling.png", 760)
    place(img, s, 10, H - s.height + 40)
    n = gold_text("161.3", 230, depth=12)
    img.alpha_composite(n, (W - n.width - 20, 90))
    k = label("KM/H", 54, fg=(255, 255, 255))
    img.alpha_composite(k, (W - k.width - 50, 340))
    v = label("vs SACHIN", 92, fg=(18, 18, 20), bg=Y + (255,), pad=(30, 12))
    img.alpha_composite(v, (W - v.width - 50, 450))
    save(img, "thumb_B_161_vs_sachin")


def thumb_c():
    """Sachin, exhausted on 98 - emotional, with THE 98 + context line."""
    img = background("assets/ai/ai_stadium.png", dim=0.7, tint=(10, 10, 14))
    s = subject("cut_sachin_crouch_cramps.png", 700)
    place(img, s, W - s.width + 10, H - s.height + 20)
    t1 = label("THE", 96, fg=(255, 255, 255), pad=(4, 4))
    img.alpha_composite(t1, (60, 110))
    n = gold_text("98", 330, depth=16)
    img.alpha_composite(n, (30, 190))
    c = label("INDIA vs PAKISTAN · 2003", 38, fg=(18, 18, 20), bg=Y + (255,), pad=(20, 10))
    img.alpha_composite(c, (66, 560))
    save(img, "thumb_C_the98_sachin")


if __name__ == "__main__":
    thumb_a()
    thumb_b()
    thumb_c()
    print("thumbnails written")

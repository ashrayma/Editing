#!/usr/bin/env python3
"""Thumbnail B for 'IPL is dying': frustrated Bumrah left, huge '220' right, 'IS NORMAL NOW?' below.
python3 make_thumb_220.py -> out/IPL_is_dying_thumbnail_B_220.jpg"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from scipy import ndimage as nd

from make_thumb import ANTON, HERE, INK, LOGO, W, H, Y, cover

RED = (229, 52, 52)


def background():
    bg = cover(Image.open(os.path.join(HERE, "up", "stadium.png")).convert("RGB"), W, H, 0.5, 0.30)
    bg = bg.filter(ImageFilter.GaussianBlur(9))                       # floodlights become soft bokeh
    a = np.asarray(bg, np.float32)
    a = a * np.array([0.62, 0.70, 0.95])                               # navy night
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W * 0.5) / (W * 0.62)) ** 2 + ((yy - H * 0.45) / (H * 0.75)) ** 2)
    edge = np.clip((r - 0.55) / 0.6, 0, 1)[..., None]
    a = a * (1 - 0.55 * edge) + np.array([150, 18, 22]) * 0.55 * edge  # red danger tint at the edges
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


def glow_edge(layer, radius=14, color=(255, 222, 89), strength=0.38):
    a = np.asarray(layer.split()[3], np.float32) / 255
    g = np.clip(nd.gaussian_filter(a, radius) - a * 0.6, 0, 1) * strength * 2.2   # a rim just outside the edge
    out = Image.new("RGBA", layer.size, color + (0,))
    out.putalpha(Image.fromarray(np.clip(g * 255, 0, 255).astype(np.uint8)))
    return out


def outlined(base, xy, text, font, fill, stroke, sw, anchor="mm", shadow=True):
    if shadow:
        sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((xy[0], xy[1] + 10), text, font=font, fill=(0, 0, 0, 200), anchor=anchor,
                                stroke_width=sw, stroke_fill=(0, 0, 0, 200))
        base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    ImageDraw.Draw(base).text(xy, text, font=font, fill=fill, anchor=anchor, stroke_width=sw, stroke_fill=stroke)


def text_mask(txt, font, size, anchor_xy):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).text(anchor_xy, txt, font=font, fill=255, anchor="mm")
    return m


def soft_shadow(mask, off, blur, alpha):
    sh = Image.new("RGBA", mask.size, (0, 0, 0, 0))
    a = np.asarray(mask, np.float32) * alpha
    sh.putalpha(Image.fromarray(a.astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur)))
    out = Image.new("RGBA", mask.size, (0, 0, 0, 0))
    out.alpha_composite(sh, off)
    return out


def big_number(base, txt, cx, cy, size):
    """'220': dark 3D shadow, yellow -> orange gradient, dark outline, thin white inner glow."""
    f = ImageFont.truetype(ANTON, size)
    m = text_mask(txt, f, base.size, (cx, cy))
    ma = np.asarray(m, np.float32) / 255
    # 3D shadow, down-right
    base.alpha_composite(soft_shadow(m, (8, 8), 2, 0.85))
    base.alpha_composite(soft_shadow(m, (12, 16), 14, 0.55))
    # outline
    ol = nd.binary_dilation(ma > 0.5, iterations=6).astype(np.float32)
    o = Image.new("RGBA", base.size, INK + (0,))
    o.putalpha(Image.fromarray((nd.gaussian_filter(ol, 0.8) * 255).astype(np.uint8)))
    base.alpha_composite(o)
    # gradient fill
    ys = np.nonzero(ma.max(1) > 0.5)[0]
    y0, y1 = ys.min(), ys.max()
    t = np.clip((np.arange(H) - y0) / max(1, y1 - y0), 0, 1)[:, None]
    top, bot = np.array([255, 236, 120]), np.array([247, 160, 30])
    col = top * (1 - t[..., None]) + bot * t[..., None]
    fill = np.zeros((H, W, 4), np.float32)
    fill[..., :3] = np.broadcast_to(col, (H, W, 3))
    fill[..., 3] = ma * 255
    base.alpha_composite(Image.fromarray(fill.astype(np.uint8)))
    # thin white inner glow along the inside edge
    er = nd.binary_erosion(ma > 0.5, iterations=5).astype(np.float32)
    inner = np.clip(ma - nd.gaussian_filter(er, 3), 0, 1) * ma
    ig = Image.new("RGBA", base.size, (255, 255, 240, 0))
    ig.putalpha(Image.fromarray((inner * 150).astype(np.uint8)))
    base.alpha_composite(ig)
    return m.getbbox()


def main():
    base = background()
    a = np.asarray(base, np.float32)
    a[..., :3] *= 0.72                                                 # background ~28% darker
    yy, xx = np.mgrid[0:H, 0:W]
    spot = np.exp(-(((xx - 940) / 330) ** 2 + ((yy - 300) / 230) ** 2))[..., None]
    a[..., :3] += spot * np.array([90, 60, 18])                        # warm spotlight behind 220
    vig = np.clip(1 - 0.55 * (((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.68)) ** 2), 0.35, 1)[..., None]
    a[..., :3] *= vig                                                  # soft vignette
    base = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

    # Bumrah: waist up, left half
    b = Image.open(os.path.join(HERE, "cut", "bumrah.png"))
    b = b.crop((0, 0, b.width, int(b.height * 0.74)))
    bh = 790
    b = b.resize((round(b.width * bh / b.height), bh), Image.LANCZOS)
    bx, by = 330 - b.width // 2, H - bh + 70
    alpha = b.split()[3]
    rgb = b.convert("RGB")
    rgb = ImageEnhance.Contrast(rgb).enhance(1.15)
    rgb = rgb.filter(ImageFilter.UnsharpMask(radius=2.2, percent=90, threshold=2))     # clarity
    rgb = rgb.filter(ImageFilter.UnsharpMask(radius=1, percent=60, threshold=1))       # detail on the face
    # tone down the bright white sponsor lettering on the chest
    ra = np.asarray(rgb, np.float32)
    hsv = np.asarray(rgb.convert("HSV"), np.float32)
    box = np.zeros(ra.shape[:2], bool)
    box[int(bh * 0.52):int(bh * 0.70), int(b.width * 0.30):int(b.width * 0.75)] = True
    logo_m = box & (hsv[..., 2] > 175) & (hsv[..., 1] < 70)
    logo_m = nd.gaussian_filter(nd.binary_dilation(logo_m, iterations=2).astype(np.float32), 1.5)[..., None]
    soft = np.asarray(rgb.filter(ImageFilter.GaussianBlur(2.5)), np.float32)
    ra = ra * (1 - logo_m) + soft * 0.55 * logo_m
    rgb = Image.fromarray(np.clip(ra, 0, 255).astype(np.uint8))
    b = rgb.convert("RGBA")
    b.putalpha(alpha)

    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    full_a = Image.new("L", (W, H), 0)
    full_a.paste(alpha, (bx, by))
    # drop shadow, to the right
    canvas.alpha_composite(soft_shadow(full_a, (22, 8), 20, 0.7))
    # thin light-yellow outline, 4 px, soft
    fa = np.asarray(full_a, np.float32) / 255
    ring = np.clip(nd.binary_dilation(fa > 0.5, iterations=4).astype(np.float32) - fa, 0, 1)
    ring = nd.gaussian_filter(ring, 1.2)
    rl = Image.new("RGBA", (W, H), (255, 244, 190, 0))
    rl.putalpha(Image.fromarray(np.clip(ring * 255, 0, 230).astype(np.uint8)))
    glow = Image.new("RGBA", (W, H), (255, 222, 89, 0))
    glow.putalpha(Image.fromarray(np.clip(nd.gaussian_filter(ring, 10) * 260, 0, 120).astype(np.uint8)))
    canvas.alpha_composite(glow)
    canvas.alpha_composite(rl)
    base = base.convert("RGBA")
    base.alpha_composite(canvas)
    base.alpha_composite(b, (bx, by))

    # faint sparks rising around 220
    rng = np.random.default_rng(7)
    sp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sp)
    for _ in range(46):
        x, y = rng.uniform(690, 1240), rng.uniform(60, 470)
        r = rng.uniform(1.2, 3.4)
        ds.ellipse((x - r, y - r, x + r, y + r), fill=(255, rng.integers(140, 210), 60, int(rng.uniform(70, 170))))
    base.alpha_composite(sp.filter(ImageFilter.GaussianBlur(0.8)))

    cx = 925
    l, t, r, bt = big_number(base, "220", cx, 292, 330)

    # red up-arrow, 30% bigger, attached to the top-right of the last 0
    d = ImageDraw.Draw(base)
    k = 1.3
    ax, ay = r + 16 + 34 * k, t + 6
    arrow = [(ax, ay), (ax + 34 * k, ay + 46 * k), (ax + 13 * k, ay + 46 * k), (ax + 13 * k, ay + 120 * k),
             (ax - 13 * k, ay + 120 * k), (ax - 13 * k, ay + 46 * k), (ax - 34 * k, ay + 46 * k)]
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).polygon([(x + 6, y + 6) for x, y in arrow], fill=(0, 0, 0, 170))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(4)))
    d.polygon(arrow, fill=RED, outline=INK, width=3)

    # IS NORMAL NOW? (red question mark), a little lower
    f2 = ImageFont.truetype(ANTON, 84)
    main_t, q = "IS NORMAL NOW", "?"
    wm, wq = d.textlength(main_t, font=f2), d.textlength(q, font=f2)
    x0 = cx - (wm + wq) / 2
    y2 = 585
    outlined(base, (x0, y2), main_t, f2, (255, 255, 255), INK, 4, anchor="lm")
    outlined(base, (x0 + wm + 2, y2), q, f2, RED, INK, 4, anchor="lm")

    logo = Image.open(LOGO).convert("RGBA")
    logo = logo.resize((140, round(logo.height * 140 / logo.width)), Image.LANCZOS)
    base.alpha_composite(logo, (W - 140 - 24, 22))

    out = os.path.join(HERE, "out", "IPL_is_dying_thumbnail_B_220.jpg")
    base.convert("RGB").save(out, quality=93)
    base.convert("RGB").resize((168, 94), Image.LANCZOS).save(os.path.join(HERE, "out", "b220_tiny.png"))
    print(out, os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    main()

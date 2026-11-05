#!/usr/bin/env python3
"""1920x1080 thumbnail, v2: "Virat Kohli's 82*: The Night That Became Cricket History | MCG 2022".

Gritty tricolour style (shared with the Ordinary Boy to GOAT v2 thumbnail): textured saffron / white
(Ashoka Chakra) / green background; Virat waving to the MCG after the win, printed into the flag as a
double exposure on the left; the six off Haris Rauf huge on the right, bat running off the side, lit by
the flag (saffron key from above, green bounce from below); THE NIGHT / 82* on a red brush block / MCG 2022.
One finishing pass (dust, highlight bloom, grade, grain) over everything so it reads as a single image.

    python3 thumb_82_v2.py  ->  thumb_82_v2.png / .jpg / _small.png
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "virat_story"))
sys.path.insert(0, os.path.join(HERE, "..", "doc_video", "thumb"))
import thumb_goat_v2 as g  # noqa: E402  (flag background, duotone, grunge text, brush box)
import thumb_wc2003 as tw  # noqa: E402
from thumb_wc2003 import H, W, arr, fade_bottom, finish, img, load_cut, place, regrade  # noqa: E402

tw.HERE = HERE
SAFFRON = np.array([255, 160, 60], np.float32)
GREEN = np.array([40, 170, 70], np.float32)
rng = np.random.default_rng(82)


def double_exposure(base, cut, x, y, strength=0.85):
    """Print a figure into the flag: its light and shade in the cloth's own colour, so it isn't pasted on."""
    a = arr(cut)
    lum = a[..., :3].mean(-1, keepdims=True) / 255
    alpha = a[..., 3:4] / 255 * strength
    region = arr(base)[y:y + cut.height, x:x + cut.width, :3]
    h, w = region.shape[:2]
    lum, alpha = lum[:h, :w], alpha[:h, :w]
    # luminosity blend: the figure's light and shade, the flag's own colour underneath it
    reg_l = region.mean(-1, keepdims=True) + 1
    hue = 1 + (region / reg_l - 1) * 0.65  # keep the cloth's tint, softened
    mixed = np.clip(hue * (25 + 230 * lum ** 1.05), 0, 255)
    out = region * (1 - alpha) + mixed * alpha
    b = arr(base)
    b[y:y + h, x:x + w, :3] = out
    return img(b, "RGBA")


def flag_light(cut):
    """Light a cut-out like it stands in front of the flag: saffron from above, green bounce from below."""
    a = arr(cut)
    h = a.shape[0]
    ys = np.linspace(0, 1, h)[:, None, None]
    top = np.clip(1 - ys / 0.45, 0, 1) ** 1.5
    bot = np.clip((ys - 0.55) / 0.45, 0, 1) ** 1.5
    rgb = a[..., :3]
    lum = rgb.mean(-1, keepdims=True) / 255
    rgb = rgb + (SAFFRON - rgb) * top * 0.16 * (0.4 + 0.6 * lum)
    rgb = rgb * (1 - bot * 0.22) + GREEN * bot * 0.1 * lum
    a[..., :3] = rgb
    return img(a, "RGBA")


def edge_glow(base, cut, x, y, color, spread=36, k=0.5):
    """Soft halo of flag light behind a figure (separates it from the background without an outline)."""
    p = 80
    al = Image.new("L", (cut.width + 2 * p, cut.height + 2 * p), 0)
    al.paste(cut.getchannel("A"), (p, p))
    al = al.filter(ImageFilter.GaussianBlur(spread))
    layer = Image.new("RGBA", al.size, tuple(int(c) for c in color) + (0,))
    layer.putalpha(al.point(lambda v: int(v * k)))
    base.alpha_composite(layer, (x - p, y - p))


def dust(base, n=420):
    """Fine floating dust / embers across the whole frame, a little denser in the light."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(n):
        x, y = rng.uniform(0, W), rng.uniform(0, H * 0.85)
        r = rng.uniform(0.8, 2.6)
        warm = rng.random() < 0.6
        col = (255, 205, 140) if warm else (235, 240, 255)
        d.ellipse((x - r, y - r, x + r, y + r), fill=col + (int(rng.uniform(70, 200)),))
    for _ in range(14):  # a few bigger out-of-focus specks
        x, y, r = rng.uniform(0, W), rng.uniform(0, H * 0.7), rng.uniform(6, 14)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 210, 150, 60))
    base.alpha_composite(layer.filter(ImageFilter.GaussianBlur(0.7)))


def bloom(base, threshold=225, k=0.22):
    a = arr(base)
    lum = a[..., :3].mean(-1)
    hi = img(np.clip((lum - threshold) * 4, 0, 255), "L").filter(ImageFilter.GaussianBlur(18))
    a[..., :3] += (arr(hi) / 255)[..., None] * np.array([255, 225, 180], np.float32) * k
    return img(np.clip(a, 0, 255), "RGBA")


def unify(base):
    """One grade over all layers: gentle vignette, warm highlights, slightly cool shadows."""
    a = arr(base)
    rgb = a[..., :3]
    lum = rgb.mean(-1, keepdims=True) / 255
    rgb = rgb + (np.array([255, 200, 140], np.float32) - rgb) * (lum ** 2) * 0.08
    rgb = rgb + (np.array([10, 18, 30], np.float32) - rgb) * ((1 - lum) ** 3) * 0.12
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = 1 - 0.45 * np.clip(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.72)) ** 2, 0, 1)
    a[..., :3] = rgb * v[..., None]
    return img(np.clip(a, 0, 255), "RGBA")


def main():
    g.CHAKRA = (845, 470, 100)  # in the gap between the two Viratas
    base = g.flag_background()

    # LEFT - after the win: Virat waving to the MCG, printed into the flag
    wv = load_cut("cut_wave.png", 1010)
    wv = regrade(wv, color=0.0, contrast=1.25, bright=1.05, sharpen=(1.0, 60, 1))
    wv = g.edge_fade(fade_bottom(wv, 520, 940), left=30, right=30)
    base = double_exposure(base, wv, 470 - wv.width // 2, 15)

    # RIGHT - the six off Rauf, huge; bat runs off the right side
    sx = Image.open(os.path.join(HERE, "cut_six.png")).convert("RGBA").crop((700, 0, 2824, 2150))
    s = 1300 / sx.height
    sx = sx.resize((int(sx.width * s), 1300), Image.LANCZOS)
    sx = regrade(sx, color=1.1, contrast=1.14, bright=1.04, sharpen=(1.0, 60, 1))
    sx = flag_light(sx)
    sx = fade_bottom(sx, 900, 1260)
    sxx, sxy = 925, -30
    edge_glow(base, sx, sxx, sxy, (255, 170, 80), spread=40, k=0.45)
    place(base, sx, sxx, sxy, wrap=0.5, rim_color=(255, 190, 110), rim_side=-1, rim_k=0.5, shadow=0.85)

    # text block, bottom left
    g.grunge_text(base, "THE NIGHT", 60, 560, 160)
    g.brush_box(base, (60, 770, 580, 1040))
    g.grunge_text(base, "82*", 120, 760, 245, shadow=False)
    g.grunge_text(base, "MCG", 630, 775, 125)
    g.grunge_text(base, "2022", 630, 900, 125, fill=(255, 222, 89))

    # finishing pass over everything
    dust(base)
    base = bloom(base)
    base = unify(base)
    finish(base, "thumb_82_v2")


if __name__ == "__main__":
    main()

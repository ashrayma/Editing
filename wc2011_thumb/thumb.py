"""Thumbnail: "What Made India World Champions in 2011? (The Untold Stories)".

Dhoni with the trophy up front, Sachin and Yuvraj either side, Sehwag celebrating behind, headline top-left. Background (night sky, fireworks, floodlight glow, crowd) is drawn here.

    python3 clean_logos.py && python3 cutouts.py && python3 thumb.py [LINE1 LINE2]  ->  out/thumb_*.jpg / .png
"""
import math
import os
import random
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
ANTON = os.path.join(HERE, "..", "doc_video", "thumb", "fonts", "Anton-Regular.woff")
W, H = 1920, 1080
YEL = (255, 222, 89)
rnd = random.Random(2011)


def cut(name):
    return Image.open(os.path.join(HERE, "cut", name + ".png")).convert("RGBA")


def fix_cuts():
    """Yuvraj's sleeve sponsor patch, and the scrap of flag beside Sachin's raised arm."""
    y = cut("yuvraj")
    a = np.array(y)
    rgb = cv2.cvtColor(a[..., :3], cv2.COLOR_RGB2BGR)
    m = np.zeros(rgb.shape[:2], np.uint8)
    m[2180:2470, 0:230] = 255
    m &= (a[..., 3] > 40).astype(np.uint8) * 255
    rgb = cv2.inpaint(rgb, m, 15, cv2.INPAINT_TELEA)
    a[..., :3] = cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)
    s = np.array(cut("sachin"))
    h, w = s.shape[:2]
    s[: int(h * 0.42), int(w * 0.72):, 3] = 0  # flag cloth right of the hand
    s[: int(h * 0.22), :, 3] = 0  # raised hand that would poke out beside Dhoni
    return Image.fromarray(a), Image.fromarray(s)


def background():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    top, bot = np.array([10, 14, 34], np.float32), np.array([3, 3, 8], np.float32)
    img = top * (1 - yy / H)[..., None] + bot * (yy / H)[..., None]
    # floodlight glow behind Dhoni + warm haze
    for cx, cy, r, col, k in [(1060, 330, 760, (255, 200, 90), 0.55), (1500, 120, 520, (255, 150, 60), 0.25),
                              (300, 160, 600, (90, 120, 255), 0.18)]:
        d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
        img += np.array(col, np.float32) * (np.clip(1 - d, 0, 1) ** 2 * k)[..., None]
    im = Image.fromarray(img.clip(0, 255).astype(np.uint8)).convert("RGBA")

    # fireworks: radial streak bursts in gold / white / saffron / green
    fw = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(fw)
    bursts = [(560, 150, 230, (255, 210, 120)), (1450, 110, 260, (255, 255, 235)), (1780, 330, 170, (255, 160, 60)),
              (980, 60, 170, (255, 230, 150)), (180, 330, 150, (120, 230, 140)), (1230, 300, 120, (255, 180, 90))]
    for cx, cy, r, col in bursts:
        for k in range(110):
            ang = rnd.uniform(0, 2 * math.pi)
            rr = r * rnd.uniform(0.55, 1.0)
            x1, y1 = cx + rr * math.cos(ang), cy + rr * math.sin(ang) + rr * 0.12
            x0, y0 = cx + rr * 0.55 * math.cos(ang), cy + rr * 0.55 * math.sin(ang)
            d.line((x0, y0, x1, y1), fill=col + (rnd.randint(90, 200),), width=2)
            d.ellipse((x1 - 3, y1 - 3, x1 + 3, y1 + 3), fill=col + (230,))
    glow = fw.filter(ImageFilter.GaussianBlur(10))
    im = Image.alpha_composite(im, glow)
    im = Image.alpha_composite(im, glow)
    im = Image.alpha_composite(im, fw)
    # gold confetti / sparks
    sp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(sp)
    for _ in range(260):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H * 0.75)
        s = rnd.uniform(1.5, 4.5)
        d.ellipse((x - s, y - s, x + s, y + s), fill=YEL + (rnd.randint(60, 200),))
    im = Image.alpha_composite(im, sp.filter(ImageFilter.GaussianBlur(0.6)))
    # stadium roof rim + crowd band with flash bulbs
    band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(band)
    for x in range(0, W, 3):
        h = 820 + 22 * math.sin(x / 37) + rnd.uniform(-14, 14)
        d.line((x, h, x, H), fill=(14, 16, 28, 255), width=3)
    for _ in range(420):
        x, y = rnd.uniform(0, W), rnd.uniform(830, H)
        c = rnd.choice([(255, 255, 255), (255, 200, 90), (80, 140, 255), (255, 140, 40)])
        d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=c + (rnd.randint(80, 220),))
    im = Image.alpha_composite(im, band.filter(ImageFilter.GaussianBlur(1.2)))
    return im


def place(base, im, cx, top, height, bottom_fade=0.0, shadow=True):
    k = height / im.height
    im = im.resize((int(im.width * k), int(height)), Image.LANCZOS)
    if bottom_fade:
        a = np.array(im.getchannel("A"), np.float32)
        h = a.shape[0]
        ramp = np.clip((h - np.arange(h)) / (h * bottom_fade), 0, 1)[:, None]
        im.putalpha(Image.fromarray((a * ramp).astype(np.uint8)))
    x = int(cx - im.width / 2)
    if shadow:  # dark rim so the cutout separates from busy fireworks
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        sh.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(18)).point(lambda v: v * 0.8))
        base.alpha_composite(sh, (x + 10, int(top) + 10))
    base.alpha_composite(im, (x, int(top)))


def rim_light(im, col=(255, 210, 120), strength=0.55):
    """Warm edge light from the floodlights, so everyone sits in the same scene."""
    a = np.array(im, np.float32)
    al = a[..., 3] / 255
    inner = np.array(Image.fromarray((al * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(9)), np.float32) / 255
    edge = np.clip(al - inner, 0, 1)[..., None] * 3
    a[..., :3] = a[..., :3] * (1 - edge * strength) + np.array(col, np.float32) * edge * strength
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))


def grade(im, sat=1.12, con=1.08, bri=1.0):
    rgb = im.convert("RGB")
    rgb = ImageEnhance.Color(rgb).enhance(sat)
    rgb = ImageEnhance.Contrast(rgb).enhance(con)
    rgb = ImageEnhance.Brightness(rgb).enhance(bri)
    out = rgb.convert("RGBA")
    out.putalpha(im.getchannel("A"))
    return out


def text(base, lines, x, y):
    for txt, size, col in lines:
        f = ImageFont.truetype(ANTON, size)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        d.text((x, y), txt, font=f, fill=(0, 0, 0, 255), stroke_width=14, stroke_fill=(0, 0, 0, 255))
        sh = layer.filter(ImageFilter.GaussianBlur(14))
        base.alpha_composite(sh)
        base.alpha_composite(sh)
        d2 = ImageDraw.Draw(base)
        d2.text((x, y), txt, font=f, fill=col, stroke_width=6, stroke_fill=(0, 0, 0))
        y += int(size * 1.02)


def build(line1, line2, name):
    bg = background()
    yuv, sac = fix_cuts()
    dho, seh = cut("dhoni"), cut("sehwag")

    place(bg, rim_light(grade(seh, 1.1, 1.05, 0.8)), 1520, 10, 700, bottom_fade=0.35)
    place(bg, rim_light(grade(yuv)), 1715, 270, 1020)
    place(bg, rim_light(grade(sac)), 430, 290, 1100, bottom_fade=0.2)
    place(bg, rim_light(grade(dho, 1.1, 1.12, 1.06), strength=0.65), 1120, 25, 1620)

    # brand + year tag
    d = ImageDraw.Draw(bg)
    f = ImageFont.truetype(ANTON, 54)
    d.rounded_rectangle((60, 60, 290, 140), 14, fill=YEL)
    d.text((175, 100), "2011", font=f, fill=(12, 12, 14), anchor="mm")
    fit = lambda t, w: int(200 * w / ImageFont.truetype(ANTON, 200).getlength(t))
    s2 = min(fit(line2, 700), 230)
    text(bg, [(line1, min(fit(line1, 700), int(s2 * 1.15)), (255, 255, 255)), (line2, s2, YEL)], 56, 150)

    out = bg.convert("RGB")
    out = ImageEnhance.Sharpness(out).enhance(1.15)
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    out.save(os.path.join(HERE, "out", f"{name}.png"))
    out.resize((1280, 720), Image.LANCZOS).save(os.path.join(HERE, "out", f"{name}.jpg"), quality=92)
    out.resize((320, 180), Image.LANCZOS).save(os.path.join(HERE, "out", f"{name}_small.png"))


if __name__ == "__main__":
    a = sys.argv[1:] or ["WORLD", "CHAMPIONS"]
    build(a[0], a[1], "thumb_" + "_".join((a[0] + " " + a[1]).lower().replace("'", "").replace(".", "").split()))

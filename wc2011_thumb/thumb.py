"""Thumbnail: "What Made India World Champions in 2011? (The Untold Stories)".

Dhoni's 2011 final six in front, Sachin and Yuvraj just behind at his eye line, one grade and one dark floor
for all three, blurred Wankhede crowd from the final behind them. Background (night sky, fireworks, floodlight glow, crowd) is drawn here.

    python3 clean_logos.py && python3 cutouts.py && python3 trophy.py && python3 thumb.py [LINE1 LINE2]  ->  out/thumb_*.jpg / .png
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
    m[1640:1900, 0:250] = 255
    m &= (a[..., 3] > 40).astype(np.uint8) * 255
    rgb = cv2.inpaint(rgb, m, 15, cv2.INPAINT_TELEA)
    a[..., :3] = cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)
    s = np.array(cut("sachin"))
    h, w = s.shape[:2]
    s[: int(h * 0.42), int(w * 0.72):, 3] = 0  # flag cloth right of the hand
    yy = np.arange(h, dtype=np.float32)[:, None]
    xx = np.arange(w, dtype=np.float32)[None, :]
    mate = np.clip(((xx - 0.13 * w) / (0.05 * w)), 0, 1) + np.clip((0.80 * h - yy) / (0.04 * h), 0, 1)
    s[..., 3] = (s[..., 3] * np.clip(mate, 0, 1)).astype(np.uint8)  # teammate's head bottom-left
    s[..., 3] = (s[..., 3] * np.clip(xx / (0.16 * w), 0, 1) ** 0.8).astype(np.uint8)  # soft edge where the photo ended
    fade = np.clip((yy - 0.20 * h) / (0.22 * h), 0, 1)  # raised arm fades out above his head
    s[..., 3] = (s[..., 3] * np.where(np.arange(w)[None, :] > 0.52 * w, fade, yy >= 0.2 * h)).astype(np.uint8)
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


def stadium():
    """Real Wankhede crowd from the final (above the boards), blurred and graded night-blue, plus floodlight bokeh."""
    src = Image.open(os.path.join(HERE, "..", "dhoni_2007_2011", "bg_2011.jpg")).convert("RGB")
    crowd = src.crop((0, 0, src.width, int(src.height * 0.27)))
    k = W / crowd.width
    crowd = crowd.resize((W, int(crowd.height * k)), Image.LANCZOS).resize((W, H), Image.LANCZOS)
    crowd = crowd.filter(ImageFilter.GaussianBlur(9))
    a = np.asarray(crowd, np.float32) / 255
    lum = a.mean(2, keepdims=True)
    tint = lum * np.array([0.35, 0.45, 0.85]) + a * 0.25  # night-blue, mostly mono
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    vign = np.clip(1 - (((xx - 1250) / 1250) ** 2 + ((yy - 380) / 820) ** 2), 0, 1)[..., None]
    base = tint * (0.30 + 0.55 * vign)
    # warm key light from behind the group + yellow brand glow
    for cx, cy, r, col, kk in [(1250, 300, 820, (1.0, 0.78, 0.35), 0.55), (1250, 1080, 900, (1.0, 0.87, 0.35), 0.18)]:
        d = np.clip(1 - np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r, 0, 1) ** 2
        base += np.array(col) * (d * kk)[..., None]
    im = Image.fromarray((base.clip(0, 1) * 255).astype(np.uint8)).convert("RGBA")
    # floodlight bokeh along the roof line
    bk = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(bk)
    for _ in range(70):
        x, y = rnd.uniform(0, W), rnd.uniform(0, 330)
        r = rnd.uniform(6, 26)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 235, 190, rnd.randint(25, 90)))
    im = Image.alpha_composite(im, bk.filter(ImageFilter.GaussianBlur(4)))
    return im


def put(base, im, cx, top, height, dim=1.0):
    """Place a cutout; `dim` < 1 pushes it back in depth (darker, cooler)."""
    k = height / im.height
    im = im.resize((int(im.width * k), int(height)), Image.LANCZOS)
    if dim < 1:
        a = np.array(im, np.float32)
        a[..., :3] = a[..., :3] * dim + np.array([10, 18, 40]) * (1 - dim)
        im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    base.alpha_composite(im, (int(cx - im.width / 2), int(top)))


def floor(base, start=0.5):
    """Everyone fades into the same dark floor, so nobody looks pasted on."""
    yy = np.arange(H, dtype=np.float32)
    a = np.clip((yy / H - start) / (0.92 - start), 0, 1) ** 1.4 * 255
    lay = Image.new("RGBA", (W, H), (4, 5, 12, 0))
    lay.putalpha(Image.fromarray(np.repeat(a[:, None], W, 1).astype(np.uint8)))
    base.alpha_composite(lay)


def left_shade(base):
    xx = np.arange(W, dtype=np.float32)
    a = np.clip(1 - xx / 900, 0, 1) ** 1.5 * 200
    lay = Image.new("RGBA", (W, H), (4, 5, 12, 0))
    lay.putalpha(Image.fromarray(np.repeat(a[None, :], H, 0).astype(np.uint8)))
    base.alpha_composite(lay)


def build(line1, line2, name):
    bg = stadium()
    yuv, sac = fix_cuts()
    six = Image.open(os.path.join(HERE, "..", "dhoni_2007_2011", "cut_2011.png")).convert("RGBA")
    look = lambda im, b=1.0: rim_light(grade(im, 1.08, 1.1, b), (255, 214, 140), 0.35)

    # back row at Dhoni's eye line, front: Dhoni's final six
    put(bg, look(sac, 0.95), 880, -70, 1160, dim=0.84)
    put(bg, look(yuv, 0.95), 1705, 165, 830, dim=0.84)
    put(bg, look(six, 1.06), 1260, -150, 1880)
    floor(bg)
    left_shade(bg)

    d = ImageDraw.Draw(bg)
    f = ImageFont.truetype(ANTON, 54)
    d.rounded_rectangle((70, 150, 300, 230), 14, fill=YEL)
    d.text((185, 190), "2011", font=f, fill=(12, 12, 14), anchor="mm")
    fit = lambda t, w: int(200 * w / ImageFont.truetype(ANTON, 200).getlength(t))
    sz = min(fit(line1, 600), fit(line2, 600), 250)
    text(bg, [(line1, sz, YEL), (line2, sz, YEL)], 66, 250)

    out = bg.convert("RGB")
    out = ImageEnhance.Sharpness(out).enhance(1.15)
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    out.save(os.path.join(HERE, "out", f"{name}.png"))
    out.resize((1280, 720), Image.LANCZOS).save(os.path.join(HERE, "out", f"{name}.jpg"), quality=92)
    out.resize((320, 180), Image.LANCZOS).save(os.path.join(HERE, "out", f"{name}_small.png"))


if __name__ == "__main__":
    a = sys.argv[1:] or ["5 UNTOLD", "STORIES"]
    build(a[0], a[1], "thumb_" + "_".join((a[0] + " " + a[1]).lower().replace("'", "").replace(".", "").split()))

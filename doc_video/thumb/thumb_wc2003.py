#!/usr/bin/env python3
"""1920x1080 YouTube thumbnail for "World Cup 2003: The Match That Changed India's Belief".

Three-layer collage built only from real 1 March 2003 material (no generated faces):
  left   - Shoaib Akhtar, broadcast frame (m_shoaib_turn), desaturated, deep green shadow
  centre - Sachin in the 2003 World Cup kit (assets/photos/bowling_card_sachin.jpg), the hero
  right  - Sachin's upper-cut off Shoaib (m_six_sideon), warm saffron/gold light, white ball
Background is the real Centurion crowd (crowd_flags), blurred and graded.
Headline uses Anton (SIL OFL, fonts/). Check the *_small.png preview at 320x180.
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1920, 1080
ANTON = os.path.join(HERE, "fonts", "Anton-Regular.woff")
RED = (214, 26, 34)
SAFFRON = (255, 153, 51)
GOLD = (255, 196, 92)
ICE = (150, 205, 255)
rng = np.random.default_rng(2003)


def arr(im):
    return np.asarray(im).astype(np.float32)


def img(a, mode="RGB"):
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), mode)


def radial(cx, cy, rx, ry, power=2.0):
    """1 at (cx, cy) falling to 0 at the ellipse edge."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
    return np.clip(1 - d, 0, 1) ** power


def background():
    im = Image.open(os.path.join(HERE, "bg_wc_crowd.png")).convert("RGB")
    im = im.crop((0, 0, im.width, im.height - 90))  # drop the broadcast score bar
    s = max(W / im.width, H / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    y = int((im.height - H) * 0.3)
    im = im.crop((0, y, W, y + H)).filter(ImageFilter.GaussianBlur(22))
    a = arr(ImageEnhance.Color(im).enhance(0.5)) * 0.42

    # split grade: forest green left -> cool blue centre -> saffron/gold right
    xs = np.linspace(0, 1, W)[None, :, None]
    left = np.array([10, 95, 55], np.float32)
    mid = np.array([20, 60, 150], np.float32)
    right = np.array([210, 105, 20], np.float32)
    tint = np.where(xs < 0.5, left + (mid - left) * (xs / 0.5), mid + (right - mid) * ((xs - 0.5) / 0.5))
    a = a * 0.55 + tint * 0.45

    # floodlight blooms + haze
    for cx, cy, r, col, k in [(250, -40, 520, (210, 235, 220), 0.55), (1700, -40, 700, GOLD, 1.1), (1500, 420, 520, SAFFRON, 0.35), (120, 380, 420, (40, 140, 80), 0.4),
                              (960, -120, 700, (200, 220, 255), 0.35)]:
        a += radial(cx, cy, r, r * 0.8, 1.6)[..., None] * np.array(col, np.float32) * k
    haze = rng.normal(0, 1, (H // 24, W // 24)).astype(np.float32)
    haze = np.asarray(img((haze * 40 + 128), "L").resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(40)),
                      np.float32) / 255
    a += (haze - 0.5)[..., None] * 40 * (1 - np.linspace(0, 1, H))[:, None, None]

    # vignette and a heavy floor of black for the headline
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = 1 - 0.8 * np.clip(((xx - W / 2) / (W * 0.6)) ** 2 + ((yy - H * 0.4) / (H * 0.75)) ** 2, 0, 1)
    a *= v[..., None]
    return img(a).convert("RGBA")


def load_cut(name, height):
    im = Image.open(os.path.join(HERE, name)).convert("RGBA")
    s = height / im.height
    return im.resize((int(im.width * s), height), Image.LANCZOS)


def regrade(im, color=1.0, contrast=1.0, bright=1.0, sharpen=(2, 80, 2), tint=None, tint_k=0.0):
    alpha = im.getchannel("A")
    rgb = im.convert("RGB").filter(ImageFilter.UnsharpMask(*sharpen))
    rgb = ImageEnhance.Color(rgb).enhance(color)
    rgb = ImageEnhance.Contrast(rgb).enhance(contrast)
    rgb = ImageEnhance.Brightness(rgb).enhance(bright)
    if tint:
        a = arr(rgb)
        a = a * (1 - tint_k) + (a.mean(-1, keepdims=True) / 255) * np.array(tint, np.float32) * tint_k * 1.6
        rgb = img(a)
    rgb.putalpha(alpha)
    return rgb


def directional_light(im, side, color, strength):
    """Warm/cool key light falling across a cut-out from one side."""
    a = arr(im)
    ramp = np.linspace(0, 1, im.width)[None, :] if side == "right" else np.linspace(1, 0, im.width)[None, :]
    ramp = ramp ** 2.2 * strength
    a[..., :3] = a[..., :3] * (1 - ramp[..., None] * 0.35) + np.array(color, np.float32) * ramp[..., None] * 0.35 \
        + a[..., :3] * ramp[..., None] * 0.25
    return img(a, "RGBA")


def rim(im, color, spread, strength, grow=7):
    a = im.getchannel("A")
    edge = Image.fromarray(np.clip(arr(a.filter(ImageFilter.MaxFilter(grow))) - arr(a) * 0.6, 0, 255).astype(np.uint8))
    glow = Image.new("RGBA", im.size, color + (0,))
    glow.putalpha(edge.filter(ImageFilter.GaussianBlur(spread)).point(lambda v: int(min(255, v * strength))))
    return glow


def pad(im, p):
    out = Image.new("RGBA", (im.width + 2 * p, im.height + 2 * p), (0, 0, 0, 0))
    out.alpha_composite(im, (p, p))
    return out


def fade_bottom(im, start, end):
    """Dissolve a cut-out into the dark floor between y=start and y=end (cut-out coords)."""
    a = arr(im.getchannel("A"))
    ys = np.arange(im.height, dtype=np.float32)[:, None]
    a *= np.clip((end - ys) / max(1, end - start), 0, 1)
    out = im.copy()
    out.putalpha(img(a, "L"))
    return out


def place(base, im, x, y, rims=()):
    p = 60
    big = pad(im, p)
    for color, spread, strength in rims:
        base.alpha_composite(rim(big, color, spread, strength), (x - p, y - p))
    base.alpha_composite(im, (x, y))


def shadow_text(base, txt, size, cx, top, fill, stroke=6, shadow=26, tracking=0):
    f = ImageFont.truetype(ANTON, size)
    l, t, r, b = f.getbbox(txt, stroke_width=stroke)
    w = r - l + tracking * (len(txt) - 1)
    x = int(cx - w / 2)
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    xx = x - l
    for ch in txt:
        d.text((xx + 6, top - t + 12), ch, font=f, fill=(0, 0, 0, 230), stroke_width=stroke, stroke_fill=(0, 0, 0, 230))
        xx += f.getlength(ch) + tracking
    base.alpha_composite(layer.filter(ImageFilter.GaussianBlur(shadow)))
    base.alpha_composite(layer.filter(ImageFilter.GaussianBlur(4)))
    d = ImageDraw.Draw(base)
    xx = x - l
    for ch in txt:
        d.text((xx, top - t), ch, font=f, fill=fill, stroke_width=stroke, stroke_fill=(8, 8, 10))
        xx += f.getlength(ch) + tracking
    return x, top, x + w, top + (b - t)


def banner(base, txt, size, cx, top):
    f = ImageFont.truetype(ANTON, size)
    tracking = 6
    l, t, r, b = f.getbbox(txt)
    w = sum(f.getlength(c) for c in txt) + tracking * (len(txt) - 1)
    pw, ph = 30, 12
    box = (int(cx - w / 2 - pw), top, int(cx + w / 2 + pw), top + (b - t) + 2 * ph)
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle((box[0] + 6, box[1] + 8, box[2] + 6, box[3] + 8), fill=(0, 0, 0, 200))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(base)
    d.rectangle(box, fill=RED + (255,))
    xx = box[0] + pw - l
    for ch in txt:
        d.text((xx, top + ph - t), ch, font=f, fill=(255, 255, 255))
        xx += f.getlength(ch) + tracking
    return box


def ball_with_trail(base, bx, by, fx, fy, r=17):
    """White ODI ball at (bx, by) streaking away from (fx, fy)."""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    n = 26
    for i in range(n):
        t = i / n
        x, y = fx + (bx - fx) * t, fy + (by - fy) * t
        rr = r * (0.35 + 0.65 * t)
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=(255, 230, 180, int(25 + 150 * t ** 2)))
    base.alpha_composite(layer.filter(ImageFilter.GaussianBlur(6)))
    glow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((bx - r * 3, by - r * 3, bx + r * 3, by + r * 3), fill=(255, 220, 160, 120))
    base.alpha_composite(glow.filter(ImageFilter.GaussianBlur(18)))
    d = ImageDraw.Draw(base)
    d.ellipse((bx - r, by - r, bx + r, by + r), fill=(250, 248, 240))
    d.ellipse((bx - r + 5, by - r + 4, bx + r - 9, by + r - 10), fill=(255, 255, 255))
    d.arc((bx - r + 3, by - r - 2, bx + r + 9, by + r + 2), 120, 230, fill=(170, 160, 150), width=2)


def grade_and_grain(im):
    a = arr(im.convert("RGB"))
    # gentle S-curve + lifted blacks toward deep blue
    a = 255 * (0.5 + 0.5 * np.tanh((a / 255 - 0.5) * 1.6) / np.tanh(0.8))
    a = a * 0.96 + np.array([4, 6, 14], np.float32)
    a += rng.normal(0, 5.5, (H, W, 1)).astype(np.float32)
    return img(a)


def floor(base, top):
    """Black gradient under the headline zone."""
    a = np.zeros((H, W, 4), np.float32)
    ys = np.clip((np.arange(H) - top) / (H - top), 0, 1)
    a[..., 3] = (ys ** 0.8 * 245)[:, None]
    base.alpha_composite(img(a, "RGBA"))


def main():
    base = background()

    # LEFT - Shoaib, the challenge: desaturated, green-shadowed, set back
    sh = load_cut("cut_wc_shoaib.png", 900)
    sh = regrade(sh, color=0.32, contrast=1.3, bright=0.85, tint=(60, 130, 90), tint_k=0.3)
    sh = directional_light(sh, "right", (225, 240, 230), 0.9)
    sh = fade_bottom(sh, 500, 720)
    place(base, sh, -170, -40, rims=[((80, 170, 120), 16, 0.7)])

    # RIGHT - the upper-cut: warm saffron/gold key, electric-blue rim
    up = load_cut("cut_wc_sachin_uppercut.png", 700)
    up = regrade(up, color=1.2, contrast=1.15, bright=1.05, sharpen=(2.5, 140, 2))
    up = directional_light(up, "right", SAFFRON, 0.9)
    up = fade_bottom(up, 560, 700)
    ux, uy = W - up.width - 120, 48
    place(base, up, ux, uy, rims=[(GOLD, 20, 1.0), ((90, 170, 255), 6, 0.9)])
    # ball flies off the top of the bat toward the upper-right corner
    ball_with_trail(base, W - 92, 74, ux + up.width - 40, uy + 150)

    # CENTRE - the hero
    hero = load_cut("cut_wc_sachin_hero.png", 900)
    hero = regrade(hero, color=1.1, contrast=1.08, bright=1.2, sharpen=(2, 70, 2))
    hero = directional_light(hero, "left", (255, 214, 170), 0.55)
    hero = fade_bottom(hero, 560, 840)
    face_cx = int(hero.width * 0.55)
    hx, hy = 960 - face_cx, 70
    place(base, hero, hx, hy, rims=[(ICE, 26, 1.1), ((255, 255, 255), 5, 0.8)])
    # soft key on the face to lift the helmet shadow, limited to the hero's own pixels
    hero_a = Image.new("L", (W, H), 0)
    hero_a.paste(hero.getchannel("A"), (hx, hy))
    lift = radial(965, 370, 230, 200, 1.4) * (arr(hero_a) / 255)
    b = arr(base)
    b[..., :3] = b[..., :3] + (255 - b[..., :3]) * lift[..., None] * 0.22
    base = img(b, "RGBA")

    finish(base, "thumb_D_wc2003_belief")


def headline(base):
    floor(base, 560)
    banner(base, "WORLD CUP 2003", 56, W // 2, 668)
    _, _, _, bottom = shadow_text(base, "INDIA'S BELIEF", 200, W // 2, 752, (255, 255, 255), stroke=5, tracking=4)
    # red accent bar between the two headlines
    d = ImageDraw.Draw(base)
    d.rectangle((W // 2 - 300, bottom + 18, W // 2 + 300, bottom + 26), fill=RED + (255,))
    l2 = ImageFont.truetype(ANTON, 92)
    w1, w2 = l2.getlength("CHANGED "), l2.getlength("FOREVER?")
    left = W / 2 - (w1 + w2) / 2
    shadow_text(base, "CHANGED", 92, left + w1 / 2 - l2.getlength(" ") / 2, bottom + 40, (255, 255, 255), stroke=4)
    shadow_text(base, "FOREVER?", 92, left + w1 + w2 / 2, bottom + 40, SAFFRON, stroke=4)


def finish(base, name):
    out = grade_and_grain(base)
    out.save(os.path.join(HERE, name + ".png"))
    out.save(os.path.join(HERE, name + ".jpg"), quality=94)
    out.resize((320, 180), Image.LANCZOS).save(os.path.join(HERE, name + "_small.png"))
    print("wrote", name)


def main_hq():
    """Same layout from the higher-resolution stills supplied for the thumbnail (cut_hq_*)."""
    base = background()

    # LEFT - Shoaib staring across at Sachin, desaturated and set back
    sh = load_cut("cut_hq_shoaib_stare.png", 900)
    sh = regrade(sh, color=0.3, contrast=1.3, bright=0.8, sharpen=(2, 90, 2), tint=(60, 130, 90), tint_k=0.3)
    sh = directional_light(sh, "right", (225, 240, 230), 0.9)
    sh = fade_bottom(sh, 420, 700)
    place(base, sh, -140, 10, rims=[((80, 170, 120), 16, 0.7)])

    # RIGHT - the upper-cut
    up = load_cut("cut_wc_sachin_uppercut.png", 640)
    up = regrade(up, color=1.2, contrast=1.15, bright=1.05, sharpen=(2.5, 140, 2))
    up = directional_light(up, "right", SAFFRON, 0.9)
    up = fade_bottom(up, 500, 640)
    ux, uy = W - up.width - 70, 60
    place(base, up, ux, uy, rims=[(GOLD, 20, 1.0), ((90, 170, 255), 6, 0.9)])
    ball_with_trail(base, W - 70, 70, ux + up.width - 40, uy + 140)

    # CENTRE - the hero close-up
    hero = load_cut("cut_hq_sachin_cap.png", 760)
    hero = regrade(hero, color=1.08, contrast=1.1, bright=1.06, sharpen=(1.6, 80, 2))
    hero = directional_light(hero, "left", (255, 214, 170), 0.45)
    hero = fade_bottom(hero, 600, 740)
    hx, hy = 960 - int(hero.width * 0.48), 0
    place(base, hero, hx, hy, rims=[(ICE, 26, 1.1), ((255, 255, 255), 5, 0.8)])

    headline(base)
    finish(base, "thumb_E_wc2003_belief_hq")

if __name__ == "__main__":
    main()
    main_hq()

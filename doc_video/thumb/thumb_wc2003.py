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


def place(base, im, x, y, depth=0.0, haze=0.0, wrap=0.55, rim_color=None, rim_side=1, rim_k=0.0, shadow=0.55):
    """Composite a cut-out into the scene instead of pasting it on top.

    Defringes the matte (pulls edge colour from the subject's interior so the source photo's
    background doesn't cling to it), matches its blacks/haze to the scene, drops a soft contact
    shadow, wraps the blurred scene light around the edges, and adds a directional edge light on
    the side facing the key light (rim_side 1 = from the right, -1 = from the left).
    """
    a = arr(im.getchannel("A")) / 255
    rgb = arr(im.convert("RGB"))
    core = arr(im.getchannel("A").filter(ImageFilter.MinFilter(7))) / 255
    num = np.stack([arr(img(rgb[..., c] * core, "L").filter(ImageFilter.GaussianBlur(6))) for c in range(3)], -1)
    den = arr(img(core * 255, "L").filter(ImageFilter.GaussianBlur(6)))[..., None] / 255 + 1e-4
    inner = np.clip(num / den, 0, 255)
    band = np.clip(1 - core, 0, 1)[..., None] * (den > 0.02)
    rgb = rgb * (1 - band) + inner * band
    a = arr(img(a * 255, "L").filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.7 + depth))) / 255

    # scene under the subject (for colour match and light wrap)
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + im.width), min(H, y + im.height)
    scene = np.zeros_like(rgb)
    blur_bg = arr(base.convert("RGB").filter(ImageFilter.GaussianBlur(30)))
    scene[y0 - y:y1 - y, x0 - x:x1 - x] = blur_bg[y0:y1, x0:x1]
    mean = scene[a > 0.5].mean(0) if (a > 0.5).any() else np.zeros(3)

    if depth:
        rgb = arr(img(rgb).filter(ImageFilter.GaussianBlur(depth)))
    lum = rgb.mean(-1, keepdims=True) / 255
    rgb = rgb + (mean * 0.9 - rgb) * (1 - lum) ** 2 * 0.35  # shadows take the scene's colour
    rgb = rgb * 0.94 + mean * 0.06
    rgb = rgb * (1 - haze) + scene * haze  # atmospheric depth for set-back figures

    # light wrap: the scene's blurred light bleeds over the inside of the edge
    soft = arr(img(a * 255, "L").filter(ImageFilter.GaussianBlur(16))) / 255
    wrapm = np.clip((a - soft) * 2.2, 0, 1)[..., None] * wrap
    rgb = rgb + (255 - rgb) * (scene / 255) * wrapm

    # directional edge light on the side facing the key light
    if rim_color and rim_k:
        sh = np.roll(a, -rim_side * 10, axis=1)
        rimm = np.clip(a - sh, 0, 1)
        rimm = arr(img(rimm * 255, "L").filter(ImageFilter.GaussianBlur(4))) / 255 * a
        rgb = rgb + (np.array(rim_color, np.float32) - rgb * 0.3) * rimm[..., None] * rim_k

    if shadow:
        sa = img(a * 255 * shadow, "L").filter(ImageFilter.GaussianBlur(28))
        sl = Image.new("RGBA", im.size, (0, 0, 0, 0))
        sl.putalpha(sa)
        p = 40
        base.alpha_composite(pad(sl, p).filter(ImageFilter.GaussianBlur(10)), (x - p + 14, y - p + 18))

    out = np.dstack([np.clip(rgb, 0, 255), a * 255])
    base.alpha_composite(img(out, "RGBA"), (x, y))


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
    place(base, sh, -170, -40, depth=1.2, haze=0.12, rim_color=(190, 235, 205), rim_side=1, rim_k=0.35)

    # RIGHT - the upper-cut: warm saffron/gold key, electric-blue rim
    up = load_cut("cut_wc_sachin_uppercut.png", 700)
    up = regrade(up, color=1.2, contrast=1.15, bright=1.05, sharpen=(2.5, 140, 2))
    up = directional_light(up, "right", SAFFRON, 0.9)
    up = fade_bottom(up, 560, 700)
    ux, uy = W - up.width - 120, 48
    place(base, up, ux, uy, depth=0.8, haze=0.06, rim_color=GOLD, rim_side=1, rim_k=0.55)
    # ball flies off the top of the bat toward the upper-right corner
    ball_with_trail(base, W - 92, 74, ux + up.width - 40, uy + 150)

    # CENTRE - the hero
    hero = load_cut("cut_wc_sachin_hero.png", 900)
    hero = regrade(hero, color=1.1, contrast=1.08, bright=1.2, sharpen=(2, 70, 2))
    hero = directional_light(hero, "left", (255, 214, 170), 0.55)
    hero = fade_bottom(hero, 560, 840)
    face_cx = int(hero.width * 0.55)
    hx, hy = 960 - face_cx, 70
    place(base, hero, hx, hy, wrap=0.45, rim_color=ICE, rim_side=-1, rim_k=0.4, shadow=0.75)
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
    """Same layout from the supplied stills, upscaled 4x with Real-ESRGAN (cut_x4_*), so every layer is downscaled."""
    base = background()

    # LEFT - Shoaib staring across at Sachin, desaturated and set back
    sh = load_cut("cut_x4_shoaib_stare.png", 760)
    sh = regrade(sh, color=0.35, contrast=1.25, bright=0.85, sharpen=(1.0, 60, 1), tint=(60, 130, 90), tint_k=0.25)
    sh = directional_light(sh, "right", (225, 240, 230), 0.8)
    sh = fade_bottom(sh, 440, 640)
    place(base, sh, -70, 30, rim_color=(190, 235, 205), rim_side=1, rim_k=0.3)

    # RIGHT - the upper-cut
    up = load_cut("cut_x4_sachin_uppercut.png", 600)
    up = regrade(up, color=1.15, contrast=1.15, bright=1.05, sharpen=(1.0, 60, 1))
    up = directional_light(up, "right", SAFFRON, 0.8)
    up = fade_bottom(up, 470, 600)
    ux, uy = W - up.width - 90, 50
    place(base, up, ux, uy, rim_color=GOLD, rim_side=1, rim_k=0.5, shadow=0)
    ball_with_trail(base, W - 70, 70, ux + up.width - 40, uy + 140)

    # CENTRE - the hero close-up
    hero = load_cut("cut_x4_sachin_cap.png", 760)
    hero = regrade(hero, color=1.08, contrast=1.1, bright=1.06, sharpen=(1.0, 50, 1))
    hero = directional_light(hero, "left", (255, 214, 170), 0.45)
    hero = fade_bottom(hero, 600, 740)
    # the source photo crops the top of the cap; keep that edge just above the frame
    hx, hy = 960 - int(hero.width * 0.48), -50
    place(base, hero, hx, hy, wrap=0.45, rim_color=ICE, rim_side=-1, rim_k=0.4, shadow=0.75)

    headline(base)
    finish(base, "thumb_E_wc2003_belief_hq")


def main_final():
    """Shoaib head-in-hand (2003 WC kit, 4x upscaled) left, hi-res Sachin hook right, cap close-up centre."""
    base = background()

    # LEFT - Shoaib, hand to his head: the challenge India answered
    sh = load_cut("cut_x4_shoaib_head.png", 600)
    sh = regrade(sh, color=0.55, contrast=1.15, bright=1.12, sharpen=(1.0, 60, 1), tint=(60, 130, 90), tint_k=0.15)
    sh = directional_light(sh, "right", (225, 240, 230), 0.7)
    sh = fade_bottom(sh, 470, 600)
    place(base, sh, -90, 70, rim_color=(190, 235, 205), rim_side=1, rim_k=0.3)

    # RIGHT - Sachin's hook, ball in the air; warm saffron key
    hk = load_cut("cut_hq_sachin_hook.png", 880)
    hk = regrade(hk, color=1.1, contrast=1.12, bright=1.02, sharpen=(1.0, 60, 1))
    hk = directional_light(hk, "right", SAFFRON, 0.75)
    hk = fade_bottom(hk, 540, 760)
    place(base, hk, W - hk.width - 40, 20, rim_color=GOLD, rim_side=1, rim_k=0.5, shadow=0)

    # CENTRE - the hero close-up
    hero = load_cut("cut_x4_sachin_cap.png", 740)
    hero = regrade(hero, color=1.08, contrast=1.1, bright=1.06, sharpen=(1.0, 50, 1))
    hero = directional_light(hero, "left", (255, 214, 170), 0.45)
    hero = fade_bottom(hero, 590, 720)
    hx, hy = 930 - int(hero.width * 0.48), -50  # cap crop sits just above the frame
    place(base, hero, hx, hy, wrap=0.45, rim_color=ICE, rim_side=-1, rim_k=0.4, shadow=0.75)

    headline(base)
    finish(base, "thumb_F_wc2003_belief")


if __name__ == "__main__":
    main()
    main_hq()
    main_final()

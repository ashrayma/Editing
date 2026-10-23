#!/usr/bin/env python3
"""Render the "Ranking the best days as a Kohli fan" countdown reel.

Usage:
    python3 render.py [config.json] [--preview]     # --preview = half-res, quick look

Everything (motion graphics, text, SFX, beat) is generated here. Drop your own
photos / face-cam into config.json ("image" per item, "facecam" at the top) and
re-render; nothing else needs touching.
"""
import json
import math
import os
import subprocess
import sys
import wave
from functools import lru_cache
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import sfx

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1920
FONT_DIR = "/usr/share/fonts/opentype/inter"
FONTS = {
    "black": "InterDisplay-Black.otf",
    "xbold": "InterDisplay-ExtraBold.otf",
    "bold": "Inter-Bold.otf",
    "semi": "Inter-SemiBold.otf",
    "italic": "InterDisplay-BoldItalic.otf",
}

GOLD = (255, 196, 0)
BLUE = (30, 91, 255)
WHITE = (255, 255, 255)
MUTED = (160, 176, 210)
INK = (8, 11, 22)

CFG = None
SEGMENTS = []


# ----------------------------------------------------------------------------- helpers

def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def prog(t, t0, dur):
    return clamp((t - t0) / dur)


def ease_out(x):
    return 1 - (1 - x) ** 3


def ease_in(x):
    return x ** 3


def ease_back(x, s=1.9):
    x -= 1
    return x * x * ((s + 1) * x + s) + 1


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


@lru_cache(maxsize=64)
def font(weight, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, FONTS[weight]), size)


@lru_cache(maxsize=512)
def text_img(text, weight, size, fill=WHITE, stroke=0, stroke_fill=INK, tracking=0):
    f = font(weight, size)
    if tracking:
        # letter-spaced text: draw glyph by glyph
        widths = [f.getlength(c) + tracking for c in text]
        w = int(sum(widths)) + 2 * stroke + 4
        asc, desc = f.getmetrics()
        im = Image.new("RGBA", (w, asc + desc + 2 * stroke + 4), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        x = stroke + 2
        for c, cw in zip(text, widths):
            d.text((x, stroke + 2), c, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
            x += cw
        return im
    l, t, r, b = f.getbbox(text, stroke_width=stroke)
    im = Image.new("RGBA", (r - l + 8, b - t + 8), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4 - l, 4 - t), text, font=f, fill=fill,
                            stroke_width=stroke, stroke_fill=stroke_fill)
    return im


def with_alpha(im, a):
    if a >= 0.999:
        return im
    im = im.copy()
    im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    return im


def place(layer, im, cx, cy, scale=1.0, alpha=1.0, anchor="c"):
    """Composite `im` onto `layer` centred (or left-anchored) at cx, cy."""
    if alpha <= 0.003 or scale <= 0.01:
        return
    if abs(scale - 1) > 0.002:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    im = with_alpha(im, alpha)
    x = int(cx - (im.width / 2 if anchor == "c" else 0))
    y = int(cy - im.height / 2)
    layer.paste(im, (x, y), im) if (x < 0 or y < 0) else layer.alpha_composite(im, (x, y))


@lru_cache(maxsize=8)
def gradient_bg(accent):
    y = np.linspace(0, 1, H)[:, None, None]
    top = np.array([12, 16, 34], float)
    bot = np.array([3, 4, 10], float)
    base = top * (1 - y) + bot * y
    # soft accent glow behind the rank number
    yy, xx = np.mgrid[0:H, 0:W]
    glow = np.exp(-(((xx - W / 2) / 520) ** 2 + ((yy - 520) / 420) ** 2))[..., None]
    img = base + glow * np.array(accent, float) * 0.28
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


BOKEH = [(np.random.default_rng(i).uniform(0, W), np.random.default_rng(i + 99).uniform(0, H),
          np.random.default_rng(i + 7).uniform(20, 90), np.random.default_rng(i + 3).uniform(-25, 25))
         for i in range(14)]


def draw_background(t, accent, ghost=None):
    bg = gradient_bg(accent).copy().convert("RGBA")
    over = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    for x, y, r, v in BOKEH:  # drifting stadium-light bokeh
        yy = (y - t * (30 + v)) % (H + 200) - 100
        xx = x + 20 * math.sin(t * 0.7 + r)
        d.ellipse((xx - r, yy - r, xx + r, yy + r), fill=accent + (16,))
    # diagonal light sweep
    sx = ((t * 520) % (W + 1400)) - 700
    d.polygon([(sx, 0), (sx + 160, 0), (sx - 640, H), (sx - 800, H)], fill=(255, 255, 255, 9))
    over = over.filter(ImageFilter.GaussianBlur(6))
    bg.alpha_composite(over)
    if ghost:
        g = text_img(ghost, "black", 900, fill=accent + (22,))
        place(bg, g, W / 2 + 30 * math.sin(t * 0.5), 980 + 10 * math.cos(t * 0.4))
    return bg


def rounded_mask(size, r):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), r, fill=255)
    return m


@lru_cache(maxsize=16)
def load_image(path):
    return Image.open(path if os.path.isabs(path) else os.path.join(HERE, path)).convert("RGB")


def ken_burns(path, size, t, dur, seed):
    im = load_image(path)
    zoom = 1.08 + 0.10 * (t / dur)
    sc = max(size[0] / im.width, size[1] / im.height) * zoom
    rw, rh = size[0] / sc, size[1] / sc
    dx = (im.width - rw) * (0.5 + 0.35 * math.sin(seed) * (t / dur - 0.5))
    dy = (im.height - rh) * 0.4
    return im.crop((int(dx), int(dy), int(dx + rw), int(dy + rh))).resize(size, Image.LANCZOS)


# ----------------------------------------------------------------------------- scene pieces

CARD = (70, 690, 1010, 1210)


def draw_header(layer, rank, t, accent):
    place(layer, text_img("BEST DAYS AS A KOHLI FAN", "bold", 30, fill=(200, 210, 235), tracking=5), W / 2, 185)
    n = len(CFG["items"])
    x0, x1, y = 150, 930, 238
    seg = (x1 - x0) / n
    over = Image.new("RGBA", (W, 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    y -= 220
    for i in range(n):
        r = n - i  # leftmost bar = #10
        bx = x0 + i * seg
        if r > rank:
            col = (255, 255, 255, 150)
        elif r == rank:
            pulse = 0.6 + 0.4 * abs(math.sin(t * 4))
            col = accent + (int(255 * pulse),)
        else:
            col = (255, 255, 255, 40)
        d.rounded_rectangle((bx + 4, y, bx + seg - 4, y + 10), 5, fill=col)
    layer.alpha_composite(over, (0, 220))


def draw_card(layer, item, t, accent, idx):
    p = ease_out(prog(t, 0.3, 0.45))
    if p <= 0:
        return
    w, h = CARD[2] - CARD[0], CARD[3] - CARD[1]
    if item.get("image"):
        card = ken_burns(item["image"], (w, h), t, item["duration"], idx).convert("RGBA")
        shade = np.zeros((h, w, 4), np.uint8)
        shade[..., 3] = (np.clip((np.linspace(0, 1, h) - 0.45) / 0.55, 0, 1) ** 1.5 * 235)[:, None]
        card.alpha_composite(Image.fromarray(shade, "RGBA"))
    else:
        yy, xx = np.mgrid[0:h, 0:w]
        f = (xx / w * 0.6 + yy / h * 0.4)[..., None]
        arr = np.array(accent, float) * (1 - f) * 0.85 + np.array(INK, float) * f
        # moving pinstripes
        stripes = (((xx + yy + t * 120) // 26) % 2 == 0)[..., None] * 10
        card = Image.fromarray(np.clip(arr + stripes, 0, 255).astype(np.uint8)).convert("RGBA")
    card.putalpha(rounded_mask((w, h), 42))
    # border glow
    border = Image.new("RGBA", (w + 60, h + 60), (0, 0, 0, 0))
    ImageDraw.Draw(border).rounded_rectangle((30, 30, w + 29, h + 29), 44, outline=accent + (200,), width=5)
    border = border.filter(ImageFilter.GaussianBlur(8))
    scale = 0.9 + 0.1 * p
    cx, cy = (CARD[0] + CARD[2]) / 2, (CARD[1] + CARD[3]) / 2
    place(layer, border, cx, cy, scale, p)
    place(layer, card, cx, cy, scale, p)

    # stat counter
    cp = ease_out(prog(t, 0.9, 1.0))
    if cp > 0:
        val = int(round(item["stat"] * cp))
        txt = f"{val:,}{item.get('stat_suffix', '') if cp >= 1 else ''}"
        punch = 1 + 0.18 * max(0, 1 - (t - 1.9) / 0.25) if t >= 1.9 else 1
        big = 210 if not item.get("image") else 150
        sy = cy - 20 if not item.get("image") else CARD[3] - 130
        place(layer, text_img(txt, "black", big, fill=WHITE, stroke=4, stroke_fill=INK), cx, sy, punch * scale, p)
        place(layer, text_img(item["stat_label"], "bold", 34, fill=WHITE if accent == GOLD else GOLD, tracking=3), cx, sy + big * 0.62, 1,
              ease_out(prog(t, 1.4, 0.4)))


def draw_rank_block(layer, item, t, accent):
    rank = item["rank"]
    sp = prog(t, 0.08, 0.32)
    if sp > 0:
        s = 2.6 - 1.6 * ease_back(sp)
        place(layer, text_img(f"#{rank}", "black", 210, fill=GOLD if rank > 1 else accent, stroke=6),
              W / 2, 410, s, min(1, sp * 3))
    words = item["title"].upper().split()
    imgs = [text_img(w_, "black", 80, fill=WHITE, stroke=3) for w_ in words]
    space = 22
    total = sum(i.width for i in imgs) + space * (len(imgs) - 1)
    scale_fit = min(1, 940 / total)
    x = W / 2 - total * scale_fit / 2
    for k, im in enumerate(imgs):
        wp = prog(t, 0.45 + 0.08 * k, 0.22)
        if wp > 0:
            s = scale_fit * (0.5 + 0.5 * ease_back(wp))
            place(layer, im, x + im.width * scale_fit / 2, 565, s, min(1, wp * 2))
        x += (im.width + space) * scale_fit
    place(layer, text_img(item["sub"], "semi", 34, fill=MUTED), W / 2, 640, 1, ease_out(prog(t, 0.75, 0.35)))


def chip_img(text, accent):
    f = font("bold", 38)
    tw = int(f.getlength(text))
    w, h = tw + 120, 78
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 39, fill=(255, 255, 255, 235))
    d.ellipse((12, 12, 66, 66), fill=accent + (255,))
    d.line([(26, 40), (36, 50), (53, 29)], fill=WHITE, width=7, joint="curve")
    d.text((86, h / 2), text, font=f, fill=INK, anchor="lm")
    return im


def draw_extras(layer, item, t, accent):
    """Quote typewriter / ball-by-ball pills, then the check-mark chips. Returns SFX cue times."""
    y = 1290
    t_chip = 2.15
    if item.get("balls"):
        balls = item["balls"]
        n = len(balls)
        gap = 128
        x0 = W / 2 - gap * (n - 1) / 2
        for k, b in enumerate(balls):
            bp = prog(t, 2.0 + 0.2 * k, 0.2)
            if bp > 0:
                ball = Image.new("RGBA", (112, 112), (0, 0, 0, 0))
                bd = ImageDraw.Draw(ball)
                fill = GOLD if b in ("4", "6") else (230, 235, 245)
                if b == "6":
                    fill = accent
                bd.ellipse((4, 4, 107, 107), fill=fill + (255,))
                bd.text((56, 58), b, font=font("black", 58), fill=INK if b != "6" else WHITE, anchor="mm")
                place(layer, ball, x0 + gap * k, y, ease_back(bp), 1)
        place(layer, text_img(item["balls_label"], "bold", 34, fill=WHITE), W / 2, y + 92, 1,
              ease_out(prog(t, 2.0 + 0.2 * n, 0.3)))
        y += 190
        t_chip = 2.0 + 0.2 * n + 0.4
    if item.get("quote"):
        q = "“" + item["quote"] + "”"
        qp = prog(t, 1.9, len(q) * 0.028)
        shown = q[:int(len(q) * qp)]
        if shown:
            # wrap to two lines max
            f = font("italic", 46)
            words, lines, cur = shown.split(" "), [], ""
            for w_ in words:
                if f.getlength((cur + " " + w_).strip()) > 900:
                    lines.append(cur)
                    cur = w_
                else:
                    cur = (cur + " " + w_).strip()
            lines.append(cur)
            for li, line in enumerate(lines):
                place(layer, text_img(line, "italic", 46, fill=WHITE), 90, y + li * 62, anchor="l")
        y += 70 + 62 * 1 + (62 if font("italic", 46).getlength(q) > 900 else 0)
        t_chip = 1.9 + len(q) * 0.028 + 0.3
    for k, c in enumerate(item.get("chips", [])):
        cp = prog(t, t_chip + 0.45 * k, 0.3)
        if cp > 0:
            im = chip_img(c, accent)
            place(layer, im, 90 - 300 * (1 - ease_out(cp)), y + k * 96, 1, min(1, cp * 2), anchor="l")
    return t_chip


CONFETTI = [(np.random.default_rng(s).uniform(0, W), np.random.default_rng(s + 1).uniform(380, 720),
             np.random.default_rng(s + 2).uniform(-80, 80), np.random.default_rng(s + 3).uniform(0, 6.28),
             s % 3) for s in range(110)]


def draw_confetti(layer, t, accent):
    if t < 0:
        return
    d = ImageDraw.Draw(layer)
    cols = [GOLD, accent, WHITE]
    for x, vy, vx, ph, ci in CONFETTI:
        yy = -40 + vy * t + 60 * t * t
        xx = x + vx * t + 30 * math.sin(t * 3 + ph)
        if yy > H:
            continue
        a = 9 * abs(math.cos(t * 5 + ph)) + 3
        d.polygon([(xx - 9, yy - a), (xx + 9, yy - a), (xx + 9, yy + a), (xx - 9, yy + a)], fill=cols[ci] + (230,))


# ----------------------------------------------------------------------------- scenes

def scene_item(t, item, idx):
    accent = hex_rgb(item["accent"]) if item.get("accent") else (BLUE if item["rank"] > 3 else GOLD)
    bg = draw_background(t, accent, ghost=str(item["rank"]))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_header(bg, item["rank"], t, accent)
    draw_rank_block(layer, item, t, accent)
    draw_card(layer, item, t, accent, idx)
    draw_extras(layer, item, t, accent)
    if item.get("crowd"):
        draw_confetti(layer, t - 1.9, accent)
    dur = item["duration"]
    # entrance slide, exit whip, impact shake
    dx = int(W * 0.4 * (1 - ease_out(prog(t, 0, 0.28))))
    dx -= int(W * 0.5 * ease_in(prog(t, dur - 0.2, 0.2)))
    shake = max(0, 1 - (t - 0.36) / 0.3) if t >= 0.36 else 0
    dx += int(16 * shake * math.sin(t * 90))
    dy = int(12 * shake * math.cos(t * 77))
    bg.paste(layer, (dx, dy), layer)
    return flash(bg, t)


def flash(img, t, length=0.16):
    a = 1 - t / length
    if a > 0:
        img = Image.blend(img, Image.new("RGBA", img.size, (255, 255, 255, 255)), 0.75 * a)
    return img


def scene_hook(t, hook):
    bg = draw_background(t, GOLD, ghost="18")
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if hook.get("image"):
        im = ken_burns(hook["image"], (940, 760), t, hook["duration"], 1).convert("RGBA")
        im.putalpha(rounded_mask(im.size, 42))
        place(layer, im, W / 2, 1180, 1, ease_out(prog(t, 0.2, 0.4)) * 0.85)
    sizes = [96, 96, 150]
    ys = [700, 820, 980]
    for k, (line, sz, y) in enumerate(zip(hook["lines"], sizes, ys)):
        p = prog(t, 0.1 + 0.32 * k, 0.26)
        if p > 0:
            col = GOLD if k == len(hook["lines"]) - 1 else WHITE
            place(layer, text_img(line, "black", sz, fill=col, stroke=5), W / 2, y, 2.2 - 1.2 * ease_back(p), min(1, 3 * p))
    bp = prog(t, 0.95, 0.35)
    if bp > 0:  # TOP 10 badge
        badge = Image.new("RGBA", (260, 260), (0, 0, 0, 0))
        bd = ImageDraw.Draw(badge)
        bd.ellipse((10, 10, 250, 250), fill=(224, 38, 43, 255), outline=WHITE + (255,), width=6)
        bd.text((130, 100), "TOP", font=font("black", 50), fill=WHITE, anchor="mm")
        bd.text((130, 162), "10", font=font("black", 92), fill=WHITE, anchor="mm")
        badge = badge.rotate(-14 + 360 * (1 - ease_out(bp)), resample=Image.BICUBIC)
        place(layer, badge, 870, 510, ease_back(bp), 1)
    tp = prog(t, 1.4, 0.9)
    if tp > 0:
        txt = hook["tease"][:max(1, int(len(hook["tease"]) * tp))]
        im = text_img(txt.upper(), "xbold", 46, fill=WHITE)
        pill = Image.new("RGBA", (im.width + 70, im.height + 40), (0, 0, 0, 0))
        ImageDraw.Draw(pill).rounded_rectangle((0, 0, pill.width - 1, pill.height - 1), 30, fill=(224, 38, 43, 240))
        pill.alpha_composite(im, (35, 20))
        place(layer, pill, W / 2, 1190, 1, 1)
    zoom_dx = int(8 * math.sin(t * 2))
    shake = max(0, 1 - (t - 0.8) / 0.3) if t >= 0.8 else 0
    bg.paste(layer, (zoom_dx + int(14 * shake * math.sin(t * 90)), int(10 * shake * math.cos(t * 70))), layer)
    return bg


def scene_suspense(t, dur):
    bg = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    beat = abs(math.sin(t / dur * math.pi * 2))
    place(bg, text_img("AND AT #1...", "black", 110, fill=WHITE), W / 2, H / 2 - 80, 1 + 0.06 * beat,
          ease_out(prog(t, 0.05, 0.3)))
    place(bg, text_img("the day we waited 18 years for", "semi", 40, fill=MUTED), W / 2, H / 2 + 30, 1,
          ease_out(prog(t, 0.45, 0.3)))
    return bg


def scene_outro(t, outro):
    bg = draw_background(t, GOLD, ghost="?")
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    p1 = prog(t, 0.05, 0.25)
    if p1 > 0:
        place(layer, text_img(outro["lines"][0], "black", 110, fill=WHITE, stroke=5), W / 2, 700,
              2 - ease_back(p1), min(1, 3 * p1))
    p2 = prog(t, 0.35, 0.3)
    if p2 > 0:
        pulse = 1 + 0.05 * math.sin(t * 8) if t > 0.8 else 1
        place(layer, text_img(outro["lines"][1], "black", 320, fill=GOLD, stroke=8), W / 2, 920,
              (2.4 - 1.4 * ease_back(p2)) * pulse, min(1, 3 * p2))
    p3 = prog(t, 1.0, 0.35)
    if p3 > 0:
        im = text_img(outro["cta"], "bold", 40, fill=INK)
        pill = Image.new("RGBA", (im.width + 80, im.height + 44), (0, 0, 0, 0))
        ImageDraw.Draw(pill).rounded_rectangle((0, 0, pill.width - 1, pill.height - 1), 34, fill=WHITE + (245,))
        pill.alpha_composite(im, (40, 22))
        place(layer, pill, W / 2, 1160, ease_back(p3), 1)
        # bouncing arrow pointing at the comments
        ay = 1290 + 22 * abs(math.sin(t * 6))
        d = ImageDraw.Draw(layer)
        d.polygon([(W / 2 - 44, ay), (W / 2 + 44, ay), (W / 2, ay + 56)], fill=GOLD + (255,))
    bg.paste(layer, (0, 0), layer)
    return flash(bg, t)


# ----------------------------------------------------------------------------- timeline + audio

def build_timeline(cfg):
    segs = [("hook", cfg["hook"], 0.0, cfg["hook"]["duration"])]
    t = cfg["hook"]["duration"]
    for idx, item in enumerate(cfg["items"]):
        if item["rank"] == 1:
            segs.append(("suspense", None, t, 1.3))
            t += 1.3
        segs.append(("item", (item, idx), t, item["duration"]))
        t += item["duration"]
    segs.append(("outro", cfg["outro"], t, cfg["outro"]["duration"]))
    return segs, t + cfg["outro"]["duration"]


def sfx_events(segs):
    ev = []  # (time, sound, gain)
    for kind, data, t0, dur in segs:
        if kind == "hook":
            ev += [(0.05, "impact", 0.8), (0.42, "impact", 0.6), (0.72, "impact", 1.0),
                   (0.9, "whoosh", 0.6), (1.2, "ding", 0.5)]
            ev += [(t0 + 1.4 + k * 0.06, "tick", 0.25) for k in range(15)]
        elif kind == "suspense":
            ev += [(t0 + 0.0, "heartbeat", 1.0), (t0 + 0.65, "heartbeat", 1.0), (t0 - 0.6, "riser", 0.7)]
        elif kind == "outro":
            ev += [(t0 - 0.12, "whoosh", 0.8), (t0 + 0.05, "impact", 0.6), (t0 + 0.42, "impact", 0.9),
                   (t0 + 1.0, "pop", 0.8), (t0 + 1.05, "ding", 0.6)]
        else:
            item, _ = data
            ev += [(t0 - 0.14, "whoosh", 0.9), (t0 + 0.3, "impact", 1.0 if item["rank"] > 1 else 1.2)]
            ev += [(t0 + 0.45 + 0.08 * k, "pop", 0.35) for k in range(len(item["title"].split()))]
            ev += [(t0 + 0.9 + k * 0.07, "tick", 0.3) for k in range(13)]
            ev += [(t0 + 1.9, "ding", 0.7)]
            t_chip = 2.15
            if item.get("balls"):
                ev += [(t0 + 2.0 + 0.2 * k, "pop" if b not in ("4", "6") else "impact", 0.45 if b in ("4", "6") else 0.5)
                       for k, b in enumerate(item["balls"])]
                t_chip = 2.0 + 0.2 * len(item["balls"]) + 0.4
            if item.get("quote"):
                q = len(item["quote"]) + 2
                ev += [(t0 + 1.9 + k * 0.028 * 3, "tick", 0.12) for k in range(q // 3)]
                t_chip = 1.9 + q * 0.028 + 0.3
            ev += [(t0 + t_chip + 0.45 * k + 0.05, "pop", 0.7) for k in range(len(item.get("chips", [])))]
            if item.get("crowd"):
                ev += [(t0 + 1.7, "crowd", 0.75), (t0 + 1.9, "camera_shutter", 0.6)]
    return ev


def build_audio(segs, total, music, path):
    cache = {}
    mix = np.zeros(int(sfx.SR * (total + 2)), np.float32)
    for t, name, gain in sfx_events(segs):
        if name not in cache:
            cache[name] = getattr(sfx, name)()
        s = cache[name]
        i = max(0, int(t * sfx.SR))
        seg = s[: len(mix) - i]
        mix[i:i + len(seg)] += seg * gain * 0.5
    if music:
        bed = sfx.beat_bed(total)
        fade = np.minimum(1, np.minimum(np.arange(len(bed)) / sfx.SR / 0.5, (total - np.arange(len(bed)) / sfx.SR) / 1.5))
        mix[:len(bed)] += bed * np.clip(fade, 0, 1) * 0.22
    mix = mix[: int(sfx.SR * total)]
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    mix = mix / max(1e-6, np.abs(mix).max()) * 0.89  # ~ -1 dBFS peak
    pcm = (mix * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sfx.SR)
        w.writeframes(pcm.tobytes())


# ----------------------------------------------------------------------------- render

def render_frame(i):
    t = i / CFG["fps"]
    for kind, data, t0, dur in SEGMENTS:
        if t0 <= t < t0 + dur:
            lt = t - t0
            if kind == "hook":
                img = scene_hook(lt, data)
            elif kind == "suspense":
                img = scene_suspense(lt, dur)
            elif kind == "outro":
                img = scene_outro(lt, data)
            else:
                img = scene_item(lt, *data)
            break
    else:
        img = scene_outro(SEGMENTS[-1][3] - 0.01, SEGMENTS[-1][1])
    img = img.convert("RGB")
    if PREVIEW:
        img = img.resize((W // 2, H // 2), Image.BILINEAR)
    return img.tobytes()


PREVIEW = False


def main():
    global CFG, SEGMENTS, PREVIEW
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    PREVIEW = "--preview" in sys.argv
    cfg_path = args[0] if args else os.path.join(HERE, "config.json")
    with open(cfg_path) as f:
        CFG = json.load(f)
    SEGMENTS, total = build_timeline(CFG)
    out = os.path.join(HERE, CFG["output"])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    base, ext = os.path.splitext(out)
    if PREVIEW:
        base += "_preview"
    silent = base + "_video.mp4"
    nframes = int(total * CFG["fps"])
    ow, oh = (W // 2, H // 2) if PREVIEW else (W, H)
    print(f"Rendering {nframes} frames ({total:.1f}s) -> {out}")

    enc = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{ow}x{oh}",
         "-r", str(CFG["fps"]), "-i", "-", "-c:v", "libx264", "-preset", "medium",
         "-crf", "23" if PREVIEW else "17", "-pix_fmt", "yuv420p", silent],
        stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for k, buf in enumerate(pool.imap(render_frame, range(nframes), chunksize=4)):
            enc.stdin.write(buf)
            if k % 150 == 0:
                print(f"  frame {k}/{nframes}", flush=True)
    enc.stdin.close()
    enc.wait()

    video = silent
    if CFG.get("facecam"):
        fc = CFG["facecam"] if os.path.isabs(CFG["facecam"]) else os.path.join(HERE, CFG["facecam"])
        keyed = base + "_facecam.mp4"
        h = 380 if PREVIEW else 760
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", silent, "-i", fc, "-filter_complex",
             f"[1:v]chromakey={CFG.get('facecam_chroma', '0x00FF00')}:0.16:0.08,scale=-2:{h}[fc];"
             f"[0:v][fc]overlay=W-w+{h // 10}:H-h:shortest=0:eof_action=pass[v]",
             "-map", "[v]", "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", keyed], check=True)
        video = keyed

    voice = ["-af", "loudnorm=I=-14:TP=-1.5:LRA=11"]
    if CFG.get("facecam") and subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", fc],
            capture_output=True, text=True).stdout.strip():
        # keep your voice on top; SFX/music sit underneath
        voice = ["-i", fc, "-filter_complex",
                 "[1:a]volume=0.55[bed];[2:a]volume=1.0[vo];[bed][vo]amix=inputs=2:normalize=0:duration=first,"
                 "loudnorm=I=-14:TP=-1.5:LRA=11[a]",
                 "-map", "0:v", "-map", "[a]"]
    for music, suffix in ((CFG.get("music", True), ""), (False, "_sfx_only")):
        wav = base + suffix + ".wav"
        build_audio(SEGMENTS, total, music, wav)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", video, "-i", wav, *voice, "-c:v", "copy", "-ar", "44100", "-c:a", "aac",
                        "-b:a", "192k", "-shortest", "-movflags", "+faststart", base + suffix + ext], check=True)
        os.remove(wav)
    print("Done:", base + ext, "and", base + "_sfx_only" + ext)


if __name__ == "__main__":
    main()

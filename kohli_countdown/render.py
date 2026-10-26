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

import music as bgm
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

GOLD = (255, 196, 0)   # accent; replaced by the brand theme in apply_theme()
BLUE = (30, 91, 255)
BG_TOP, BG_BOT = (12, 16, 34), (3, 4, 10)
LOGO = None
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
    top = np.array(BG_TOP, float)
    bot = np.array(BG_BOT, float)
    base = top * (1 - y) + bot * y
    # soft accent glow behind the rank number
    yy, xx = np.mgrid[0:H, 0:W]
    glow = np.exp(-(((xx - W / 2) / 520) ** 2 + ((yy - 520) / 420) ** 2))[..., None]
    img = base + glow * np.array(accent, float) * 0.16
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
    """Slow push-in. Photos whose shape doesn't match the card sit on a blurred, darkened copy of themselves."""
    im = load_image(path)
    cover = max(size[0] / im.width, size[1] / im.height)
    contain = min(size[0] / im.width, size[1] / im.height)
    zoom = 1.0 + 0.10 * (t / dur)
    if cover / contain < 1.35:  # close enough in shape: plain cover crop
        sc = cover * (zoom + 0.06)
        rw, rh = size[0] / sc, size[1] / sc
        dx = (im.width - rw) * (0.5 + 0.35 * math.sin(seed) * (t / dur - 0.5))
        dy = (im.height - rh) * 0.3
        return im.crop((int(dx), int(dy), int(dx + rw), int(dy + rh))).resize(size, Image.LANCZOS)
    bg = blurred_fill(path, size)
    sc = min(contain * 1.18, cover) * zoom
    fg = im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)
    x = (size[0] - fg.width) // 2
    y = int((size[1] - fg.height) * 0.3)
    out = bg.copy()
    out.paste(fg, (x, y))
    return out


@lru_cache(maxsize=16)
def blurred_fill(path, size):
    im = load_image(path)
    sc = max(size[0] / im.width, size[1] / im.height) * 1.1
    big = im.resize((int(im.width * sc) + 1, int(im.height * sc) + 1))
    x, y = (big.width - size[0]) // 2, (big.height - size[1]) // 2
    big = big.crop((x, y, x + size[0], y + size[1])).filter(ImageFilter.GaussianBlur(28))
    return Image.blend(big, Image.new("RGB", size, INK), 0.45)


@lru_cache(maxsize=4)
def clip_frames(clip_dir):
    return sorted(os.path.join(clip_dir, f) for f in os.listdir(clip_dir))


def clip_frame(clip_dir, t):
    frames = clip_frames(clip_dir)
    return Image.open(frames[min(int(t * CFG["fps"]), len(frames) - 1)]).convert("RGB")


def extract_clip(item, idx, cache_root):
    """Pre-cut the item's clip into card-sized JPEG frames (cover-fit, starting at clip_start)."""
    src = item["clip"] if os.path.isabs(item["clip"]) else os.path.join(HERE, item["clip"])
    out = os.path.join(cache_root, f"clip_{idx:02d}")
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        os.remove(os.path.join(out, f))
    w, h = CARD_MEDIA[2] - CARD_MEDIA[0], CARD_MEDIA[3] - CARD_MEDIA[1]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(item.get("clip_start", 0)), "-i", src,
                    "-t", str(item["duration"]), "-an", "-vf",
                    f"fps={CFG['fps']},scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}",
                    "-q:v", "3", os.path.join(out, "%05d.jpg")], check=True)
    item["_clip_dir"] = out


# ----------------------------------------------------------------------------- scene pieces

CARD = (70, 690, 1010, 1130)
CARD_MEDIA = (30, 625, 1050, 1325)  # near full-bleed when it holds a photo / clip


def card_box(item):
    return CARD_MEDIA if (item.get("image") or item.get("clip")) else CARD
VO_START = {"hook": 0.15, "item": 0.55, "outro": 0.55}
VO_TAIL = {"hook": 0.35, "item": 0.5, "outro": 1.0}


def draw_header(layer, rank, t, accent):
    if LOGO:
        draw_logo(layer, 300, W / 2, 182)
    else:
        place(layer, text_img("BEST DAYS AS A KOHLI FAN", "bold", 30, fill=(200, 210, 235), tracking=5), W / 2, 185)
    n = CFG.get("_total_ranks", len(CFG["items"]))
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
    box = card_box(item)
    w, h = box[2] - box[0], box[3] - box[1]
    has_media = item.get("_clip_dir") or item.get("image")
    if has_media:
        if item.get("_clip_dir"):
            card = clip_frame(item["_clip_dir"], t).convert("RGBA")
        else:
            card = ken_burns(item["image"], (w, h), t, item["duration"], idx).convert("RGBA")
        shade = np.zeros((h, w, 4), np.uint8)
        # darken top-left (stat) and bottom (captions) so text reads on any photo
        yy = np.linspace(0, 1, h)[:, None]
        xx = np.linspace(0, 1, w)[None, :]
        top = np.clip((0.32 - yy) / 0.32, 0, 1) * np.clip((0.75 - xx) / 0.75, 0, 1) ** 0.6
        bottom = np.clip((yy - 0.6) / 0.4, 0, 1) ** 1.4
        shade[..., 3] = (np.clip(top * 0.85 + bottom, 0, 1) * 200).astype(np.uint8)
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
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    place(layer, border, cx, cy, scale, p)
    place(layer, card, cx, cy, scale, p)

    # stat counter
    cp = ease_out(prog(t, 0.9, 1.0))
    if cp > 0:
        val = int(round(item["stat"] * cp))
        txt = f"{val:,}{item.get('stat_suffix', '') if cp >= 1 else ''}"
        punch = 1 + 0.18 * max(0, 1 - (t - 1.9) / 0.25) if t >= 1.9 else 1
        label = text_img(item["stat_label"], "bold", 34 if not has_media else 28,
                         fill=WHITE if accent == GOLD else GOLD, tracking=3, stroke=3 if has_media else 0)
        lp = ease_out(prog(t, 1.4, 0.4))
        if has_media:
            # keep the photo's subject clear: stat sits small in the bottom-left corner
            num = text_img(txt, "black", 110, fill=WHITE, stroke=4, stroke_fill=INK)
            place(layer, num, box[0] + 34, box[1] + 82, punch, p, anchor="l")
            place(layer, label, box[0] + 40, box[1] + 148, 1, lp, anchor="l")
            return
        place(layer, text_img(txt, "black", 210, fill=WHITE, stroke=4, stroke_fill=INK), cx, cy - 20, punch * scale, p)
        place(layer, label, cx, cy - 20 + 210 * 0.62, 1,
              ease_out(prog(t, 1.4, 0.4)))


def draw_rank_block(layer, item, t, accent):
    rank = item["rank"]
    sp = prog(t, 0.08, 0.32)
    if sp > 0:
        s = 2.6 - 1.6 * ease_back(sp)
        place(layer, text_img(f"#{rank}", "black", 210, fill=GOLD if rank > 1 else accent, stroke=6),
              W / 2, 385, s, min(1, sp * 3))
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
            place(layer, im, x + im.width * scale_fit / 2, 528, s, min(1, wp * 2))
        x += (im.width + space) * scale_fit
    place(layer, text_img(item["sub"], "semi", 34, fill=MUTED), W / 2, 590, 1, ease_out(prog(t, 0.75, 0.35)))


def chip_img(text, accent):
    f = font("bold", 38)
    tw = int(f.getlength(text))
    w, h = tw + 120, 78
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 39, fill=(255, 255, 255, 235))
    d.ellipse((12, 12, 66, 66), fill=accent + (255,))
    d.line([(26, 40), (36, 50), (53, 29)], fill=on_color(accent), width=7, joint="curve")
    d.text((86, h / 2), text, font=f, fill=INK, anchor="lm")
    return im


def extras_timing(item):
    """When the chips start and how far apart they land (spread over longer, voiced scenes)."""
    t_chip = 2.15
    if item.get("balls"):
        t_chip = 2.0 + 0.2 * len(item["balls"]) + 0.4
    if item.get("quote"):
        t_chip = 1.9 + (len(item["quote"]) + 2) * 0.028 + 0.3
    n = len(item.get("chips", []))
    gap = max(0.45, min(1.1, (item["duration"] - 1.2 - t_chip) / max(1, n - 1)))
    return t_chip, gap


def draw_caption(layer, sc, lt, start, y=1400):
    """Word-by-word subtitles; word timing is spread over the voice line by word length."""
    if not sc.get("caption") or not sc.get("_vo_dur"):
        return
    words = sc["caption"].split()
    weights = np.array([len(w_) + 2 for w_ in words], float)
    # spread words over the voiced stretches only, so captions wait through the speaker's pauses
    regions = sc.get("_vo_voiced") or [(0, sc["_vo_dur"])]
    lens = np.array([b - a for a, b in regions])
    pos = np.cumsum(weights) / weights.sum() * lens.sum()
    ends = np.empty_like(pos)
    for k, p_ in enumerate(pos):
        r = min(int(np.searchsorted(np.cumsum(lens), p_)), len(regions) - 1)
        ends[k] = regions[r][0] + (p_ - (np.cumsum(lens)[r] - lens[r]))
    tt = lt - start
    if tt < 0 or tt > sc["_vo_dur"] + 0.4:
        return
    cur = int(min(np.searchsorted(ends, tt), len(words) - 1))
    # group into chunks of <= 3 words, breaking after punctuation
    chunks, c = [], []
    for k, w_ in enumerate(words):
        c.append(k)
        if len(c) == 3 or w_[-1] in ".,?!" or k == len(words) - 1:
            chunks.append(c)
            c = []
    chunk = next(ch for ch in chunks if cur in ch)
    t_chunk = ends[chunk[0] - 1] if chunk[0] > 0 else 0
    pop = 0.85 + 0.15 * ease_back(clamp((tt - t_chunk) / 0.15))
    imgs = [text_img(words[k].upper(), "black", 60, fill=GOLD if k == cur else WHITE, stroke=6) for k in chunk]
    total = sum(i.width for i in imgs) + 18 * (len(imgs) - 1)
    fit = min(1, 960 / total) * pop
    x = W / 2 - total * fit / 2
    for im in imgs:
        place(layer, im, x + im.width * fit / 2, y, fit)
        x += (im.width + 18) * fit


def draw_extras(layer, item, t, accent):
    """Quote typewriter / ball-by-ball pills, then the check-mark chips. Returns SFX cue times."""
    y = card_box(item)[3] + 75
    t_chip, gap = extras_timing(item)
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
    for k, c in enumerate(item.get("chips", [])):
        cp = prog(t, t_chip + gap * k, 0.3)
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
    box = card_box(item)
    draw_caption(layer, item, t, VO_START["item"], box[3] - 70 if box is CARD_MEDIA else 1640)
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
    if hook.get("image"):  # full-bleed, darkened photo behind the title
        im = ken_burns(hook["image"], (W, H), t, hook["duration"], 1)
        im = Image.blend(im, Image.new("RGB", (W, H), INK), 0.55).convert("RGBA")
        bg = Image.blend(bg, im, ease_out(prog(t, 0.0, 0.5)))
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
        bd.ellipse((10, 10, 250, 250), fill=GOLD + (255,), outline=WHITE + (255,), width=6)
        top, big = hook.get("badge", ["TOP", "10"])
        bd.text((130, 100), top, font=font("black", 50), fill=on_color(GOLD), anchor="mm")
        bd.text((130, 162), big, font=font("black", 92), fill=on_color(GOLD), anchor="mm")
        badge = badge.rotate(-14 + 360 * (1 - ease_out(bp)), resample=Image.BICUBIC)
        place(layer, badge, 870, 510, ease_back(bp), 1)
    tp = prog(t, 1.4, 0.9)
    if tp > 0:
        txt = hook["tease"][:max(1, int(len(hook["tease"]) * tp))]
        im = text_img(txt.upper(), "xbold", 46, fill=on_color(GOLD))
        pill = Image.new("RGBA", (im.width + 70, im.height + 40), (0, 0, 0, 0))
        ImageDraw.Draw(pill).rounded_rectangle((0, 0, pill.width - 1, pill.height - 1), 30, fill=GOLD + (245,))
        pill.alpha_composite(im, (35, 20))
        place(layer, pill, W / 2, 1190, 1, 1)
    if LOGO:  # brand reveal: the logo wipes on, left to right like its yellow bar
        draw_logo(layer, 560, W / 2, 330, ease_out(prog(t, 0.05, 0.6)))
    draw_caption(layer, hook, t, VO_START["hook"])
    zoom_dx = int(8 * math.sin(t * 2))
    shake = max(0, 1 - (t - 0.8) / 0.3) if t >= 0.8 else 0
    bg.paste(layer, (zoom_dx + int(14 * shake * math.sin(t * 90)), int(10 * shake * math.cos(t * 70))), layer)
    return bg


def on_color(c):
    """Ink or white, whichever reads on top of colour c."""
    return INK if (0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]) > 150 else WHITE


@lru_cache(maxsize=8)
def logo_img(width):
    im = Image.open(os.path.join(HERE, LOGO)).convert("RGBA")
    return im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)


def draw_logo(layer, width, cx, cy, reveal=1.0):
    """Brand logo centred at (cx, cy); `reveal` < 1 wipes it on from the left."""
    if reveal <= 0:
        return
    im = logo_img(width)
    if reveal < 1:
        im = im.crop((0, 0, max(1, int(im.width * reveal)), im.height))
    layer.alpha_composite(im, (int(cx - width / 2), int(cy - im.height / 2)))


def apply_theme(theme):
    """Brand colours: accent for ranks, chips, captions and badges; a dark background to match the logo."""
    global GOLD, BLUE, BG_TOP, BG_BOT, LOGO
    if not theme:
        return
    GOLD = BLUE = hex_rgb(theme["accent"])
    BG_TOP, BG_BOT = hex_rgb(theme["bg_top"]), hex_rgb(theme["bg_bottom"])
    LOGO = theme.get("logo")
    gradient_bg.cache_clear()


def scene_suspense(t, dur):
    bg = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    beat = abs(math.sin(t / dur * math.pi * 2))
    place(bg, text_img("AND AT #1...", "black", 110, fill=WHITE), W / 2, H / 2 - 80, 1 + 0.06 * beat,
          ease_out(prog(t, 0.05, 0.3)))
    place(bg, text_img("the day we waited 18 years for", "semi", 40, fill=MUTED), W / 2, H / 2 + 30, 1,
          ease_out(prog(t, 0.45, 0.3)))
    return bg


def scene_outro(t, outro):
    bg = draw_background(t, GOLD, ghost=outro.get("ghost", "?"))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    p1 = prog(t, 0.05, 0.25)
    if p1 > 0:
        place(layer, text_img(outro["lines"][0], "black", 110, fill=WHITE, stroke=5), W / 2, 700,
              2 - ease_back(p1), min(1, 3 * p1))
    p2 = prog(t, 0.35, 0.3)
    if p2 > 0:
        pulse = 1 + 0.05 * math.sin(t * 8) if t > 0.8 else 1
        big = text_img(outro["lines"][1], "black", 320, fill=GOLD, stroke=8)
        place(layer, big, W / 2, 920, (2.4 - 1.4 * ease_back(p2)) * pulse * min(1, 980 / big.width), min(1, 3 * p2))
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
    if LOGO:
        draw_logo(layer, 620, W / 2, 470, ease_out(prog(t, 0.1, 0.6)))
    draw_caption(layer, outro, t, VO_START["outro"])
    bg.paste(layer, (0, 0), layer)
    return flash(bg, t)


# ----------------------------------------------------------------------------- timeline + audio

def attach_voiceover(cfg, manifest_path, prefix=""):
    """Stretch each scene to fit its voice line (from voiceover.py) and remember where the audio is."""
    if not os.path.exists(manifest_path):
        return
    with open(manifest_path) as f:
        man = json.load(f)
    scenes = [(prefix + "hook", "hook", cfg["hook"]), (prefix + "outro", "outro", cfg["outro"])]
    scenes += [(str(it["rank"]), "item", it) for it in cfg["items"]]
    for key, kind, sc in scenes:
        if key in man:
            sc["_vo_path"], sc["_vo_dur"] = man[key]["path"], man[key]["dur"]
            sc["_vo_voiced"] = man[key].get("voiced") or [(0, man[key]["dur"])]
            sc["duration"] = max(sc["duration"], round(VO_START[kind] + man[key]["dur"] + VO_TAIL[kind], 2))


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
            t_chip, gap = extras_timing(item)
            if item.get("balls"):
                ev += [(t0 + 2.0 + 0.2 * k, "pop" if b not in ("4", "6") else "impact", 0.45 if b in ("4", "6") else 0.5)
                       for k, b in enumerate(item["balls"])]
            if item.get("quote"):
                q = len(item["quote"]) + 2
                ev += [(t0 + 1.9 + k * 0.028 * 3, "tick", 0.12) for k in range(q // 3)]
            ev += [(t0 + t_chip + gap * k + 0.05, "pop", 0.7) for k in range(len(item.get("chips", [])))]
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
        bed = bgm.track(total)
        fade = np.minimum(1, np.minimum(np.arange(len(bed)) / sfx.SR / 0.5, (total - np.arange(len(bed)) / sfx.SR) / 1.5))
        mix[:len(bed)] += bed * np.clip(fade, 0, 1) * 0.22
    vo = np.zeros_like(mix)
    for kind, data, t0, dur in segs:
        sc = data[0] if kind == "item" else data
        if kind in VO_START and sc.get("_vo_path"):
            v = np.fromfile(os.path.join(HERE, sc["_vo_path"]), np.float32)
            i = int((t0 + VO_START[kind]) * sfx.SR)
            vo[i:i + len(v)] += v[: len(vo) - i]
    if vo.any():
        # duck SFX + music under the voice (fast attack, slow release)
        hop = 441
        env = np.abs(vo[: len(vo) // hop * hop]).reshape(-1, hop).max(1)
        env = np.convolve(env > 0.03, np.ones(25), "same") > 0
        duck = np.repeat(np.where(env, 0.4, 1.0), hop)
        duck = np.convolve(duck, np.ones(2205) / 2205, "same")
        mix[: len(duck)] *= duck
        mix += vo * 0.95
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


def part_config(base, part):
    """The config for one reel: its hook/outro and only its ranks; the progress bar still counts all of them."""
    cfg = {k: v for k, v in base.items() if k != "parts"}
    cfg.update(hook=part["hook"], outro=part["outro"], output=part["output"], _total_ranks=len(base["items"]),
               items=[it for it in base["items"] if it["rank"] in part["ranks"]])
    return cfg


def main():
    global PREVIEW
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    PREVIEW = "--preview" in sys.argv
    only = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--part=")), None)
    cfg_path = args[0] if args else os.path.join(HERE, "config.json")
    with open(cfg_path) as f:
        base = json.load(f)
    if "parts" not in base:
        return render_part(base, "")
    for part in base["parts"]:
        if only in (None, part["name"]):
            render_part(part_config(base, part), part["name"] + "_")


def render_part(cfg, prefix):
    global CFG, SEGMENTS
    CFG = cfg
    apply_theme(CFG.get("theme"))
    out = os.path.join(HERE, CFG["output"])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    attach_voiceover(CFG, os.path.join(os.path.dirname(out), "vo", "manifest.json"), prefix)
    for idx, item in enumerate(CFG["items"]):
        if item.get("clip"):
            extract_clip(item, idx, os.path.join(os.path.dirname(out), "cache"))
    SEGMENTS, total = build_timeline(CFG)
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

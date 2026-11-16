#!/usr/bin/env python3
"""Long-form 16:9: "Karun Nair — 303 ne bachaya nahi, khatam kiya" (~15 min).

    python3 make_long.py            ->  out/Karun_303.mp4 (+ _upload.mp4, 5 Mbit/s)
    python3 make_long.py --sheet    ->  out/chk/sheet.jpg (one frame per beat)

Voice: vo/vo_clean.wav (clean_vo.py). The edit is laid out in VO seconds (vo/clean_lines.txt); HOLDS add
cinematic beats where the voice pauses (cold open, title, chapter cards, the 303 moment with crowd, number cards,
the subscribe click, the end screen). Look: the IPL/Kohli hook style — letterbox, dark warm grade, slow push-ins,
bottom-left captions behind a yellow bar, Anton numbers. Footage: AI-upscaled 303 highlight clips (clips/*/up) and
photos (up/ when upscaled, else assets/). On-screen text is English; the VO is Hinglish.
"""
import math
import os
import subprocess
import sys
import wave
from functools import lru_cache
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "kohli_countdown"))
sys.path.insert(0, os.path.join(ROOT, "doc_video"))
import sfx  # noqa: E402
import soundtrack as st  # noqa: E402
from virat_hook import braam, drone  # noqa: E402

W, H, FPS = 1920, 1080, 30
SR = sfx.SR
OUT = os.path.join(HERE, "out")
Y, RED, WHITE, GREY, INK, GREEN = (255, 222, 89), (232, 52, 52), (255, 255, 255), (185, 187, 196), (10, 10, 14), (70, 200, 110)
ANTON = os.path.join(ROOT, "doc_video", "thumb", "fonts", "Anton-Regular.woff")
BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
BOLD = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
LOGO = os.path.join(ROOT, "kohli_countdown", "assets", "logo.png")
BAR = 40
VO_LEN = None  # set in main


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def ein(t, t0, d=0.3):
    return ease((t - t0) / d)


_fc = {}


def font(p, s):
    if (p, s) not in _fc:
        _fc[(p, s)] = ImageFont.truetype(p, s)
    return _fc[(p, s)]


# ============================================================================ sources

@lru_cache(maxsize=12)
def photo(name):
    up = os.path.join(HERE, "up", name + ".png")
    src = [f for f in os.listdir(os.path.join(HERE, "assets")) if os.path.splitext(f)[0] == name][0]
    o = Image.open(os.path.join(HERE, "assets", src)).convert("RGB")
    if os.path.exists(up):
        e = Image.open(up).convert("RGB")
        o2 = o.resize(e.size, Image.LANCZOS)
        return Image.fromarray((np.asarray(e, np.float32) * 0.78 + np.asarray(o2, np.float32) * 0.22).astype(np.uint8))
    if o.width < 2000:
        o = o.resize((2000, int(o.height * 2000 / o.width)), Image.LANCZOS)
    return o


@lru_cache(maxsize=1)
def clip_list(name):
    d = os.path.join(HERE, "clips", name, "up")
    return sorted(os.path.join(d, f) for f in os.listdir(d))


@lru_cache(maxsize=6)
def clip_img(path):
    return Image.open(path).convert("RGB").resize((W, int(W * 992 / 1760)), Image.LANCZOS)


def clip_frame(name, lt, speed=0.5, start=0.0):
    fr = clip_list(name)
    f = (start + lt * speed) * 30
    i = min(int(f), len(fr) - 1)
    j = min(i + 1, len(fr) - 1)
    k = f - int(f)
    a = np.asarray(clip_img(fr[i]), np.float32)
    if k > 0.05 and j != i:
        a = a * (1 - k) + np.asarray(clip_img(fr[j]), np.float32) * k
    im = Image.fromarray(a.astype(np.uint8))
    y0 = (im.height - H) // 2
    return im.crop((0, y0, W, y0 + H))


# ============================================================================ look

_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = (1 - 0.48 * np.clip(((_xx - W / 2) / (W * 0.62)) ** 2 + ((_yy - H / 2) / (H * 0.66)) ** 2, 0, 1) ** 1.2)[..., None]
LOW = (np.clip((_yy - H * 0.5) / (H * 0.5), 0, 1) * np.clip(1 - _xx / (W * 0.6), 0, 1))[..., None]


def grade(im, gray=0.0, dark=1.0):
    a = np.asarray(im, np.float32) / 255
    lum = a.mean(-1, keepdims=True)
    a = lum + (a - lum) * (0.86 - 0.86 * gray)
    a = np.clip((a - 0.5) * 1.12 + 0.5, 0, 1) ** 1.02
    a = a + np.array([0.0, 0.012, 0.03]) * (1 - lum)
    a = a * VIG * dark * (1 - 0.28 * LOW)
    return a * 255


def cover(im, z, fx, fy, w=W, h=H):
    s = max(w / im.width, h / im.height) * z
    cw, ch = w / s, h / s
    x0 = min(max(fx * im.width - cw / 2, 0), im.width - cw)
    y0 = min(max(fy * im.height - ch / 2, 0), im.height - ch)
    return im.crop((x0, y0, x0 + cw, y0 + ch)).resize((w, h), Image.BILINEAR)


_dust = np.random.default_rng(303).random((80, 4))


def plate(t, tint=(1.0, 0.82, 0.35)):
    cx = W * (0.5 + 0.25 * math.sin(t * 0.21))
    cy = H * (0.42 + 0.12 * math.cos(t * 0.17))
    g = np.exp(-(((_xx[::4, ::4] - cx) / 640) ** 2 + ((_yy[::4, ::4] - cy) / 420) ** 2))
    lo = np.stack([g * 44 * tint[0], g * 44 * tint[1], g * 44 * tint[2]], -1)
    a = np.asarray(Image.fromarray(lo.astype(np.uint8)).resize((W, H), Image.BILINEAR), np.float32) + np.array(INK)
    off = (t * 14) % 96
    a = a + ((((_xx + off) % 96 < 1.4) | ((_yy + off * 0.5) % 96 < 1.4)).astype(np.float32)[..., None] * 7)
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    for x0, y0, sp, r in _dust:
        x = (x0 * W + t * 18 * (sp - 0.5)) % W
        y = (y0 * H - t * (12 + 28 * sp)) % H
        rr = 1 + 3 * r
        c = int(55 + 100 * r)
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=(c, int(c * 0.9), int(c * 0.45)))
    return np.asarray(im, np.float32)


# ---------------------------------------------------------------------------- background kinds

def BG_P(name, z0=1.04, z1=1.16, f0=(0.5, 0.35), f1=None, gray=0.0, dark=1.0):
    def bg(t, lt, dur):
        f = f1 or f0
        k = ease(lt / dur)
        return grade(cover(photo(name), z0 + (z1 - z0) * lt / dur, f0[0] + (f[0] - f0[0]) * k,
                           f0[1] + (f[1] - f0[1]) * k), gray, dark)
    return bg


def BG_PANEL(name, box_w=1180, gray=0.0, y=0.47):
    """Photo shown whole (credits stay visible) in a yellow-edged panel over its own blurred copy."""
    def bg(t, lt, dur):
        im = photo(name)
        back = np.asarray(cover(im, 1.0, 0.5, 0.5).filter(ImageFilter.GaussianBlur(30)), np.float32) * 0.36
        base = Image.fromarray(back.astype(np.uint8))
        z = 1.0 + 0.04 * lt / dur
        bw = int(box_w * z)
        bh = int(bw * im.height / im.width)
        if bh > 760 * z:
            bh = int(760 * z)
            bw = int(bh * im.width / im.height)
        pan = im.resize((bw, bh), Image.LANCZOS)
        if gray:
            pan = ImageOps.grayscale(pan).convert("RGB")
        x0, y0 = (W - bw) // 2, int(H * y - bh / 2)
        ImageDraw.Draw(base).rectangle((x0 - 5, y0 - 5, x0 + bw + 4, y0 + bh + 4), fill=Y)
        base.paste(pan, (x0, y0))
        return np.asarray(base, np.float32) * VIG
    return bg


def BG_CLIP(name, speed=0.5, start=0.0, dark=1.0):
    return lambda t, lt, dur: grade(clip_frame(name, lt, speed, start), dark=dark)


def BG_PL(tint=(1.0, 0.82, 0.35)):
    return lambda t, lt, dur: plate(t, tint)


# ---------------------------------------------------------------------------- overlays

def text_img(lines, size, path=ANTON, gap=0.08, maxw=1700):
    rows = []
    for txt, col in lines:
        s = size
        while font(path, s).getlength(txt) > maxw and s > 24:
            s -= 2
        f = font(path, s)
        l, tt, r, b = f.getbbox(txt)
        rows.append((txt, col, f, l, tt, r - l, b - tt))
    pad = 40
    wid = max(r[5] for r in rows)
    hgt = sum(r[6] for r in rows) + int(size * gap) * (len(rows) - 1)
    im = Image.new("RGBA", (wid + 2 * pad, hgt + 2 * pad), (0, 0, 0, 0))
    yy = pad
    for txt, col, f, l, tt, w, h in rows:
        ImageDraw.Draw(im).text((pad + (wid - w) // 2 - l, yy - tt), txt, font=f, fill=col)
        yy += h + int(size * gap)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(12)).point(lambda v: int(v * 0.85)))
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (4, 7))
    out.alpha_composite(im)
    return out


_ti = {}


def T(lines, size, path=ANTON):
    k = (tuple(lines), size, path)
    if k not in _ti:
        _ti[k] = text_img(lines, size, path)
    return _ti[k]


def put(base, im, cx, cy, s=1.0, a=1.0):
    if a <= 0.01:
        return
    if s != 1.0:
        im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BILINEAR)
    if a < 1:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def life(t, t0, t1, d_in=0.3, d_out=0.25):
    if t < t0 or t > t1:
        return 0.0
    return ein(t, t0, d_in) * (1 - ein(t, t1 - d_out, d_out))


def cap(t0, t1, l1, l2=None):
    """Bottom-left caption: line 1 white, line 2 yellow, thin yellow bar (the hook style)."""
    def ov(base, t):
        a = life(t, t0, t1)
        if a <= 0:
            return
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        x, y = 96, 812
        rows = [(l1, WHITE, t0)] + ([(l2, Y, t0 + 0.45)] if l2 else [])
        hgt = 0
        for k, (txt, col, ti) in enumerate(rows):
            p = ein(t, ti, 0.35)
            if p <= 0:
                continue
            d.text((x + 34, y + k * 82 + int(16 * (1 - p))), txt, font=font(BOLD, 66), fill=col + (int(255 * p * a),))
            hgt = (k + 1) * 82
        if hgt:
            d.rectangle((x, y + 8, x + 6, y + hgt - 6), fill=Y + (int(255 * a),))
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sh.putalpha(lay.getchannel("A").filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.6)))
        base.alpha_composite(sh, (3, 5))
        base.alpha_composite(lay)
    return ov


def big(t0, t1, txt, sub=None, col=Y, size=300, cy=470, slam=True):
    def ov(base, t):
        a = life(t, t0, t1, 0.15 if slam else 0.35)
        if a <= 0:
            return
        k = ein(t, t0, 0.15)
        s = (1.35 - 0.35 * k) if slam else 1.0
        put(base, T([(txt, col)], size), W / 2, cy, s, a)
        if sub:
            put(base, T([(sub, WHITE)], 62, BOLD), W / 2, cy + size * 0.62, 1.0, life(t, t0 + 0.3, t1))
    return ov


def lines(t0, t1, rows, size=110, cy=520, step=0.45):
    def ov(base, t):
        for k, (txt, col) in enumerate(rows):
            a = life(t, t0 + k * step, t1)
            put(base, T([(txt, col)], size), W / 2, cy + (k - (len(rows) - 1) / 2) * size * 1.15 + 20 * (1 - ein(t, t0 + k * step, 0.3)), 1.0, a)
    return ov


def stamp(t0, t1, word, cy=540, color=RED, angle=-8, size=150, cx=W / 2):
    f = font(BLACK, size)
    l, tt, r, b = f.getbbox(word)
    im = Image.new("RGBA", (r - l + 90, b - tt + 80), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((7, 7, im.width - 8, im.height - 8), outline=color + (255,), width=14)
    d.text((45 - l, 40 - tt), word, font=f, fill=color + (255,))
    al = np.asarray(im.getchannel("A"), np.float32) * np.where(np.random.default_rng(len(word)).random((im.height, im.width)) > 0.88, 0.35, 1)
    im.putalpha(Image.fromarray(al.astype(np.uint8)))
    im = im.rotate(angle, expand=True, resample=Image.BICUBIC)

    def ov(base, t):
        if t < t0 or t > t1:
            return
        k = t - t0
        put(base, im, cx, cy, 1 + 1.0 * (1 - ease(k / 0.12)), ease(k / 0.05) * (1 - ein(t, t1 - 0.25, 0.25)))
    return ov


def quote(t0, t1, who, text, cy=500):
    def ov(base, t):
        a = life(t, t0, t1, 0.4)
        if a <= 0:
            return
        put(base, T([("“" + text + "”", WHITE)], 70, BOLD), W / 2, cy + 18 * (1 - ein(t, t0, 0.4)), 1.0, a)
        put(base, T([("— " + who, Y)], 46, BOLD), W / 2, cy + 120, 1.0, life(t, t0 + 0.4, t1))
    return ov


def ticker(t0, t1, vals, label=None, cy=520, col=WHITE, last_col=None):
    def ov(base, t):
        n = len(vals)
        gap = 230
        x0 = W / 2 - (n - 1) * gap / 2
        for k, v in enumerate(vals):
            a = life(t, t0 + 0.35 * k, t1)
            c = last_col if (last_col and k == n - 1) else col
            put(base, T([(str(v), c)], 170), x0 + k * gap, cy + 30 * (1 - ein(t, t0 + 0.35 * k, 0.3)), 1.0, a)
        if label:
            put(base, T([(label, Y)], 70, BOLD), W / 2, cy + 175, 1.0, life(t, t0 + 0.35 * n, t1))
    return ov


def chapter_ov(num, title, sub=None):
    def ov(base, t, lt, dur):
        a = life(lt, 0, dur, 0.4, 0.35)
        put(base, T([(f"CHAPTER {num}", Y)], 46, BOLD), W / 2, 420, 1.0, a)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        w = 140 * ein(lt, 0.2, 0.5)
        ImageDraw.Draw(lay).rectangle((W / 2 - w, 470, W / 2 + w, 476), fill=Y + (int(255 * a),))
        base.alpha_composite(lay)
        put(base, T([(title, WHITE)], 150), W / 2, 580 + 20 * (1 - ein(lt, 0.25, 0.4)), 1.0, life(lt, 0.25, dur, 0.4, 0.35))
        if sub:
            put(base, T([(sub, GREY)], 50, BOLD), W / 2, 720, 1.0, life(lt, 0.6, dur, 0.4, 0.35))
    return ov


def photo_card(t0, t1, name, w=1100, cy=500):
    """A photo (e.g. the 'Dear Cricket' post) floating in over the background."""
    def ov(base, t):
        a = life(t, t0, t1, 0.4)
        if a <= 0:
            return
        im = photo(name)
        h = int(w * im.height / im.width)
        if h > 700:
            h = 700
            ww = int(h * im.width / im.height)
        else:
            ww = w
        card = im.resize((ww, h), Image.LANCZOS).convert("RGBA")
        fr = Image.new("RGBA", (ww + 12, h + 12), Y + (255,))
        fr.alpha_composite(card, (6, 6))
        put(base, fr, W / 2, cy + 30 * (1 - ein(t, t0, 0.4)), 1.0 + 0.02 * (t - t0) / max(0.1, t1 - t0), a)
    return ov


def multi(*ovs):
    def ov(base, t):
        for o in ovs:
            o(base, t)
    return ov


NOOV = lambda base, t, *a: None  # noqa: E731


# ============================================================================ the edit (VO seconds, vo/clean_lines.txt)

B = []  # (vo_t0, vo_t1, background, overlay)


def beat(t0, t1, bg, ov=NOOV):
    B.append((t0, t1, bg, ov))


# HOOK
beat(0.0, 8.4, BG_PANEL("sehwag_triple_bat_helmet", 820),
     multi(big(0.4, 8.2, "303*", None, Y, 220, 860, False), cap(3.2, 8.2, "Only two Indians have", "scored 300 in a Test")))
beat(8.4, 13.5, BG_CLIP("walkoff", 0.45),
     multi(big(10.2, 13.4, "3 TESTS", "after the 303", Y, 200, 470)))
beat(13.5, 21.1, BG_CLIP("drop34", 0.42),
     cap(13.7, 21.0, "381 balls.", "Three dropped chances."))
beat(21.1, 27.8, BG_CLIP("dressing100", 0.5), cap(21.3, 27.7, "\"India's No.5", "for the next 10 years\""))
beat(27.8, 35.2, BG_PL((0.6, 0.6, 0.75)),
     multi(big(28.4, 31.2, "3 MONTHS", None, WHITE, 230, 470), big(31.2, 35.1, "8 YEARS", "until his next Test", Y, 230, 470)))
beat(35.2, 49.3, BG_P("karun_303_chennai_2016", 1.05, 1.18, (0.55, 0.3)),
     multi(big(35.6, 41.5, "303", None, Y, 320, 470), cap(41.6, 49.2, "\"Dropped. A huge injustice.\"", "That's not the whole story.")))
beat(49.3, 58.2, BG_P("karun_2025_portrait_fence", 1.1, 1.22, (0.55, 0.3)),
     cap(49.5, 58.1, "303 wasn't his defence.", "It was his sentence."))
# RIVER
beat(58.2, 92.9, BG_P("pampa_river", 1.04, 1.22, (0.5, 0.55), (0.5, 0.4), dark=0.9),
     multi(cap(61.9, 72.0, "Pampa river, Kerala", "July 2016"), cap(75.2, 84.5, "~100 on board.", "2 never came back."),
           cap(85.4, 92.8, "Saved once by the river.", "Five months later: Chennai.")))
# CHENNAI
beat(92.9, 102.0, BG_P("karun_303_chennai_2016", 1.2, 1.32, (0.5, 0.25)),
     multi(cap(93.0, 97.6, "Test debut: Nov 2016", "4 & 13"), cap(97.8, 101.9, "A slow start.", "Nobody noticed.")))
beat(102.0, 106.5, BG_CLIP("crowd", 0.5), cap(102.1, 106.4, "Chennai · Dec 2016", "5th Test vs England"))
beat(106.5, 111.8, BG_CLIP("drop34", 0.35), multi(big(106.8, 111.7, "DROPPED ON 34", "Alastair Cook, first slip", WHITE, 150, 470)))
beat(111.8, 115.3, BG_CLIP("hundred", 0.45), cap(111.9, 115.2, "Maiden Test hundred", "off 185 balls"))
beat(115.3, 121.4, BG_PANEL("kl_rahul_199_reuters_credit", 1180), cap(115.4, 121.3, "KL Rahul out for 199", "One run short"))
beat(121.4, 125.9, BG_CLIP("bat150", 0.45), cap(121.5, 125.8, "Dropped again on 217", "Joe Root"))
beat(125.9, 135.6, BG_CLIP("shot300", 0.5), cap(126.0, 135.5, "A four off Adil Rashid…", "300"))
beat(135.6, 145.4, BG_CLIP("armclose", 0.45),
     multi(big(135.8, 140.0, "303*", "381 balls · 32 fours · 4 sixes", Y, 280, 450), big(140.0, 145.3, "759/7 dec.", "India's highest Test total (then)", WHITE, 200, 450)))
beat(145.4, 153.8, BG_CLIP("kohli300", 0.4), cap(145.5, 153.7, "Won by an innings & 75", "Series 4-0"))
beat(153.8, 160.9, BG_PANEL("sehwag_triple_bat_helmet", 760),
     quote(151.0, 160.8, "Virender Sehwag", "Welcome to the 300 club. Lonely here for 12 years 8 months.", 940))
beat(160.9, 169.4, BG_P("karun_303_chennai_2016", 1.08, 1.2, (0.5, 0.3)),
     multi(cap(161.0, 165.2, "Maiden hundred → 300", "Only the 3rd ever"), cap(165.3, 169.3, "after Garry Sobers", "& Bob Simpson")))
beat(169.4, 173.3, BG_PL(), big(169.6, 173.2, "160", "Test average after 3 Tests", Y, 320, 470))
beat(173.3, 189.9, BG_CLIP("walk381", 0.4, dark=0.85),
     multi(quote(177.8, 184.8, "Karun Nair, Dec 2016", "What's the pressure of a ton after cheating death?", 470),
           cap(185.0, 189.8, "But now something else", "was coming for him: 303")))
# CEILING
beat(189.9, 232.6, BG_PL(),
     multi(lines(190.0, 201.0, [("HOW IS A BATTER JUDGED?", WHITE), ("BY HIS LAST SCORE", Y)], 110, 500),
           lines(201.2, 208.8, [("BEFORE CHENNAI: A YOUNG BATTER", WHITE), ("AFTER CHENNAI: THE 303 GUY", Y)], 96, 500),
           lines(209.0, 220.0, [("YOUNG BATTER: SCORE RUNS", WHITE), ("303 GUY: PROVE IT WASN'T ONE DAY", Y)], 90, 500),
           lines(220.2, 227.8, [("WHY NO RUNS?", WHITE), ("WHY NO 300?", Y)], 130, 500),
           lines(228.0, 232.5, [("NOT A CROWN.", WHITE), ("A BENCHMARK.", Y)], 140, 500)))
beat(232.6, 244.9, BG_P("karun_nets_2025", 1.08, 1.2, (0.5, 0.3), dark=0.9),
     cap(232.8, 244.8, "Your best day, declared", "\"never to be repeated\"?"))
# NEXT TEST
beat(244.9, 255.5, BG_PL((0.7, 0.7, 0.85)),
     multi(lines(245.0, 251.0, [("HYDERABAD · 9 FEB 2017", WHITE), ("THE VERY NEXT TEST", Y)], 110, 480), stamp(251.4, 255.4, "BENCHED", 560)))
beat(255.5, 262.4, BG_P("kohli_presser_2017", 1.05, 1.15, (0.5, 0.35)), cap(255.6, 262.3, "Kohli, before the Test:", "Rahane is back"))
beat(262.4, 275.5, BG_PL(),
     multi(lines(262.6, 272.5, [("HUTTON · INZAMAM", WHITE), ("MISSED THE NEXT TEST: INJURED", GREY)], 110, 470),
           lines(272.6, 275.4, [("KARUN: FIT. STILL OUT.", Y)], 120, 560)))
beat(275.5, 299.1, BG_PL((0.6, 0.7, 0.8)),
     multi(lines(275.6, 284.0, [("RAHANE DID NOTHING WRONG.", WHITE), ("THE TEAM CHOSE EXPERIENCE.", Y)], 100, 500),
           quote(284.2, 293.1, "Karun's father", "It was fair to pick Rahane.", 500),
           quote(293.3, 299.0, "Karun Nair", "One game doesn't overshadow two years of hard work.", 500)))
beat(299.1, 318.8, BG_P("karun_303_chennai_2016", 1.25, 1.1, (0.5, 0.3), gray=0.6, dark=0.85),
     multi(cap(299.2, 309.0, "No conspiracy.", "No villain."), cap(309.2, 318.7, "What he didn't have:", "time")))
# AUSTRALIA
beat(318.8, 328.9, BG_P("karun_bowled_bengaluru_2017", 1.04, 1.14, (0.62, 0.45)),
     multi(cap(318.9, 323.0, "vs Australia", "March 2017"), ticker(323.2, 328.8, [26, 0, 23, 5], "54 RUNS · 4 INNINGS", 470, WHITE)))
beat(328.9, 341.4, BG_P("karun_bowled_bengaluru_2017", 1.14, 1.24, (0.55, 0.4), dark=0.8),
     cap(329.0, 341.3, "India won the series 2-1.", "The questions found him."))
beat(341.4, 366.0, BG_PL(),
     multi(lines(341.5, 350.8, [("MEASURED AGAINST 303.", WHITE), ("NOT AGAINST 30.", Y)], 120, 500),
           lines(350.9, 357.9, [("4 BAD INNINGS: NORMAL.", WHITE), ("FOR THE 303 GUY? NOT FORM.", Y)], 110, 500), stamp(358.0, 362.6, "NOT FORM", 440, GREY, -6, 110), lines(359.4, 365.9, [("PROOF.", RED)], 170, 650)))
beat(366.0, 383.2, BG_P("karun_bowled_bengaluru_2017", 1.2, 1.3, (0.6, 0.45), gray=0.9, dark=0.75),
     multi(cap(366.1, 374.0, "Dharamsala · 25 Mar 2017", "His last Test"), lines(374.5, 383.1, [("THE STORY SHOULD HAVE ENDED HERE.", WHITE), ("IT DIDN'T.", Y)], 96, 500)))
# 2018
beat(383.2, 392.1, BG_PL((0.6, 0.65, 0.8)),
     multi(lines(383.3, 391.9, [("ENGLAND TOUR · 2018", WHITE), ("IN THE SQUAD. TESTS PLAYED: 0", Y)], 100, 500)))
beat(392.1, 406.0, BG_P("vihari_batting_2021era", 1.18, 1.28, (0.5, 0.3)),
     multi(cap(392.2, 398.5, "Debut at The Oval:", "Hanuma Vihari"), cap(398.6, 405.9, "Next: West Indies squad", "Karun — dropped")))
beat(406.0, 424.0, BG_P("msk_prasad_kohli", 1.04, 1.14, (0.3, 0.35), (0.25, 0.35)),
     multi(quote(406.1, 411.9, "Karun Nair", "No communication.", 340), quote(412.1, 421.9, "Chief selector MSK Prasad", "We spoke to him. He's in the plans.", 340)))
beat(424.0, 438.8, BG_PL(),
     multi(big(424.2, 430.2, "62.33", "his Test average, watching from the dressing room", Y, 220, 470),
           lines(430.4, 438.7, [("FROM 303...", WHITE), ("TO A NAME ON A SQUAD LIST", Y)], 110, 500)))
# LOST YEARS
beat(438.8, 454.3, BG_PL((0.75, 0.75, 0.8)),
     multi(lines(439.0, 443.7, [("2018 · 2019 · 2020 · 2021 · 2022", WHITE), ("EVERY SELECTION. ONE ANSWER:", Y)], 100, 500), big(443.8, 449.0, "\"CONSISTENCY\"", None, WHITE, 180, 470),
           lines(449.1, 454.2, [("FITNESS? CONSISTENCY.", GREY), ("TECHNIQUE? CONSISTENCY.", GREY), ("COMBINATION? CONSISTENCY.", GREY)], 80, 520, 0.3)))
beat(454.3, 470.8, BG_P("karun_karnataka_helmet_raised", 1.1, 1.22, (0.5, 0.25), gray=0.5, dark=0.8),
     multi(cap(454.4, 462.6, "Dec 2022: out of", "even Karnataka's side"), photo_card(462.7, 470.7, "dear_cricket_post", 1000, 470)))
beat(470.8, 490.5, BG_P("karun_northants_hundred", 1.05, 1.16, (0.5, 0.3)),
     multi(cap(470.9, 480.0, "County cricket, 2023", "Northamptonshire"), cap(480.2, 490.4, "First county hundred", "vs Surrey")))
# VIDARBHA
beat(490.5, 503.6, BG_P("karun_vidarbha_hundred", 1.04, 1.14, (0.5, 0.3)),
     multi(cap(490.6, 495.2, "Karnataka → Vidarbha", None), cap(495.3, 503.5, "Year one: 690 runs", "Ranji final lost")))
beat(503.6, 522.3, BG_PL(),
     multi(big(503.8, 511.6, "779", "VIJAY HAZARE 2024-25 · 5 HUNDREDS · AVG 389", Y, 300, 450),
           lines(511.8, 522.2, [("RANJI FINAL vs KERALA: 86 & 135", WHITE), ("VIDARBHA: CHAMPIONS", Y)], 100, 520)))
# IPL 2025 (insert)
beat(522.3, 535.2, BG_PL((0.4, 0.55, 1.0)),
     multi(lines(522.4, 530.5, [("IPL 2025 · DELHI CAPITALS", WHITE)], 110, 420), big(526.0, 530.5, "1,077 DAYS", "since his last IPL game", Y, 200, 600),
           lines(530.7, 535.1, [("vs MUMBAI INDIANS", WHITE), ("BALL IN BUMRAH'S HAND", Y)], 110, 500)))
beat(535.2, 548.2, BG_PL((0.4, 0.55, 1.0)),
     multi(big(535.3, 538.9, "89 (40)", "12 FOURS · 5 SIXES", Y, 260, 450), big(539.0, 545.4, "18", "off one Bumrah over — most by an Indian in the IPL", WHITE, 300, 450),
           lines(545.5, 548.1, [("DELHI LOST BY 12", RED)], 130, 500)))
beat(548.2, 561.9, BG_PL(),
     multi(quote(548.3, 554.0, "Karun Nair", "No value of individual runs if the team loses.", 470),
           lines(554.2, 561.8, [("THE MAN MEASURED BY ONE SCORE", WHITE), ("SAYS SCORES DON'T MATTER", Y)], 100, 500)))
beat(561.9, 569.7, BG_PL(), multi(big(562.0, 566.5, "204", "India A vs England Lions", Y, 300, 450), lines(566.6, 569.6, [("THE WALL BROKE.", WHITE)], 130, 700)))
# 2025 RETURN
beat(569.7, 581.6, BG_P("karun_arrival_2025", 1.04, 1.14, (0.5, 0.3)),
     multi(cap(569.8, 572.4, "Headingley", "20 June 2025"), big(572.5, 575.8, "3,006 DAYS", "back in an India Test cap", Y, 200, 430), cap(575.9, 581.5, "\"Now the story", "will be complete\"")))
beat(581.6, 594.5, BG_P("karun_duck_headingley_2025", 1.04, 1.14, (0.4, 0.35)),
     multi(cap(581.7, 585.5, "4 balls. 0.", "Ollie Pope's catch"), ticker(586.0, 594.4, [20, 31, 26, 40, 14], None, 470, WHITE)))
beat(594.5, 603.9, BG_P("karun_walkoff_lords_2025", 1.05, 1.16, (0.5, 0.3)),
     multi(cap(594.6, 598.3, "A start every time.", "\"That's it?\""), cap(598.4, 603.8, "4th Test: left out", "5th Test: The Oval")))
beat(603.9, 611.8, BG_P("karun_oval_fifty_2025", 1.04, 1.14, (0.5, 0.3)),
     multi(big(604.0, 607.4, "57", "first Test fifty in ~9 years", Y, 280, 420),
           quote(607.5, 611.7, "Dinesh Karthik", "His career is well and truly back.", 760)))
beat(611.8, 623.6, BG_P("karun_dejected_2025_close", 1.05, 1.15, (0.5, 0.25)),
     multi(cap(611.9, 617.9, "LBW, Josh Tongue.", "Review lost. Then 17."), big(618.0, 623.5, "205", "8 innings · avg 25.62", WHITE, 260, 420)))
beat(623.6, 638.3, BG_P("karun_2025_portrait_fence", 1.12, 1.22, (0.5, 0.3), dark=0.9),
     multi(quote(623.7, 627.5, "Karun Nair", "I wasn't trying to prove anything.", 450),
           cap(627.6, 638.2, "Everyone around him was:", "that 303 wasn't one day")))
# VERDICT
beat(638.3, 650.2, BG_P("agarkar_presser", 1.04, 1.14, (0.5, 0.35)),
     multi(cap(638.4, 643.4, "West Indies squad:", "not picked"), quote(643.5, 650.1, "Chief selector Ajit Agarkar", "We expected more from Karun in England.", 330)))
beat(650.2, 666.3, BG_P("karun_karnataka_bat_raised", 1.05, 1.16, (0.5, 0.3), dark=0.85),
     multi(quote(650.3, 654.6, "Karun Nair", "I deserved more than one series.", 330),
           cap(654.7, 660.8, "Back to Karnataka.", "Back-to-back Ranji hundreds."), big(661.9, 666.2, "303", "still the measure", Y, 280, 420)))
beat(666.3, 672.9, BG_PL(),
     multi(lines(666.4, 671.3, [("RAHANE?", WHITE), ("THE SELECTORS?", WHITE), ("LUCK?", WHITE)], 120, 520, 0.6),
           stamp(671.4, 672.8, "ALL WRONG", 540, RED, -6, 140)))
beat(672.9, 680.0, BG_PL(), NOOV)   # CTA is drawn by the CTA hold below
# TRUTH
beat(680.0, 702.1, BG_P("karun_303_chennai_2016", 1.18, 1.05, (0.5, 0.3), dark=0.85),
     multi(lines(680.1, 690.0, [("WHO ENDED KARUN NAIR'S CAREER?", WHITE), ("NOT RAHANE. NOT THE SELECTORS.", Y)], 92, 500),
           lines(694.0, 702.0, [("NOT A RIVER. NOT A SQUAD LIST. NOT 8 YEARS.", GREY), ("A NUMBER.", Y)], 84, 520)))
beat(702.1, 719.1, BG_PL(),
     multi(lines(702.2, 704.4, [("KARUN NEVER CALLED 303", WHITE), ("A BURDEN", Y)], 120, 500), quote(704.5, 710.6, "Karun Nair", "It is definitely not a burden.", 420),
           quote(710.7, 715.0, "Karun Nair", "It is something that is never going to go away from me.", 420),
           lines(715.1, 719.0, [("IT NEVER WENT AWAY.", WHITE), ("IT JUST STOPPED BEING HIS.", Y)], 100, 520)))
beat(719.1, 740.8, BG_P("karun_dejected_2025_close", 1.05, 1.18, (0.5, 0.25), gray=0.4, dark=0.8),
     multi(cap(719.2, 730.4, "We made him a character:", None), lines(730.5, 740.7, [("\"THE 303 GUY\"", WHITE), ("\"THE VICTIM\"", GREY)], 140, 470)))
beat(740.8, 750.0, BG_P("karun_2025_portrait_fence", 1.05, 1.2, (0.55, 0.3)),
     multi(stamp(745.3, 749.9, "THE 303 GUY", 470, GREY, -4, 120), lines(747.8, 749.9, [("KARUN NAIR", Y)], 180, 700)))
beat(750.0, 9999, BG_CLIP("arms300", 0.35, dark=0.75),
     lines(750.1, 9999, [("OUT FOR 30 IN CHENNAI —", WHITE), ("WOULD HE STILL BE PLAYING?", Y)], 110, 480))


# ---------------------------------------------------------------------------- holds (VO paused)
# (at VO second, duration, background, overlay(base, t, lt, dur), sound)

def hold_cold(base, t, lt, dur):
    a = life(lt, 1.0, dur - 0.2, 0.6, 0.4)
    put(base, T([("CHENNAI · 19 DECEMBER 2016", WHITE)], 54, BOLD), W / 2, 930, 1.0, a)


def hold_title(base, t, lt, dur):
    a = life(lt, 0.2, dur, 0.5, 0.4)
    put(base, T([("KARUN NAIR", Y)], 210), W / 2, 470, 1.0 + 0.04 * lt / dur, a)
    put(base, T([("303 DIDN'T SAVE HIM. IT ENDED HIM.", WHITE)], 64, BOLD), W / 2, 620, 1.0, life(lt, 0.9, dur, 0.5, 0.4))


def hold_card(txt, sub=None, col=Y):
    def ov(base, t, lt, dur):
        k = ein(lt, 0, 0.15)
        put(base, T([(txt, col)], 260), W / 2, 470, 1.35 - 0.35 * k, life(lt, 0, dur, 0.15, 0.3))
        if sub:
            put(base, T([(sub, WHITE)], 60, BOLD), W / 2, 640, 1.0, life(lt, 0.3, dur))
    return ov


def hold_cta(base, t, lt, dur):
    pass  # drawn in frame() from the CTA timeline


def hold_end(base, t, lt, dur):
    a = life(lt, 0.0, dur + 1, 0.6)
    put(base, T([("COMMENT ↓", RED)], 80, BLACK), W / 2, 230, 1.0, a)
    put(base, T([("NEXT: THE CRICKETER RUINED NOT BY 300, BUT BY 30", WHITE)], 56, BOLD), W / 2, 330, 1.0, life(lt, 0.8, dur + 1))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for x in (300, 1020):   # end-screen video slots (YouTube elements sit here)
        d.rounded_rectangle((x, 450, x + 600, 787), 22, outline=Y + (int(200 * a),), width=4)
    base.alpha_composite(lay)


HOLDS = [
    (0.0, 12.0, BG_CLIP("arms300", 0.3), hold_cold, "cold"),
    (58.2, 6.0, BG_PL(), hold_title, "title"),
    (75.2, 4.0, BG_P("pampa_river", 1.15, 1.2, (0.5, 0.5), dark=0.75), NOOV, "water"),
    (110.2, 3.5, BG_CLIP("drop34", 0.3, 1.2), NOOV, "crowd_s"),
    (115.3, 4.0, BG_CLIP("dressing100b", 0.5), NOOV, "crowd_s"),
    (135.6, 16.0, BG_CLIP("arms300", 0.4), NOOV, "crowd"),
    (173.3, 5.0, BG_CLIP("walkoff", 0.45), NOOV, "crowd_s"),
    (255.5, 3.0, BG_PL((0.7, 0.7, 0.85)), hold_card("BENCHED", "after a triple hundred", RED), "hit"),
    (328.9, 3.0, BG_PL(), hold_card("54", "runs · 4 innings", WHITE), "hit"),
    (470.8, 3.0, BG_PL(), hold_card("ONE MORE CHANCE", None, WHITE), "hit"),
    (522.3, 3.0, BG_P("karun_vidarbha_hundred", 1.1, 1.14, (0.5, 0.3)), hold_card("CHAMPIONS", "Vidarbha, Ranji Trophy 2024-25", Y), "crowd_s"),
    (575.9, 3.0, BG_P("karun_arrival_2025", 1.14, 1.18, (0.5, 0.3)), NOOV, "hit"),
    (603.9, 4.0, BG_P("karun_oval_fifty_2025", 1.14, 1.2, (0.5, 0.3)), NOOV, "crowd_s"),
    (623.6, 3.0, BG_PL(), hold_card("205", "8 innings · 2025", WHITE), "hit"),
    (679.99, 4.5, BG_PL(), hold_cta, "cta"),
    (750.0, 3.0, BG_P("karun_2025_portrait_fence", 1.2, 1.24, (0.55, 0.3)), NOOV, "none"),
    (9999, 25.0, BG_PL(), hold_end, "end"),
]
# chapter cards (each a short hold)
for at, n, title, sub in [(92.9, 1, "CHENNAI", "December 2016"), (189.9, 2, "THE CEILING", None),
                          (244.9, 3, "THE VERY NEXT TEST", "Hyderabad, 2017"), (318.8, 4, "AUSTRALIA", "March 2017"),
                          (383.2, 5, "THE TOUR WITHOUT A MATCH", "England, 2018"), (438.8, 6, "THE LOST YEARS", None),
                          (490.5, 7, "VIDARBHA", "2023–25"), (569.7, 8, "THE RETURN", "England, 2025"),
                          (638.3, 9, "THE VERDICT", None), (680.0, 10, "THE TRUTH", None)]:
    HOLDS.append((at - 0.001, 3.4, BG_PL(), chapter_ov(n, title, sub), "chapter"))
HOLDS.sort(key=lambda h: h[0])

CTA_START = 672.6    # VO second where the CTA line starts; runs on into its hold


# ============================================================================ timeline

def build_timeline(vo_len):
    """List of (out_t0, out_t1, kind, payload): 'vo' -> (vo_t0) ; 'hold' -> hold tuple."""
    tl, out, vo = [], 0.0, 0.0
    for h in HOLDS:
        at = vo_len if h[0] >= 9999 else h[0]
        if at > vo:
            tl.append((out, out + at - vo, "vo", vo))
            out += at - vo
            vo = at
        tl.append((out, out + h[1], "hold", h))
        out += h[1]
    if vo < vo_len:
        tl.append((out, out + vo_len - vo, "vo", vo))
        out += vo_len - vo
    return tl, out


TL = None


def locate(t):
    for t0, t1, kind, p in TL:
        if t0 <= t < t1:
            return t0, t1, kind, p
    return TL[-1]


def vo_at(t):
    """VO second at output second t (holds freeze at their VO point)."""
    t0, t1, kind, p = locate(t)
    if kind == "vo":
        return p + (t - t0)
    return VO_LEN if p[0] >= 9999 else p[0]


_logo = None


def frame(i):
    global _logo
    t = i / FPS
    t0, t1, kind, p = locate(t)
    if kind == "hold":
        at, dur, bg, ov, snd = p
        lt = t - t0
        a = bg(t, lt, dur)
        base = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
        ov(base, t, lt, dur)
    else:
        v = p + (t - t0)
        b = next((b for b in B if b[0] <= v < b[1]), B[-1])
        a = b[2](v, v - b[0], b[1] - b[0])
        base = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
        b[3](base, v)
    # CTA (VO line + its hold): the IPL video's subscribe animation
    cs = out_of_vo(CTA_START)
    if cs <= t < cs + 11.9:
        sys.path.insert(0, os.path.join(ROOT, "ipl_killed"))
        import hook as ipl_hook
        if _logo is None:
            _logo = Image.open(LOGO).convert("RGBA")
        lt = t - cs
        base.alpha_composite(ipl_hook.cta_layer(lt, _logo))
    if t < 0.8:
        base = Image.fromarray((np.asarray(base.convert("RGB"), np.float32) * (t / 0.8)).astype(np.uint8)).convert("RGBA")
    out = np.asarray(base.convert("RGB")).copy()
    out[:BAR] = 0
    out[H - BAR:] = 0
    return out


def out_of_vo(v):
    for t0, t1, kind, p in TL:
        if kind == "vo" and p <= v < p + (t1 - t0):
            return t0 + (v - p)
    return 0.0


def render_chunk(args):
    i0, i1 = args
    return b"".join(frame(i).tobytes() for i in range(i0, i1))


# ============================================================================ sound

def at_(buf, x, t, g):
    i = int(t * SR)
    if 0 <= i < len(buf):
        n = min(len(x), len(buf) - i)
        buf[i:i + n] += x[:n] * g


def soundtrack(path, total):
    n = int(total * SR)
    w = wave.open(os.path.join(HERE, "vo", "vo_clean.wav"))
    vo = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
    if w.getframerate() != SR:
        import scipy.signal as ss
        vo = ss.resample_poly(vo, SR, w.getframerate())
    voice = np.zeros(n)
    fx = np.zeros(n)
    for t0, t1, kind, p in TL:
        if kind == "vo":
            seg = vo[int(p * SR):int((p + t1 - t0) * SR)]
            at_(voice, seg, t0, 1.0)
        else:
            snd = p[4]
            if snd == "crowd":
                at_(fx, sfx.crowd(min(p[1], 14)), t0 + 0.2, 0.55)
                at_(fx, braam(weight=1.2), t0 + 0.1, 0.45)
            elif snd == "crowd_s":
                at_(fx, sfx.crowd(p[1]), t0, 0.28)
            elif snd in ("hit", "chapter"):
                at_(fx, sfx.whoosh(0.4), t0 - 0.2, 0.22)
                at_(fx, braam(weight=0.8), t0 + 0.02, 0.4 if snd == "hit" else 0.25)
            elif snd == "title":
                at_(fx, braam(weight=1.2), t0 + 0.2, 0.55)
            elif snd == "cold":
                at_(fx, sfx.crowd(p[1]), t0 + 1.0, 0.45)
            elif snd == "water":
                rng = np.random.default_rng(7)
                wn = rng.standard_normal(int(p[1] * SR))
                wn = np.convolve(wn, np.ones(40) / 40, "same") * np.minimum(1, np.minimum(np.arange(len(wn)), len(wn) - np.arange(len(wn))) / (0.6 * SR))
                at_(fx, wn, t0, 0.5)
    tt = np.arange(n) / SR
    # music: tension under the hook, low sad bed through the fall, warm lift from Vidarbha, quiet for the truth
    sad = st.pad(st.D_MINOR, total, cutoff=1000)[:n]
    warm = st.pad(st.WARM, total, cutoff=1500)[:n]
    o = out_of_vo
    m_sad = np.interp(tt, [0, o(58), o(92), o(244), o(366), o(490), o(569), o(638), o(680), o(719), total],
                      [0.25, 0.3, 0.2, 0.32, 0.4, 0.15, 0.2, 0.35, 0.15, 0.3, 0.2])
    m_warm = np.interp(tt, [0, o(92), o(125), o(170), o(244), o(490), o(522), o(569), o(604), o(638), total],
                       [0.0, 0.05, 0.35, 0.3, 0.05, 0.1, 0.4, 0.35, 0.3, 0.05, 0.1])
    bed = sad * m_sad + warm * m_warm + drone(total)[:n] * 0.06
    duck = 1 - 0.55 * np.convolve(np.abs(voice) > 0.02, np.ones(int(0.25 * SR)) / int(0.25 * SR), "same")
    mix = voice + (bed * 0.5 + fx * 0.7) * duck
    mix[-int(2 * SR):] *= np.linspace(1, 0, int(2 * SR))
    mix = np.tanh(mix * 1.05) * 0.95
    pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w2:
        w2.setnchannels(2)
        w2.setsampwidth(2)
        w2.setframerate(SR)
        w2.writeframes(np.repeat(pcm[:, None], 2, axis=1).tobytes())


# ============================================================================ main

def setup():
    global TL, VO_LEN
    w = wave.open(os.path.join(HERE, "vo", "vo_clean.wav"))
    VO_LEN = w.getnframes() / w.getframerate()
    TL, total = build_timeline(VO_LEN)
    return total


def sheet():
    total = setup()
    ts = [3, 14, 40, 70, 95, 112, 128, 141, 158, 170, 200, 252, 268, 300, 330, 375, 395, 415, 440, 462, 480, 500,
          515, 528, 540, 552, 575, 590, 606, 620, 645, 660, 675, 690, 712, 735, 760, 800, 850, 880]
    ims = []
    for s in ts:
        tt = min(s, total - 0.1)
        ims.append(Image.fromarray(frame(int(tt * FPS))).resize((384, 216)))
    sh = Image.new("RGB", (384 * 8, 216 * 5))
    for k, im in enumerate(ims):
        sh.paste(im, ((k % 8) * 384, (k // 8) * 216))
    os.makedirs(os.path.join(OUT, "chk"), exist_ok=True)
    sh.save(os.path.join(OUT, "chk", "sheet.jpg"))
    print(f"total {int(total // 60)}:{total % 60:04.1f}")


def main():
    if "--sheet" in sys.argv:
        return sheet()
    total = setup()
    print(f"total {int(total // 60)}:{total % 60:04.1f}", flush=True)
    os.makedirs(OUT, exist_ok=True)
    wav = os.path.join(OUT, "mix.wav")
    soundtrack(wav, total)
    silent = os.path.join(OUT, "video.mp4")
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                            "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    nfr = int(total * FPS)
    chunks = [(i, min(i + 15, nfr)) for i in range(0, nfr, 15)]
    with Pool(os.cpu_count()) as pool:
        for k, buf in enumerate(pool.imap(render_chunk, chunks)):
            enc.stdin.write(buf)
            if k % 200 == 0:
                print(f"  {k * 15}/{nfr}", flush=True)
    enc.stdin.close()
    enc.wait()
    full = os.path.join(OUT, "Karun_303.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", silent, "-i", wav, "-c:v", "copy",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
                    "-shortest", full], check=True)
    up = full  # the CRF 18 master is ~280 MB, already under the 400 MB upload limit
    print("LONG_DONE", full, up)


if __name__ == "__main__":
    main()

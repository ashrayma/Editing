#!/usr/bin/env python3
"""9:16 Short: "Dada's 51* — Wanderers, December 2006".

    python3 make_short.py            ->  out/Dada_51_Short.mp4  (1080x1920, 30 fps, -14 LUFS)
    python3 make_short.py --sheet    ->  out/chk/sheet.jpg      (contact sheet, no encode)

Voice: the creator's own recording (vo/vo_raw.m4a). Beat times below are voiceover seconds, read from a Whisper
transcript of the recording (vo/words.json) and silence detection. Visuals: the supplied photos (assets/, the small
ones AI-upscaled into up/), Ken Burns on every photo, and graphics drawn here (51*, scoreboards, the email leak,
the bowler cards, a subscribe CTA, the end question). Music and SFX are synthesised.
"""
import math
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "kohli_countdown"))
sys.path.insert(0, os.path.join(ROOT, "doc_video"))
import sfx  # noqa: E402
import soundtrack as st  # noqa: E402
from virat_hook import braam, drone  # noqa: E402

W, H, FPS = 1080, 1920, 30
SR = sfx.SR
OUT = os.path.join(HERE, "out")
OFF = 1.9                         # VO seconds trimmed from the head (speech starts at 2.06)
END_VO = 96.6                     # end card runs to here (VO ends 92.5)
DUR = END_VO - OFF
Y, RED, WHITE, GREEN, INK = (255, 222, 89), (232, 48, 48), (255, 255, 255), (70, 200, 110), (10, 10, 14)
ANTON = os.path.join(ROOT, "doc_video", "thumb", "fonts", "Anton-Regular.woff")
BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
BOLD = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
LOGO = os.path.join(ROOT, "kohli_countdown", "assets", "logo.png")
TEXT_Y = 1300                     # caption band on photos (faces sit in the top half; Shorts UI below ~1600)


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


# ----------------------------------------------------------------------------- photos

_ph = {}


def photo(name):
    """Upscaled copy (75% ESRGAN + 25% Lanczos, keeps skin texture) when there is one, else the original."""
    if name in _ph:
        return _ph[name]
    src = Image.open(os.path.join(HERE, "assets", name + ".jpg")).convert("RGB")
    up = os.path.join(HERE, "up", name + ".png")
    if os.path.exists(up):
        e = Image.open(up).convert("RGB")
        o = src.resize(e.size, Image.LANCZOS)
        src = Image.fromarray((np.asarray(e, np.float32) * 0.75 + np.asarray(o, np.float32) * 0.25).astype(np.uint8))
    elif src.width < 1400:
        k = 1400 / src.width
        src = src.resize((1400, int(src.height * k)), Image.LANCZOS)
    _ph[name] = src
    return src


def cover(im, z, fx, fy, w=W, h=H):
    """Crop to w:h around focus (fx, fy) at zoom z (1 = just covers)."""
    s = max(w / im.width, h / im.height) * z
    cw, ch = w / s, h / s
    x0 = min(max(fx * im.width - cw / 2, 0), im.width - cw)
    y0 = min(max(fy * im.height - ch / 2, 0), im.height - ch)
    return im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((w, h), Image.BILINEAR)


_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = (1 - 0.5 * np.clip(((_xx - W / 2) / (W * 0.62)) ** 2 + ((_yy - H * 0.45) / (H * 0.62)) ** 2, 0, 1))[..., None]
LOWER = np.clip((_yy - H * 0.52) / (H * 0.3), 0, 1)[..., None] ** 1.2


def look(im, gray=0.0, dark=1.0):
    a = np.asarray(im, np.float32)
    lum = a.mean(-1, keepdims=True)
    a = lum + (a - lum) * (1.08 - gray)
    a = (a - 128) * 1.08 + 128
    a = a * VIG * dark
    a = a * (1 - 0.62 * LOWER)                      # caption band
    return a


def photo_bg(name, lt, dur, z0=1.06, z1=1.18, f0=(0.5, 0.3), f1=None, gray=0.0, dark=1.0):
    f1 = f1 or f0
    k = ease(lt / dur) if f1 != f0 else lt / dur
    fx = f0[0] + (f1[0] - f0[0]) * k
    fy = f0[1] + (f1[1] - f0[1]) * k
    return look(cover(photo(name), z0 + (z1 - z0) * lt / dur, fx, fy), gray, dark)


def panel_bg(name, lt, dur, fy=0.45, box_h=760, gray=0.0):
    """Landscape photo: blurred copy fills the frame, the photo sits sharp in a yellow-edged panel."""
    im = photo(name)
    back = cover(im, 1.0, 0.5, 0.5).filter(ImageFilter.GaussianBlur(28))
    a = np.asarray(back, np.float32) * 0.42
    z = 1.04 + 0.08 * lt / dur
    pw = W - 80
    pan = cover(im, z, 0.5, 0.5, pw, box_h)
    if gray:
        pan = ImageOps.grayscale(pan).convert("RGB")
    base = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    y = int(H * fy - box_h / 2)
    ImageDraw.Draw(base).rectangle((36, y - 4, W - 36, y + box_h + 4), fill=Y)
    base.paste(pan, (40, y))
    return np.asarray(base, np.float32) * VIG


_dust = np.random.default_rng(51).random((70, 4))


def plate(t, tint=(1.0, 0.85, 0.35)):
    """Moving dark plate for text screens: slow glow, drifting grid, dust."""
    cx = W * (0.5 + 0.25 * math.sin(t * 0.3))
    cy = H * (0.4 + 0.1 * math.cos(t * 0.21))
    g = np.exp(-(((_xx[::4, ::4] - cx) / 520) ** 2 + ((_yy[::4, ::4] - cy) / 700) ** 2))
    lo = np.stack([g * 46 * tint[0], g * 46 * tint[1], g * 46 * tint[2]], -1)
    a = np.asarray(Image.fromarray(lo.astype(np.uint8)).resize((W, H), Image.BILINEAR), np.float32) + np.array(INK)
    off = (t * 16) % 90
    grid = (((_xx + off) % 90 < 1.5) | ((_yy + off * 0.6) % 90 < 1.5)).astype(np.float32)[..., None] * 8
    a = a + grid
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    for x0, y0, sp, r in _dust:
        x = (x0 * W + t * 18 * (sp - 0.5)) % W
        y = (y0 * H - t * (14 + 30 * sp)) % H
        rr = 1 + 3 * r
        c = int(60 + 100 * r)
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=(c, int(c * 0.9), int(c * 0.45)))
    return np.asarray(im, np.float32)


# ----------------------------------------------------------------------------- text and graphics

def text_img(lines, size, path=ANTON, gap=0.08, maxw=980):
    rows = []
    for txt, col in lines:
        s = size
        while font(path, s).getlength(txt) > maxw and s > 24:
            s -= 2
        f = font(path, s)
        l, t, r, b = f.getbbox(txt)
        rows.append((txt, col, f, l, t, r - l, b - t))
    pad = 40
    wid = max(r[5] for r in rows)
    hgt = sum(r[6] for r in rows) + int(size * gap) * (len(rows) - 1)
    im = Image.new("RGBA", (wid + 2 * pad, hgt + 2 * pad), (0, 0, 0, 0))
    y = pad
    for txt, col, f, l, t, w, h in rows:
        ImageDraw.Draw(im).text((pad + (wid - w) // 2 - l, y - t), txt, font=f, fill=col)
        y += h + int(size * gap)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(12)).point(lambda v: int(v * 0.85)))
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (4, 7))
    out.alpha_composite(im)
    return out


def put(base, im, cx, cy, s=1.0, a=1.0):
    if a <= 0:
        return
    if s != 1.0:
        im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BILINEAR)
    if a < 1:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def rise(base, t, t0, lines, size, cy, path=ANTON, t1=None):
    """Text rises in; fades out before t1."""
    if t < t0 or (t1 and t > t1):
        return
    k = ein(t, t0, 0.3)
    a = k * (1 - ein(t, t1 - 0.2, 0.2) if t1 else 1)
    put(base, text_img(lines, size, path), W / 2, cy + 40 * (1 - k), 1.0, a)


def slam(base, t, t0, lines, size, cy, path=ANTON, t1=None):
    """Text slams in from big."""
    if t < t0 or (t1 and t > t1):
        return
    k = ein(t, t0, 0.14)
    a = k * (1 - ein(t, t1 - 0.2, 0.2) if t1 else 1)
    put(base, text_img(lines, size, path), W / 2, cy, 1.5 - 0.5 * k, a)


def chip(base, t, t0, label, cy, bg=Y, fg=INK, size=52, cx=W / 2, t1=None):
    if t < t0 or (t1 and t > t1):
        return
    f = font(BLACK, size)
    w = int(f.getlength(label)) + 60
    im = Image.new("RGBA", (w, size + 44), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, size + 43), 18, fill=bg + (255,))
    d.text((w / 2, (size + 44) / 2), label, font=f, fill=fg, anchor="mm")
    k = ein(t, t0, 0.25)
    a = k * (1 - ein(t, t1 - 0.2, 0.2) if t1 else 1)
    put(base, im, cx + 60 * (1 - k), cy, 1.0, a)


def stamp(base, t, t0, word, cy, color=RED, angle=-8, size=130, cx=W / 2, t1=None):
    if t < t0 or (t1 and t > t1):
        return
    f = font(BLACK, size)
    l, tt, r, b = f.getbbox(word)
    im = Image.new("RGBA", (r - l + 80, b - tt + 70), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((6, 6, im.width - 7, im.height - 7), outline=color + (255,), width=12)
    d.text((40 - l, 35 - tt), word, font=f, fill=color + (255,))
    al = np.asarray(im.getchannel("A"), np.float32)
    al = al * np.where(np.random.default_rng(len(word)).random(al.shape) > 0.88, 0.3, 1.0)
    im.putalpha(Image.fromarray(al.astype(np.uint8)))
    im = im.rotate(angle, expand=True, resample=Image.BICUBIC)
    k = t - t0
    a = ease(k / 0.05) * (1 - ein(t, t1 - 0.2, 0.2) if t1 else 1)
    put(base, im, cx, cy, 1 + 1.0 * (1 - ease(k / 0.12)), a)


def scorebug(base, t, t0, team, score, note, cy, col=Y, count_from=0, t1=None):
    """Broadcast-style score bar; the runs count up."""
    if t < t0 or (t1 and t > t1):
        return
    k = ein(t, t0, 0.3)
    p = ease((t - t0 - 0.1) / 0.9)
    runs, rest = score.split("/") if "/" in score else (score.split(" ")[0], None)
    shown = int(count_from + (int(runs) - count_from) * p)
    txt = f"{shown}/{rest}" if rest else f"{shown}" + score[len(runs):]
    im = Image.new("RGBA", (960, 190), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, 959, 189), 26, fill=(16, 17, 24, 240), outline=(80, 82, 96), width=2)
    d.rounded_rectangle((0, 0, 230, 189), 26, fill=col + (255,))
    d.rectangle((200, 0, 230, 189), fill=col + (255,))
    d.text((115, 95), team, font=font(ANTON, 76), fill=INK, anchor="mm")
    d.text((270, 95), txt, font=font(ANTON, 104), fill=WHITE, anchor="lm")
    d.text((930, 95), note, font=font(BLACK, 40), fill=(200, 202, 212), anchor="rm")
    a = k * (1 - ein(t, t1 - 0.2, 0.2) if t1 else 1)
    put(base, im, W / 2, cy + 50 * (1 - k), 1.0, a)


def counter(base, t, t0, t1, label, v1, cy, col=Y, cx=W / 2):
    if t < t0:
        return
    v = int(v1 * ease((t - t0) / (t1 - t0)))
    im = text_img([(str(v), col)], 230)
    put(base, im, cx, cy, 1.0, ein(t, t0, 0.2))
    put(base, text_img([(label, WHITE)], 54, BLACK), cx, cy + 160, 1.0, ein(t, t0, 0.2))


def email_card(base, t, t0):
    if t < t0:
        return
    k = ein(t, t0, 0.35)
    im = Image.new("RGBA", (900, 560), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, 899, 559), 30, fill=(240, 240, 244, 255))
    d.rounded_rectangle((0, 0, 899, 110), 30, fill=(40, 42, 54, 255))
    d.rectangle((0, 80, 899, 110), fill=(40, 42, 54, 255))
    d.text((40, 55), "CONFIDENTIAL", font=font(BLACK, 46), fill=WHITE, anchor="lm")
    d.text((40, 170), "To:  BCCI", font=font(BOLD, 40), fill=(60, 62, 72))
    d.text((40, 230), "From:  Coach", font=font(BOLD, 40), fill=(60, 62, 72))
    d.text((40, 290), "Re:  Sourav Ganguly", font=font(BOLD, 40), fill=(60, 62, 72))
    for k_, w_ in enumerate((780, 700, 760, 520)):
        d.rounded_rectangle((40, 370 + k_ * 42, 40 + w_, 392 + k_ * 42), 8, fill=(190, 192, 200))
    put(base, im.rotate(-4, expand=True, resample=Image.BICUBIC), W / 2, 860 + 120 * (1 - k), 1.0, k)


def wicket_list(base, t):
    for k, (name, t0) in enumerate([("SEHWAG", 52.4), ("SACHIN", 53.6), ("DRAVID", 54.8)]):
        if t < t0:
            continue
        y = 620 + k * 170
        a = ein(t, t0, 0.2)
        put(base, text_img([(name, WHITE)], 120), W / 2, y, 1.0, a)
        s = ein(t, t0 + 0.25, 0.25)
        if s > 0:
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(lay).rectangle((W / 2 - 230, y - 6, W / 2 - 230 + 460 * s, y + 8), fill=RED + (255,))
            base.alpha_composite(lay)
            if s >= 1:
                put(base, text_img([("OUT", RED)], 64, BLACK), W / 2 + 330, y, 1.0, 1.0)


def path_graphic(base, t, t0):
    """2003 World Cup run: stages light up, ending on FINAL."""
    steps = ["GROUP", "SUPER SIX", "SEMI-FINAL", "FINAL"]
    for k, s in enumerate(steps):
        tk = t0 + 0.55 * k
        if t < tk:
            continue
        y = 520 + k * 200
        on = ein(t, tk, 0.25)
        col = Y if s == "FINAL" else WHITE
        put(base, text_img([(s, col)], 120 if s == "FINAL" else 92), W / 2, y, 1.0, on)
        if k:
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(lay).rectangle((W / 2 - 3, y - 140, W / 2 + 3, y - 140 + 80 * on), fill=Y + (255,))
            base.alpha_composite(lay)


def bowler_card(base, name, label, lt, dur, focus):
    a = photo_bg(name, lt, dur, 1.1, 1.22, focus)
    return a, label


def bell(size, ang):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    s = size
    d.pieslice((s * 0.2, s * 0.12, s * 0.8, s * 0.72), 180, 360, fill=WHITE)
    d.polygon([(s * 0.2, s * 0.42), (s * 0.8, s * 0.42), (s * 0.9, s * 0.72), (s * 0.1, s * 0.72)], fill=WHITE)
    d.ellipse((s * 0.42, s * 0.72, s * 0.58, s * 0.86), fill=WHITE)
    d.ellipse((s * 0.45, s * 0.04, s * 0.55, s * 0.14), fill=WHITE)
    return im.rotate(ang, resample=Image.BICUBIC, center=(s / 2, s * 0.1))


_logo = None


def subscribe_card(base, t, t0, click):
    global _logo
    if t < t0:
        return
    if _logo is None:
        _logo = Image.open(LOGO).convert("RGBA")
    q = ein(t, t0, 0.4)
    cw, ch = 980, 330
    card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle((0, 0, cw - 1, ch - 1), 40, fill=(22, 23, 30, 245), outline=(70, 72, 84), width=2)
    cd.ellipse((36, 36, 166, 166), fill=INK, outline=Y, width=4)
    lg = _logo.copy()
    lg.thumbnail((118, 70))
    card.alpha_composite(lg, (101 - lg.width // 2, 101 - lg.height // 2))
    cd.text((200, 78), "TheCricketLounge", font=font(BLACK, 54), fill=WHITE, anchor="lm")
    cd.text((200, 132), "Cricket stories, the way fans feel them", font=font(BOLD, 30), fill=(170, 172, 180),
            anchor="lm")
    clicked = t >= click
    press = 0.92 if click - 0.1 <= t < click + 0.07 else 1.0
    bw, bh = 520, 96
    btn = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    bd = ImageDraw.Draw(btn)
    bd.rounded_rectangle((0, 0, bw - 1, bh - 1), 48, fill=(72, 74, 84) if clicked else (229, 33, 33))
    bd.text((bw / 2, bh / 2), "SUBSCRIBED" if clicked else "SUBSCRIBE", font=font(BLACK, 40),
            fill=(225, 225, 230) if clicked else WHITE, anchor="mm")
    btn = btn.resize((int(bw * press), int(bh * press)), Image.BILINEAR)
    bx, by = 60, 200
    card.alpha_composite(btn, (bx + (bw - btn.width) // 2, by + (bh - btn.height) // 2))
    if clicked:
        e = t - click
        card.alpha_composite(bell(90, 28 * math.sin(e * 26) * math.exp(-e * 3.2)), (bx + bw + 60, by + 3))
    x, y = (W - cw) // 2, int(1120 + 60 * (1 - q))
    card.putalpha(card.getchannel("A").point(lambda v: int(v * q)))
    base.alpha_composite(card, (x, y))
    if click - 1.0 <= t < click + 0.6:
        m = ease((t - (click - 1.0)) / 0.8)
        tx, ty = x + bx + bw / 2, y + by + bh / 2 + 10
        cx, cy = 980 + (tx - 980) * m, 1800 + (ty - 1800) * m
        pts = [(0, 0), (0, 56), (15, 43), (26, 67), (35, 62), (24, 39), (44, 39)]
        d = ImageDraw.Draw(base)
        d.polygon([(cx + px + 3, cy + py + 4) for px, py in pts], fill=(0, 0, 0, 150))
        d.polygon([(cx + px, cy + py) for px, py in pts], fill=WHITE, outline=(0, 0, 0))


def strike(base, t, t0, cy, w=640):
    s = ein(t, t0, 0.3)
    if s <= 0:
        return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(lay).line((W / 2 - w / 2, cy + 30, W / 2 - w / 2 + w * s, cy - 30), fill=Y + (255,), width=22)
    base.alpha_composite(lay)


# ----------------------------------------------------------------------------- the beats (VO seconds)
# (start, end, background(t, lt, dur) -> float array, overlay(base, t))

def P(name, z0=1.06, z1=1.18, f0=(0.5, 0.3), f1=None, gray=0.0, dark=1.0):
    return lambda t, lt, dur: photo_bg(name, lt, dur, z0, z1, f0, f1, gray, dark)


def PN(name, fy=0.42, box_h=760, gray=0.0):
    return lambda t, lt, dur: panel_bg(name, lt, dur, fy, box_h, gray)


def PL(tint=(1.0, 0.85, 0.35)):
    return lambda t, lt, dur: plate(t, tint)


def ov_hook(b, t):
    rise(b, t, 2.1, [("MY FAVOURITE", WHITE), ("TEST INNINGS?", Y)], 120, TEXT_Y, t1=5.6)


def ov_51(b, t):
    rise(b, t, 5.7, [("SOURAV GANGULY", WHITE)], 96, TEXT_Y - 170)
    slam(b, t, 7.25, [("51*", Y)], 420, TEXT_Y + 60)


def ov_laugh(b, t):
    rise(b, t, 8.5, [("\"BHAI...\"", (200, 202, 210))], 90, 470, BLACK)
    slam(b, t, 10.3, [("200", WHITE)], 300, 800)
    slam(b, t, 11.1, [("300", WHITE)], 300, 1100)
    rise(b, t, 13.1, [("...AND YOU'RE STUCK", WHITE), ("ON 51?", Y)], 110, 1450)


def ov_notjust(b, t):
    rise(b, t, 15.1, [("NOT JUST", WHITE), ("51 RUNS.", WHITE)], 170, 900)


def ov_statement(b, t):
    slam(b, t, 17.1, [("A STATEMENT.", Y)], 200, 920)


def ov_wc(b, t):
    chip(b, t, 19.6, "2003 WORLD CUP", TEXT_Y - 40)
    rise(b, t, 20.4, [("CAPTAIN", WHITE), ("SOURAV GANGULY", Y)], 100, TEXT_Y + 150)


def ov_path(b, t):
    rise(b, t, 21.6, [("INDIA, 2003", (200, 202, 210))], 70, 330, BLACK)
    path_graphic(b, t, 22.6)


def ov_dada(b, t):
    slam(b, t, 27.9, [("\"DADA\"", Y)], 260, TEXT_Y)


def ov_chappell(b, t):
    chip(b, t, 30.2, "NEW COACH: GREG CHAPPELL", TEXT_Y + 40, size=50)


def ov_email(b, t):
    rise(b, t, 32.0, [("2005", (200, 202, 210))], 80, 380, BLACK)
    email_card(b, t, 32.0)
    stamp(b, t, 32.9, "LEAKED", 1000, angle=-10, size=150)


def ov_khatam(b, t):
    chip(b, t, 33.9, "CAPTAINCY  ✗", TEXT_Y - 120, bg=(40, 42, 54), fg=WHITE)
    chip(b, t, 35.0, "TEAM  ✗", TEXT_Y + 10, bg=(40, 42, 54), fg=WHITE)
    stamp(b, t, 36.4, "DADA KHATAM?", 900, size=118)


def ov_year(b, t):
    chip(b, t, 39.3, "~11 MONTHS LATER", TEXT_Y - 60)
    rise(b, t, 40.9, [("INDIA LOSING", WHITE), ("IN SOUTH AFRICA", Y)], 100, TEXT_Y + 130)


def ov_recall(b, t):
    stamp(b, t, 43.6, "RECALLED", TEXT_Y, color=Y, angle=-6, size=150)


def ov_jo(b, t):
    if t >= 45.1:
        txt = "JOHANNESBURG"
        n = int(len(txt) * min(1, (t - 45.1) / 0.6))
        put(b, text_img([(txt[:max(1, n)], WHITE)], 150), W / 2, 820, 1.0, 1.0)
    rise(b, t, 45.9, [("DECEMBER 2006", Y)], 110, 1010)
    chip(b, t, 47.0, "GREEN PITCH", 1200, bg=GREEN, fg=INK)


BOWLERS = [("pollock_bowling", "POLLOCK", 47.75, (0.6, 0.3)), ("steyn_stump", "STEYN", 48.45, (0.45, 0.2)),
           ("ntini_bowling", "NTINI", 49.15, (0.5, 0.25)), ("nel_appeal", "NEL", 49.85, (0.5, 0.22)),
           ("kallis_bowling", "KALLIS", 50.55, (0.5, 0.3))]


def ov_bowler(label):
    return lambda b, t: put(b, text_img([(label, Y)], 170), W / 2, TEXT_Y + 40, 1.0, 1.0)


def ov_pace(b, t):
    slam(b, t, 51.4, [("ONLY PACE.", Y)], 170, 380, t1=52.3)
    wicket_list(b, t)
    scorebug(b, t, 56.0, "IND", "110/4", "DAY 1", 1300)


def ov_walkin(b, t):
    rise(b, t, 58.0, [("SOURAV GANGULY", Y)], 120, TEXT_Y)
    chip(b, t, 58.6, "WALKS IN AT 110/4", TEXT_Y + 150, bg=(40, 42, 54), fg=WHITE)


def ov_cta(b, t):
    rise(b, t, 60.0, [("BEFORE WHAT", WHITE), ("HAPPENED NEXT...", WHITE)], 100, 560, t1=61.1)
    slam(b, t, 61.3, [("TRUE CRICKET", WHITE), ("FAN?", Y)], 170, 760)
    subscribe_card(b, t, 62.4, 63.6)


def ov_balls(b, t):
    counter(b, t, 64.8, 66.6, "BALLS", 101, 1180, WHITE, W * 0.28)
    counter(b, t, 65.6, 67.9, "RUNS", 51, 1180, Y, W * 0.72)
    if t > 68.7:
        k = 0.5 + 0.5 * math.sin((t - 68.7) * 10)
        put(b, text_img([("EVERY BALL: DANGER", RED)], 100), W / 2, 1520, 1.0, ein(t, 68.7, 0.2) * (0.7 + 0.3 * k))


def ov_notout(b, t):
    slam(b, t, 70.3, [("51*", Y)], 420, TEXT_Y - 30)
    chip(b, t, 71.6, "TOP SCORER", TEXT_Y + 210)


def ov_249(b, t):
    rise(b, t, 73.2, [("FIRST INNINGS", (200, 202, 210))], 70, 700, BLACK)
    scorebug(b, t, 73.4, "IND", "249 ALL OUT", "", 960, count_from=110)


def ov_sree(b, t):
    chip(b, t, 76.3, "SREESANTH  5/40", TEXT_Y - 80)
    scorebug(b, t, 79.5, "SA", "84 ALL OUT", "", TEXT_Y + 120, col=GREEN, count_from=0)


def ov_win(b, t):
    rise(b, t, 81.7, [("INDIA'S FIRST TEST WIN", WHITE), ("IN SOUTH AFRICA", WHITE)], 96, 1300)
    slam(b, t, 84.3, [("EVER.", Y)], 230, 1530)


def ov_answer(b, t):
    rise(b, t, 86.1, [("NOT JUST 51 RUNS.", WHITE)], 110, TEXT_Y - 120, t1=88.0)
    rise(b, t, 88.0, [("DADA'S ANSWER.", Y)], 130, TEXT_Y - 120)
    if t >= 90.6:
        stamp(b, t, 90.6, "DADA KHATAM", TEXT_Y + 110, size=110)
        strike(b, t, 91.6, TEXT_Y + 110)


def ov_end(b, t):
    rise(b, t, 92.7, [("DADA'S 51", WHITE)], 150, 1080)
    rise(b, t, 93.1, [("OR", (200, 202, 210))], 80, 1220, BLACK)
    rise(b, t, 93.4, [("LAXMAN'S 281?", Y)], 150, 1360)
    chip(b, t, 94.3, "COMMENT  ↓", 1560, bg=RED, fg=WHITE)


BEATS = [
    (1.9, 5.58, P("dada_odi_walking_cap", 1.12, 1.24, (0.5, 0.22)), ov_hook),
    (5.58, 8.4, P("dada_odi_walking_cap", 1.32, 1.45, (0.5, 0.2)), ov_51),
    (8.4, 15.0, PL(), ov_laugh),
    (15.0, 16.95, PL((0.6, 0.6, 0.7)), ov_notjust),
    (16.95, 18.4, PL(), ov_statement),
    (18.4, 21.5, P("dada_fistpump_wc2003", 1.05, 1.16, (0.5, 0.26)), ov_wc),
    (21.5, 27.5, PL(), ov_path),
    (27.5, 29.8, PN("dada_lords_1996", 0.36, 820), ov_dada),
    (29.8, 32.0, P("dada_chappell_2005", 1.12, 1.22, (0.42, 0.2), (0.7, 0.12)), ov_chappell),
    (32.0, 33.7, PL((0.8, 0.8, 0.9)), ov_email),
    (33.7, 39.1, P("dada_odi_dejected_2003", 1.05, 1.2, (0.5, 0.24), gray=0.85, dark=0.85), ov_khatam),
    (39.1, 42.8, P("dada_running_bengal", 1.08, 1.2, (0.5, 0.18)), ov_year),
    (42.8, 45.0, P("dada_bengal_partner", 1.08, 1.18, (0.62, 0.16)), ov_recall),
    (45.0, 47.75, PL((0.45, 0.9, 0.5)), ov_jo),
] + [(t0, (BOWLERS[k + 1][2] if k + 1 < len(BOWLERS) else 51.3), P(n, 1.1, 1.22, f), ov_bowler(lab))
     for k, (n, lab, t0, f) in enumerate(BOWLERS)] + [
    (51.3, 57.4, PL((0.45, 0.9, 0.5)), ov_pace),
    (57.4, 59.8, P("dada_walking_off_test", 1.25, 1.42, (0.5, 0.17)), ov_walkin),
    (59.8, 64.6, PL(), ov_cta),
    (64.6, 70.2, P("dada_batting_bengal", 1.45, 1.62, (0.64, 0.2)), ov_balls),
    (70.2, 73.1, P("dada_bat_raised_test", 1.05, 1.15, (0.45, 0.36)), ov_notout),
    (73.1, 75.7, PL(), ov_249),
    (75.7, 81.4, P("sreesanth", 1.5, 1.62, (0.22, 0.3)), ov_sree),
    (81.4, 86.0, PN("india_win_wanderers_2006", 0.4, 780), ov_win),
    (86.0, 92.6, P("dada_bat_raised_test", 1.25, 1.05, (0.45, 0.32)), ov_answer),
    (92.6, END_VO, PN("kolkata_2001_laxman_dravid", 0.28, 660), ov_end),
]
SLAMS = [7.25, 17.1, 27.9, 32.9, 36.4, 43.6, 56.0, 61.3, 70.3, 79.5, 84.3, 90.6]   # braam / impact hits


def beat_at(t):
    for b in BEATS:
        if b[0] <= t < b[1]:
            return b
    return BEATS[-1]


def frame(i):
    t = OFF + i / FPS                      # VO time
    t0, t1, bg, ov = beat_at(t)
    lt, dur = t - t0, t1 - t0
    a = bg(t, lt, dur)
    if lt < 0.1 and t0 > OFF + 0.01:       # quick flash on the cut
        a = a + 255 * 0.18 * (1 - lt / 0.1)
    for h in SLAMS:                         # punch of light on hits
        if 0 <= t - h < 0.25:
            a = a + 255 * 0.12 * (1 - (t - h) / 0.25)
    base = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    ov(base, t)
    if i < 6:                               # fade in from black
        base = Image.fromarray((np.asarray(base.convert("RGB"), np.float32) * (i / 6)).astype(np.uint8))
    return base.convert("RGB")


# ----------------------------------------------------------------------------- sound

def at(buf, x, t, g):
    i = int(t * SR)
    if 0 <= i < len(buf):
        n = min(len(x), len(buf) - i)
        buf[i:i + n] += x[:n] * g


def load_vo():
    chain = ("highpass=f=85,afftdn=nf=-28:nr=12,equalizer=f=250:t=q:w=1.2:g=-2,equalizer=f=3500:t=q:w=1.0:g=3,"
             "acompressor=threshold=-22dB:ratio=3.5:attack=4:release=90:makeup=4")
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(HERE, "vo", "vo_raw.m4a"), "-af", chain,
                          "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    vo = np.frombuffer(raw, np.float32).astype(np.float64)
    return vo / (np.abs(vo).max() + 1e-9) * 0.9


def soundtrack(path):
    n = int(DUR * SR)
    tt = np.arange(n) / SR + OFF                       # VO time
    vo = load_vo()[int(OFF * SR):][:n]
    voice = np.zeros(n)
    voice[:len(vo)] = vo
    # music: sad pad through the fall (Dm), warm + pulse from the recall, lift at the win
    sad = st.pad(st.D_MINOR, DUR, cutoff=1100)[:n]
    warm = st.pad(st.WARM, DUR, cutoff=1600)[:n]
    pulse = st.pulse(DUR, 92, lambda x: min(1.0, max(0.0, (x + OFF - 45) / 20)))[:n]
    m_sad = np.interp(tt, [OFF, 18, 29, 33, 42, 45, 60, 64.6, 92, END_VO], [0.5, 0.6, 0.5, 0.75, 0.75, 0.3, 0.2, 0.0, 0, 0])
    m_warm = np.interp(tt, [OFF, 42, 45, 60, 61, 64.6, 81, 86, 92.6, END_VO], [0.0, 0.0, 0.35, 0.35, 0.1, 0.45, 0.6, 0.75, 0.6, 0.0])
    m_pulse = np.interp(tt, [OFF, 44, 46, 59.5, 60, 64.6, 92.6, END_VO], [0, 0, 0.5, 0.6, 0.1, 0.6, 0.5, 0])
    bed = sad * m_sad + warm * m_warm + pulse * m_pulse * 0.8
    bed += drone(DUR)[:n] * np.interp(tt, [OFF, 30, 40, 50, 58, 60, END_VO], [0.05, 0.08, 0.12, 0.16, 0.2, 0.05, 0.03])
    fx = np.zeros(n)
    for h in SLAMS:
        at(fx, braam(weight=1.0 if h in (56.0, 70.3, 84.3) else 0.75), h - OFF - 0.02, 0.5)
    for t0, *_ in BEATS[1:]:
        at(fx, sfx.whoosh(0.35), t0 - OFF - 0.18, 0.12)
    at(fx, sfx.tick(), 63.6 - OFF, 0.8)
    at(fx, sfx.ding(0.9, 1320), 63.68 - OFF, 0.3)
    t = 64.8
    while t < 67.9:                                    # counter ticks
        at(fx, sfx.tick(), t - OFF, 0.25)
        t += 0.08
    at(fx, sfx.crowd(4.0), 81.4 - OFF, 0.35)            # the win
    duck = 1 - 0.5 * np.convolve(np.abs(voice) > 0.03, np.ones(int(0.2 * SR)) / int(0.2 * SR), "same")
    mix = voice + (bed * 0.55 + fx * 0.7) * duck
    tail = int(1.0 * SR)
    mix[-tail:] *= np.linspace(1, 0, tail)
    mix = np.tanh(mix * 1.05) * 0.95
    pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(np.repeat(pcm[:, None], 2, axis=1).tobytes())


# ----------------------------------------------------------------------------- render

def sheet():
    ts = [3.0, 7.6, 11.5, 13.6, 17.4, 20.8, 24.6, 28.3, 31.3, 33.2, 37.0, 41.5, 44.0, 46.3, 48.0, 50.8, 55.0, 56.6,
          58.8, 63.8, 66.5, 69.0, 71.9, 74.5, 80.0, 84.6, 91.9, 94.6]
    ims = [frame(int(round((t - OFF) * FPS))).resize((270, 480)) for t in ts]
    sh = Image.new("RGB", (270 * 7, 480 * 4))
    for k, im in enumerate(ims):
        sh.paste(im, ((k % 7) * 270, (k // 7) * 480))
    os.makedirs(os.path.join(OUT, "chk"), exist_ok=True)
    sh.save(os.path.join(OUT, "chk", "sheet.jpg"))


def main():
    os.makedirs(OUT, exist_ok=True)
    if "--sheet" in sys.argv:
        return sheet()
    wav = os.path.join(OUT, "mix.wav")
    soundtrack(wav)
    silent = os.path.join(OUT, "video.mp4")
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                            "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        enc.stdin.write(frame(i).tobytes())
    enc.stdin.close()
    enc.wait()
    out = os.path.join(OUT, "Dada_51_Short.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", silent, "-i", wav, "-c:v", "copy",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
                    "-shortest", out], check=True)
    print("DONE", out)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""9:16 Short / Reel: "ODI cricket is dying. And we might be the reason."

    python3 make_short.py            ->  out/ODI_Dying_Short.mp4  (1080x1920, 30 fps, -14 LUFS)
    python3 make_short.py --preview  ->  out/preview_sheet.jpg    (one frame per beat, no encode)

Every beat is timed to the ElevenLabs voiceover (vo/vo_raw.mp3); line timings come from silence detection plus
PocketSphinx recognition of each chunk (see TIMINGS). Visuals: the supplied photos (assets/), Ken Burns
moves, an old-film look for 1971, rain + stamp for the washed-out Test, rolling numbers, a 50-overs bar,
a Test/T20 split screen and a closing "ODI YA T20?" card. Music and SFX are synthesised (doc_video/soundtrack.py,
kohli_countdown/sfx.py, the braam hit from doc_video/virat_hook.py), so everything is royalty-free.
"""
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "kohli_countdown"))
sys.path.insert(0, os.path.join(ROOT, "doc_video"))
import sfx  # noqa: E402
import soundtrack as st  # noqa: E402
from virat_hook import braam, drone  # noqa: E402

A = os.path.join(HERE, "assets")
OUT = os.path.join(HERE, "out")
VO = os.path.join(HERE, "vo", "vo_raw.mp3")
W, H, FPS = 1080, 1920, 30
END = 92.2                       # VO ends 88.5; end card to 92.2
Y = (255, 222, 89)               # brand #FFDE59
RED = (232, 48, 48)
WHITE = (255, 255, 255)
BLACK_F = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
XB_F = "/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf"
ANTON = os.path.join(ROOT, "doc_video", "thumb", "fonts", "Anton-Regular.woff")
rng = np.random.default_rng(1971)

# VO line timings (seconds), from silence detection + PocketSphinx on each chunk
TIMINGS = {
    "dying": 0.00, "reason": 2.63, "began": 4.73, "date": 7.54, "melbourne": 10.18, "never": 11.93,
    "scheduled": 15.90, "rain": 18.98, "oneday": 21.43, "justlike": 25.36, "history": 26.63, "wc": 28.43,
    "revolution": 32.20, "colours": 34.03, "moments": 40.81, "kapil": 44.45, "desert": 46.96, "dhoni": 48.81,
    "t20": 51.19, "faster": 53.56, "suddenly": 57.13, "forgetting": 60.78, "offers": 62.55, "patience": 66.85,
    "excitement": 68.49, "innings": 70.72, "mistake": 74.35, "outdated": 77.55, "importance": 81.03,
    "lose": 84.30, "identity": 86.21, "vo_end": 88.48,
}
T = TIMINGS


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def arr(im):
    return np.asarray(im, np.float32)


def img(a, mode="RGB"):
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), mode)


# ----------------------------------------------------------------------------- image prep

def load(name):
    p = os.path.join(A, name)
    for alt in (p.replace(".jpg", "_x4.jpg"),):
        if os.path.exists(alt):
            p = alt
    return Image.open(p).convert("RGB")


class Plate:
    """A photo prepared for a portrait frame.

    mode "cover": fills 9:16 (portrait photos).  mode "card": landscape photo shown large in the middle over a
    blurred, darkened copy of itself.  Ken Burns zoom/pan is applied per frame from the oversized master.
    """

    def __init__(self, name, mode="cover", focus=(0.5, 0.4), card_scale=1.25, card_y=0.42, mask=False):
        self.name = name
        self.im = load(name) if not mask else Image.open(
            os.path.join(HERE, "masks", name.replace(".jpg", ".png"))).convert("RGB")
        self.mode, self.focus, self.card_y, self.card_scale = mode, focus, card_y, card_scale
        if mode == "cover":
            s = max(W / self.im.width, H / self.im.height) * 1.18
            self.master = self.im.resize((int(self.im.width * s), int(self.im.height * s)), Image.LANCZOS)
        else:
            s = max(W / self.im.width, H / self.im.height) * 1.1
            bg = self.im.resize((int(self.im.width * s), int(self.im.height * s)), Image.BILINEAR)
            bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2, (bg.width - W) // 2 + W, (bg.height - H) // 2 + H))
            bg = bg.filter(ImageFilter.GaussianBlur(28))
            self.bg = arr(ImageEnhance.Brightness(bg).enhance(0.45)) * (0 if mask else 1)
            fw = int(W * card_scale)
            self.fg = self.im.resize((fw, int(self.im.height * fw / self.im.width)), Image.LANCZOS)

    def frame(self, p, zoom=(1.0, 1.08), pan=(0.0, 0.0)):
        """p: 0..1 progress through the shot."""
        z = zoom[0] + (zoom[1] - zoom[0]) * p
        if self.mode == "cover":
            m = self.master  # 1.18x the size that just covers the frame
            vis_w, vis_h = min(m.width, W * 1.18 / z), min(m.height, H * 1.18 / z)
            fx = self.focus[0] + pan[0] * p
            fy = self.focus[1] + pan[1] * p
            x0 = np.clip(fx * m.width - vis_w / 2, 0, m.width - vis_w)
            y0 = np.clip(fy * m.height - vis_h / 2, 0, m.height - vis_h)
            return arr(m.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + vis_w, y0 + vis_h)))
        out = self.bg.copy()
        fg = self.fg
        fw, fh = int(fg.width * z), int(fg.height * z)
        f = fg.resize((fw, fh), Image.BILINEAR)
        x = int((W - fw) / 2 + pan[0] * W * (p - 0.5))
        y = int(H * self.card_y - fh / 2)
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(W, x + fw), min(H, y + fh)
        if x1 > x0 and y1 > y0:
            out[y0:y1, x0:x1] = arr(f)[y0 - y:y1 - y, x0 - x:x1 - x]
        # soft edges top/bottom of the card
        edge = 70
        for k in range(edge):
            a = k / edge
            for yy in (y0 + k, y1 - 1 - k):
                if 0 <= yy < H:
                    out[yy] = out[yy] * a + self.bg[yy] * (1 - a)
        return out


# ----------------------------------------------------------------------------- looks

MASK = False  # True while rendering protected-area masks instead of pictures
GRAIN = [rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32) for _ in range(6)]
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
VIGNETTE = (1 - 0.55 * np.clip(((XX - W / 2) / (W * 0.62)) ** 2 + ((YY - H / 2) / (H * 0.6)) ** 2, 0, 1))[..., None]


def grain(a, amount, i):
    if MASK:
        return a
    g = GRAIN[i % len(GRAIN)]
    g = np.repeat(np.repeat(g, 2, 0), 2, 1)[: a.shape[0], : a.shape[1], None]
    return a + g * amount


def gray(a, k):
    if MASK:
        return a
    if k <= 0:
        return a
    l = a @ np.array([0.299, 0.587, 0.114], np.float32)
    return a * (1 - k) + l[..., None] * k


def old_film(a, i, t):
    """Sepia, flicker, grain, vertical scratches, dust."""
    if MASK:
        return a
    l = a @ np.array([0.299, 0.587, 0.114], np.float32)
    a = l[..., None] * np.array([1.05, 0.96, 0.82], np.float32)
    a *= 0.92 + 0.08 * np.sin(t * 37) * np.sin(t * 11)
    a = grain(a, 16, i)
    r = np.random.default_rng(int(t * FPS))
    for _ in range(r.integers(0, 3)):
        x = int(r.uniform(0, W))
        a[:, x:x + 2] = a[:, x:x + 2] * 0.6 + 200 * 0.4
    for _ in range(r.integers(2, 7)):
        x, y, s = int(r.uniform(0, W)), int(r.uniform(0, a.shape[0])), int(r.uniform(2, 6))
        a[y:y + s, x:x + s] *= 0.3
    return a


RAIN_TILES = []
for k in range(4):
    im = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(im)
    r = np.random.default_rng(k)
    for _ in range(900):
        x, y, ln = r.uniform(-200, W), r.uniform(-100, H), r.uniform(30, 90)
        d.line((x, y, x + ln * 0.25, y + ln), fill=int(r.uniform(60, 170)), width=2)
    RAIN_TILES.append(arr(im.filter(ImageFilter.GaussianBlur(0.8)))[..., None] / 255)


def rain(a, i, k):
    if MASK:
        return a
    return a * (1 - 0.25 * k) + RAIN_TILES[i % 4] * 230 * k


def flash(a, k, color=(255, 255, 255)):
    if MASK:
        return a
    return a + (np.array(color, np.float32) - a) * k


# ----------------------------------------------------------------------------- text

_font_cache = {}


def font(path, size):
    key = (path, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


def text_block(lines, size, path=BLACK_F, gap=0.1, stroke=0, shadow=True):
    """lines: [(text, colour)] -> RGBA block, each line auto-shrunk to fit 980 px."""
    rows = []
    for txt, col in lines:
        s = size
        while font(path, s).getlength(txt) > 980 and s > 30:
            s -= 4
        f = font(path, s)
        l, t, r, b = f.getbbox(txt, stroke_width=stroke)
        rows.append((txt, col, f, l, t, r - l, b - t))
    hgt = sum(r[6] for r in rows) + int(size * gap) * (len(rows) - 1)
    wid = max(r[5] for r in rows)
    pad = 50
    im = Image.new("RGBA", (wid + 2 * pad, hgt + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    y = pad
    for txt, col, f, l, t, w, h in rows:
        x = pad + (wid - w) // 2 - l
        ImageDraw.Draw(sh).text((x, y - t + 6), txt, font=f, fill=(0, 0, 0, 230), stroke_width=stroke + 6,
                                stroke_fill=(0, 0, 0, 230))
        ImageDraw.Draw(im).text((x, y - t), txt, font=f, fill=col, stroke_width=stroke, stroke_fill=(0, 0, 0))
        y += h + int(size * gap)
    if shadow:
        out = Image.new("RGBA", im.size, (0, 0, 0, 0))
        out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
        out.alpha_composite(im)
        return out
    return im


class Headline:
    def __init__(self, t_in, t_out, lines, y, size=110, anim="rise", path=BLACK_F, stroke=0):
        self.t_in, self.t_out, self.y, self.anim = t_in, t_out, y, anim
        self.lines, self.size, self.path, self.stroke = lines, size, path, stroke
        self.im = text_block(lines, size, path, stroke=stroke)
        self.text = "".join(t for t, _ in lines)
        self.pref_y, self.follow, self.dy, self.cx = y, None, 0, W / 2

    def set_scale(self, k):
        self.im = text_block(self.lines, int(self.size * k), self.path, stroke=self.stroke)

    def footprint(self):
        return footprint_of(self.im)

    def draw(self, base, t):
        if not (self.t_in <= t < self.t_out):
            return
        k = t - self.t_in
        out_k = ease((t - (self.t_out - 0.18)) / 0.18)
        im = self.im
        if self.anim == "slam":
            s = 1 + 0.35 * (1 - ease(k / 0.16))
            a = ease(k / 0.08)
            jx = jy = 0
            if 0.14 < k < 0.4:
                amp = 10 * (1 - (k - 0.14) / 0.26)
                jx, jy = rng.uniform(-amp, amp, 2)
        elif self.anim == "type":
            n = len(self.text)
            shown = int(min(1, k / (0.05 * n + 0.01)) * n)
            s, a, jx, jy = 1.0, 1.0, 0, 0
            if shown < n:  # reveal left to right by cropping the block
                frac = shown / max(1, n)
                im = im.crop((0, 0, max(1, int(50 + (im.width - 100) * frac)), im.height))
        else:  # rise
            s, a, jx, jy = 1.0, ease(k / 0.3), 0, 40 * (1 - ease(k / 0.35))
        a *= 1 - out_k
        if a <= 0:
            return
        if s != 1:
            im = im.resize((int(im.width * s), int(im.height * s)), Image.BILINEAR)
        if a < 1:
            im = im.copy()
            im.putalpha(im.getchannel("A").point(lambda v, a=a: int(v * a)))
        x = int(self.cx - (self.im.width * s if self.anim != "type" else self.im.width) / 2 + jx)
        base.alpha_composite(im, (max(-im.width, x), int(self.y - im.height / 2 + jy)))


def footprint_of(im):
    return (np.asarray(im.getchannel("A")) > 60).astype(np.float32)


class Number:
    """Rolling number (e.g. 0 -> 175*) with a label underneath."""

    def __init__(self, t_in, t_out, start, end, y, suffix="", label="", size=330, roll=0.9, color=Y):
        self.t_in, self.t_out, self.start, self.end, self.y = t_in, t_out, start, end, y
        self.suffix, self.size, self.roll, self.color = suffix, size, roll, color
        self.label = text_block([(label, WHITE)], 54, XB_F) if label else None
        self.pref_y, self.follow, self.dy, self.cx, self.base_size = y, None, 0, W / 2, size

    def set_scale(self, k):
        self.size = int(self.base_size * k)

    def footprint(self):
        """Number at its final value plus the label below, stacked as drawn (centred on y)."""
        num = text_block([(f"{self.end}{self.suffix}", self.color)], self.size, ANTON)
        h = int(num.height / 2 + self.size * 0.55 + (self.label.height if self.label else 0))
        top = num.height // 2
        fp = np.zeros((top + h + 10, max(num.width, self.label.width if self.label else 0)), np.float32)
        ox = (fp.shape[1] - num.width) // 2
        fp[:num.height, ox:ox + num.width] = footprint_of(num)
        if self.label:
            lx, ly = (fp.shape[1] - self.label.width) // 2, top + int(self.size * 0.55)
            lf = footprint_of(self.label)
            fp[ly:ly + lf.shape[0], lx:lx + lf.shape[1]] = np.maximum(fp[ly:ly + lf.shape[0], lx:lx + lf.shape[1]], lf)
        self.fp_offset = top  # y is the centre of the number, i.e. top of footprint + top
        return fp

    def draw(self, base, t):
        if not (self.t_in <= t < self.t_out):
            return
        k = t - self.t_in
        v = int(round(self.start + (self.end - self.start) * ease(k / self.roll)))
        a = ease(k / 0.12) * (1 - ease((t - (self.t_out - 0.18)) / 0.18))
        im = text_block([(f"{v}{self.suffix}", self.color)], self.size, ANTON)
        s = 1 + 0.18 * (1 - ease(k / 0.2))
        im = im.resize((int(im.width * s), int(im.height * s)), Image.BILINEAR)
        im.putalpha(im.getchannel("A").point(lambda q: int(q * a)))
        base.alpha_composite(im, (int(self.cx - im.width / 2), int(self.y - im.height / 2)))
        if self.label:
            la = ease((k - 0.3) / 0.3) * (1 - ease((t - (self.t_out - 0.18)) / 0.18))
            if la > 0:
                lb = self.label.copy()
                lb.putalpha(lb.getchannel("A").point(lambda q: int(q * la)))
                base.alpha_composite(lb, (int(self.cx - lb.width / 2), int(self.y + self.size * 0.55)))


class Stamp:
    """Rubber-stamp text (rotated, red box) that slams in."""

    def __init__(self, t_in, t_out, txt, y, color=RED, angle=-8):
        self.t_in, self.t_out, self.y = t_in, t_out, y
        f = font(BLACK_F, 120)
        l, t, r, b = f.getbbox(txt)
        im = Image.new("RGBA", (r - l + 80, b - t + 70), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rectangle((6, 6, im.width - 7, im.height - 7), outline=color + (255,), width=12)
        d.text((40 - l, 35 - t), txt, font=f, fill=color + (255,))
        m = np.asarray(im.getchannel("A"), np.float32)
        holes = np.random.default_rng(3).random(m.shape) > 0.9
        m[holes] *= 0.35
        im.putalpha(img(m, "L"))
        self.im = im.rotate(angle, expand=True, resample=Image.BICUBIC)
        self.pref_y, self.follow, self.dy, self.cx = y, None, 0, W / 2

    def set_scale(self, k):
        pass

    def footprint(self):
        return footprint_of(self.im)

    def draw(self, base, t):
        if not (self.t_in <= t < self.t_out):
            return
        k = t - self.t_in
        s = 1 + 0.9 * (1 - ease(k / 0.14))
        a = ease(k / 0.06) * (1 - ease((t - (self.t_out - 0.15)) / 0.15))
        im = self.im.resize((int(self.im.width * s), int(self.im.height * s)), Image.BILINEAR)
        im.putalpha(im.getchannel("A").point(lambda q: int(q * a)))
        base.alpha_composite(im, ((W - im.width) // 2, int(self.y - im.height / 2)))


class OversBar:
    """'50 OVERS' bar that fills slowly while a clock ticks."""

    def __init__(self, t_in, t_out, y):
        self.t_in, self.t_out, self.y = t_in, t_out, y
        self.pref_y, self.follow, self.dy, self.cx = y, None, 0, W / 2

    def set_scale(self, k):
        pass

    def footprint(self):
        fp = np.ones((46 + 24 + 60, W - 220), np.float32)
        self.fp_offset = 0
        return fp

    def draw(self, base, t):
        if not (self.t_in <= t < self.t_out):
            return
        k = t - self.t_in
        a = ease(k / 0.2) * (1 - ease((t - (self.t_out - 0.18)) / 0.18))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        x0, x1, h = 110, W - 110, 46
        d.rounded_rectangle((x0, self.y, x1, self.y + h), radius=23, fill=(255, 255, 255, 60))
        fill = min(1.0, k / (self.t_out - self.t_in - 0.3)) ** 2.2
        if fill > 0.02:
            d.rounded_rectangle((x0, self.y, x0 + (x1 - x0) * fill, self.y + h), radius=23, fill=Y + (255,))
        overs = int(fill * 50)
        f = font(XB_F, 48)
        d.text((x0, self.y + h + 24), f"OVER {overs}/50", font=f, fill=(235, 235, 235, 255))
        layer.putalpha(layer.getchannel("A").point(lambda q: int(q * a)))
        base.alpha_composite(layer)


# ----------------------------------------------------------------------------- the edit

P = {}
PM = {}  # the same plates built from the protected-area masks


def plates():
    P["dhoni"] = Plate("dhoni_2011_six.jpg", "cover", focus=(0.45, 0.42))
    P["odi71"] = Plate("first_odi_1971.jpg", "card", card_scale=1.7, card_y=0.47)
    P["odi71b"] = Plate("first_odi_1971.jpg", "card", card_scale=2.3, card_y=0.5)
    P["captains"] = Plate("wc1992_captains_collage.jpg", "card", card_scale=0.86, card_y=0.4)
    P["opera"] = Plate("wc1992_captains_opera_house.jpg", "card", card_scale=1.6, card_y=0.5)
    P["trophy"] = Plate("t20wc_trophy_floodlights.jpg", "card", card_scale=0.62, card_y=0.31)
    P["kapil"] = Plate("kapil_1983.jpg", "cover", focus=(0.45, 0.4))
    P["sachin"] = Plate("sachin_sharjah_drive.jpg", "cover", focus=(0.4, 0.4))
    P["storm"] = Plate("sachin_desert_storm_gilchrist.jpg", "card", card_scale=1.7, card_y=0.48)
    P["ipl"] = Plate("ipl_rcb_title_wide.jpg", "card", card_scale=1.65, card_y=0.47)
    P["iplk"] = Plate("ipl_rcb_title_kohli.jpg", "card", card_scale=1.0, card_y=0.4)
    P["empty"] = Plate("empty_stands.jpg", "card", card_scale=1.8, card_y=0.5)
    for k in list(P):
        q = P[k]
        PM[k] = Plate(q.name, q.mode, q.focus, card_scale=getattr(q, "card_scale", 1.25), card_y=q.card_y, mask=True)
    P["logo"] = Image.open(os.path.join(ROOT, "kohli_countdown", "assets", "logo.png")).convert("RGBA")


def split_frame(t):
    """Test (1971, top) vs T20 (IPL, bottom), the active half lit by the VO."""
    top = Image.fromarray(np.clip(P["odi71"].frame(0.5, zoom=(1.15, 1.15)), 0, 255).astype(np.uint8))
    bot = Image.fromarray(np.clip(P["ipl"].frame(0.5, zoom=(1.1, 1.1)), 0, 255).astype(np.uint8))
    out = np.zeros((H, W, 3), np.float32)
    half = H // 2
    out[:half] = old_film(arr(top.crop((0, H * 0.47 - half / 2, W, H * 0.47 + half / 2)).resize((W, half))), 0, t)
    out[half:] = arr(bot.crop((0, H * 0.47 - half / 2, W, H * 0.47 + half / 2)).resize((W, H - half)))
    if t >= T["patience"]:
        dim_bot = ease((t - T["patience"]) / 0.3) * (1 - ease((t - T["excitement"]) / 0.3))
        dim_top = ease((t - T["excitement"]) / 0.3)
        out[half:] *= 1 - 0.65 * dim_bot
        out[:half] *= 1 - 0.65 * dim_top
    out[half - 4:half + 4] = Y
    return out


def montage(t):
    keys = ["kapil", "sachin", "dhoni"]
    i = int((t - 40.7) / 0.45) % 3
    a = gray(P[keys[i]].frame(0.5, zoom=(1.1, 1.1)), 0.85) * 0.5
    return a


def background(t, i):
    """The picture under the text at time t (float RGB)."""
    def seg(t0, t1):
        return (t - t0) / max(0.01, t1 - t0)

    if t < 4.45:
        a = P["dhoni"].frame(seg(0, 4.45), zoom=(1.0, 1.1))
        return gray(a, ease((t - 1.0) / 3.0)) * (1 - 0.25 * ease((t - 1.0) / 3.0))
    if t < 7.3:  # rewind: shrink back, flicker, jitter
        p = seg(4.45, 7.3)
        a = gray(P["dhoni"].frame(1 - p, zoom=(0.9, 1.12), pan=(0, 0)), 1.0)
        a = np.roll(a, int(rng.uniform(-14, 14)), axis=1) * (0.55 + 0.15 * np.sin(t * 50))
        return old_film(a, i, t) * 0.85
    if t < 21.2:
        p = seg(7.3, 21.2)
        a = old_film(P["odi71"].frame(p, zoom=(1.0, 1.18), pan=(0.35, 0)), i, t)
        if t >= T["scheduled"]:
            a *= 1 - 0.25 * ease((t - T["scheduled"]) / 1.5)
        if t >= T["rain"] - 0.3:
            a = rain(a, i, ease((t - T["rain"] + 0.3) / 0.6) * 0.9)
        return a
    if t < 28.2:
        a = old_film(P["odi71b"].frame(seg(21.2, 28.2), zoom=(1.05, 1.15), pan=(-0.3, 0)), i, t)
        if T["history"] <= t < T["history"] + 0.35:
            a = flash(a, 1 - (t - T["history"]) / 0.35)
        return a
    if t < 33.95:
        a = old_film(P["odi71"].frame(0.5, zoom=(1.3, 1.36)), i, t) * 0.32
        if t > T["revolution"]:
            a = a * (1 + 1.2 * ease((t - T["revolution"]) / 1.7))
        return a
    if t < 38.5:
        a = P["captains"].frame(seg(33.95, 38.5), zoom=(1.0, 1.12), pan=(0, 0.1))
        if t < 34.25:
            a = flash(a, 1 - (t - 33.95) / 0.3)
        return a * 0.9
    if t < 40.7:
        return P["opera"].frame(seg(38.5, 40.7), zoom=(1.0, 1.08)) * 0.9
    if t < 44.4:
        return montage(t)
    if t < 46.85:
        return P["kapil"].frame(seg(44.4, 46.85), zoom=(1.02, 1.14)) * 0.82
    if t < 48.7:
        return P["sachin"].frame(seg(46.85, 48.7), zoom=(1.02, 1.14)) * 0.82
    if t < 51.05:
        return P["dhoni"].frame(seg(48.7, 51.05), zoom=(1.0, 1.1)) * 0.85
    if t < 54.6:
        a = P["ipl"].frame(seg(51.05, 54.6), zoom=(1.0, 1.15), pan=(0.2, 0))
        if t < T["t20"] + 0.3 and t >= T["t20"]:
            a = flash(a, 1 - (t - T["t20"]) / 0.3)
        return a * 0.88
    if t < 57.0:
        return P["iplk"].frame(seg(54.6, 57.0), zoom=(1.0, 1.15)) * 0.85
    if t < 60.6:
        return gray(P["trophy"].frame(seg(57.0, 60.6), zoom=(1.05, 1.12)), 0.5) * 0.55
    if t < 62.45:
        return np.zeros((H, W, 3), np.float32) + 8
    if t < 70.6:
        return split_frame(t)
    if t < 77.3:
        a = P["storm"].frame(seg(70.6, 77.3), zoom=(1.0, 1.2), pan=(0.25, 0))
        if t >= T["mistake"]:
            k = ease((t - T["mistake"]) / 0.4)
            a = gray(a, 0.7 * k) * (1 - 0.3 * k) + np.array([90, 0, 0], np.float32) * 0.35 * k
            if t < T["mistake"] + 0.25:
                a = flash(a, (1 - (t - T["mistake"]) / 0.25) * 0.8, RED)
        return a * 0.88
    if t < 84.1:
        return gray(P["empty"].frame(seg(77.3, 84.1), zoom=(1.0, 1.16)), 0.35) * 0.7
    if t < 88.9:  # colour returns to Dhoni's six as the point lands
        p = seg(84.1, 88.9)
        return gray(P["dhoni"].frame(p, zoom=(1.12, 1.0)), 1 - ease(p)) * (0.6 + 0.3 * p)
    p = seg(88.9, END)
    return gray(P["dhoni"].frame(1.0, zoom=(1.0, 1.0)), 0.0) * (0.35 - 0.1 * p)


def build_overlays():
    hl = []
    add = hl.append
    add(Headline(0.05, T["reason"], [("ODI CRICKET", WHITE), ("IS DYING.", Y)], 560, 150, "slam"))
    add(Headline(T["reason"], 4.45, [("AND WE MIGHT BE", WHITE), ("THE REASON.", RED)], 400, 110, "rise"))
    add(Headline(T["began"], 7.3, [("HOW DID IT", WHITE), ("BEGIN?", Y)], 820, 140, "rise"))
    add(Headline(T["date"], T["melbourne"] + 1.2, [("5 JAN 1971", Y)], 470, 150, "type", ANTON))
    add(Headline(T["melbourne"], 15.8, [("MELBOURNE, AUSTRALIA", WHITE)], 600, 66, "rise", XB_F))
    add(Headline(T["never"], 15.8, [("NEVER SUPPOSED", WHITE), ("TO HAPPEN", Y)], 1330, 104, "rise"))
    add(Headline(T["scheduled"], 21.2, [("AUS vs ENG", WHITE), ("TEST MATCH", Y)], 470, 120, "rise"))
    add(Stamp(T["rain"] + 0.1, 21.2, "WASHED OUT", 1330))
    add(Headline(T["oneday"], 25.3, [("TEST MATCH", (170, 170, 170))], 470, 110, "rise"))
    add(Headline(T["oneday"] + 1.6, 25.3, [("ONE-DAY MATCH", Y)], 640, 120, "slam"))
    add(Headline(T["justlike"], 28.2, [("AND JUST LIKE THAT…", WHITE)], 470, 84, "rise"))
    add(Headline(T["history"], 28.2, [("CRICKET HISTORY", WHITE), ("CHANGED.", Y)], 1300, 120, "slam"))
    add(Number(T["wc"], 32.1, 1971, 1975, 800, label="FIRST CRICKET WORLD CUP", roll=1.1))
    add(Headline(T["revolution"], 33.95, [("THEN CAME A", WHITE), ("REVOLUTION", Y)], 860, 124, "slam"))
    for t0, t1, txt in [(T["colours"], 35.3, "COLOURED JERSEYS"), (35.3, 36.3, "WHITE BALLS"),
                        (36.3, 37.3, "FLOODLIGHTS"), (37.3, 38.5, "DAY-NIGHT CRICKET")]:
        add(Headline(t0, t1, [(txt, Y)], 1380, 110, "slam"))
    add(Headline(38.5, 40.7, [("A GLOBAL", WHITE), ("SPECTACLE", Y)], 1380, 120, "rise"))
    add(Headline(T["moments"], 44.4, [("MOMENTS WE'LL", WHITE), ("NEVER FORGET", Y)], 900, 120, "rise"))
    add(Number(T["kapil"], 46.85, 0, 175, 1250, suffix="*", label="KAPIL DEV · 1983", size=320, roll=0.8))
    add(Headline(T["desert"], 48.7, [("DESERT STORM", Y)], 1200, 130, "slam"))
    add(Headline(T["desert"] + 0.25, 48.7, [("SACHIN · SHARJAH 1998", WHITE)], 1340, 58, "rise", XB_F))
    add(Headline(T["dhoni"], 51.05, [("THE SIX", Y)], 1230, 150, "slam"))
    add(Headline(T["dhoni"] + 0.25, 51.05, [("DHONI · WORLD CUP 2011", WHITE)], 1370, 58, "rise", XB_F))
    add(Headline(T["t20"], 53.5, [("THEN CAME", WHITE), ("T20", Y)], 1330, 150, "slam"))
    for t0, t1, txt in [(T["faster"], 54.6, "FASTER GAMES."), (54.6, 55.6, "BIGGER SIXES."),
                        (55.6, 57.0, "MORE ENTERTAINMENT.")]:
        add(Headline(t0, t1, [(txt, Y)], 1380, 108, "slam"))
    add(Headline(T["suddenly"], 60.6, [("50 OVERS", Y)], 640, 170, "slam", ANTON))
    add(OversBar(T["suddenly"] + 0.3, 60.6, 840))
    add(Headline(58.1, 60.6, [("STARTED FEELING", WHITE), ("TOO LONG?", RED)], 1250, 110, "rise"))
    add(Headline(T["forgetting"], 62.45, [("BUT HERE'S WHAT", WHITE), ("WE'RE FORGETTING", Y)], 900, 100, "rise"))
    add(Headline(T["offers"], 66.75, [("ODI GIVES WHAT", WHITE), ("NO OTHER FORMAT CAN", Y)], 960, 84, "rise"))
    add(Headline(T["patience"], 70.6, [("THE PATIENCE OF TEST", WHITE)], 820, 74, "rise"))
    add(Headline(T["excitement"], 70.6, [("THE EXCITEMENT OF T20", Y)], 1100, 74, "rise"))
    add(Headline(T["innings"], 74.3, [("ONE INNINGS CAN", WHITE), ("CHANGE EVERYTHING", Y)], 1330, 100, "rise"))
    add(Headline(T["mistake"], 77.3, [("ONE MISTAKE CAN", WHITE), ("COST THE MATCH", RED)], 1330, 100, "slam"))
    add(Headline(T["outdated"], 81.0, [("NOT DYING BECAUSE", WHITE), ("IT'S OUTDATED…", (200, 200, 200))], 520, 96,
                 "rise"))
    add(Headline(T["importance"], 84.1, [("WE STOPPED", WHITE), ("GIVING IT IMPORTANCE", Y)], 1340, 96, "slam"))
    add(Headline(T["lose"], 86.15, [("IF WE LOSE", WHITE), ("ODI CRICKET…", Y)], 600, 120, "rise"))
    add(Headline(T["identity"], 88.9, [("WE LOSE A PART OF", WHITE), ("CRICKET'S IDENTITY", Y)], 1340, 96, "rise"))
    add(Headline(88.9, END, [("ODI", Y), ("YA", WHITE), ("T20?", Y)], 820, 210, "slam", ANTON))
    add(Headline(89.4, END, [("COMMENT KARO", WHITE)], 1300, 72, "rise", XB_F))
    add(Headline(89.7, END, [("FOLLOW FOR MORE CRICKET STORIES", (220, 220, 220))], 1420, 44, "rise", XB_F))

    by = {getattr(o, "text", type(o).__name__): o for o in hl}

    def follow(child, parent, dy):
        by[child].follow, by[child].dy = by[parent], dy

    follow("MELBOURNE, AUSTRALIA", "5 JAN 1971", 140)
    follow("ONE-DAY MATCH", "TEST MATCH", 170)
    follow("SACHIN · SHARJAH 1998", "DESERT STORM", 140)
    follow("DHONI · WORLD CUP 2011", "THE SIX", 160)
    follow("OversBar", "50 OVERS", 160)
    follow("COMMENT KARO", "ODIYAT20?", 420)
    follow("FOLLOW FOR MORE CRICKET STORIES", "COMMENT KARO", 110)
    by["50 OVERS"].band = (940, BOTTOM_LIMIT)           # below the trophy card
    by["STARTED FEELINGTOO LONG?"].band = (940, BOTTOM_LIMIT)
    by["THE PATIENCE OF TEST"].band = (TOP_LIMIT, H // 2)       # stays on the Test half
    by["THE EXCITEMENT OF T20"].band = (H // 2, BOTTOM_LIMIT)  # stays on the T20 half
    return hl


# ----------------------------------------------------------------------------- keep text off faces and players

TOP_LIMIT, BOTTOM_LIMIT = 240, 1640   # below the logo; above the Shorts/Reels caption + button area
_mask_cache = {}


def protected(t):
    """Protected-area map (0..1, faces = 1, bodies/objects ~0.6) for the picture at time t."""
    global MASK, P
    key = round(t, 1)
    if key not in _mask_cache:
        saved = P
        MASK, P = True, {**P, **PM}
        try:
            m = background(key, int(key * FPS))[..., 0] / 255
        finally:
            MASK, P = False, saved
        _mask_cache[key] = np.clip(m, 0, 1) ** 2  # faces dominate the cost
    return _mask_cache[key]


def place_overlays(overlays, report=True):
    """Put every text element where it covers the least of anyone (faces weighted most).

    Each title is placed together with the sub-labels that `follow` it, as one group. Candidates: every height
    between the logo and the Shorts UI, centred / left / right, at full size or slightly smaller. Groups that
    are on screen at the same time never overlap each other.
    """
    groups = [o for o in overlays if o.follow is None]
    kids = {id(o): [c for c in overlays if c.follow is o] for o in groups}
    placed = []

    for o in groups:
        members = [o] + kids[id(o)]
        ts = np.linspace(min(m.t_in for m in members) + 0.1, max(m.t_out for m in members) - 0.1, 5)
        prot = np.max([protected(t) for t in ts], axis=0)
        lo, hi = getattr(o, "band", (TOP_LIMIT, BOTTOM_LIMIT))
        best = None
        for k in (1.0, 0.86, 0.74, 0.64):
            for m in members:
                m.set_scale(k)
            fps = [(m, m.footprint(), getattr(m, "fp_offset", None)) for m in members]
            for side in ("c", "l", "r"):
                for y in range(lo, hi, 10):
                    total = hit = clash = 0.0
                    ok = True
                    boxes = []
                    for m, fp, off in fps:
                        my = y + (m.dy * k if m is not o else 0)
                        top = int(my - (off if off is not None else fp.shape[0] // 2))
                        bot = top + fp.shape[0]
                        if top < lo - (0 if m is o else 400) or bot > hi or fp.shape[1] > W + 40:
                            ok = False
                            break
                        w = fp.shape[1]
                        x0 = {"c": (W - w) // 2, "l": min(10, (W - w) // 2), "r": max(W - 10 - w, (W - w) // 2)}[side]
                        xs = max(0, x0)
                        reg = prot[top:bot:4, xs:x0 + w:4]
                        f = fp[:, xs - x0:][::4, ::4][: reg.shape[0], : reg.shape[1]]
                        hit += float((reg * f).sum())
                        total += float(f.sum())
                        boxes.append((m, x0, top, x0 + w, bot))
                    if not ok:
                        continue
                    for q, qx0, qt, qx1, qb in placed:
                        for m, x0, top, x1, bot in boxes:
                            if q.t_in < m.t_out and m.t_in < q.t_out and top < qb and qt < bot and x0 < qx1 and qx0 < x1:
                                clash += 5.0
                    frac = hit / (total + 1e-6)
                    c = frac + clash + 0.00006 * abs(y - o.pref_y) + 0.02 * (1 - k) + (0.008 if side != "c" else 0)
                    if best is None or c < best[0]:
                        best = (c, frac, k, side, y, boxes)
        c, frac, k, side, y, boxes = best
        for m in members:
            m.set_scale(k)
        for m, x0, top, x1, bot in boxes:
            m.y = y + (m.dy * k if m is not o else 0)
            m.cx = (x0 + x1) / 2
            placed.append((m, x0, top, x1, bot))
        if report:
            name = getattr(o, "text", None) or type(o).__name__
            print(f"{o.t_in:6.2f}  y={y:5.0f} {side} x{k:.2f}  covers {frac * 100:5.1f}%  {name[:44]}")
    return overlays


def render_frame(i, overlays):
    t = i / FPS
    a = background(t, i)
    a = grain(a * VIGNETTE, 5, i)
    base = img(a).convert("RGBA")
    for o in overlays:
        o.draw(base, t)
    lg = P["logo"]
    s = 230 / lg.width
    lg = lg.resize((230, int(lg.height * s)), Image.LANCZOS)
    lg.putalpha(lg.getchannel("A").point(lambda q: int(q * 0.85)))
    base.alpha_composite(lg, ((W - lg.width) // 2, 120))
    return base.convert("RGB")


# ----------------------------------------------------------------------------- sound

def soundtrack(path):
    SR = sfx.SR
    n = int(END * SR)
    mus = np.zeros(n)

    def put(buf, x, t0, g=1.0):
        i = int(t0 * SR)
        x = x[: max(0, n - i)]
        buf[i:i + len(x)] += x * g

    # music beds following the story
    mus += st.section(drone(4.5) * 0.5, 0.0, END, 0.05, 0.3)
    mus += st.section(st.pad(st.A_MINOR, 21.0, cutoff=700) * 0.5, 7.3, END, 1.0, 1.0)
    mus += st.section(st.ticker(13.0, 100) * 0.5, 7.5, END, 0.5, 0.8)
    mus += st.section(st.pad(st.D_MINOR, 6.0, cutoff=900) * 0.5, 28.2, END, 0.5, 0.4)
    beat = st.pulse(26.5, 112, lambda x: min(1.0, 0.45 + x / 20))
    mus += st.section(beat * 0.6 + st.arps(st.A_MINOR, 26.5, step=0.25, gain=0.16), 34.0, END, 0.1, 0.6)
    mus += st.section(st.pad(st.WARM, 30.0, cutoff=1100) * 0.45, 62.3, END, 1.2, 2.5)
    mus += st.section(st.arps(st.WARM, 22.0, step=0.5, gain=0.1), 66.0, END, 2.0, 2.0)
    mus = st.norm(mus, 0.32)

    fx = np.zeros(n)
    for t0, g, w in [(0.05, 0.85, 1.2), (T["reason"], 0.5, 0.8), (T["history"], 0.7, 1.0),
                     (T["revolution"] + 1.7, 0.75, 1.1), (T["t20"], 0.75, 1.2), (T["mistake"], 0.7, 1.2),
                     (88.9, 0.85, 1.3)]:
        put(fx, braam(weight=w), t0, g)
    rev = sfx.whoosh(1.2)[::-1]
    put(fx, rev * 0.5, T["began"] - 0.2)
    for k in range(10):  # typewriter on the date
        put(fx, sfx.tick(), T["date"] + k * 0.05, 0.6)
    rain_n = st.lp(rng.standard_normal(int(2.6 * SR)), 3000) * 0.18
    put(fx, rain_n * np.minimum(1, np.linspace(0, 6, len(rain_n))), T["rain"] - 0.3)
    for t0 in [T["rain"] + 0.1, T["oneday"] + 1.6, 34.03, 35.3, 36.3, 37.3, T["desert"], T["dhoni"], T["faster"],
               54.6, 55.6, T["suddenly"], T["importance"]]:
        put(fx, sfx.impact() * 0.45, t0)
    for t0 in [7.25, 21.15, 33.9, 38.45, 44.35, 46.8, 48.65, 51.0, 54.55, 57.0, 62.4, 70.55, 77.25, 84.05]:
        put(fx, sfx.whoosh() * 0.3, t0 - 0.15)
    put(fx, sfx.riser(1.8) * 0.4, T["revolution"])
    put(fx, sfx.riser(1.6) * 0.3, T["wc"])
    put(fx, sfx.crowd(3.5) * 0.25, 51.1)
    for k in range(int((60.6 - T["suddenly"]) / 0.5)):
        put(fx, sfx.tick() * 0.5, T["suddenly"] + 0.3 + k * 0.5)
    put(fx, sfx.heartbeat() * 0.6, T["forgetting"])
    put(fx, sfx.heartbeat() * 0.5, T["forgetting"] + 0.9)
    for t0 in [T["kapil"]]:
        put(fx, sfx.riser(0.8) * 0.3, t0)
    fx = np.tanh(fx * 0.9)

    # voice
    tmp = os.path.join(OUT, "vo_44k.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VO, "-ar", str(SR), "-ac", "1", tmp], check=True)
    with wave.open(tmp) as w:
        vo = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    voice = np.zeros(n)
    voice[: min(n, len(vo))] = vo[:n]
    # duck music under the voice
    env = np.abs(voice)
    k = int(0.25 * SR)
    env = np.convolve(env, np.ones(k) / k, mode="same")
    duck = 1 - 0.55 * np.clip(env / (env.max() * 0.25 + 1e-6), 0, 1)
    mix = voice * 1.0 + mus * duck + fx * 0.55
    mix = np.tanh(mix * 1.05) * 0.95
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
        w.writeframes(np.repeat(pcm[:, None], 2, axis=1).tobytes())


# ----------------------------------------------------------------------------- main

def qa_sheet(overlays):
    """For each overlay, its frame with the protected areas tinted red, so placements can be checked by eye."""
    th = []
    for o in overlays:
        t = min(o.t_out - 0.05, o.t_in + 0.6)
        fr = arr(render_frame(int(t * FPS), overlays))
        m = protected(t)[..., None]
        fr = fr * (1 - 0.45 * m) + np.array([255, 0, 0], np.float32) * 0.45 * m
        th.append(img(fr).resize((180, 320)))
    cols = 10
    sheet = Image.new("RGB", (180 * cols, 320 * ((len(th) + cols - 1) // cols)), "white")
    for k, im in enumerate(th):
        sheet.paste(im, ((k % cols) * 180, (k // cols) * 320))
    sheet.save(os.path.join(OUT, "qa_sheet.jpg"), quality=88)
    print("qa sheet written")


def main():
    os.makedirs(OUT, exist_ok=True)
    plates()
    overlays = place_overlays(build_overlays())
    if "--qa" in sys.argv:
        qa_sheet(overlays)
        return
    if "--preview" in sys.argv:
        times = [0.3, 3.2, 5.5, 9.0, 13.5, 17.0, 20.0, 23.5, 27.5, 30.0, 33.0, 35.0, 39.5, 42.0, 45.8, 47.6, 50.0,
                 52.0, 55.0, 59.0, 61.5, 64.0, 67.5, 69.5, 72.5, 75.5, 79.0, 82.5, 85.5, 87.5, 90.5]
        th = [render_frame(int(t * FPS), overlays).resize((216, 384)) for t in times]
        sheet = Image.new("RGB", (216 * 8, 384 * ((len(th) + 7) // 8)), "white")
        for k, im in enumerate(th):
            sheet.paste(im, ((k % 8) * 216, (k // 8) * 384))
        sheet.save(os.path.join(OUT, "preview_sheet.jpg"), quality=88)
        print("preview written")
        return
    audio = os.path.join(OUT, "mix.wav")
    soundtrack(audio)
    silent = os.path.join(OUT, "video_silent.mp4")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                          "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    total = int(END * FPS)
    for i in range(total):
        p.stdin.write(render_frame(i, overlays).tobytes())
        if i % 300 == 0:
            print(f"frame {i}/{total}", flush=True)
    p.stdin.close()
    p.wait()
    final = os.path.join(OUT, "ODI_Dying_Short.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", audio, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000", "-c:a", "aac",
                    "-b:a", "256k", "-shortest", "-movflags", "+faststart", final], check=True)
    print("SHORT_DONE", final)


if __name__ == "__main__":
    main()

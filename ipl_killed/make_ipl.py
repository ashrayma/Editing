#!/usr/bin/env python3
"""16:9 long-form: "IPL Ko Kisne Maara?" – a four-suspect murder mystery (~3:40).

    python3 make_ipl.py            ->  out/IPL_Ko_Kisne_Maara.mp4 (1920x1080, 30 fps, -14 LUFS)
    python3 make_ipl.py --preview  ->  out/preview_sheet.jpg

Voice: vo/vo_full.wav = the original take plus the 16 recorded inserts (merge_vo.py; timings in
vo/timings_full.json), with a 1.5 s full silence inserted before the reveal. Look: case-file graphics in the channel's yellow (#FFDE59) on near-black; photos sit in
yellow-edged panels (the reference's blue panels, re-done in our colours). Everything is drawn here; music and
SFX are synthesised, so the video is royalty-free apart from the photos.
"""
import json
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "kohli_countdown"))
sys.path.insert(0, os.path.join(ROOT, "doc_video"))
import sfx  # noqa: E402
import soundtrack as st  # noqa: E402
from virat_hook import braam, drone  # noqa: E402

W, H, FPS = 1920, 1080, 30
Y, RED, WHITE, GREY, INK = (255, 222, 89), (232, 52, 52), (255, 255, 255), (170, 172, 180), (11, 12, 16)
ANTON = os.path.join(ROOT, "doc_video", "thumb", "fonts", "Anton-Regular.woff")
BLACK_F = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
XB_F = "/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf"
MONO = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf"
OUT = os.path.join(HERE, "out")
rng = np.random.default_rng(2026)

TIM = json.load(open(os.path.join(HERE, "vo", "timings_full.json")))   # original lines + 16 inserts (merge_vo.py)
LN = TIM["lines"]
INS = TIM["inserts"]
GAP_AT, GAP = LN[35]["start"] - 0.2, 1.5          # full silence before the reveal


# Rohit on the Club Prairie Fire podcast (Gilchrist's question + Rohit's answer), played with its own sound
# right after insert 6 ("Rohit Sharma ne khud kaha tha…"); the voiceover pauses for it
CLIP_AT = INS[5]["end"] + 0.45          # voiceover time
CLIP_SRC = (0.3, 39.3)                  # in assets/screenrec_raw.mp4
CLIP_DUR = CLIP_SRC[1] - CLIP_SRC[0] + 0.4


def SH(t):
    """Voiceover time -> output time (podcast clip and reveal silence pushed in)."""
    return t + (CLIP_DUR if t >= CLIP_AT else 0) + (GAP if t >= GAP_AT else 0)


def L(i, off=0.0):
    return SH(LN[i]["start"] + off)


CLIP_OUT = CLIP_AT
GAP_OUT = SH(GAP_AT - 1e-6)


def I(k, off=0.0):
    """Start of insert k (1-based) on the output timeline."""
    return SH(INS[k - 1]["start"] + off)


def IE(k):
    return SH(INS[k - 1]["end"])


# each insert owns the frames from the cut before it to the next original line
WINDOWS = []
for k in range(1, 17):
    a, b = INS[k - 1]["start"] - 0.45, INS[k - 1]["end"] + 0.45
    WINDOWS.append((k, SH(a), SH(b - 1e-3) + 1e-3))
WINDOWS.append(("clip", CLIP_OUT, CLIP_OUT + CLIP_DUR))

END = TIM["duration"] + GAP + CLIP_DUR + 3.0

# ----------------------------------------------------------------------------- helpers


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def arr(im):
    return np.asarray(im, np.float32)


def img(a, mode="RGB"):
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), mode)


_fc = {}


def font(p, s):
    if (p, s) not in _fc:
        _fc[(p, s)] = ImageFont.truetype(p if os.path.exists(p) else XB_F, s)
    return _fc[(p, s)]


_ti = {}


def text_img(lines, size, path=ANTON, maxw=1700, align="c", gap=0.1):
    key = (tuple(lines), size, path, maxw, align)
    if key in _ti:
        return _ti[key]
    rows = []
    for txt, col in lines:
        s = size
        while font(path, s).getlength(txt) > maxw and s > 20:
            s -= 2
        f = font(path, s)
        l, t, r, b = f.getbbox(txt)
        rows.append((txt, col, f, l, t, r - l, b - t))
    pad = 30
    wid = max(r[5] for r in rows)
    hgt = sum(r[6] for r in rows) + int(size * gap) * (len(rows) - 1)
    im = Image.new("RGBA", (wid + 2 * pad, hgt + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    y = pad
    for txt, col, f, l, t, w, h in rows:
        x = pad + {"l": 0, "c": (wid - w) // 2, "r": wid - w}[align] - l
        ImageDraw.Draw(sh).text((x + 4, y - t + 6), txt, font=f, fill=(0, 0, 0, 230))
        ImageDraw.Draw(im).text((x, y - t), txt, font=f, fill=col)
        y += h + int(size * gap)
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(9)))
    out.alpha_composite(im)
    _ti[key] = out
    return out


def fade(im, a):
    if a >= 1:
        return im
    im = im.copy()
    im.putalpha(im.getchannel("A").point(lambda v: int(v * max(0, a))))
    return im


def paste_center(base, im, cx, cy, s=1.0, a=1.0):
    if s != 1.0:
        im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BILINEAR)
    base.alpha_composite(fade(im, a), (int(cx - im.width / 2), int(cy - im.height / 2)))


# ----------------------------------------------------------------------------- photos

PHOTO_PATHS = {
    "ipl": os.path.join(ROOT, "odi_short", "assets", "ipl_rcb_title_wide_x4.jpg"),
    "iplk": os.path.join(ROOT, "odi_short", "assets", "ipl_rcb_title_kohli_x4.jpg"),
    "trophy": os.path.join(ROOT, "odi_short", "assets", "t20wc_trophy_floodlights.jpg"),
    "empty": os.path.join(ROOT, "odi_short", "assets", "empty_stands.jpg"),
    "kohli": os.path.join(ROOT, "kohli_countdown", "assets", "photo_9.jpg"),
    "kohli2": os.path.join(ROOT, "kohli_countdown", "assets", "photo_4.jpg"),
    "six": os.path.join(ROOT, "odi_short", "assets", "dhoni_2011_six.jpg"),
    "pitch": os.path.join(HERE, "assets", "pitch_flat.jpg"),
    "pant": os.path.join(HERE, "assets", "pant_pitch.jpg"),
    "rcbkneel": os.path.join(ROOT, "kohli_countdown", "assets", "photo_1.jpg"),
    "slump": os.path.join(ROOT, "kohli_countdown", "assets", "photo_3.jpg"),
    "batup": os.path.join(ROOT, "kohli_countdown", "assets", "photo_8.jpg"),
    "team": os.path.join(ROOT, "kohli_countdown", "assets", "photo_5.jpg"),
    "hit": os.path.join(ROOT, "kohli_countdown", "assets", "photo_2.jpg"),
    "crowd": os.path.join(ROOT, "virat_82", "bg_mcg.jpg"),
    **{n: os.path.join(HERE, "assets", n + ".jpg") for n in (
        "rcb_huddle", "mi_celebrate", "mccullum_2008", "mccullum_2008b", "gt_celebrate", "ceat_timeout",
        "kohli_rcb_walk", "srh_fist", "srh_arms", "rohit_mi", "super_sixes", "impact_signal",
        "six_crowd", "mi_bowler", "chahar_chepauk", "kuldeep_down", "narine", "hardik_six", "rashid_celebrate",
        "rashid_six", "rabada_fist", "dhoni_bowled", "mi_pointing", "toss")},
}
CLIPS = {"pollard": os.path.join(HERE, "assets", "pollard_clean.mp4"),
         "crowd": os.path.join(HERE, "assets", "crowd_clean.mp4")}
INTL = {"trophy", "empty", "kohli", "kohli2", "six", "slump", "batup", "hit", "team", "crowd"}   # never shown
_clip = {}


class SeqReader:
    """Frames of a longer clip read sequentially through ffmpeg (re-opened if the time jumps)."""

    def __init__(self, path, start):
        self.path, self.start, self.p, self.t = path, start, None, None
        self.last = None

    def frame(self, t):
        if self.p is None or self.t is None or not (0 <= t - self.t < 0.2):
            if self.p:
                self.p.kill()
            self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(self.start + t), "-i", self.path,
                                       "-vf", f"fps={FPS},scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                      stdout=subprocess.PIPE)
            self.t = t - 1 / FPS
        while self.t < t - 1e-6:
            buf = self.p.stdout.read(W * H * 3)
            if len(buf) == W * H * 3:
                self.last = Image.frombuffer("RGB", (W, H), buf, "raw", "RGB", 0, 1)
            self.t += 1 / FPS
        return self.last


SEQ = {"screenrec": SeqReader(os.path.join(HERE, "assets", "screenrec_raw.mp4"), CLIP_SRC[0])}


def clip_frame(name, t):
    """Frame of a short clip (looped), cached in memory at 960x540."""
    if name not in _clip:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", CLIPS[name], "-vf", "fps=30,scale=960:540",
                              "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
        _clip[name] = np.frombuffer(raw, np.uint8).reshape(-1, 540, 960, 3)
    fr = _clip[name]
    return Image.fromarray(fr[int(t * 30) % len(fr)])
_ph = {}


def photo(name):
    if name not in _ph:
        p = PHOTO_PATHS[name]
        up = os.path.join(HERE, "assets", "x4", os.path.basename(p))
        _ph[name] = Image.open(up if os.path.exists(up) else p).convert("RGB")
    return _ph[name]


def cover(im, w, h, z=1.0, fx=0.5, fy=0.45):
    s = max(w / im.width, h / im.height) * z
    fw, fh = int(im.width * s) + 1, int(im.height * s) + 1
    r = im.resize((fw, fh), Image.BILINEAR)
    x = int(np.clip(fx * fw - w / 2, 0, fw - w))
    y = int(np.clip(fy * fh - h / 2, 0, fh - h))
    return r.crop((x, y, x + w, y + h))


YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = (1 - 0.6 * np.clip(((XX - W / 2) / (W * 0.6)) ** 2 + ((YY - H / 2) / (H * 0.62)) ** 2, 0, 1))[..., None]
GRAIN = [rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32) for _ in range(5)]
_bg = {}


def backdrop(name, t, t0, t1, dark=0.32, gray=0.0):
    """Full-frame photo, darkened and pushing in; None -> plain dark plate with a faint grid."""
    if name is None:
        if "plate" not in _bg:
            a = np.zeros((H, W, 3), np.float32) + np.array(INK, np.float32)
            a += np.exp(-(((XX - W * 0.5) / (W * 0.55)) ** 2 + ((YY - H * 0.3) / (H * 0.8)) ** 2))[..., None] * \
                np.array([34, 30, 14], np.float32)
            g = ((XX % 80 < 1.5) | (YY % 80 < 1.5)).astype(np.float32)[..., None] * 9
            _bg["plate"] = a + g
        return _bg["plate"].copy()
    p = (t - t0) / max(0.5, t1 - t0)
    if name.startswith("seq:"):
        fr = SEQ[name[4:]].frame(max(0.0, min(t - t0, CLIP_SRC[1] - CLIP_SRC[0] - 0.05)))
        return arr(fr) * dark if fr is not None else np.zeros((H, W, 3), np.float32)
    if name.startswith("clip:"):
        im = clip_frame(name[5:], t - t0).resize((W, H), Image.BILINEAR)
        a = arr(im)
        return (a * (1 - gray) + a.mean(-1, keepdims=True) * gray) * dark
    im = cover(photo(name), W, H, 1.04 + 0.06 * p)
    a = arr(im)
    if gray:
        lum = a.mean(-1, keepdims=True)
        a = a * (1 - gray) + lum * gray
    return a * dark


def panel(base, name, box, t, t0, t1, z0=1.0, fx=0.5, fy=0.42, tilt=0):
    """Photo in a yellow-edged panel that slides in (the reference's blue panels, in our colours)."""
    x, y, w, h = box
    k = t - t0
    a = ease(k / 0.25) * (1 - ease((t - (t1 - 0.15)) / 0.15))
    if a <= 0:
        return
    p = (t - t0) / max(0.5, t1 - t0)
    im = cover(photo(name), w, h, z0 + 0.05 * p, fx, fy).convert("RGBA")
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w - 1, h - 1), outline=Y + (255,), width=6)
    sh = Image.new("RGBA", (w + 80, h + 80), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle((40, 50, 40 + w, 50 + h), fill=(0, 0, 0, 200))
    sh = sh.filter(ImageFilter.GaussianBlur(20))
    if tilt:
        im = im.rotate(tilt, expand=True, resample=Image.BICUBIC)
    dx = int(160 * (1 - ease(k / 0.3)))
    base.alpha_composite(fade(sh, a), (x - 40 + dx, y - 40))
    base.alpha_composite(fade(im, a), (x + dx, y))


# ----------------------------------------------------------------------------- elements


class E:
    """A timed on-screen element: draw(base, t) between t0 and t1."""

    def __init__(self, t0, t1, fn, sfx_kind=None):
        self.t0, self.t1, self.fn, self.sfx = t0, t1, fn, sfx_kind
        self.win = None          # insert number this element belongs to (None: the original script)


def txt(t0, t1, lines, cx, cy, size=120, path=ANTON, anim="rise", maxw=1700, align="c", sfx_kind=None):
    im = None

    def draw(base, t):
        nonlocal im
        if im is None:
            im = text_img(tuple(lines), size, path, maxw, align)
        k = t - t0
        a = (1 - ease((t - (t1 - 0.15)) / 0.15))
        if anim == "slam":
            s = 1 + 0.4 * (1 - ease(k / 0.14))
            a *= ease(k / 0.06)
            j = (rng.uniform(-8, 8, 2) * (1 - k / 0.25)) if k < 0.25 else (0, 0)
            paste_center(base, im, cx + j[0], cy + j[1], s, a)
        elif anim == "type":
            n = sum(len(t_) for t_, _ in lines)
            frac = min(1, k / (0.045 * n))
            crop = im.crop((0, 0, max(1, int(im.width * frac)), im.height))
            x0 = cx - im.width / 2
            base.alpha_composite(fade(crop, a), (int(x0), int(cy - im.height / 2)))
        else:
            a *= ease(k / 0.25)
            paste_center(base, im, cx, cy + 30 * (1 - ease(k / 0.3)), 1.0, a)
    e = E(t0, t1, draw, sfx_kind or ("hit" if anim == "slam" else None))
    e.kind, e.lines = "txt", lines
    return e


def stamp(t0, t1, word, cx, cy, color=RED, angle=-9, size=110):
    f = font(BLACK_F, size)
    l, t, r, b = f.getbbox(word)
    im = Image.new("RGBA", (r - l + 70, b - t + 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((5, 5, im.width - 6, im.height - 6), outline=color + (255,), width=10)
    d.text((35 - l, 30 - t), word, font=f, fill=color + (255,))
    m = arr(im.getchannel("A"))
    m[np.random.default_rng(len(word)).random(m.shape) > 0.88] *= 0.3
    im.putalpha(img(m, "L"))
    im = im.rotate(angle, expand=True, resample=Image.BICUBIC)

    def draw(base, t):
        k = t - t0
        s = 1 + 1.0 * (1 - ease(k / 0.12))
        a = ease(k / 0.05) * (1 - ease((t - (t1 - 0.15)) / 0.15))
        paste_center(base, im, cx, cy, s, a)
    return E(t0, t1, draw, "stamp")


def chip(t0, t1, label, x, y, bg=Y, fg=INK, size=40):
    f = font(XB_F, size)
    l, t, r, b = f.getbbox(label)
    im = Image.new("RGBA", (r - l + 44, b - t + 26), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=10, fill=bg + (255,))
    d.text((22 - l, 13 - t), label, font=f, fill=fg)

    def draw(base, t):
        k = t - t0
        a = ease(k / 0.2) * (1 - ease((t - (t1 - 0.15)) / 0.15))
        base.alpha_composite(fade(im, a), (int(x + 60 * (1 - ease(k / 0.25))), int(y)))
    return E(t0, t1, draw, "pop")


def photo_panel(t0, t1, name, box, **kw):
    e = E(t0, t1, lambda base, t: panel(base, name, box, t, t0, t1, **kw), "whoosh")
    e.photo = name
    return e


def mugshot(t0, t1, num, title, name, cx, cy, w=380, h=470, accent=Y, show_q=False):
    """Suspect card: height-chart background, photo or silhouette, number plate."""
    def draw(base, t):
        name = e.photo
        k = t - t0
        a = ease(k / 0.2) * (1 - ease((t - (t1 - 0.15)) / 0.15))
        if a <= 0:
            return
        card = Image.new("RGBA", (w, h), (24, 26, 32, 255))
        d = ImageDraw.Draw(card)
        for i, yy in enumerate(range(40, h - 110, 34)):
            d.line((0, yy, w, yy), fill=(70, 72, 80, 255), width=2 if i % 2 else 1)
        if name:
            ph = cover(photo(name), w - 30, h - 130, 1.0, 0.5, 0.35).convert("L").convert("RGB")
            ph = img(arr(ph) * 0.9)
            card.paste(ph, (15, 15))
        else:
            d.ellipse((w / 2 - 70, 70, w / 2 + 70, 210), fill=(48, 50, 58, 255))
            d.rounded_rectangle((w / 2 - 130, 220, w / 2 + 130, h - 130), radius=70, fill=(48, 50, 58, 255))
            if show_q:
                d.text((w / 2, 190), "?", font=font(ANTON, 150), fill=accent, anchor="mm")
        d.rectangle((0, h - 115, w, h), fill=INK + (255,))
        d.text((24, h - 105), f"SUSPECT /{num}", font=font(MONO, 30), fill=accent)
        f = font(ANTON, 52)
        s = 52
        while f.getlength(title) > w - 40 and s > 26:
            s -= 2
            f = font(ANTON, s)
        d.text((24, h - 68), title, font=f, fill=WHITE)
        d.rectangle((0, 0, w - 1, h - 1), outline=accent + (255,), width=5)
        sc = 1 + 0.15 * (1 - ease(k / 0.18))
        paste_center(base, card, cx, cy, sc, a)
        if k < 0.12:  # camera flash
            fl = Image.new("RGBA", base.size, (255, 255, 255, int(110 * (1 - k / 0.12))))
            base.alpha_composite(fl)
    e = E(t0, t1, draw, "shutter")
    e.photo, e.kind = name, "mug"
    return e


def bars(t0, t1, data, cx, cy, maxv, label):
    """Animated bar chart; a tick per bar as it grows."""
    def draw(base, t):
        k = t - t0
        a = ease(k / 0.2) * (1 - ease((t - (t1 - 0.15)) / 0.15))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        bw, gap, hmax = 220, 160, 520
        n = len(data)
        x0 = cx - (n * bw + (n - 1) * gap) / 2
        base_y = cy + hmax / 2
        d.line((x0 - 60, base_y, x0 + n * bw + (n - 1) * gap + 60, base_y), fill=GREY + (255,), width=4)
        for i, (yr, v, col) in enumerate(data):
            g = ease((k - 0.3 - i * 0.9) / 0.8)
            hh = hmax * v / maxv * g
            x = x0 + i * (bw + gap)
            d.rectangle((x, base_y - hh, x + bw, base_y), fill=col + (255,))
            d.text((x + bw / 2, base_y + 50), yr, font=font(ANTON, 64), fill=WHITE, anchor="mm")
            if g > 0.05:
                d.text((x + bw / 2, base_y - hh - 70), str(int(round(v * g))), font=font(ANTON, 110), fill=col,
                       anchor="mm")
        d.text((cx, base_y + 140), label, font=font(XB_F, 46), fill=GREY, anchor="mm")
        base.alpha_composite(fade(lay, a))
    return E(t0, t1, draw, None)


def pitch_gfx(t0, t1, cx, cy):
    def draw(base, t):
        k = t - t0
        a = ease(k / 0.3) * (1 - ease((t - (t1 - 0.15)) / 0.15))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        pts = [(cx - 150, cy - 380), (cx + 150, cy - 380), (cx + 260, cy + 380), (cx - 260, cy + 380)]
        d.polygon(pts, fill=(196, 170, 120, 255))
        for i in range(60):
            yy = cy - 380 + i * 12.7
            d.line((cx - 150 - 110 * i / 60, yy, cx + 150 + 110 * i / 60, yy), fill=(186, 160, 112, 255))
        for yy, half in ((cy - 300, 175), (cy + 300, 240)):
            d.line((cx - half, yy, cx + half, yy), fill=WHITE + (255,), width=6)
        # the ball: straight line, no deviation
        p = ((t - t0) * 0.7) % 1.0
        by = cy - 300 + 600 * p
        d.ellipse((cx - 16, by - 16, cx + 16, by + 16), fill=(220, 40, 40, 255))
        d.line((cx, cy - 300, cx, by), fill=(255, 255, 255, 110), width=4)
        base.alpha_composite(fade(lay, a))
    return E(t0, t1, draw, "whoosh")


def phone_gfx(t0, t1, cx, cy, rows, header="MY TEAM"):
    def draw(base, t):
        k = t - t0
        a = ease(k / 0.25) * (1 - ease((t - (t1 - 0.15)) / 0.15))
        w, h = 470, 880
        ph = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(ph)
        d.rounded_rectangle((0, 0, w - 1, h - 1), radius=56, fill=(20, 22, 28, 255), outline=(90, 92, 100, 255), width=8)
        d.rounded_rectangle((26, 26, w - 27, h - 27), radius=40, fill=(32, 36, 46, 255))
        d.rounded_rectangle((w / 2 - 70, 40, w / 2 + 70, 62), radius=11, fill=(14, 14, 18, 255))
        d.text((w / 2, 120), header, font=font(ANTON, 54), fill=Y, anchor="mm")
        for i, (name, pts) in enumerate(rows):
            ry = 200 + i * 105
            ri = ease((k - 0.3 - i * 0.25) / 0.25)
            if ri <= 0:
                continue
            d.rounded_rectangle((50, ry, w - 50, ry + 84), radius=16, fill=(48, 54, 68, int(255 * ri)))
            d.text((76, ry + 42), name, font=font(XB_F, 34), fill=WHITE, anchor="lm")
            col = (90, 220, 120) if pts.startswith("+") else (RED if pts.startswith("-") else WHITE)
            d.text((w - 76, ry + 42), pts, font=font(ANTON, 44), fill=col, anchor="rm")
        paste_center(base, ph, cx, cy + 60 * (1 - ease(k / 0.3)), 1.0, a)
    return E(t0, t1, draw, "whoosh")


def tv_gfx(t0, t1, cx, cy, label, name="ipl"):
    holder = {}
    def draw(base, t):
        k = t - t0
        a = ease(k / 0.25) * (1 - ease((t - (t1 - 0.15)) / 0.15))
        w, h = 760, 560
        tv = Image.new("RGBA", (w, h + 70), (0, 0, 0, 0))
        d = ImageDraw.Draw(tv)
        d.rounded_rectangle((0, 0, w - 1, h - 1), radius=50, fill=(58, 46, 34, 255))
        nm = holder["e"].photo
        if nm is None:
            scr = Image.new("RGB", (w - 140, h - 120), (40, 40, 44))
        else:
            scr = cover(photo(nm), w - 140, h - 120, 1.0).convert("L").convert("RGB")
        a_ = arr(scr)
        a_[::3] *= 0.75
        tv.paste(img(a_ * 0.95), (40, 60))
        d.rounded_rectangle((40, 60, w - 100, h - 60), radius=40, outline=(30, 24, 18, 255), width=10)
        for yy in (120, 200):
            d.ellipse((w - 80, yy, w - 40, yy + 40), fill=(30, 24, 18, 255))
        d.line((140, h, 100, h + 60), fill=(58, 46, 34, 255), width=14)
        d.line((w - 140, h, w - 100, h + 60), fill=(58, 46, 34, 255), width=14)
        d.text((w / 2 - 30, h - 30), label, font=font(ANTON, 40), fill=Y, anchor="mm")
        paste_center(base, tv, cx, cy, 1 + 0.1 * (1 - ease(k / 0.2)), a)
    e = E(t0, t1, draw, "whoosh")
    e.photo, e.kind = name, "tv"
    holder["e"] = e
    return e


def scale_gfx(t0, t1, cx, cy):
    """BAT vs BALL balance that tips to the bat."""
    def draw(base, t):
        k = t - t0
        a = ease(k / 0.25) * (1 - ease((t - (t1 - 0.15)) / 0.15))
        ang = np.radians(-14 * ease((k - 0.6) / 0.8))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        d.polygon([(cx - 60, cy + 260), (cx + 60, cy + 260), (cx, cy - 20)], fill=GREY + (255,))
        L_, ca, sa = 360, np.cos(ang), np.sin(ang)
        p1 = (cx - L_ * ca, cy - 20 - L_ * sa)
        p2 = (cx + L_ * ca, cy - 20 + L_ * sa)
        d.line((p1, p2), fill=WHITE + (255,), width=10)
        for (px, py), word, col in ((p1, "BAT", Y), (p2, "BALL", RED)):
            d.line((px, py, px, py + 120), fill=GREY + (255,), width=4)
            d.rounded_rectangle((px - 130, py + 120, px + 130, py + 210), radius=14, fill=col + (255,))
            d.text((px, py + 165), word, font=font(ANTON, 64), fill=INK, anchor="mm")
        base.alpha_composite(fade(lay, a))
    return E(t0, t1, draw, None)


def strings_gfx(t0, t1):
    """Red strings from four suspects converging on one point (the re-hook)."""
    pts = [(300, 300), (W - 300, 300), (300, H - 300), (W - 300, H - 300)]

    def draw(base, t):
        k = t - t0
        a = (1 - ease((t - (t1 - 0.15)) / 0.15))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        for i, (x, y) in enumerate(pts):
            g = ease((k - 0.2 * i) / 0.6)
            ex, ey = x + (W / 2 - x) * g, y + (H / 2 - y) * g
            d.line((x, y, ex, ey), fill=RED + (230,), width=6)
            d.ellipse((x - 18, y - 18, x + 18, y + 18), fill=Y + (255,))
        d.ellipse((W / 2 - 26, H / 2 - 26, W / 2 + 26, H / 2 + 26), fill=RED + (255,))
        base.alpha_composite(fade(lay, a))
    return E(t0, t1, draw, None)


def merge_gfx(t0, t1):
    """The four suspect cards slide together and become SCOREBOARD."""
    titles = ["IMPACT PLAYER", "THE PITCH", "FANTASY APPS", "THE BROADCAST"]

    def draw(base, t):
        k = t - t0
        g = ease((k - 0.4) / 1.0)
        a_cards = 1 - ease((k - 1.3) / 0.3)
        for i, ttl in enumerate(titles):
            sx = 330 + i * 420
            x = sx + (W / 2 - sx) * g
            card = Image.new("RGBA", (360, 140), (0, 0, 0, 0))
            d = ImageDraw.Draw(card)
            d.rounded_rectangle((0, 0, 359, 139), radius=14, fill=(24, 26, 32, 255), outline=Y + (255,), width=4)
            d.text((180, 46), f"/0{i + 1}", font=font(MONO, 30), fill=Y, anchor="mm")
            d.text((180, 96), ttl, font=font(ANTON, 44), fill=WHITE, anchor="mm")
            if a_cards > 0:
                paste_center(base, card, x, 540, 1.0, a_cards)
        if k > 1.35:
            kk = k - 1.35
            im = text_img((("SCOREBOARD", Y),), 230, ANTON)
            paste_center(base, im, W / 2, 540, 1 + 0.35 * (1 - ease(kk / 0.15)), ease(kk / 0.06) *
                         (1 - ease((t - (t1 - 0.15)) / 0.15)))
    return E(t0, t1, draw, None)


def case_header(t0, t1, txt_="CASE FILE: #IPL2026"):
    def draw(base, t):
        k = t - t0
        a = ease(k / 0.2) * (1 - ease((t - (t1 - 0.15)) / 0.15))
        n = len(txt_)
        shown = txt_[: int(min(1, k / (0.05 * n)) * n)]
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        d.rectangle((120, 90, 900, 170), fill=(236, 232, 220, 255))
        d.text((150, 130), shown, font=font(MONO, 46), fill=INK, anchor="lm")
        base.alpha_composite(fade(lay, a))
    return E(t0, t1, draw, "type")


# ----------------------------------------------------------------------------- the edit

# ----------------------------------------------------------------------------- the 16 inserts

def beat_times(k, n):
    """Split insert k into n beats at sentence ends (proportional to text length)."""
    import re as _re
    text = INS[k - 1]["text"]
    a, b = I(k), IE(k)
    sents = [x for x in _re.split(r"(?<=[.?!])\s+", text) if x]
    cum = np.cumsum([len(x) for x in sents]) / len(text)
    cuts = [a]
    for j in range(1, n):
        f = cum[np.argmin(np.abs(cum[:-1] - j / n))] if len(cum) > 1 else j / n
        cuts.append(max(cuts[-1] + 0.8, a + (b - a) * f))
    cuts.append(b + 0.45)
    return list(zip(cuts[:-1], cuts[1:]))


# per insert: beats = (backdrop, dark, gray, [element makers(t0, t1)])
def T_(lines, size=130, anim="slam", path=ANTON, cy=540, cx=W / 2, maxw=1700):
    return lambda t0, t1: txt(t0, t1, lines, cx, cy, size, path=path, anim=anim, maxw=maxw)


def C_(labels, x=140, y0=300, size=60, bg=Y, fg=INK, step=0.5):
    def make(t0, t1):
        return [chip(t0 + step * i, t1, lab, x, y0 + i * 140, bg=bg, fg=fg, size=size) for i, lab in enumerate(labels)]
    return make


def P_(name, box=(1080, 160, 720, 760), **kw):
    return lambda t0, t1: photo_panel(t0, t1, name, box, **kw)


def ST_(word, cy=600, color=RED, size=110):
    return lambda t0, t1: stamp(t0 + 0.3, t1, word, W / 2, cy, color=color, size=size)


PHONE_ROWS = [("BATTER (C)", "+86"), ("BOWLER", "+48"), ("WK", "+22"), ("ALL-ROUNDER", "+31"), ("KOHLI", "OUT")]

INSERT_BEATS = {
    1: [("six", 0.35, 0.7, [T_([("THE LAST OVER:", WHITE), ("DINNER COULD WAIT", Y)])]),
        (None, 1, 0, [lambda a, b: tv_gfx(a, b, W / 2, 560, "EVERY BALL", "crowd"),
                      T_([("ONE TV. EVERY BALL.", Y)], 90, "rise", cy=110)]),
        ("empty", 0.4, 0.6, [T_([("TODAY?", WHITE)], 200)]),
        ("empty", 0.3, 0.8, [lambda a, b: phone_gfx(a, b, 1400, 560, PHONE_ROWS, "SECOND SCREEN"),
                             T_([("MATCH ON.", WHITE), ("MIND ELSEWHERE.", Y)], 120, "rise", cx=640, maxw=1000)])],
    2: [(None, 1, 0, [T_([("NOT JUST A FEELING", WHITE)], 130, "rise")]),
        ("clip:pollard", 0.45, 0, [T_([("200 EVERY OTHER GAME", WHITE), ("= NOT SPECIAL", Y)], 120)]),
        ("crowd", 0.3, 0.6, [T_([("WHAT HAPPENS DAILY", WHITE), ("ISN'T REMEMBERED", RED)], 120, "rise")])],
    3: [(None, 1, 0, [lambda a, b: case_header(a, b, "OPENING THE CASE…"),
                      T_([("4 SUSPECTS. 1 TRUTH.", Y)], 130, "rise")]),
        (None, 1, 0, [lambda a, b: [mugshot(a + 0.2 * i, b, f"0{i + 1}", "???", None, 300 + i * 440, 560, show_q=True)
                                    for i in range(4)]]),
        ("rcb_huddle", 0.3, 0.3, [lambda a, b: chip(a, b, "STAY TILL THE END", 640, 500, bg=RED, fg=WHITE, size=72)])],
    4: [(None, 1, 0, [T_([("2023", Y)], 260), T_([("IMPACT PLAYER RULE", WHITE)], 80, "rise", cy=760)]),
        ("iplk", 0.3, 0, [T_([("MORE CHANCES.", WHITE), ("MORE STRATEGY.", Y)], 130, "rise")]),
        ("impact_signal", 0.35, 0, [T_([("SWAP 1 PLAYER", WHITE), ("AFTER THE TOSS", Y)], 130, cx=1300, maxw=1000)]),
        (None, 1, 0, [ST_("SMART ON PAPER", 540, Y, 120)])],
    5: [("slump", 0.4, 0.5, [T_([("THEN: 6 DOWN", WHITE), ("= GAME OVER", RED)], 140)]),
        (None, 1, 0, [T_([("NO. 7, 8:", WHITE), ("BOWLERS SWINGING", GREY)], 130, "rise")]),
        ("batup", 0.4, 0, [T_([("NOW: NO. 8", WHITE), ("IS A REAL BATTER", Y)], 130, cx=700, maxw=1100)]),
        ("srh_fist", 0.35, 0, [T_([("TOP ORDER:", WHITE), ("NO BRAKES", Y)], 150, cx=1250, maxw=1100)]),
        ("clip:pollard", 0.45, 0, [T_([("ATTACK FROM BALL 1", Y)], 140)]),
        ("slump", 0.35, 0.7, [T_([("BOWLER:", WHITE), ("NO RELIEF", RED)], 160)])],
    6: [(None, 1, 0, [T_([("NOT JUST MY OPINION", WHITE)], 130, "rise")]),
        (None, 1, 0, [P_("rohit_mi", (1160, 100, 600, 880), fy=0.3),
                      T_([("ROHIT SHARMA:", WHITE), ("“NOT A FAN”", Y)], 140, cx=600, maxw=950),
                      T_([("ON THE IMPACT PLAYER RULE", GREY)], 50, "rise", path=XB_F, cy=760, cx=600, maxw=950)]),
        ("batup", 0.35, 0, [T_([("ALL-ROUNDERS", WHITE), ("NOT BOWLING", RED)], 140, cx=720, maxw=1100)])],
    7: [(None, 1, 0, [lambda a, b: mugshot(a, b, "01", "IMPACT PLAYER", "iplk", 560, 540, w=460, h=600),
                      lambda a, b: stamp(a + 0.6, b, "GUILTY", 1300, 540, size=150)]),
        (None, 1, 0, [C_(["RUNS ↑", "RISK ↑", "BALANCE ↓"], x=760, y0=330, size=80, step=0.6)]),
        ("srh_arms", 0.25, 0.4, [T_([("BUT IF IT WAS", WHITE), ("THE ONLY CULPRIT…", Y)], 130, "rise")])],
    8: [("slump", 0.35, 0.5, [T_([("T20: HARD ENOUGH", WHITE), ("FOR BOWLERS", Y)], 130)]),
        (None, 1, 0, [C_(["4 OVERS", "FIELD RESTRICTIONS", "SHORT BOUNDARIES"], x=560, y0=330, size=70)]),
        ("pitch", 0.45, 0, [T_([("HIS LAST HOPE:", WHITE), ("THE PITCH", Y)], 150)]),
        ("pant", 0.4, 0, [C_(["SWING", "TURN", "UNEVEN BOUNCE"], x=1100, y0=330, size=70)]),
        ("pitch", 0.35, 0, [T_([("HIS ONLY WEAPON", Y)], 160)])],
    9: [("pitch", 0.3, 0.6, [T_([("BOWLER =", WHITE), ("BOWLING MACHINE", Y)], 140)]),
        (None, 1, 0, [T_([("SAME HEIGHT.", WHITE), ("SAME SPEED.", Y)], 160, "rise")]),
        ("clip:pollard", 0.45, 0, [T_([("JUST STAND & HIT", Y)], 150)]),
        (None, 1, 0, [T_([("SKILL ↓   GUESSWORK ↑", Y)], 110, path=BLACK_F)])],
    10: [("mi_celebrate", 0.4, 0, [T_([("WHEN 140", WHITE), ("WAS ENOUGH", Y)], 160)]),
         ("crowd", 0.35, 0.3, [T_([("LOW-SCORING", WHITE), ("THRILLERS", Y)], 160, "rise")]),
         ("pant", 0.3, 0.5, [T_([("EVERY RUN EARNED.", WHITE), ("EVERY WICKET MATTERED.", Y)], 110)])],
    11: [(None, 1, 0, [lambda a, b: phone_gfx(a, b, 560, 560, PHONE_ROWS, "FANTASY"),
                       T_([("A NEW", WHITE), ("AUDIENCE", Y)], 150, "rise", cx=1300, maxw=900)]),
         ("crowd", 0.3, 0.5, [T_([("NON-FANS", WHITE), ("NOW PICK TEAMS", Y)], 140)]),
         (None, 1, 0, [T_([("BUT IT CHANGED", WHITE), ("HOW WE WATCH", RED)], 140, "rise")])],
    12: [("gt_celebrate", 0.35, 0, [T_([("THEN:", WHITE), ("WILL MY TEAM WIN?", Y)], 130)]),
         (None, 1, 0, [lambda a, b: phone_gfx(a, b, 560, 560, PHONE_ROWS, "MY POINTS"),
                       T_([("NOW: HOW MANY", WHITE), ("POINTS?", Y)], 130, "rise", cx=1300, maxw=900)]),
         ("slump", 0.35, 0.4, [T_([("MAIDEN OVER", WHITE), ("= A FEW POINTS", GREY)], 140)]),
         ("ipl", 0.3, 0.5, [T_([("MATCH-WINNING 20", WHITE), ("= ZERO FANTASY VALUE", RED)], 120)])],
    13: [("rcb_huddle", 0.35, 0, [T_([("ONE OF THE BIGGEST", WHITE), ("LEAGUES IN THE WORLD", Y)], 120)]),
         (None, 1, 0, [T_([("MEDIA RIGHTS:", WHITE), ("THOUSANDS OF CRORES", Y)], 130)]),
         ("ipl", 0.3, 0.5, [T_([("EVERY SECOND", WHITE), ("IS FOR SALE", RED)], 160, "rise")])],
    14: [("ceat_timeout", 0.3, 0, [C_(["STRATEGIC TIMEOUT", "INNINGS BREAK", "AD AFTER EVERY WICKET"], x=420, y0=320,
                                      size=72, bg=RED, fg=WHITE)]),
         ("iplk", 0.3, 0.5, [T_([("THE BROADCAST", WHITE), ("SETS THE PACE", Y)], 140)]),
         ("clip:pollard", 0.45, 0, [T_([("WHAT SELLS?", WHITE)], 130, "rise", cy=360),
                                    T_([("THE SIX.", Y)], 200, cy=620)]),
         (None, 1, 0, [P_("super_sixes", (1040, 300, 760, 481)),
                       C_(["HIGHLIGHTS: SIX", "REELS: SIX", "ADS: SIX"], x=140, y0=330, size=80)]),
         ("pitch", 0.3, 0.5, [T_([("A PERFECT YORKER", WHITE), ("HAS NO SPONSOR", RED)], 140)])],
    15: [(None, 1, 0, [C_(["BOARD → VIEWERS", "BROADCASTER → AD SLOTS", "FANTASY APPS → POINTS"], x=360, y0=280,
                          size=80, step=1.6)]),
         ("ipl", 0.25, 0.5, [T_([("EASIEST WAY TO GIVE", WHITE), ("EVERYONE THAT?", WHITE)], 110, "rise", cy=380),
                             T_([("RUNS.", Y)], 230, cy=700)])],
    16: [(None, 1, 0, [P_("mccullum_2008b", (1080, 100, 720, 880), fy=0.3),
                       T_([("THE OLD IPL NIGHTS", Y)], 130, "rise", cx=560, maxw=900)]),
         ("crowd", 0.35, 0, [T_([("LAST OVER.", WHITE), ("12 NEEDED.", Y)], 170)]),
         ("slump", 0.3, 0.7, [T_([("YORKER. YORKER. YORKER.", Y)], 130)]),
         ("clip:crowd", 0.9, 0, [T_([("THE STADIUM ROSE", WHITE)], 150, "rise")]),
         (None, 1, 0, [T_([("DRAMA CAME FROM", WHITE), ("THE CONTEST, NOT RUNS", Y)], 120)])],
}


MISSING = []
# photos you sent for specific empty spots: output time (m:ss) -> photo
FILL = {"1:31": "toss", "1:43": "mi_pointing", "1:57": "rashid_celebrate", "2:03": "hardik_six", "2:05": "kuldeep_down",
        "3:42": "chahar_chepauk", "3:57": "rabada_fist", "4:14": "rashid_six", "4:27": "narine", "5:27": "mi_bowler",
        "6:26": "six_crowd", "6:35": "dhoni_bowled"}


def enforce_unique(S, El):
    """No international photos, no photo or clip shown twice: later repeats become graphic-only and are listed."""
    items = [(s_[0], "scene", j) for j, s_ in enumerate(S) if s_[2]] + \
            [(e.t0, "el", j) for j, e in enumerate(El) if getattr(e, "photo", None)]
    used = set()
    for t0, kind, j in sorted(items):
        key = S[j][2] if kind == "scene" else El[j].photo
        if key.startswith("seq:"):
            continue
        if key in INTL or key in used:
            fill = FILL.get(f"{int(t0 // 60)}:{int(t0 % 60):02d}") if kind == "scene" else None
            if fill and fill not in used:
                a, b, _, dark, gray = S[j]
                S[j] = (a, b, fill, dark, gray)
                used.add(fill)
                continue
            MISSING.append((t0, key))
            if kind == "scene":
                a, b, _, dark, gray = S[j]
                S[j] = (a, b, None, dark, gray)
            elif getattr(El[j], "kind", "") in ("mug", "tv"):
                El[j].photo = None
            else:
                El[j].t1 = El[j].t0          # drop the panel
        else:
            used.add(key)


def add_inserts(S, El):
    for k, beats in INSERT_BEATS.items():
        _, wa, wb = WINDOWS[k - 1]
        spans = beat_times(k, len(beats))
        spans[0] = (wa, spans[0][1])
        spans[-1] = (spans[-1][0], wb)
        for (t0, t1), (bg, dark, gray, makers) in zip(spans, beats):
            S.insert(0, (t0, t1, bg, dark, gray))
            for mk in makers:
                out = mk(t0, t1)
                for e in (out if isinstance(out, list) else [out]):
                    e.win = k
                    El.append(e)



def build():
    S = []   # (t0, t1, backdrop, dark, gray)
    El = []
    add = El.append

    def scene(t0, t1, bg=None, dark=0.3, gray=0.0):
        S.append((t0, t1, bg, dark, gray))

    # COLD OPEN
    scene(0, L(0, 2.0), "ipl", 0.55)
    add(txt(0.1, L(0, 2.0), [("2022", WHITE)], W / 2, 380, 150, anim="slam"))
    add(txt(0.6, L(0, 2.0), [("200+ TOTALS: 18", Y)], W / 2, 600, 120, anim="rise"))
    scene(L(0, 2.0), L(1), None)
    add(bars(L(0, 2.0), L(1), [("2022", 18, GREY), ("2026", 61, Y)], W / 2, 600, 61, "200+ TOTALS IN THE IPL"))
    add(txt(L(0, 3.4), L(1), [("18 → 61", RED)], W / 2, 150, 120, path=BLACK_F, anim="slam"))
    scene(L(1), L(1, 3.3), "srh_fist", 0.4)
    add(chip(L(1, 0.2), L(1, 3.3), "SIXES ↑", 140, 300, size=64))
    add(chip(L(1, 1.4), L(1, 3.3), "RUNS ↑", 140, 430, size=64))
    scene(L(1, 3.3), L(2), "empty", 0.45, 0.5)
    add(txt(L(1, 3.3), L(2), [("…BUT THE FANS", WHITE), ("ARE ON THEIR PHONES", Y)], W / 2, 540, 110))
    scene(L(2), L(3), None)
    add(txt(L(2), L(2, 1.9), [("SOMETHING IS DYING.", WHITE)], W / 2, 540, 120, anim="rise"))
    add(txt(L(2, 1.9), L(3), [("IPL KO", WHITE), ("KISNE MAARA?", RED)], W / 2, 540, 190, anim="slam"))
    scene(L(3), L(5), None)
    for i, (ttl) in enumerate(["???", "???", "???", "???"]):
        add(mugshot(L(3, 0.25 * i), L(5), f"0{i + 1}", ttl, None, 300 + i * 440, 560, show_q=True))
    add(txt(L(4), L(5), [("THE REAL CULPRIT?", RED)], W / 2, 140, 96))

    # THE CRIME
    scene(L(5), L(8), "mi_celebrate", 0.25, 0.6)
    add(case_header(L(5), L(8)))
    add(txt(L(5, 0.4), L(6), [("THEN: 160 DEFENDED", WHITE), ("LAST-OVER THRILLERS", Y)], W / 2, 560, 120))
    add(txt(L(6), L(7), [("NOW: 220 ISN'T SAFE", WHITE), ("DECIDED BY THE 6TH OVER", Y)], W / 2, 560, 120))
    add(txt(L(7), L(8), [("THE PROBLEM ISN'T RUNS.", WHITE)], W / 2, 430, 96))
    add(stamp(L(7, 2.0), L(8), "SUSPENSE: DEAD", W / 2, 640, size=120))

    # SUSPECT 01: IMPACT PLAYER
    scene(L(8), L(9), None)
    add(mugshot(L(8), L(9), "01", "IMPACT PLAYER", "impact_signal", 560, 540, w=460, h=600))
    add(txt(L(8, 0.4), L(9), [("SUSPECT /01", Y), ("IMPACT PLAYER", WHITE)], 1300, 540, 120, align="l", maxw=900))
    scene(L(9), L(10), "impact_signal", 0.3)
    add(txt(L(9), L(10), [("+1 PLAYER", Y)], W / 2, 420, 220, anim="slam"))
    add(txt(L(9, 1.8), L(10), [("BUT THE EFFECT?", WHITE)], W / 2, 690, 90))
    scene(L(10), L(11), None)

    def lineup(base, t, t0=L(10), t1=L(11)):
        k = t - t0
        a = 1 - ease((t - (t1 - 0.15)) / 0.15)
        for i in range(8):
            g = ease((k - 0.15 * i) / 0.25)
            if g <= 0:
                continue
            x = 260 + i * 200
            col = Y if i >= 6 else WHITE
            chipim = text_img(((f"#{i + 1}", col),), 110, ANTON)
            paste_center(base, chipim, x, 470 + 40 * (1 - g), 1.0, g * a)
            bat = text_img((("BAT", GREY),), 44, XB_F)
            paste_center(base, bat, x, 600, 1.0, g * a)
    add(E(L(10), L(11), lineup, "ticks"))
    add(txt(L(10, 0.2), L(11), [("BATTING TILL NO. 8", Y)], W / 2, 220, 110))
    scene(L(11), L(12), "kohli2", 0.3)
    add(txt(L(11), L(11, 2.0), [("FEAR OF WICKETS:", WHITE), ("GONE", RED)], W / 2, 540, 140, anim="slam"))
    add(txt(L(11, 2.0), L(12), [("RISK:", WHITE), ("UNLIMITED", Y)], W / 2, 540, 150, anim="slam"))
    scene(L(12), L(13), None)
    add(txt(L(12), L(12, 2.4), [("ALL-ROUNDER", GREY)], W / 2, 420, 150))
    add(stamp(L(12, 1.4), L(12, 2.4), "NOT NEEDED", W / 2, 560, size=90))
    add(txt(L(12, 2.4), L(13), [("SPECIALIST BATTER", WHITE), ("+ SWAP", Y)], W / 2, 540, 140))
    scene(L(13), L(14), None)
    add(scale_gfx(L(13), L(14), W / 2, 560))
    add(txt(L(13, 0.2), L(14), [("ONE RULE BROKE THE BALANCE", WHITE)], W / 2, 150, 90))
    scene(L(14), L(15), "rcb_huddle", 0.25)
    add(stamp(L(14), L(14, 0.9), "CASE CLOSED?", W / 2, 460, color=Y))
    add(txt(L(14, 0.8), L(15), [("GUILTY?", RED)], W / 2, 640, 200, anim="slam"))
    scene(L(15), L(16), None)
    add(txt(L(15), L(15, 3.4), [("NOT SO FAST.", WHITE)], W / 2, 300, 110))
    add(txt(L(15, 1.2), L(15, 5.2), [("SCORES WERE RISING", WHITE), ("BEFORE 2023", Y)], W / 2, 600, 120))
    add(txt(L(15, 5.2), L(16), [("SOMEONE ELSE", WHITE), ("WAS INVOLVED…", RED)], W / 2, 540, 140, anim="slam"))

    # SUSPECT 02: THE PITCH
    scene(L(16), L(17), None)
    add(mugshot(L(16), L(17), "02", "THE PITCH", "pant", 560, 540, w=460, h=600))
    add(txt(L(16, 0.4), L(17), [("SUSPECT /02", Y), ("THE PITCH", WHITE)], 1300, 540, 120, align="l", maxw=900))
    scene(L(17), L(19), "pitch", 0.3, 0.3)
    add(photo_panel(L(17), L(19), "pitch", (110, 190, 820, 700)))
    for i, w_ in enumerate(["NO SWING", "NO SEAM", "PREDICTABLE BOUNCE"]):
        add(chip(L(17, 0.6 + 1.1 * i), L(18), w_, 1040, 330 + i * 130, size=56))
    add(stamp(L(18), L(19), "NO MOVEMENT", 1350, 560, color=Y, size=100))
    scene(L(19), L(20), "trophy", 0.3)
    add(txt(L(19), L(20), [("CHEPAUK", Y)], W / 2, 250, 120))
    add(txt(L(19, 1.4), L(19, 3.2), [("170 = SAFE", WHITE)], W / 2, 560, 170, anim="slam"))
    add(txt(L(19, 3.2), L(20), [("200 = CHASED", RED)], W / 2, 560, 170, anim="slam"))
    scene(L(20), L(21), "six", 0.35)
    add(txt(L(20, 0.3), L(20, 3.4), [("THE BALL TURNED…", WHITE)], W / 2, 400, 110))
    add(txt(L(20, 3.4), L(21), [("DIFFICULT = DRAMA", Y)], W / 2, 560, 150, anim="slam"))
    scene(L(21), L(23), None)
    add(txt(L(21), L(23), [("WHO MAKES THE PITCH?", WHITE)], W / 2, 330, 110))
    add(txt(L(21, 2.0), L(23), [("WHO BENEFITS?", Y)], W / 2, 520, 140, anim="slam"))
    add(chip(L(22), L(23), "REMEMBER THIS", 760, 720, bg=RED, fg=WHITE, size=56))

    # SUSPECT 03: FANTASY APPS
    scene(L(23), L(24), None)
    add(mugshot(L(23), L(24), "03", "FANTASY APPS", None, 560, 540, w=460, h=600))
    add(txt(L(23, 0.4), L(24), [("SUSPECT /03", Y), ("FANTASY APPS", WHITE)], 1300, 540, 120, align="l", maxw=900))
    scene(L(24), L(27), "kohli_rcb_walk", 0.25, 0.5)
    add(phone_gfx(L(24), L(27), 560, 560, [("BATTER (C)", "+86"), ("BOWLER", "+48"), ("WK", "+22"),
                                           ("ALL-ROUNDER", "+31"), ("KOHLI", "OUT")]))
    add(txt(L(24), L(25), [("CRORES DON'T WATCH THE MATCH", WHITE), ("THEY WATCH THEIR TEAM", Y)], 1330, 540, 64,
            maxw=900))
    add(txt(L(25), L(26), [("KOHLI OUT?", WHITE), ("MY CAPTAIN: 3 WKTS", Y)], 1330, 540, 90, maxw=900))
    add(txt(L(26), L(27), [("THE RESULT?", WHITE), ("DOESN'T MATTER", RED)], 1330, 540, 100, anim="slam",
            maxw=900))
    scene(L(27), L(28), None)
    add(txt(L(27, 0.3), L(28), [("THE STORY", GREY)], W / 2, 400, 140))
    add(txt(L(27, 3.0), L(28), [("→ JUST A SCORECARD", Y)], W / 2, 620, 110, path=BLACK_F, anim="slam"))
    scene(L(28), L(29), "empty", 0.3, 0.9)
    add(txt(L(28, 0.3), L(29), [("THE DARK SIDE", GREY), ("SAVINGS LOST", WHITE)], W / 2, 540, 120))

    # SUSPECT 04: THE BROADCAST
    scene(L(29), L(30), None)
    add(mugshot(L(29), L(30), "04", "THE BROADCAST", None, 560, 540, w=460, h=600))
    add(txt(L(29, 0.4), L(30), [("SUSPECT /04", Y), ("THE BROADCAST", WHITE)], 1300, 540, 120, align="l", maxw=900))
    scene(L(30), L(31), None)
    add(tv_gfx(L(30), L(30, 2.4), W / 2, 520, "IPL 2008", "mccullum_2008"))
    add(txt(L(30), L(30, 2.4), [("2008: AN EVENT", Y)], W / 2, 110, 90))
    add(txt(L(30, 2.4), L(31), [("TODAY: 74 MATCHES", WHITE), ("EVERY DAY. DOUBLE-HEADERS.", Y)], W / 2, 540, 120))
    scene(L(31), L(33), "ceat_timeout", 0.35)
    add(chip(L(31), L(33), "AD BREAK", 120, 120, bg=RED, fg=WHITE, size=56))
    add(chip(L(31, 1.6), L(33), "SPONSORED SIX", 120, 260, bg=Y, size=56))
    add(txt(L(32), L(33), [("BOUNDARY = INVENTORY", Y)], W / 2, 620, 140, anim="slam"))
    scene(L(33), L(34), None)
    add(photo_panel(L(33), L(34), "super_sixes", (560, 470, 800, 506)))
    add(txt(L(33), L(34), [("MORE SIXES =", WHITE)], W / 2, 200, 120))
    add(txt(L(33, 1.8), L(34), [("“SIXES BROUGHT TO YOU BY…”", Y)], W / 2, 360, 100))
    scene(L(34), GAP_OUT + GAP, None)
    add(strings_gfx(L(34), GAP_OUT))
    add(txt(L(34, 1.2), GAP_OUT, [("ALL FOUR POINT", WHITE), ("ONE WAY…", RED)], W / 2, 540, 120))

    # THE REVEAL
    scene(GAP_OUT + GAP, L(36), None)
    pairs = [("IMPACT PLAYER", "MORE RUNS"), ("FLAT PITCH", "MORE RUNS"), ("FANTASY", "MORE POINTS"),
             ("BROADCAST", "MORE SIXES + ADS")]
    for i, (a_, b_) in enumerate(pairs):
        t0 = L(35, 2.3 * i)
        add(txt(t0, L(36), [(a_, WHITE)], 640, 230 + i * 190, 80, maxw=700))
        add(txt(t0 + 0.6, L(36), [("→ " + b_, Y)], 1320, 230 + i * 190, 72, path=BLACK_F, anim="slam", maxw=800))
    scene(L(36), L(37), None)
    add(merge_gfx(L(36), L(37)))
    scene(L(37), L(39), "gt_celebrate", 0.28)
    add(txt(L(37), L(37, 2.6), [("IPL ISN'T BORING.", WHITE)], W / 2, 400, 130))
    add(txt(L(37, 2.6), L(38), [("IT'S BUILT TO BE", WHITE), ("PREDICTABLE.", Y)], W / 2, 540, 140, anim="slam"))
    add(txt(L(38) - 0.2, L(39), [("220 SELLS.", Y), ("140 DOESN'T.", GREY)], W / 2, 540, 150, anim="slam"))
    scene(L(39), L(41), "six", 0.35)
    add(txt(L(39, 1.6), L(40), [("THE FUN ISN'T THE SIX.", WHITE), ("IT'S THE FEAR OF IT.", Y)], W / 2, 540, 120))
    add(txt(L(40), L(41), [("NO FEAR = A HOLLOW SIX", RED)], W / 2, 540, 130, anim="slam"))
    scene(L(41), L(42), None)
    add(txt(L(41), L(42), [("WHO KILLED THE IPL?", WHITE)], W / 2, 330, 110))
    add(txt(L(41, 2.4), L(42), [("BALANCE DIED.", Y)], W / 2, 600, 220, anim="slam"))

    # THE FIX + END
    scene(L(42), L(43), "trophy", 0.3)
    for i, w_ in enumerate(["+ SOME GRASS", "LIMIT IMPACT PLAYER", "GIVE BOWLERS A WEAPON"]):
        add(chip(L(42, 1.0 + 1.2 * i), L(43), w_, 140, 300 + i * 140, size=60))
    add(txt(L(42, 5.0), L(43), [("180 = THRILLER", Y)], 1350, 540, 130, anim="slam", maxw=900))
    scene(L(43), END, "srh_arms", 0.2, 0.3)
    add(txt(L(43), END, [("IMPACT PLAYER:", WHITE)], W / 2, 300, 110))
    add(txt(L(43, 1.2), END, [("KEEP / BAN?", Y)], W / 2, 500, 220, anim="slam"))
    add(txt(L(43, 2.4), END, [("ONE WORD IN THE COMMENTS", GREY)], W / 2, 680, 60, path=XB_F))
    add(chip(L(44), END, "NEXT: BUMRAH vs ABHISHEK", 640, 860, bg=RED, fg=WHITE, size=52))
    add_inserts(S, El)
    S.insert(0, (CLIP_OUT, CLIP_OUT + CLIP_DUR, "seq:screenrec", 1.0, 0))
    enforce_unique(S, El)
    for e in (chip(CLIP_OUT + 0.6, CLIP_OUT + CLIP_DUR - 0.3, "ROHIT SHARMA ON THE IMPACT PLAYER RULE", 60, 930, size=40),
              chip(CLIP_OUT + 0.9, CLIP_OUT + CLIP_DUR - 0.3, "CLUB PRAIRIE FIRE PODCAST", 60, 1000, bg=INK, fg=GREY,
                   size=28)):
        e.win = "clip"
        El.append(e)
    return S, El


LOGO = Image.open(os.path.join(ROOT, "kohli_countdown", "assets", "logo.png")).convert("RGBA")
LOGO = LOGO.resize((200, int(LOGO.height * 200 / LOGO.width)), Image.LANCZOS)
LOGO.putalpha(LOGO.getchannel("A").point(lambda v: int(v * 0.8)))


BAND = (1 - 0.82 * np.clip((YY - 640) / 300, 0, 1) ** 1.2)[..., None]


def window_at(t):
    return next((k for k, a, b in WINDOWS if a <= t < b), None)


def render(S, El, t, i):
    sc = next((s for s in S if s[0] <= t < s[1]), S[-1])
    dark = sc[3] if not sc[2] or str(sc[2]).startswith("seq:") else 0.92
    a = backdrop(sc[2], t, sc[0], sc[1], dark, min(sc[4], 0.25))
    g = GRAIN[i % len(GRAIN)]
    a = (a + np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None] * 5) * VIG
    if t - sc[0] < 0.08 and sc[0] > 0:  # cut flash
        a = a + 60 * (1 - (t - sc[0]) / 0.08)
    photo_mode = bool(sc[2])
    if photo_mode:   # darken only the bottom band where the words go
        a = a * BAND
    base = img(a).convert("RGBA")
    w = window_at(t)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)) if photo_mode else None
    for e in El:
        if e.t0 <= t < e.t1 and e.win == w:
            if photo_mode and getattr(e, "kind", "") == "txt":
                e.fn(layer, t)
            else:
                e.fn(base, t)
    if layer is not None:
        bb = layer.getchannel("A").getbbox()
        if bb:
            blk = layer.crop(bb)
            s_ = min(1.0, 1700 / blk.width, 330 / blk.height)
            if s_ < 1:
                blk = blk.resize((int(blk.width * s_), int(blk.height * s_)), Image.BILINEAR)
            base.alpha_composite(blk, ((W - blk.width) // 2, int(890 - blk.height / 2)))
    base.alpha_composite(LOGO, (W - LOGO.width - 46, 36))
    return base.convert("RGB")


# ----------------------------------------------------------------------------- sound

def soundtrack(path, S, El):
    SR = sfx.SR
    n = int(END * SR)

    def put(buf, x, t0, gn=1.0):
        i = int(t0 * SR)
        if i >= n or i < 0:
            return
        x = x[: n - i]
        buf[i:i + len(x)] += x * gn

    tmp = os.path.join(OUT, "vo44.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(HERE, "vo", "vo_full.wav"), "-ar", str(SR),
                    "-ac", "1", tmp], check=True)
    with wave.open(tmp) as w:
        vo = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    voice = np.zeros(n)
    c1, c2 = int(CLIP_AT * SR), int(GAP_AT * SR)
    put(voice, vo[:c1], 0.0)
    put(voice, vo[c1:c2], CLIP_AT + CLIP_DUR)
    put(voice, vo[c2:], GAP_OUT + GAP)
    # the podcast clip's own sound, levelled up to sit with the voiceover
    tmp2 = os.path.join(OUT, "clip44.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(CLIP_SRC[0]), "-to", str(CLIP_SRC[1]), "-i",
                    os.path.join(HERE, "assets", "screenrec_raw.mp4"), "-vn", "-ac", "1", "-ar", str(SR),
                    "-af", "volume=6dB,afade=in:d=0.15,areverse,afade=in:d=0.3,areverse", tmp2], check=True)
    with wave.open(tmp2) as w:
        cl = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    put(voice, cl, CLIP_OUT + 0.2)

    mus = np.zeros(n)
    mus += st.section(drone(L(5)) * 0.5, 0.0, END, 0.1, 0.5)
    mus += st.section(st.pad(st.A_MINOR, GAP_OUT - L(5), cutoff=900) * 0.5, L(5), END, 0.8, 0.05)
    mus += st.section(st.pulse(GAP_OUT - L(8), 100, lambda x: 0.45 + 0.3 * (x / max(1, GAP_OUT - L(8)))), L(8), END,
                      0.3, 0.05) * 0.8
    mus += st.section(st.arps(st.A_MINOR, GAP_OUT - L(16), step=0.25, gain=0.1), L(16), END, 1.0, 0.05)
    mus += st.section(st.pulse(END - (GAP_OUT + GAP), 72, lambda x: 0.3), GAP_OUT + GAP, END, 0.4, 2.0) * 0.7
    mus += st.section(st.pad(st.WARM, END - L(41), cutoff=1200) * 0.45, L(41), END, 1.5, 2.5)
    mus = st.norm(mus, 0.3)
    mus[int(GAP_OUT * SR):int((GAP_OUT + GAP) * SR)] = 0  # the one real silence
    a_, b_ = int(CLIP_OUT * SR), int((CLIP_OUT + CLIP_DUR) * SR)
    mus[a_:b_] *= 0.15  # podcast clip: music almost out

    fx = np.zeros(n)
    hb = sfx.heartbeat()
    for k in range(3):
        put(fx, hb, L(2, 0.2) + 0.85 * k, 0.5)
    put(fx, braam(weight=1.2), L(0, 3.4), 0.5)
    put(fx, braam(weight=1.2), L(41, 2.4), 0.5)
    put(fx, braam(weight=1.3), GAP_OUT + GAP, 0.45)
    put(fx, braam(weight=1.0), L(36, 1.35), 0.4)
    for s in S:
        put(fx, sfx.whoosh() * 0.10, max(0, s[0] - 0.15))
    for e in El:
        if e.sfx == "hit":
            put(fx, sfx.impact(), e.t0, 0.22)
        elif e.sfx == "stamp":
            put(fx, sfx.impact(0.4), e.t0 + 0.08, 0.28)
        elif e.sfx == "pop":
            put(fx, sfx.pop(), e.t0, 0.25)
        elif e.sfx == "shutter":
            put(fx, sfx.riser(0.9), e.t0 - 0.9, 0.12)
            put(fx, sfx.camera_shutter(), e.t0, 0.35)
        elif e.sfx == "type":
            for k in range(14):
                put(fx, sfx.tick(), e.t0 + k * 0.05, 0.45)
        elif e.sfx == "ticks":
            for k in range(8):
                put(fx, sfx.tick(), e.t0 + 0.15 * k, 0.5)
    for k in range(2):  # bar-chart ticks
        put(fx, sfx.tick(), L(0, 2.3 + 0.9 * k), 0.5)
    t_ch = L(33, 1.8)  # cash register: two quick dings
    put(fx, sfx.ding(0.4, 2093), t_ch, 0.18)
    put(fx, sfx.ding(0.5, 2637), t_ch + 0.09, 0.15)
    fx = np.tanh(fx)

    env = np.convolve(np.abs(voice), np.ones(int(0.3 * SR)) / int(0.3 * SR), mode="same")
    duck = 1 - 0.75 * np.clip(env / (env.max() * 0.2 + 1e-6), 0, 1)   # ~12 dB under the voice
    mix = voice + mus * duck + fx * 0.25
    mix = np.tanh(mix * 1.05) * 0.95
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(np.repeat((np.clip(mix, -1, 1) * 32767).astype(np.int16)[:, None], 2, axis=1).tobytes())


# ----------------------------------------------------------------------------- main

def main():
    os.makedirs(OUT, exist_ok=True)
    S, El = build()
    print(f"total {END:.1f}s, {len(S)} scenes, {len(El)} elements")
    print(f"{len(MISSING)} spots without a unique IPL photo (graphic only):")
    for t0, k in sorted(MISSING):
        txts = [ln[0] for e in El if getattr(e, "kind", "") == "txt" and e.t0 <= t0 + 0.5 < e.t1
                for ln in (getattr(e, "lines", []) or [])]
        print(f"  {int(t0 // 60)}:{int(t0 % 60):02d}  (was {k})")
    if "--preview" in sys.argv:
        times = [s[0] + min(1.6, (s[1] - s[0]) * 0.75) for s in S]
        th = [render(S, El, t, int(t * FPS)).resize((320, 180)) for t in times]
        cols = 8
        sheet = Image.new("RGB", (320 * cols, 180 * ((len(th) + cols - 1) // cols)), "white")
        for k, im in enumerate(th):
            sheet.paste(im, ((k % cols) * 320, (k // cols) * 180))
        sheet.save(os.path.join(OUT, "preview_sheet.jpg"), quality=88)
        print("preview written")
        return
    audio = os.path.join(OUT, "mix.wav")
    soundtrack(audio, S, El)
    silent = os.path.join(OUT, "video_silent.mp4")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                          "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    total = int(END * FPS)
    for i in range(total):
        p.stdin.write(render(S, El, i / FPS, i).tobytes())
        if i % 900 == 0:
            print(f"frame {i}/{total}", flush=True)
    p.stdin.close()
    p.wait()
    final = os.path.join(OUT, "IPL_Ko_Kisne_Maara.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", audio, "-map", "0:v", "-map", "1:a",
                    "-c:v", "libx264", "-preset", "slow", "-b:v", "8M", "-maxrate", "11M", "-bufsize", "16M",
                    "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000", "-c:a", "aac",
                    "-b:a", "256k", "-shortest", "-movflags", "+faststart", final], check=True)
    print("IPL_DONE", final)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""16:9 long-form: the Cape Town sandpaper story and Usman Khawaja's book "Sabr" (~3:25).

    python3 make_long.py            ->  out/Sandpaper_Sabr.mp4 (1920x1080, 30 fps, -14 LUFS)
    python3 make_long.py --preview  ->  out/preview_sheet.jpg

Voice: the ElevenLabs Hinglish voiceover (vo/vo_raw.mp3, line timings in vo/timings.json from align_vo.py),
with three of Khawaja's own sound bites from his Instagram reel cut in where the script quotes him.
Pictures: footage and stills pulled from the reference reel by extract_assets.py, shown as framed cards over a
blurred copy of themselves; English headlines in the channel style beside them. Music and SFX are synthesised.
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
Y = (255, 222, 89)
RED = (232, 48, 48)
WHITE = (255, 255, 255)
GREY = (190, 190, 196)
BLACK_F = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
XB_F = "/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf"
SEMI_F = "/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf"
ANTON = os.path.join(ROOT, "doc_video", "thumb", "fonts", "Anton-Regular.woff")
FOOT = os.path.join(HERE, "footage")
OUT = os.path.join(HERE, "out")
rng = np.random.default_rng(2018)

# ----------------------------------------------------------------------------- timeline

TIM = json.load(open(os.path.join(HERE, "vo", "timings.json")))
VO_LINES = TIM["lines"]
VO_DUR = TIM["duration"]
# Khawaja's bites: (after VO line, file, reel clip, offset into that clip where the bite starts)
BITES = [(27, "k1", "reel1", 0.74), (31, "k2", "reel1", 33.83), (37, "k3", "reel2", 0.73)]
PAD = 0.35
BITE_LEN = {}
for _, k, _, _ in BITES:
    with wave.open(os.path.join(FOOT, "khawaja", k + ".wav")) as w:
        BITE_LEN[k] = w.getnframes() / w.getframerate()
INS = [(VO_LINES[i]["end"] + 0.25, k, BITE_LEN[k] + 2 * PAD) for i, k, _, _ in BITES]  # (vo time, bite, out length)


def out_t(t_vo):
    """VO time -> output time (each bite pushes everything after it)."""
    return t_vo + sum(d for p, _, d in INS if p <= t_vo)


def L(i, off=0.0):
    return out_t(VO_LINES[i]["start"]) + off


def K(k, off=0.0):
    p, _, _ = next(x for x in INS if x[1] == k)
    return out_t(p - 1e-6) + PAD + off


END = out_t(VO_DUR) + 3.5

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
        _fc[(p, s)] = ImageFont.truetype(p, s)
    return _fc[(p, s)]


def text_img(lines, size, path=BLACK_F, maxw=720, align="l", gap=0.12, track=0):
    """lines: [(text, colour)] -> RGBA with soft shadow; each line shrinks to fit maxw."""
    rows = []
    for txt, col in lines:
        s = size
        while font(path, s).getlength(txt) + track * len(txt) > maxw and s > 22:
            s -= 2
        f = font(path, s)
        l, t, r, b = f.getbbox(txt)
        w = int(sum(f.getlength(c) for c in txt) + track * (len(txt) - 1)) if track else r - l
        rows.append((txt, col, f, l, t, w, b - t))
    pad = 30
    wid = max(r[5] for r in rows)
    hgt = sum(r[6] for r in rows) + int(size * gap) * (len(rows) - 1)
    im = Image.new("RGBA", (wid + 2 * pad, hgt + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    y = pad
    for txt, col, f, l, t, w, h in rows:
        x = pad + {"l": 0, "c": (wid - w) // 2, "r": wid - w}[align] - (l if not track else 0)
        for target, fill, dy in ((sh, (0, 0, 0, 220), 5), (im, col, 0)):
            d = ImageDraw.Draw(target)
            if track:
                xx = x
                for c in txt:
                    d.text((xx, y - t + dy), c, font=f, fill=fill)
                    xx += f.getlength(c) + track
            else:
                d.text((x, y - t + dy), txt, font=f, fill=fill)
        y += h + int(size * gap)
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    out.alpha_composite(im)
    return out


def fade(im, a):
    if a >= 1:
        return im
    im = im.copy()
    im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    return im


# ----------------------------------------------------------------------------- media


class Clip:
    """Sequential frame reader for a footage clip (loops; optional start offset)."""

    def __init__(self, name, offset=0.0):
        self.path = os.path.join(FOOT, "clips", name + ".mp4")
        probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
                                "stream=width,height", "-of", "csv=p=0", self.path], capture_output=True, text=True)
        self.w, self.h = map(int, probe.stdout.strip().split(","))
        self.offset = offset
        self.p = None
        self.last = None

    def _open(self, off):
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(off), "-i", self.path, "-f", "rawvideo",
                                   "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)

    def next(self):
        if self.p is None:
            self._open(self.offset)
        buf = self.p.stdout.read(self.w * self.h * 3)
        if len(buf) < self.w * self.h * 3:
            self.p.stdout.close()
            self.p.wait()
            self._open(0)
            buf = self.p.stdout.read(self.w * self.h * 3)
        if len(buf) == self.w * self.h * 3:
            self.last = Image.frombuffer("RGB", (self.w, self.h), buf, "raw", "RGB", 0, 1)
        return self.last

    def close(self):
        if self.p:
            self.p.stdout.close()
            self.p.kill()
            self.p = None


class Still:
    def __init__(self, name):
        self.im = Image.open(os.path.join(FOOT, "stills", name + ".png")).convert("RGB")

    def next(self):
        return self.im

    def close(self):
        pass


def make_media(spec):
    if spec is None:
        return None
    kind, name, *rest = spec
    return Clip(name, rest[0] if rest else 0.0) if kind == "clip" else Still(name)


_masks = {}


def rounded(w, h, r=24):
    if (w, h) not in _masks:
        m = Image.new("L", (w, h), 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), radius=r, fill=255)
        sh = Image.new("L", (w + 120, h + 120), 0)
        ImageDraw.Draw(sh).rounded_rectangle((60, 72, 60 + w, 72 + h), radius=r, fill=210)
        _masks[(w, h)] = (m, sh.filter(ImageFilter.GaussianBlur(26)))
    return _masks[(w, h)]


def fit(im, box_w, box_h):
    s = min(box_w / im.width, box_h / im.height)
    return int(im.width * s), int(im.height * s)


# card boxes per layout: (x, y, w, h) of the area the card is fitted into
BOX = {"R": (900, 150, 900, 720), "L": (120, 150, 900, 720), "C": (260, 120, 1400, 660),
       "RP": (1240, 120, 560, 860), "LP": (120, 120, 560, 860)}
TEXT_X = {"R": 120, "L": 1110, "C": None, "RP": 140, "LP": 760, None: None}

GRAIN = [rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32) for _ in range(6)]
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = (1 - 0.6 * np.clip(((XX - W / 2) / (W * 0.6)) ** 2 + ((YY - H / 2) / (H * 0.62)) ** 2, 0, 1))[..., None]
GLOW = np.exp(-(((XX - W * 0.3) / (W * 0.5)) ** 2 + ((YY - H * 0.2) / (H * 0.7)) ** 2))[..., None] * \
    np.array([40, 32, 10], np.float32)


def backdrop(frame, k_dark=0.32):
    base = np.zeros((H, W, 3), np.float32) + np.array([10, 11, 15], np.float32)
    if frame is not None:
        small = frame.resize((96, 54), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3))
        base = base * 0.4 + arr(small.resize((W, H), Image.BILINEAR)) * k_dark
    return base + GLOW


# ----------------------------------------------------------------------------- shots

class Text:
    def __init__(self, t, lines, size=78, path=BLACK_F, anim="rise", maxw=None, track=0, align=None):
        self.t, self.lines, self.size, self.path, self.anim = t, lines, size, path, anim
        self.maxw, self.track, self.align = maxw, track, align


def T(t, *lines, size=78, **kw):
    return Text(t, list(lines), size, **kw)


def kick(t, txt, color=Y):
    return Text(t, [(txt, color)], 30, XB_F, "rise", track=4)


class Shot:
    def __init__(self, t0, media=None, layout="C", texts=(), special=None, dark=0.32, hit=None):
        self.t0, self.media_spec, self.layout, self.texts = t0, media, layout, list(texts)
        self.special, self.dark, self.hit = special, dark, hit
        self.media = None
        self.t1 = None


def build_shots():
    S = []
    a = S.append
    a(Shot(0.0, ("clip", "yellow"), "C", [T(0.15, ("A TINY YELLOW PIECE.", WHITE), size=92),
                                          T(L(1), ("SMALLER THAN A PALM.", Y), size=70)], hit="soft"))
    a(Shot(L(2), ("clip", "smith"), "R", [T(L(2), ("IT HUMBLED", WHITE), ("AUSTRALIAN", WHITE), ("CRICKET.", Y), size=96)]))
    a(Shot(L(3), ("clip", "hands"), None, [kick(L(3), "3RD TEST · DAY 3 · 24 MARCH"),
                                           T(L(3, 0.2), ("CAPE TOWN, 2018", WHITE), size=150, path=ANTON, anim="slam",
                                             align="c", maxw=1500)], special="title", dark=0.5, hit="braam"))
    a(Shot(L(4), ("clip", "hands"), "L", [kick(L(4), "THE CAMERA CATCH"), T(L(4), ("THE BALL.", WHITE), size=84),
                                          T(L(5), ("THE CAMERAS.", WHITE), size=84),
                                          T(L(6), ("THE BIG SCREEN.", Y), size=84)]))
    a(Shot(L(7), ("clip", "walkie"), "R", [kick(L(7), "THE DRESSING ROOM"),
                                           T(L(7), ("CAMERA ON", WHITE), ("COACH LEHMANN", Y), size=84),
                                           T(L(8), ("WALKIE-TALKIE.", WHITE), size=72)]))
    a(Shot(L(9), ("clip", "handscomb"), "L", [kick(L(9), "THE MESSAGE"),
                                              T(L(9), ("TO 12TH MAN", WHITE), ("HANDSCOMB", Y), size=84)]))
    a(Shot(L(10), ("clip", "yellow"), "C", [T(L(10, 0.3), ("SANDPAPER. DOWN THE TROUSERS.", Y), size=70, align="c",
                                              maxw=1500)], hit="impact"))
    a(Shot(L(11), ("clip", "pouch"), "R", [kick(L(11), "THE UMPIRES ARRIVE"),
                                           T(L(11, 1.2), ("OUT COMES…", WHITE), size=72),
                                           T(L(11, 2.4), ("A SUNGLASSES", Y), ("POUCH.", Y), size=88)]))
    a(Shot(L(12), ("clip", "bancroft"), "L", [T(L(12, 0.2), ("ACTING", WHITE), ("BOLLYWOOD", Y), ("WOULD ENVY.", WHITE),
                                                size=84)]))
    a(Shot(L(13), None, None, [kick(L(13), "THE BANS"), ], special="bans", hit="braam"))
    a(Shot(L(14), ("still", "lehmann"), "R", [kick(L(14), "COACH DARREN LEHMANN"),
                                              T(L(14), ("CLEARED BY", WHITE), ("THE INQUIRY.", WHITE), size=80),
                                              T(L(14, 2.3), ("STILL QUIT.", Y), size=96)]))
    a(Shot(L(15), ("still", "huddle"), "C", [T(L(15), ("SILENCE IN THE DRESSING ROOM.", WHITE), size=64, align="c",
                                               maxw=1500),
                                             T(L(16), ("BUT ONE MAN WAS WRITING.", Y), size=64, align="c", maxw=1500)],
           dark=0.25))
    a(Shot(L(17), ("still", "khawaja"), "R", [kick(L(17), "THE MAN WITH THE NOTES"),
                                              T(L(17), ("USMAN", WHITE), ("KHAWAJA", Y), size=120),
                                              T(L(18), ("WROTE IT ALL DOWN", WHITE), ("DAYS AFTER CAPE TOWN", WHITE),
                                                size=52, path=XB_F),
                                              T(L(19), ("HID IT FOR 8 YEARS.", Y), size=64)], hit="impact"))
    a(Shot(L(20), ("still", "sabr"), "LP", [kick(L(20), "THE BOOK"), T(L(20, 1.2), ("SABR", Y), size=200, path=ANTON),
                                            T(L(20, 1.5), ("PATIENCE.", WHITE), size=64)], hit="impact"))
    a(Shot(L(21), None, None, [T(L(21), ("NOW THE REAL", WHITE), ("DRAMA BEGINS.", Y), size=120, anim="slam",
                                 align="c", maxw=1500)], special="title", hit="braam"))
    a(Shot(L(22), ("still", "lehmann"), "L", [kick(L(22), "LEHMANN · ABC RADIO"),
                                              T(L(22, 1.0), ("“BOOKS ARE", WHITE), ("THERE TO SELL.”", Y), size=88),
                                              T(L(23), ("SPEAKING UP", WHITE), ("FOR MONEY?", RED), size=64)]))
    a(Shot(L(24), ("clip", "reel1"), "RP", [kick(L(24), "HOURS LATER"),
                                            T(L(24), ("KHAWAJA PICKS", WHITE), ("UP HIS PHONE.", WHITE), size=80),
                                            T(L(25), ("NO PRESS CONFERENCE.", Y), ("NO PR TEAM.", Y), size=56),
                                            T(L(27), ("“EVERYONE KNEW?”", WHITE), size=64)]))
    a(Shot(K("k1", -PAD), ("clip", "reel1", 0.74 - PAD), "RP", [kick(K("k1", -PAD), "IN HIS OWN WORDS", GREY),
                                                                  T(K("k1"), ("“AM I GOING TO DENY", WHITE),
                                                                    ("THAT EVERYONE KNEW?”", WHITE), size=68),
                                                                  T(K("k1", 4.6), ("“NAH. I WON'T", Y), ("DENY THAT EITHER.”", Y),
                                                                    size=68)], special="bite"))
    a(Shot(L(28), None, None, [T(L(28), ("THEN CAME", WHITE), ("THE BIG HIT.", Y), size=120, anim="slam", align="c",
                                 maxw=1500)], special="title", hit="braam"))
    a(Shot(L(29), ("still", "khawaja"), "L", [T(L(29), ("DOUBT MY STORY?", WHITE), ("GO AHEAD.", Y), size=80),
                                              T(L(30), ("MY MEMORY?", WHITE), ("IT'S ALL", WHITE), ("WRITTEN DOWN.", Y),
                                                size=80)]))
    a(Shot(L(31), ("still", "huddle"), "R", [kick(L(31), "KHAWAJA'S CLAIM"),
                                             T(L(31, 0.5), ("“WE ALL", WHITE), ("MESSED UP.", WHITE), size=84),
                                             T(L(31, 3.4), ("WE FACE IT", Y), ("TOGETHER.”", Y), size=84)]))
    a(Shot(K("k2", -PAD), ("clip", "reel1", 33.83 - PAD), "RP", [kick(K("k2", -PAD), "IN HIS OWN WORDS", GREY),
                                                                   T(K("k2"), ("“…INCLUDING ME.", WHITE),
                                                                     ("WE'RE NOT THE VICTIMS.”", WHITE), size=62),
                                                                   T(K("k2", 7.0), ("“THESE THREE GUYS", Y),
                                                                     ("TOOK THE BLAME.", Y), ("THEY'RE THE VICTIMS.”", Y),
                                                                     size=62)], special="bite"))
    a(Shot(L(32), ("still", "huddle"), None, [kick(L(32), "HIS ACCOUNT"),
                                              T(L(32), ("2 SENIOR PLAYERS", WHITE), ("BLOCKED IT.", Y), size=84),
                                              T(L(33), ("NAMES?", WHITE), ("STILL UNKNOWN.", RED), size=64)],
           special="unknown", dark=0.22))
    a(Shot(L(34), ("still", "bowlers"), "L", [kick(L(34), "2021 · THE BOWLERS' STATEMENT"),
                                              T(L(34), ("CUMMINS · STARC", WHITE), ("HAZLEWOOD · LYON", WHITE), size=56,
                                                path=XB_F),
                                              T(L(34, 2.2), ("“WE DIDN'T KNOW.”", Y), size=80),
                                              T(L(34, 4.4), ("WHY WAS KHAWAJA", WHITE), ("SILENT?", RED), size=72)]))
    a(Shot(L(35), None, None, [T(L(35), ("THE ANSWER STINGS.", WHITE), size=110, anim="slam", align="c", maxw=1500)],
           special="title", hit="impact"))
    a(Shot(L(36), ("clip", "reel2"), "RP", [T(L(36), ("“CALL ME", WHITE), ("A CHICKEN.”", Y), size=110),
                                            T(L(37), ("IN THE TEAM.", WHITE), ("NO FIGHT LEFT.", WHITE), size=64)]))
    a(Shot(K("k3", -PAD), ("clip", "reel2", 0.73 - PAD), "RP", [kick(K("k3", -PAD), "IN HIS OWN WORDS", GREY),
                                                                  T(K("k3", 2.6), ("“I WASN'T GONNA GO TO WAR", WHITE),
                                                                    ("WITH THOSE GUYS BACK THEN.”", WHITE), size=54),
                                                                  T(K("k3", 6.9), ("“I WASN'T COMFORTABLE.", WHITE),
                                                                    ("THAT'S THE TRUTH.”", WHITE), size=54),
                                                                  T(K("k3", 10.1), ("“CALL ME A CHICKEN", Y),
                                                                    ("OR WHATEVER YOU WANT.”", Y), size=54)],
           special="bite"))
    a(Shot(L(38), None, None, [T(L(38), ("BUT THE STORY", WHITE), ("ISN'T OVER.", Y), size=120, anim="slam", align="c",
                                 maxw=1500)], special="title", hit="braam"))
    a(Shot(L(39), None, None, [kick(L(39), "THE OTHER SIDE")], special="denials"))
    a(Shot(L(40), None, None, [], special="ca_file"))
    a(Shot(L(41), ("clip", "walkie"), "L", [kick(L(41), "ACCORDING TO CRICKET AUSTRALIA"),
                                            T(L(41, 0.3), ("NO WARNING", WHITE), ("ON THE RADIO.", WHITE), size=80),
                                            T(L(41, 4.6), ("LEHMANN ONLY ASKED:", Y), size=52, path=XB_F),
                                            T(L(41, 5.6), ("“WHAT THE **** IS", WHITE), ("GOING ON?”", WHITE), size=72)]))
    a(Shot(L(42), None, None, [], special="versus_file"))
    a(Shot(L(44), ("still", "huddle"), "C", [T(L(44), ("THE TRUTH?", WHITE), size=72, align="c", maxw=1500),
                                             T(L(44, 1.4), ("ONLY THE DRESSING ROOM WALLS KNOW.", Y), size=60, align="c",
                                               maxw=1500)], dark=0.2))
    a(Shot(L(45), None, None, [], special="verdict", hit="braam"))
    for s, nxt in zip(S, S[1:] + [None]):
        s.t1 = nxt.t0 if nxt else END
    return S


# ----------------------------------------------------------------------------- drawing

def draw_texts(base, shot, t, x0, top=210, align="l"):
    """Stack the shot's text items in its column; each animates in at its own time."""
    y = top
    for tx in shot.texts:
        maxw = tx.maxw or (700 if shot.layout in ("R", "L") else 1000)
        im = text_img(tx.lines, tx.size, tx.path, maxw, tx.align or align, track=tx.track)
        h = im.height
        if t >= tx.t:
            k = t - tx.t
            if tx.anim == "slam":
                s = 1 + 0.3 * (1 - ease(k / 0.16))
                a = ease(k / 0.08)
                im2 = im.resize((int(im.width * s), int(im.height * s)), Image.BILINEAR)
                dy = -(im2.height - h) / 2
            else:
                a = ease(k / 0.3)
                im2, dy = im, 34 * (1 - ease(k / 0.35))
            a *= 1 - ease((t - (shot.t1 - 0.2)) / 0.2)
            if (tx.align or align) == "c":
                x = (W - im2.width) // 2
            else:
                x = x0 - 30
            base.alpha_composite(fade(im2, a), (int(x), int(y + dy)))
        y += h - 26 + (18 if tx.size >= 60 else 4)
    return y


def draw_card(base, frame, box, t, shot, scale_in=True):
    bx, by, bw, bh = box
    w, h = fit(frame, bw, bh)
    k = t - shot.t0
    z = 1.0 + 0.03 * min(1.0, k / max(1.0, shot.t1 - shot.t0))
    cw, ch = int(w * z), int(h * z)
    f = frame.resize((cw, ch), Image.BILINEAR).crop(((cw - w) // 2, (ch - h) // 2, (cw - w) // 2 + w, (ch - h) // 2 + h))
    m, sh = rounded(w, h)
    a = ease(k / 0.3) * (1 - ease((t - (shot.t1 - 0.2)) / 0.2))
    x = bx + (bw - w) // 2
    y = by + (bh - h) // 2 + int(40 * (1 - ease(k / 0.35)))
    shadow = Image.new("RGBA", sh.size, (0, 0, 0, 0))
    shadow.putalpha(sh.point(lambda v: int(v * a)))
    base.alpha_composite(shadow, (x - 60, y - 60))
    card = f.convert("RGBA")
    card.putalpha(m.point(lambda v: int(v * a)))
    base.alpha_composite(card, (x, y))
    return x, y, w, h


def chip(base, txt, x, y, fg=(14, 12, 6), bg=Y, size=30):
    f = font(XB_F, size)
    l, t, r, b = f.getbbox(txt)
    d = ImageDraw.Draw(base)
    d.rounded_rectangle((x, y, x + r - l + 36, y + b - t + 22), radius=8, fill=bg + (255,))
    d.text((x + 18 - l, y + 11 - t), txt, font=f, fill=fg)


STILL_CACHE = {}


def still(name):
    if name not in STILL_CACHE:
        STILL_CACHE[name] = Image.open(os.path.join(FOOT, "stills", name + ".png")).convert("RGB")
    return STILL_CACHE[name]


def special(base, shot, t):
    k = t - shot.t0
    if shot.special == "bans":
        names = [("smith", "STEVE SMITH", "12 MONTHS"), ("warner", "DAVID WARNER", "12 MONTHS"),
                 ("bancroft", "CAMERON BANCROFT", "9 MONTHS")]
        for j, (n, who, ban) in enumerate(names):
            kk = k - 0.25 * j
            if kk < 0:
                continue
            fr = shot.extra[n].next()
            sub = Shot(shot.t0 + 0.25 * j)
            sub.t1 = shot.t1
            x, y, w, h = draw_card(base, fr, (90 + j * 590, 230, 560, 420), t, sub)
            a = ease((kk - 0.2) / 0.3) * (1 - ease((t - (shot.t1 - 0.2)) / 0.2))
            if a > 0:
                lab = text_img([(who, WHITE)], 40, XB_F, 540, "c")
                base.alpha_composite(fade(lab, a), (x + (w - lab.width) // 2, y + h + 18))
                num = text_img([(ban, Y)], 76, ANTON, 540, "c")
                base.alpha_composite(fade(num, a), (x + (w - num.width) // 2, y + h + 70))
        hdr = text_img([("ONLY THREE BANNED.", WHITE)], 72, BLACK_F, 1600, "c")
        base.alpha_composite(fade(hdr, ease(k / 0.3)), ((W - hdr.width) // 2, 70))
        return
    if shot.special == "unknown":
        for j, cx in enumerate((W * 0.62, W * 0.82)):
            a = ease((k - 0.4 - 0.25 * j) / 0.3) * (1 - ease((t - (shot.t1 - 0.2)) / 0.2))
            if a <= 0:
                continue
            lay = Image.new("RGBA", (300, 380), (0, 0, 0, 0))
            d = ImageDraw.Draw(lay)
            d.ellipse((90, 20, 210, 140), fill=(40, 42, 50, 255), outline=RED + (255,), width=5)
            d.rounded_rectangle((40, 150, 260, 370), radius=60, fill=(40, 42, 50, 255), outline=RED + (255,), width=5)
            q = font(ANTON, 150)
            d.text((150, 230), "?", font=q, fill=Y, anchor="mm")
            base.alpha_composite(fade(lay, a), (int(cx - 150), 330))
        draw_texts(base, shot, t, 120, 300)
        return
    if shot.special == "denials":
        for j, (n, who, said) in enumerate([("lehmann", "DARREN LEHMANN", "“I DIDN'T KNOW.”"),
                                             ("bowlers", "THE FOUR BOWLERS", "“WE DIDN'T KNOW.”")]):
            sub = Shot(shot.t0 + 0.35 * j)
            sub.t1 = shot.t1
            if k < 0.35 * j:
                continue
            x, y, w, h = draw_card(base, still(n), (130 + j * 860, 200, 800, 470), t, sub)
            a = ease((k - 0.35 * j - 0.3) / 0.3) * (1 - ease((t - (shot.t1 - 0.2)) / 0.2))
            if a > 0:
                lab = text_img([(who, GREY)], 36, XB_F, 760, "c")
                base.alpha_composite(fade(lab, a), (x + (w - lab.width) // 2, y + h + 20))
                q = text_img([(said, Y)], 78, BLACK_F, 760, "c")
                base.alpha_composite(fade(q, a), (x + (w - q.width) // 2, y + h + 72))
        draw_texts(base, shot, t, 130, 80)
        return
    if shot.special in ("ca_file", "versus_file"):
        def doc(x, y, w, h, a, title, lines, accent):
            lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            d = ImageDraw.Draw(lay)
            d.rounded_rectangle((0, 0, w - 1, h - 1), radius=18, fill=(236, 232, 220, 255))
            d.rectangle((0, 0, w, 14), fill=accent + (255,))
            d.text((44, 50), title, font=font(XB_F, 30), fill=(90, 86, 80))
            yy = 110
            for ln, f in lines:
                d.text((44, yy), ln, font=f, fill=(20, 20, 24))
                yy += f.size + 18
            base.alpha_composite(fade(lay, a), (x, int(y + 30 * (1 - a))))
        if shot.special == "ca_file":
            a = ease(k / 0.35) * (1 - ease((t - (shot.t1 - 0.2)) / 0.2))
            doc(310, 200, 1300, 600, a, "CRICKET AUSTRALIA · 2018 INVESTIGATION · ON RECORD",
                [("Plan known to:", font(BLACK_F, 60)), ("Smith · Warner · Bancroft.", font(BLACK_F, 60)),
                 ("No other player knew.", font(SEMI_F, 52)), ("Coach Lehmann: not aware.", font(SEMI_F, 52))], RED)
            st_a = ease((k - 1.5) / 0.15)
            if st_a > 0:
                stamp = text_img([("OFFICIAL", RED)], 90, BLACK_F, 600, "c").rotate(-8, expand=True)
                base.alpha_composite(fade(stamp, st_a * a), (1040, 620))
            return
        # versus: official file (L42) vs 8-year-old notes (L43)
        a1 = ease(k / 0.35) * (1 - ease((t - (shot.t1 - 0.2)) / 0.2))
        doc(130, 220, 780, 560, a1, "CRICKET AUSTRALIA · 2018",
            [("THE OFFICIAL", font(BLACK_F, 64)), ("FILE", font(BLACK_F, 64)), ("Three players knew.", font(SEMI_F, 44))],
            RED)
        k2 = t - L(43)
        if k2 > 0:
            a2 = ease(k2 / 0.35) * (1 - ease((t - (shot.t1 - 0.2)) / 0.2))
            doc(1010, 220, 780, 560, a2, "USMAN KHAWAJA · SABR",
                [("ONE MAN'S", font(BLACK_F, 64)), ("8-YEAR-OLD NOTES", font(BLACK_F, 64)),
                 ("“It was all of us.”", font(SEMI_F, 44))], Y)
            vs = text_img([("VS", Y)], 110, ANTON, 300, "c")
            base.alpha_composite(fade(vs, a2), ((W - vs.width) // 2, 410))
        return
    if shot.special == "verdict":
        for j, (n, who, col) in enumerate([("khawaja", "KHAWAJA", Y), ("lehmann", "LEHMANN", RED)]):
            sub = Shot(shot.t0 + 0.2 * j)
            sub.t1 = END + 1
            if k < 0.2 * j:
                continue
            x, y, w, h = draw_card(base, still(n), (150 + j * 1000, 170, 620, 560), t, sub)
            lab = text_img([(who, col)], 84, ANTON, 600, "c")
            base.alpha_composite(fade(lab, ease((k - 0.4) / 0.3)), (x + (w - lab.width) // 2, y + h + 10))
        q = text_img([("?", Y)], 260, ANTON, 300, "c")
        s = 1 + 0.4 * (1 - ease((k - 0.6) / 0.2))
        if k > 0.6:
            q = q.resize((int(q.width * s), int(q.height * s)), Image.BILINEAR)
            base.alpha_composite(q, ((W - q.width) // 2, 330 - (q.height - 330) // 2))
        if t > out_t(VO_DUR) - 0.3:
            k3 = t - (out_t(VO_DUR) - 0.3)
            v = text_img([("YOUR VERDICT? COMMENT BELOW", WHITE)], 54, XB_F, 1500, "c")
            base.alpha_composite(fade(v, ease(k3 / 0.4)), ((W - v.width) // 2, 900))
        return


LOGO = Image.open(os.path.join(ROOT, "kohli_countdown", "assets", "logo.png")).convert("RGBA")
LOGO = LOGO.resize((200, int(LOGO.height * 200 / LOGO.width)), Image.LANCZOS)
LOGO.putalpha(LOGO.getchannel("A").point(lambda v: int(v * 0.8)))


def render(shots, t, i):
    shot = next(s for s in shots if s.t0 <= t < s.t1)
    if shot.media is None and shot.media_spec is not None:
        shot.media = make_media(shot.media_spec)
    if shot.special == "bans" and not hasattr(shot, "extra"):
        shot.extra = {n: Clip(n) for n in ("smith", "warner", "bancroft")}
    frame = shot.media.next() if shot.media else None
    bgsrc = frame
    if shot.special == "verdict":
        bgsrc = None
    a = backdrop(bgsrc, shot.dark)
    g = GRAIN[i % len(GRAIN)]
    a = (a + np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None] * 5) * VIG
    base = img(a).convert("RGBA")
    if shot.special in ("bans", "unknown", "denials", "ca_file", "versus_file", "verdict"):
        special(base, shot, t)
    elif shot.special == "title":
        y = draw_texts(base, shot, t, 0, 380, "c")
    else:
        lay = shot.layout
        if frame is not None and lay is not None:
            x, y, w, h = draw_card(base, frame, BOX[lay], t, shot)
            if shot.special == "bite":
                chip(base, "USMAN KHAWAJA · INSTAGRAM", x, y + h + 18, bg=Y)
                # sound-on badge
                pulse = 0.5 + 0.5 * np.sin(t * 6)
                d = ImageDraw.Draw(base)
                d.ellipse((x + 24, y + 24, x + 46, y + 46), fill=(232, 48, 48, int(150 + 105 * pulse)))
        if lay == "C":
            bx, by, bw, bh = BOX["C"]
            draw_texts(base, shot, t, 0, 800, "c")
        elif lay is not None:
            draw_texts(base, shot, t, TEXT_X[lay] + 30, 200 if lay in ("R", "L") else 230)
        else:
            draw_texts(base, shot, t, 120, 300)
    base.alpha_composite(LOGO, (W - LOGO.width - 50, 40))
    # close media of shots we've left
    for s in shots:
        if s.t1 <= t and s.media is not None:
            s.media.close()
            s.media = None
        if s.t1 <= t and hasattr(s, "extra"):
            for c in s.extra.values():
                c.close()
            del s.extra
    return base.convert("RGB")


# ----------------------------------------------------------------------------- sound

def soundtrack(path, shots):
    SR = sfx.SR
    n = int(END * SR)

    def load(p):
        tmp = os.path.join(OUT, "tmp.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", p, "-ar", str(SR), "-ac", "1", tmp], check=True)
        with wave.open(tmp) as w:
            return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768

    def put(buf, x, t0, g=1.0):
        i = int(t0 * SR)
        if i >= n:
            return
        x = x[: n - i]
        buf[i:i + len(x)] += x * g

    voice = np.zeros(n)
    vo = load(os.path.join(HERE, "vo", "vo_raw.mp3"))
    # split the VO at the bite points and lay it on the output timeline
    cuts = [0.0] + [p for p, _, _ in INS] + [VO_DUR]
    for a, b in zip(cuts, cuts[1:]):
        put(voice, vo[int(a * SR):int(b * SR)], out_t(a + 1e-6) if a > 0 else 0.0)
    bite = np.zeros(n)
    for _, k, _, _ in BITES:
        x = load(os.path.join(FOOT, "khawaja", k + ".wav"))
        x = x / (np.abs(x).max() + 1e-6) * 0.8
        put(bite, x, K(k))

    mus = np.zeros(n)
    mus += st.section(drone(L(3)) * 0.6, 0.0, END, 0.1, 0.5)
    mus += st.section(st.pad(st.D_MINOR, END, cutoff=800) * 0.55, L(3), END, 1.0, 2.5)
    mus += st.section(st.pulse(L(13) - L(3), 92, lambda x: 0.5 + x / 60), L(3), END, 0.3, 0.6) * 0.8
    mus += st.section(st.ticker(L(13) - L(4), 92) * 0.45, L(4), END, 0.3, 0.6)
    mus += st.section(st.pulse(L(28) - L(21), 84, lambda x: 0.35), L(21), END, 0.5, 0.8) * 0.6
    mus += st.section(st.arps(st.D_MINOR, L(38) - L(28), step=0.5, gain=0.1), L(28), END, 1.0, 1.0)
    mus += st.section(st.pulse(END - L(38), 96, lambda x: 0.4 + x / 40), L(38), END, 0.3, 3.0) * 0.8
    mus += st.section(st.ticker(L(45) - L(39), 96) * 0.4, L(39), END, 0.4, 1.0)
    mus = st.norm(mus, 0.3)

    fx = np.zeros(n)
    for s in shots:
        put(fx, sfx.whoosh() * 0.22, max(0, s.t0 - 0.18))
        if s.hit == "braam":
            put(fx, braam(weight=1.1), s.t0, 0.6)
        elif s.hit == "impact":
            put(fx, sfx.impact(), s.t0 + 0.2, 0.35)
        elif s.hit == "soft":
            put(fx, sfx.heartbeat(), 0.1, 0.5)
            put(fx, sfx.heartbeat(), 1.0, 0.45)
    for _, k, _, _ in BITES:  # a tape-stop style dip into each bite
        put(fx, sfx.whoosh(0.6)[::-1] * 0.25, K(k) - 0.5)
    fx = np.tanh(fx)

    speech = voice + bite
    env = np.convolve(np.abs(speech), np.ones(int(0.3 * SR)) / int(0.3 * SR), mode="same")
    duck = 1 - 0.6 * np.clip(env / (env.max() * 0.2 + 1e-6), 0, 1)
    bduck = np.convolve((np.abs(bite) > 0.01).astype(np.float32), np.ones(int(0.5 * SR)) / int(0.5 * SR), mode="same")
    mix = voice + bite * 1.05 + mus * duck * (1 - 0.6 * np.clip(bduck * 3, 0, 1)) + fx * 0.5
    mix = np.tanh(mix * 1.05) * 0.95
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
        w.writeframes(np.repeat(pcm[:, None], 2, axis=1).tobytes())


# ----------------------------------------------------------------------------- main

def main():
    os.makedirs(OUT, exist_ok=True)
    shots = build_shots()
    print(f"total {END:.1f}s, {len(shots)} shots")
    if "--preview" in sys.argv:
        times = [s.t0 + min(1.8, (s.t1 - s.t0) * 0.7) for s in shots]
        th = []
        for t in times:
            th.append(render(shots, t, int(t * FPS)).resize((384, 216)))
            for s in shots:
                if s.media:
                    s.media.close()
                    s.media = None
                if hasattr(s, "extra"):
                    for c in s.extra.values():
                        c.close()
                    del s.extra
        cols = 5
        sheet = Image.new("RGB", (384 * cols, 216 * ((len(th) + cols - 1) // cols)), "white")
        for k, im in enumerate(th):
            sheet.paste(im, ((k % cols) * 384, (k // cols) * 216))
        sheet.save(os.path.join(OUT, "preview_sheet.jpg"), quality=88)
        print("preview written")
        return
    audio = os.path.join(OUT, "mix.wav")
    soundtrack(audio, shots)
    silent = os.path.join(OUT, "video_silent.mp4")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                          "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    total = int(END * FPS)
    for i in range(total):
        p.stdin.write(render(shots, i / FPS, i).tobytes())
        if i % 600 == 0:
            print(f"frame {i}/{total}", flush=True)
    p.stdin.close()
    p.wait()
    final = os.path.join(OUT, "Sandpaper_Sabr.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", audio, "-map", "0:v", "-map", "1:a",
                    "-c:v", "libx264", "-preset", "slow", "-b:v", "9M", "-maxrate", "12M", "-bufsize", "18M",
                    "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000", "-c:a", "aac",
                    "-b:a", "256k", "-shortest", "-movflags", "+faststart", final], check=True)
    print("LONG_DONE", final)


if __name__ == "__main__":
    main()

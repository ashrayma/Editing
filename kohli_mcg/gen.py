#!/usr/bin/env python3
"""Build the HyperFrames composition for "31 for 4: The Night Kohli Came Back" from the narration timeline.

    python3 gen.py            ->  hf_main/index.html (+ copies media into hf_main/media)
    cd hf_main && npx hyperframes render -o ../out/video_silent.mp4

Visual language (Apple-clean, theCricketLounge brand): charcoal stage, white type, #FEDE5C accent.
Real match footage plays full-bleed in the centre; B-roll cards glide in from the left or right with a slight 3D turn and a slow push-in; headlines reveal
line by line behind a mask; numbers roll like an odometer; 3D hero shots play full frame.
"""
import html
import json
import os
import shutil
import sys

from PIL import Image, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from footage import ai, clip  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "hf_main")
MEDIA = os.path.join(OUT, "media")
W, H, FPS = 1920, 1080, 30
VO_OFFSET = 0.6          # narration starts this many seconds into the film
TAIL = 5.0               # logo end card after the last line
Y = "#FEDE5C"

os.makedirs(MEDIA, exist_ok=True)
TL = json.load(open(os.path.join(HERE, "out", "vo_timeline.json")))
BEAT = {b["id"]: (b["start"] + VO_OFFSET, b["end"] + VO_OFFSET) for b in TL["beats"]}
TOTAL = round(TL["duration"] + VO_OFFSET + TAIL, 2)

els, js, EVENTS = [], [], []  # EVENTS: (time, kind) for the sound design
_n = [0]


def nid(p="e"):
    _n[0] += 1
    return f"{p}{_n[0]}"


def b(beat, off=0.0):
    """Absolute time: offset into a beat (negative offsets count back from its end)."""
    s, e = BEAT[beat]
    return round((e + off) if off < 0 else (s + off), 2)


def media(src, kind="photos"):
    """Copy a media file into the project once and return its relative path."""
    srcp = os.path.join(HERE, src)
    dst = os.path.join(MEDIA, os.path.basename(src))
    dst = os.path.join(MEDIA, src.replace("/", "_"))
    if not os.path.exists(dst) or os.path.getmtime(srcp) > os.path.getmtime(dst):
        shutil.copy(srcp, dst)
    return "media/" + os.path.basename(dst)


def img_size(src):
    with Image.open(os.path.join(HERE, src)) as im:
        return im.size


def fit(w, h, mw, mh):
    s = min(mw / w, mh / h)
    return round(w * s), round(h * s)


def add(html_, start, dur, z=10):
    els.append((start, dur, z, html_))


def anim(line):
    js.append(line)


# ----------------------------------------------------------------------------- components

def card(src, start, dur, side="right", label=None, sub=None, video=False, maxw=1080, maxh=900, z=20, kb=True, gray=False,
         media_start=0.0):
    """A media card that glides in from `side`, pushes in slowly, and exits the other way."""
    i = nid("card")
    if video:
        w, h = 1920, 1080
    else:
        w, h = img_size(src)
    cw, ch = fit(w, h, maxw, maxh)
    cx = W * (0.69 if side == "right" else 0.31) if side != "center" else W / 2
    EVENTS.append((start, "whoosh"))
    left, top = round(cx - cw / 2), round(H / 2 - ch / 2)
    rel = media(src)
    if video:
        inner = (f'<video id="{i}v" class="clip" src="{rel}" muted playsinline data-start="{start}" '
                 f'data-duration="{dur}" data-media-start="{media_start}" style="width:100%;height:100%;object-fit:cover"></video>')
    else:
        inner = f'<img id="{i}i" src="{rel}" style="width:100%;height:100%;object-fit:cover">'
    tag = ""
    if label:
        tag = (f'<div class="tag" id="{i}t"><span class="tagbar"></span><b>{html.escape(label)}</b>'
               + (f'<em>{html.escape(sub)}</em>' if sub else "") + "</div>")
    add(f'<div id="{i}" class="card clip" data-start="{start}" data-duration="{dur}" '
        f'style="left:{left}px;top:{top}px;width:{cw}px;height:{ch}px;z-index:{z}{';filter:grayscale(1) contrast(1.1)' if gray else ''}">'
        f'<div class="frame">{inner}{'<div class="tagfade"></div>' if label else ''}</div>{tag}</div>', start, dur, z)
    d = 1 if side != "left" else -1
    anim(f'tl.fromTo("#{i}",{{x:{d * 760},rotationY:{-d * 14},opacity:0}},'
         f'{{x:0,rotationY:0,opacity:1,duration:1.0,ease:"expo.out"}},{start})')
    anim(f'tl.to("#{i}",{{x:{-d * 380},opacity:0,duration:0.55,ease:"power2.in"}},{round(start + dur - 0.55, 2)})')
    if kb and not video:
        anim(f'tl.fromTo("#{i}i",{{scale:1.12}},{{scale:1.0,duration:{dur},ease:"none"}},{start})')
    if kb and video:
        anim(f'tl.fromTo("#{i}v",{{scale:1.06}},{{scale:1.0,duration:{dur},ease:"none"}},{start})')
    if label:
        anim(f'tl.fromTo("#{i}t",{{y:30,opacity:0}},{{y:0,opacity:1,duration:0.7,ease:"expo.out"}},{start + 0.45})')
    return i


def headline(lines, start, dur, side="left", size=96, accent_idx=None, y=None, align=None, sub=None, z=30):
    """Big type revealed line by line from behind a mask, with the brand's yellow bar."""
    i = nid("hl")
    size = round(size * 0.78)  # Apple-clean: generous whitespace, type a size smaller
    align = align or ("left" if side == "left" else ("right" if side == "right" else "center"))
    x = {"left": 150, "right": W - 150, "center": W / 2}[side]
    top = y if y is not None else H / 2 - (len(lines) * size * 1.08) / 2 - (30 if sub else 0)
    rows = []
    for k, ln in enumerate(lines):
        col = Y if (accent_idx is not None and k in (accent_idx if isinstance(accent_idx, (list, tuple)) else [accent_idx])) else "#fff"
        rows.append(f'<div class="mask"><div class="ln" id="{i}l{k}" style="color:{col}">{html.escape(ln)}</div></div>')
    subh = f'<div class="hsub" id="{i}s">{html.escape(sub)}</div>' if sub else ""
    pos = {"left": f"left:{x}px", "right": f"right:{W - x}px", "center": f"left:0;right:0"}[side]
    bar = f'<div class="hbar" id="{i}b"></div>' if side != "center" else ""
    add(f'<div id="{i}" class="hl clip" data-start="{start}" data-duration="{dur}" '
        f'style="{pos};top:{top}px;font-size:{size}px;text-align:{align};z-index:{z}">{bar}{"".join(rows)}{subh}</div>',
        start, dur, z)
    EVENTS.append((start + 0.1, "impact" if size >= 110 else "soft"))
    if bar:
        anim(f'tl.fromTo("#{i}b",{{scaleY:0}},{{scaleY:1,duration:0.6,ease:"expo.out"}},{start})')
    for k in range(len(lines)):
        anim(f'tl.fromTo("#{i}l{k}",{{yPercent:110}},{{yPercent:0,duration:0.9,ease:"expo.out"}},{round(start + 0.12 + 0.11 * k, 2)})')
    if sub:
        anim(f'tl.fromTo("#{i}s",{{opacity:0,y:16}},{{opacity:1,y:0,duration:0.8,ease:"expo.out"}},{round(start + 0.35 + 0.11 * len(lines), 2)})')
    anim(f'tl.to("#{i}",{{opacity:0,y:-20,duration:0.45,ease:"power2.in"}},{round(start + dur - 0.45, 2)})')
    return i


def odometer(text, start, dur, side="left", size=230, label=None, color=Y, roll=1.4, y=None, z=30):
    """A number that rolls into place digit by digit (Apple-style), with a small label under it."""
    i = nid("od")
    size = round(size * 0.75)
    EVENTS.append((start + 0.1, "roll"))
    x = {"left": 150, "right": W - 150, "center": W / 2}[side]
    cols = []
    for k, ch in enumerate(text):
        if ch.isdigit():
            strip = "".join(f"<span>{d}</span>" for d in "0123456789")
            cols.append(f'<span class="dcol"><span class="dstrip" id="{i}d{k}">{strip}</span></span>')
            anim(f'tl.fromTo("#{i}d{k}",{{yPercent:0}},{{yPercent:{-int(ch) * 10},duration:{roll + 0.12 * k},'
                 f'ease:"expo.out"}},{start + 0.1})')
        else:
            cols.append(f'<span class="dchar">{html.escape(ch)}</span>')
    pos = {"left": f"left:{x}px", "right": f"right:{W - x}px", "center": "left:0;right:0;text-align:center"}[side]
    top = y if y is not None else H / 2 - size * 0.62
    lab = f'<div class="olab" id="{i}lab">{html.escape(label)}</div>' if label else ""
    add(f'<div id="{i}" class="odo clip" data-start="{start}" data-duration="{dur}" '
        f'style="{pos};top:{top}px;font-size:{size}px;color:{color};z-index:{z}">'
        f'<div class="digits">{"".join(cols)}</div>{lab}</div>', start, dur, z)
    anim(f'tl.fromTo("#{i}",{{opacity:0,scale:0.96}},{{opacity:1,scale:1,duration:0.5,ease:"power2.out"}},{start})')
    if label:
        anim(f'tl.fromTo("#{i}lab",{{opacity:0,y:14}},{{opacity:1,y:0,duration:0.7,ease:"expo.out"}},{start + 0.6})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.45,ease:"power2.in"}},{round(start + dur - 0.45, 2)})')
    return i


def pills(items, start, dur, side="left", y=None, gap=0.45, z=30):
    """Stacked rounded chips that pop in one after another."""
    i = nid("pl")
    x = {"left": 150, "right": W - 150}[side]
    pos = f"left:{x}px" if side == "left" else f"right:{W - x}px"
    top = y if y is not None else H / 2 - len(items) * 52
    rows = "".join(f'<div class="pill" id="{i}p{k}"><span class="dot"></span>{t}</div>' for k, t in enumerate(items))
    add(f'<div id="{i}" class="pills clip" data-start="{start}" data-duration="{dur}" style="{pos};top:{top}px;'
        f'align-items:{"flex-start" if side == "left" else "flex-end"};z-index:{z}">{rows}</div>', start, dur, z)
    for k in range(len(items)):
        EVENTS.append((round(start + gap * k, 2), "pop"))
        anim(f'tl.fromTo("#{i}p{k}",{{x:{-60 if side == "left" else 60},opacity:0}},{{x:0,opacity:1,duration:0.7,'
             f'ease:"expo.out"}},{round(start + gap * k, 2)})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.45}},{round(start + dur - 0.45, 2)})')
    return i


def full_video(src, start, dur, z=40, fade=0.35):
    i = nid("fv")
    EVENTS.append((start, "hit"))
    add(f'<video id="{i}" class="full clip" src="{media(src)}" muted playsinline data-start="{start}" '
        f'data-duration="{dur}" data-media-start="0" style="z-index:{z}"></video>', start, dur, z)
    anim(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:{fade}}},{start})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:{fade}}},{round(start + dur - fade, 2)})')
    return i


def phone(src, start, dur, side="right", z=25, media_start=0.0):
    """The scorecard screen recording inside a clean phone frame."""
    i = nid("ph")
    EVENTS.append((start, "whoosh"))
    cx = W * (0.7 if side == "right" else 0.3)
    pw, ph_ = 380, 822
    add(f'<div id="{i}" class="phone clip" data-start="{start}" data-duration="{dur}" '
        f'style="left:{round(cx - pw / 2)}px;top:{round(H / 2 - ph_ / 2)}px;width:{pw}px;height:{ph_}px;z-index:{z}">'
        f'<video class="clip" src="{media(src)}" muted playsinline data-start="{start}" data-duration="{dur}" '
        f'data-media-start="{media_start}"></video></div>', start, dur, z)
    d = 1 if side == "right" else -1
    anim(f'tl.fromTo("#{i}",{{y:900,rotationX:18,opacity:0}},{{y:0,rotationX:0,opacity:1,duration:1.1,ease:"expo.out"}},{start})')
    anim(f'tl.to("#{i}",{{y:700,opacity:0,duration:0.55,ease:"power2.in"}},{round(start + dur - 0.55, 2)})')
    return i


def timeline_graphic(nodes, start, dur, z=30):
    """1999 -> 2003: a horizontal line drawing across with years lighting up on cue."""
    i = nid("tg")
    n = len(nodes)
    x0, x1 = 230, W - 230
    parts = [f'<div class="tline" id="{i}line"></div>']
    for k, (year, label, t) in enumerate(nodes):
        x = x0 + (x1 - x0) * k / (n - 1)
        parts.append(f'<div class="tnode" id="{i}n{k}" style="left:{x}px"><div class="tdot"></div>'
                     f'<div class="tyear">{year}</div><div class="tlab">{html.escape(label)}</div></div>')
        anim(f'tl.fromTo("#{i}n{k}",{{opacity:0.18,y:12}},{{opacity:1,y:0,duration:0.7,ease:"expo.out"}},{t})')
        anim(f'tl.fromTo("#{i}n{k} .tdot",{{scale:0.5,backgroundColor:"#555"}},{{scale:1,backgroundColor:"{Y}",'
             f'duration:0.5,ease:"back.out(3)"}},{t})')
    add(f'<div id="{i}" class="tgraph clip" data-start="{start}" data-duration="{dur}" style="z-index:{z}">'
        + "".join(parts) + "</div>", start, dur, z)
    anim(f'tl.fromTo("#{i}line",{{scaleX:0}},{{scaleX:1,duration:{nodes[-1][2] - start + 0.5},ease:"power1.inOut"}},{start})')
    anim(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.5}},{start})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.5}},{round(start + dur - 0.5, 2)})')


def chapter(num, title, start, dur=4.5):
    i = nid("ch")
    EVENTS.append((start, "swell"))
    add(f'<div id="{i}" class="chapter clip" data-start="{start}" data-duration="{dur}">'
        f'<span class="chnum">{num}</span><span class="chbar"></span><span class="chtitle">{html.escape(title)}</span></div>',
        start, dur, 60)
    anim(f'tl.fromTo("#{i}",{{opacity:0,x:-30}},{{opacity:1,x:0,duration:0.8,ease:"expo.out"}},{start})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.6}},{round(start + dur - 0.6, 2)})')


def backdrop(src, start, dur, opacity=0.28, z=2):
    """A blurred, darkened copy of a photo filling the frame behind a card (pre-blurred: cheap to render)."""
    i = nid("bd")
    p = os.path.join(HERE, src)
    out = os.path.join(MEDIA, "bd_" + os.path.basename(src).rsplit(".", 1)[0] + ".jpg")
    if not os.path.exists(out):
        im = Image.open(p).convert("RGB")
        s = max(W / im.width, H / im.height) * 1.15
        im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1))
        x, y_ = (im.width - W) // 2, (im.height - H) // 2
        im.crop((x, y_, x + W, y_ + H)).filter(ImageFilter.GaussianBlur(40)).save(out, quality=88)
    add(f'<img id="{i}" class="full clip" src="media/{os.path.basename(out)}" data-start="{start}" '
        f'data-duration="{dur}" style="z-index:{z}">', start, dur, z)
    anim(f'tl.fromTo("#{i}",{{opacity:0,scale:1.08}},{{opacity:{opacity},scale:1,duration:{dur},ease:"none"}},{start})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.6}},{round(start + dur - 0.6, 2)})')


def fullimg(src, start, dur, dim=0.35, ai=True, z=8, push=1.10, origin="50% 50%", end=1.0):
    """Full-bleed image with a slow push-in, darkened for type on top; AI images carry a small disclosure tag."""
    i = nid("fi")
    EVENTS.append((start, "whoosh"))
    tag = '<div class="aitag">AI illustration</div>' if ai else ""
    add(f'<div id="{i}" class="full clip" data-start="{start}" data-duration="{dur}" style="z-index:{z};overflow:hidden">'
        f'<img id="{i}i" src="{media(src)}" style="width:100%;height:100%;object-fit:cover;transform-origin:{origin}">'
        f'<div class="full" style="background:rgba(5,5,6,{dim})"></div>{tag}</div>', start, dur, z)
    anim(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.6,ease:"power2.out"}},{start})')
    anim(f'tl.fromTo("#{i}i",{{scale:{push}}},{{scale:{end},duration:{dur},ease:"none"}},{start})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.5}},{round(start + dur - 0.5, 2)})')


def stage(start, dur, z=40):
    """A full-frame dark stage for the hero moments (fades in and out)."""
    i = nid("st")
    EVENTS.append((start, "hit"))
    anim(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.3}},{start})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.35}},{round(start + dur - 0.35, 2)})')
    return i


def big98(start, dur, z=40):
    """Gold, extruded '98' rising into place in perspective; underline draws; soft reflection."""
    i = stage(start, dur, z)
    depth = ",".join(f"0 {k}px 0 #6b4c0c" for k in range(1, 16)) + ",0 40px 60px rgba(0,0,0,.7)"
    add(f'<div id="{i}" class="stage clip" data-start="{start}" data-duration="{dur}" style="z-index:{z}">'
        f'<div class="persp"><div class="n98" id="{i}n"><span class="back" style="text-shadow:{depth}">98</span>'
        f'<span class="gold">98</span></div>'
        f'<div class="n98 refl" id="{i}r"><span class="gold">98</span></div></div>'
        f'<div class="uline" id="{i}u"></div></div>', start, dur, z)
    anim(f'tl.fromTo("#{i}n",{{y:260,rotationX:55,opacity:0}},{{y:0,rotationX:0,opacity:1,duration:1.3,ease:"expo.out"}},{start + 0.1})')
    anim(f'tl.fromTo("#{i}r",{{opacity:0}},{{opacity:0.22,duration:1.2}},{start + 0.5})')
    anim(f'tl.fromTo("#{i}n",{{rotationY:-10}},{{rotationY:8,duration:{dur},ease:"sine.inOut"}},{start})')
    anim(f'tl.fromTo("#{i}u",{{scaleX:0}},{{scaleX:1,duration:0.9,ease:"expo.out"}},{start + 0.9})')


def date_card(start, dur, z=40):
    i = stage(start, dur, z)
    add(f'<div id="{i}" class="stage clip" data-start="{start}" data-duration="{dur}" style="z-index:{z}">'
        f'<div class="persp datewrap" id="{i}w"><div class="dbar" id="{i}b"></div>'
        f'<div class="dl1" id="{i}a">1 MARCH</div><div class="dl2" id="{i}c">2003</div></div></div>', start, dur, z)
    anim(f'tl.fromTo("#{i}b",{{scaleY:0}},{{scaleY:1,duration:0.6,ease:"expo.out"}},{start + 0.05})')
    anim(f'tl.fromTo("#{i}a",{{rotationX:-95,opacity:0}},{{rotationX:0,opacity:1,duration:1.0,ease:"expo.out"}},{start + 0.25})')
    anim(f'tl.fromTo("#{i}c",{{rotationX:-95,opacity:0}},{{rotationX:0,opacity:1,duration:1.0,ease:"expo.out"}},{start + 0.45})')
    anim(f'tl.fromTo("#{i}w",{{scale:1}},{{scale:1.05,duration:{dur},ease:"none"}},{start})')


def logo_sting(start, dur, end=False, z=45):
    i = stage(start, dur, z)
    foot = '<div class="lfoot" id="{0}f">Follow for more cricket stories</div>'.format(i) if end else ""
    add(f'<div id="{i}" class="stage clip" data-start="{start}" data-duration="{dur}" style="z-index:{z}">'
        f'<img class="lbig" id="{i}l" src="media/logo.png"><div class="lsweep" id="{i}s"></div>{foot}</div>', start, dur, z)
    anim(f'tl.fromTo("#{i}l",{{clipPath:"inset(0% 100% 0% 0%)",scale:0.96}},{{clipPath:"inset(0% 0% 0% 0%)",scale:1,'
         f'duration:1.1,ease:"expo.inOut"}},{start + 0.15})')
    anim(f'tl.fromTo("#{i}s",{{x:-900,opacity:0.0}},{{x:900,opacity:0.9,duration:1.4,ease:"power2.inOut"}},{start + 0.6})')
    anim(f'tl.to("#{i}s",{{opacity:0,duration:0.3}},{start + 1.9})')
    if end:
        anim(f'tl.fromTo("#{i}f",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.8,ease:"expo.out"}},{start + 1.2})')


# ----------------------------------------------------------------------------- new components (31 for 4)

def pre(beat, off):
    """Absolute time `off` seconds before a beat starts (b() with a negative offset counts back from the END)."""
    return round(BEAT[beat][0] - off, 2)


def D(beat):
    s, e = BEAT[beat]
    return round(e - s, 2)


def till_end(beat, off, pad=0.2):
    """Duration from b(beat, off) to the end of the beat (+pad)."""
    return round(BEAT[beat][1] - b(beat, off) + pad, 2)


def hero(src, start, dur, dim=0.3, z=5, gray=False, push=1.08, media_start=0.0, fade=0.35):
    """Real match footage, full-bleed in the centre of the frame, slow push-in, darkened for type on top."""
    i = nid("hv")
    EVENTS.append((start, "cut"))
    filt = "filter:grayscale(1) contrast(1.12);" if gray else ""
    add(f'<div id="{i}" class="full clip" data-start="{start}" data-duration="{dur}" style="z-index:{z};overflow:hidden;{filt}">'
        f'<video id="{i}v" class="clip" src="{media(src)}" muted playsinline data-start="{start}" data-duration="{dur}" '
        f'data-media-start="{media_start}" style="width:100%;height:100%;object-fit:cover"></video>'
        f'<div class="full" style="background:rgba(5,5,6,{dim})"></div></div>', start, dur, z)
    anim(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:{fade}}},{start})')
    anim(f'tl.fromTo("#{i}v",{{scale:{push}}},{{scale:1.0,duration:{dur},ease:"none"}},{start})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:{fade}}},{round(start + dur - fade, 2)})')
    return i


def ytag(text, start, dur):
    """Top-left date tag (the reference film's running year marker), in the brand yellow."""
    i = nid("yt")
    add(f'<div id="{i}" class="ytag clip" data-start="{start}" data-duration="{dur}">{html.escape(text)}</div>', start, dur, 85)
    anim(f'tl.fromTo("#{i}",{{clipPath:"inset(0% 100% 0% 0%)"}},{{clipPath:"inset(0% 0% 0% 0%)",duration:0.6,ease:"expo.out"}},{start})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.3}},{round(start + dur - 0.3, 2)})')


def blackout(start, dur, z=35):
    i = nid("bo")
    add(f'<div id="{i}" class="stage clip" data-start="{start}" data-duration="{dur}" style="z-index:{z}"></div>', start, dur, z)
    anim(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.25}},{start})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.3}},{round(start + dur - 0.3, 2)})')


def ecg(start, dur, flat_after=None, color="#ff453a", y=800, z=50):
    """A heartbeat line drawing across the frame; with flat_after (seconds) the beats stop and it flatlines."""
    i = nid("ecg")
    pts, x, k = [], 0, 0
    period = 300
    draw = dur * 0.85
    while x <= W:
        t = start + draw * x / W
        alive = flat_after is None or t < start + flat_after
        pts.append(f"{x},100")
        if alive and x > 80:
            pts += [f"{x + 30},100", f"{x + 45},40", f"{x + 60},170", f"{x + 75},10", f"{x + 92},120", f"{x + 110},100"]
            EVENTS.append((round(t, 2), "heartbeat"))
        x += period
        k += 1
    if flat_after is not None:
        EVENTS.append((round(start + flat_after, 2), "flatline"))
    add(f'<svg id="{i}" class="ecg clip" data-start="{start}" data-duration="{dur}" viewBox="0 0 {W} 200" '
        f'style="top:{y}px;z-index:{z}"><polyline points="{" ".join(pts)}" pathLength="1" '
        f'style="fill:none;stroke:{color};stroke-width:4;stroke-dasharray:1;stroke-dashoffset:1;'
        f'filter:drop-shadow(0 0 10px {color})"/></svg>', start, dur, z)
    anim(f'tl.fromTo("#{i} polyline",{{strokeDashoffset:1}},{{strokeDashoffset:0,duration:{draw},ease:"none"}},{start})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.4}},{round(start + dur - 0.4, 2)})')


def rewind(start, dur, to_year="2019", z=75):
    """VHS-style rewind: the frame drains to grey, scanlines roll, '◀◀ 2022 → 2019'."""
    i = nid("rw")
    EVENTS.append((start, "rewind"))
    add(f'<div id="{i}" class="rewind clip" data-start="{start}" data-duration="{dur}" style="z-index:{z}">'
        f'<div class="rwlines" id="{i}l"></div><div class="rwtag">◀◀ REWIND</div>'
        f'<div class="rwyear" id="{i}y">{to_year}</div></div>', start, dur, z)
    anim(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.2}},{start})')
    anim(f'tl.fromTo("#{i}l",{{backgroundPositionY:"0px"}},{{backgroundPositionY:"-600px",duration:{dur},ease:"none"}},{start})')
    anim(f'tl.fromTo("#{i}y",{{scale:1.6,opacity:0}},{{scale:1,opacity:1,duration:0.7,ease:"expo.out"}},{round(start + dur * 0.35, 2)})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.25}},{round(start + dur - 0.25, 2)})')


def tracker(title, balls, start, dur, z=60):
    """Ball-by-ball chips along the bottom: each ball pops in on its moment (W red, six yellow, extras grey)."""
    i = nid("tr")
    chips = []
    for k, (lab, kind, t) in enumerate(balls):
        chips.append(f'<div class="chip {kind}" id="{i}c{k}">{html.escape(lab)}</div>')
        EVENTS.append((round(t, 2), "chip_" + kind))
        anim(f'tl.fromTo("#{i}c{k}",{{scale:0.2,opacity:0}},{{scale:1,opacity:1,duration:0.55,ease:"back.out(2.6)"}},{round(t, 2)})')
    add(f'<div id="{i}" class="tracker clip" data-start="{start}" data-duration="{dur}" style="z-index:{z}">'
        f'<div class="trtitle">{html.escape(title)}</div><div class="trrow">{"".join(chips)}</div></div>', start, dur, z)
    anim(f'tl.fromTo("#{i}",{{y:60,opacity:0}},{{y:0,opacity:1,duration:0.7,ease:"expo.out"}},{start})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.4}},{round(start + dur - 0.4, 2)})')


def need(steps, end, z=62):
    """Top-right 'NEED x OFF y' pill that updates on each moment: steps = [(time, html), ...]."""
    for k, (t, txt) in enumerate(steps):
        i = nid("nd")
        t2 = steps[k + 1][0] if k + 1 < len(steps) else end
        add(f'<div id="{i}" class="need clip" data-start="{t}" data-duration="{round(t2 - t, 2)}" style="z-index:{z}">{txt}</div>',
            t, round(t2 - t, 2), z)
        anim(f'tl.fromTo("#{i}",{{y:-14,opacity:0}},{{y:0,opacity:1,duration:0.4,ease:"expo.out"}},{t})')


# ----------------------------------------------------------------------------- the film

def shot(name):
    """A rendered 3D shot, or (until blender/render_all.sh has made it) a dark stand-in so the edit still builds."""
    real = os.path.join("blender", "renders", name + ".mp4")
    if os.path.exists(os.path.join(HERE, real)):
        return real
    stub = os.path.join("footage", "placeholders", "3d_" + name + ".mp4")
    if not os.path.exists(os.path.join(HERE, stub)):
        import subprocess
        os.makedirs(os.path.join(HERE, "footage", "placeholders"), exist_ok=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=0x101012:s=1920x1080:r=30:d=4",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", os.path.join(HERE, stub)], check=True)
    return stub

SHOT = "assets/photos/screenshot_drought.png"
REC = "footage/screenrec_match_centre.mp4"

# COLD OPEN: tease the Rauf over, cut away before the ball lands
ytag("MCG · 23 OCT 2022", 0.0, BEAT["open_tease"][1])
hero(clip("F01"), 0.0, b("open_tease", 0.0) + 0.3, dim=0.35, fade=0.01)
headline(["8 balls.", "28 runs."], 0.25, D("open_equation") + 0.6, "left", size=150, accent_idx=1)
card(clip("F02"), b("open_rauf", 0.0), D("open_rauf") + 0.3, "right", "HARIS RAUF", "3 overs · 21 runs · 2 wickets", video=True)
odometer("21", b("open_rauf", 0.5), D("open_rauf") - 0.3, "left", size=280, label="RUNS IN 3 OVERS")
hero(clip("F16"), b("open_tease", 0.0), 4.8, dim=0.25, media_start=0.0)
headline(["“The shot of", "the century.”"], b("open_tease", 0.4), 4.2, "center", size=120, accent_idx=1)
rewind(b("open_tease", 4.9), till_end("open_tease", 4.9, 0.0) - 0.4, "2019")
full_video(shot("ball"), round(BEAT["open_tease"][1] - 0.45, 2), 0.85, z=78, fade=0.05)
blackout(round(BEAT["open_tease"][1] + 0.35, 2), 2.9, z=70)
headline(["31 for 4"], round(BEAT["open_tease"][1] + 0.45, 2), 2.7, "center", size=210, accent_idx=0, z=72,
         sub="The night Kohli came back")

# 01 THE SILENCE (grey: the drought years)
chapter("01", "The Silence", b("drought_70", 0.0))
ytag("NOV 2019", b("drought_70", 0.0), D("drought_70"))
card(clip("F03"), b("drought_70", 0.0), D("drought_70") * 0.6, "right", "CENTURY NO. 70", "vs Bangladesh · Kolkata", video=True)
headline(["Century", "No. 70"], b("drought_70", 0.2), D("drought_70") * 0.6 - 0.2, "left", size=130, accent_idx=1)
fullimg(ai("ai_lonely_bat"), b("drought_70", D("drought_70") * 0.6), till_end("drought_70", D("drought_70") * 0.6, 0.3), dim=0.35)
ecg(b("drought_70", D("drought_70") * 0.6), till_end("drought_70", D("drought_70") * 0.6, 0.3), flat_after=1.2, color="#ff453a")
full_video(shot("days1020"), pre("drought_days", 0.1), D("drought_days") + 0.4)
ytag("2019 → 2022", b("drought_capt", 0.0), D("drought_capt") + D("drought_voices") + 0.9)
pills(["T20I captaincy · <b>gave up</b>", "Test captaincy · <b>gave up</b>", "Dubai 2021 · lost by <b>10 wickets</b>"],
      b("drought_capt", 0.2), D("drought_capt"), "left", gap=D("drought_capt") / 3.4)
card(clip("F05"), b("drought_capt", 0.0), D("drought_capt") * 0.55, "right", video=True, gray=True)
card(clip("F04"), b("drought_capt", D("drought_capt") * 0.55), till_end("drought_capt", D("drought_capt") * 0.55),
     "right", "T20 WORLD CUP 2021 · DUBAI", "Pakistan win by 10 wickets", video=True, gray=True)
hero(clip("F05"), pre("drought_voices", 0.1), D("drought_voices") + 0.4, dim=0.55, gray=True, media_start=4.0)
headline(["“Kohli is finished.”"], b("drought_voices", 0.1), D("drought_voices"), "center", size=120, accent_idx=0)
ytag("SEP 2022 · DUBAI", b("comeback_71", 0.0), D("comeback_71"))
card(SHOT, b("comeback_71", 0.0), D("comeback_71") * 0.42, "left", "SCREENSHOT", "From 70 to 71", maxw=880)
card(clip("F06"), b("comeback_71", 0.0), D("comeback_71") * 0.55, "right", "CENTURY NO. 71", "122* vs Afghanistan", video=True)
headline(["The real test", "was still to come."], b("comeback_71", D("comeback_71") * 0.55), till_end("comeback_71", D("comeback_71") * 0.55, 0),
         "center", size=110, accent_idx=1)

# 02 THE STAGE
chapter("02", "The Stage", b("mcg", 0.0))
ytag("MCG · 23 OCT 2022", b("mcg", 0.0), BEAT["target"][1] - BEAT["mcg"][0])
fullimg(ai("ai_stadium_night"), b("mcg", 0.0), D("mcg") * 0.5, dim=0.3)
headline(["Melbourne", "Cricket Ground"], b("mcg", 0.3), D("mcg") * 0.5 - 0.3, "left", size=120, accent_idx=1)
hero(clip("F07"), b("mcg", D("mcg") * 0.5), till_end("mcg", D("mcg") * 0.5), dim=0.4)
odometer("90,293", b("mcg", D("mcg") * 0.5 + 0.2), till_end("mcg", D("mcg") * 0.5 + 0.2, 0), "left", size=230, label="IN THE STANDS")
card(clip("F08"), b("pak_innings", 0.0), D("pak_innings") * 0.5, "right", "BABAR AZAM · LBW b ARSHDEEP", "First ball. 0", video=True)
card(clip("F09"), b("pak_innings", D("pak_innings") * 0.5), till_end("pak_innings", D("pak_innings") * 0.5), "right",
     "IFTIKHAR 51 · MASOOD 52*", "Pakistan 159/8", video=True)
pills(["Babar · <b>0</b>", "Rizwan · <b>4</b>", "Iftikhar · <b>51</b>", "Masood · <b>52*</b>"], b("pak_innings", 0.4),
      D("pak_innings"), "left", gap=D("pak_innings") / 4.5)
blackout(pre("target", 0.1), D("target") + 0.4)
odometer("160", b("target", 0.0), D("target") + 0.2, "left", size=300, label="TARGET", z=40)
headline(["Shaheen.", "Naseem.", "Rauf."], b("target", 0.8), D("target") - 0.6, "right", size=96, accent_idx=2, z=40)

# 03 31 FOR 4
chapter("03", "31 for 4", b("collapse", 0.0))
q = D("collapse") / 4
for k, (fid, who) in enumerate([("F10", "KL RAHUL · 4"), ("F11", "ROHIT SHARMA · 4"), ("F12", "SURYAKUMAR · 15"), ("F13", "AXAR PATEL · RUN OUT")]):
    hero(clip(fid), b("collapse", q * k), q + 0.15, dim=0.2, fade=0.12)
    card(clip(fid), b("collapse", q * k + 0.05), q, "left" if k % 2 else "right", who, video=True, maxw=760)
full_video(shot("score314"), pre("31_4", 0.15), D("31_4") + 0.5)
hero(clip("F14"), b("silence", 0.0), D("silence") + 0.3, dim=0.45, gray=True)
headline(["Half the stadium", "went silent."], b("silence", 0.3), D("silence") * 0.5, "left", size=100, accent_idx=1)
ecg(b("silence", D("silence") * 0.5), till_end("silence", D("silence") * 0.5, 0.3), color="#ff453a", y=760)
blackout(pre("rehook_2", 0.1), D("rehook_2") + 0.4)
headline(["The real drama", "hadn't even begun."], b("rehook_2", 0.0), D("rehook_2") + 0.2, "center", size=110, accent_idx=1, z=40)

# 04 THE PLAN
chapter("04", "The Plan", b("hardik", 0.0))
card(clip("F14"), b("hardik", 0.0), D("hardik") + D("asking_rate") + 0.6, "right", "KOHLI × PANDYA", "Take it deep", video=True)
headline(["Don't lose", "a wicket."], b("hardik", 0.3), D("hardik"), "left", size=120, accent_idx=1)
odometer("45/4", b("asking_rate", 0.0), D("asking_rate") + 0.2, "left", size=240, label="AFTER 10 OVERS", color="#fff")
card(clip("F15"), b("eighteen", 0.0), D("eighteen") + 0.3, "right", "SHAHEEN AFRIDI · OVER 18", "17 runs", video=True)
odometer("48", b("eighteen", 0.2), D("eighteen") * 0.55, "left", size=260, label="NEEDED OFF 18 BALLS")
odometer("17", b("eighteen", D("eighteen") * 0.6), till_end("eighteen", D("eighteen") * 0.6, 0), "left", size=260, label="RUNS OFF OVER 18")
blackout(pre("equation_12", 0.1), D("equation_12") + 0.4)
odometer("31", b("equation_12", 0.0), D("equation_12") + 0.2, "center", size=340, label="OFF 12 BALLS", z=40)

# 05 28 OFF 8
chapter("05", "28 off 8", b("rauf_over", 0.0))
hero(clip("F01"), b("rauf_over", 0.0), D("rauf_over") * 0.45, dim=0.3, media_start=3.0)
headline(["Over 19.", "Haris Rauf."], b("rauf_over", 0.2), D("rauf_over") * 0.45 - 0.2, "left", size=120, accent_idx=1)
full_video(shot("eight28"), b("rauf_over", D("rauf_over") * 0.45), till_end("rauf_over", D("rauf_over") * 0.45, 0.3))
fullimg(ai("ai_tv_off"), pre("tv_off", 0.1), D("tv_off") + 0.4, dim=0.15)
hero(clip("F16"), b("six_one", 0.0), D("six_one") + 0.3, dim=0.1)
odometer("6", b("six_one", D("six_one") * 0.72), till_end("six_one", D("six_one") * 0.72, 0), "right", size=380, label="STRAIGHT DOWN THE GROUND")
card(clip("F16"), b("six_one_why", 0.0), D("six_one_why") + 0.3, "right", "THE REPLAY", "Back foot · straight bat", video=True, media_start=6.0)
headline(["No slog.", "No swing.", "Just a straight bat."], b("six_one_why", 0.2), D("six_one_why"), "left", size=86, accent_idx=2)
hero(clip("F17"), b("six_two", 0.0), D("six_two") + 0.3, dim=0.1)
odometer("6", b("six_two", D("six_two") * 0.6), till_end("six_two", D("six_two") * 0.6, 0), "left", size=380, label="OVER FINE LEG")
blackout(pre("equation_6", 0.1), D("equation_6") + 0.4)
odometer("16", b("equation_6", 0.0), D("equation_6") + 0.2, "center", size=340, label="OFF 6 BALLS", z=40)

# 06 THE LAST OVER: ball-by-ball tracker + the equation updating top-right
chapter("06", "The Last Over", b("nawaz", 0.0))
L0, L1 = b("nawaz", 0.0), BEAT["ashwin"][1] + 0.3
nb, fh, dk, ash = D("nawaz"), D("free_hit"), D("dk_out"), D("ashwin")
balls = [("W", "w", b("nawaz", nb * 0.38)), ("1", "n", b("nawaz", nb * 0.62)), ("2", "n", b("nawaz", nb * 0.85)),
         ("6nb", "six", b("no_ball", D("no_ball") * 0.4)), ("wd", "x", b("free_hit", fh * 0.05)),
         ("3b", "x", b("free_hit", fh * 0.75)), ("W", "w", b("dk_out", dk * 0.15)), ("wd", "x", b("ashwin", ash * 0.3)),
         ("1", "win", b("ashwin", ash * 0.8))]
tracker("OVER 20 · MOHAMMAD NAWAZ", balls, L0, L1 - L0)
need([(L0, "NEED <b>16</b> OFF 6"), (balls[0][2], "NEED <b>16</b> OFF 5"), (balls[1][2], "NEED <b>15</b> OFF 4"),
      (balls[2][2], "NEED <b>13</b> OFF 3"), (balls[3][2], "NEED <b>6</b> OFF 3 · FREE HIT"), (balls[4][2], "NEED <b>5</b> OFF 3 · FREE HIT"),
      (balls[5][2], "NEED <b>2</b> OFF 2"), (balls[6][2], "NEED <b>2</b> OFF 1"), (balls[7][2], "NEED <b>1</b> OFF 1"),
      (balls[8][2], "<b>INDIA WIN</b>")], L1)
card(clip("F18"), b("nawaz", 0.0), D("nawaz") + 0.3, "right", "HARDIK · c BABAR b NAWAZ", "40 off 37", video=True)
headline(["Last over.", "16 to win."], b("nawaz", 0.2), D("nawaz") * 0.55, "left", size=110, accent_idx=1)
hero(clip("F19"), b("no_ball", 0.0), D("no_ball") + 0.3, dim=0.15)
headline(["NO-BALL!"], b("no_ball", D("no_ball") * 0.62), till_end("no_ball", D("no_ball") * 0.62, 0), "left", size=170, accent_idx=0)
card(clip("F20"), b("free_hit", 0.0), D("free_hit") + 0.3, "right", "FREE HIT", "Bowled, but not out · 3 byes", video=True)
pills(["Free hit", "Bowled · <b>not out</b>", "Ran <b>3 byes</b>"], b("free_hit", fh * 0.2), fh * 0.85, "left", gap=fh * 0.22)
card(clip("F21"), b("dk_out", 0.0), D("dk_out") + 0.3, "left", "DINESH KARTHIK · STUMPED", video=True)
hero(clip("F22"), b("ashwin", 0.0), D("ashwin") + 0.6, dim=0.15)
headline(["INDIA WIN!"], b("ashwin", ash * 0.82), till_end("ashwin", ash * 0.82, 0.4), "center", size=190, accent_idx=0, z=55)

# 07 THE ANSWER (end within 40 s of the win)
chapter("07", "The Answer", b("punch", 0.0))
hero(clip("F23"), b("punch", 0.0), D("punch") * 0.5, dim=0.15)
card(clip("F24"), b("punch", D("punch") * 0.45), till_end("punch", D("punch") * 0.45), "right", "ROHIT LIFTS KOHLI", video=True)
headline(["On Rohit's", "shoulders."], b("punch", D("punch") * 0.5), till_end("punch", D("punch") * 0.5, 0), "left", size=110, accent_idx=1)
full_video(shot("hero82"), pre("82", 0.1), 3.1)
phone(REC, b("82", 3.0), till_end("82", 3.0, 0.3), "right", media_start=0.0)
headline(["82* off 53.", "When it looked over."], b("82", 3.2), till_end("82", 3.2, 0), "left", size=96, accent_idx=1)
card(clip("F25"), b("own_words", 0.0), D("own_words") + 0.3, "right", "VIRAT KOHLI", "After the match", video=True)
headline(["Mohali used to be", "his best innings.", "Not anymore."], b("own_words", 0.4), D("own_words"), "left", size=86, accent_idx=2)
hero(clip("F23"), b("close", 0.0), D("close") + 0.3, dim=0.5, media_start=2.0)
headline(["1,020 days of questions.", "One night. One answer."], b("close", 0.3), D("close"), "center", size=96, accent_idx=1)
blackout(pre("cta", 0.1), D("cta") + 0.4)
headline(["MCG or Mohali?"], b("cta", 0.1), D("cta") + 0.1, "center", size=140, accent_idx=0, z=40,
         sub="Comment below · Next story: Hobart 2012")
logo_sting(round(BEAT["cta"][1] + 0.3, 2), TOTAL - BEAT["cta"][1] - 0.3, end=True)

CSS = f"""
html,body{{margin:0;background:#060607}}
#root{{position:relative;width:{W}px;height:{H}px;overflow:hidden;background:#0a0a0b;
  font-family:"Inter Display","Inter",system-ui,sans-serif;perspective:1600px}}
.bg{{position:absolute;inset:0;background:radial-gradient(120% 90% at 50% 40%,#1b1b1e 0%,#0b0b0c 55%,#050506 100%)}}
.glow{{position:absolute;width:1400px;height:1400px;left:-200px;top:-500px;border-radius:50%;
  background:radial-gradient(circle,rgba(254,222,92,0.10),rgba(254,222,92,0) 60%)}}
.grain{{position:absolute;inset:0;opacity:.07;mix-blend-mode:overlay;background-image:url(media/grain.png)}}
.vig{{position:absolute;inset:0;background:radial-gradient(ellipse at center,rgba(0,0,0,0) 55%,rgba(0,0,0,.55) 100%);z-index:90;pointer-events:none}}
.full{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}
.card{{position:absolute;transform-style:preserve-3d}}
.card .frame{{width:100%;height:100%;border-radius:30px;overflow:hidden;
  box-shadow:0 50px 110px rgba(0,0,0,.65),0 0 0 1px rgba(255,255,255,.08)}}
.tagfade{{position:absolute;left:0;right:0;bottom:0;height:160px;background:linear-gradient(0deg,rgba(0,0,0,.75),rgba(0,0,0,0))}}
.card .frame{{position:relative}}
.tag{{position:absolute;left:30px;bottom:26px;display:flex;align-items:center;gap:14px;color:#fff;white-space:nowrap}}
.tag b{{font-weight:800;font-size:23px;letter-spacing:2px}}
.tag em{{font-style:normal;font-weight:500;font-size:20px;color:rgba(255,255,255,.62)}}
.tagbar{{width:6px;height:34px;background:{Y};border-radius:3px}}
.hl{{position:absolute;font-weight:800;letter-spacing:-0.03em;line-height:1.04;color:#fff}}
.hl .mask{{overflow:hidden;padding-bottom:.06em}}
.hl .ln{{display:block}}
.hbar{{position:absolute;left:-46px;top:.08em;width:10px;height:calc(100% - .16em);background:{Y};border-radius:5px;transform-origin:top}}
.hsub{{font-size:28px;font-weight:500;letter-spacing:0;color:rgba(255,255,255,.66);margin-top:22px}}
.odo{{position:absolute;font-weight:800;letter-spacing:-0.04em;line-height:1}}
.digits{{display:inline-flex}}
.dcol{{display:inline-block;height:1em;overflow:hidden}}
.dstrip{{display:flex;flex-direction:column}}
.dstrip span{{height:1em;line-height:1em}}
.dchar{{display:inline-block}}
.olab{{font-size:24px;font-weight:700;letter-spacing:6px;color:rgba(255,255,255,.72);margin-top:22px}}
.pills{{position:absolute;display:flex;flex-direction:column;gap:22px}}
.pill{{display:flex;align-items:center;gap:18px;padding:18px 28px;border-radius:999px;background:rgba(255,255,255,.07);
  box-shadow:inset 0 0 0 1px rgba(255,255,255,.10);color:#fff;font-size:32px;font-weight:600;white-space:nowrap}}
.pill b{{color:{Y};font-weight:800}}
.pill .dot{{width:14px;height:14px;border-radius:50%;background:{Y}}}
.phone{{position:absolute;border-radius:56px;padding:14px;background:#111;box-shadow:0 0 0 2px #2a2a2c,0 60px 120px rgba(0,0,0,.7);transform-style:preserve-3d}}
.phone video{{width:100%;height:100%;object-fit:cover;object-position:top;border-radius:44px}}
.tgraph{{position:absolute;inset:0}}
.tline{{position:absolute;left:230px;right:230px;top:540px;height:4px;background:linear-gradient(90deg,{Y},rgba(254,222,92,.25));transform-origin:left}}
.tnode{{position:absolute;top:470px;transform:translateX(-50%);text-align:center;width:340px}}
.tdot{{width:30px;height:30px;border-radius:50%;margin:56px auto 0}}
.tyear{{position:absolute;top:-60px;left:0;right:0;font-size:66px;font-weight:800;color:#fff;letter-spacing:-2px}}
.tlab{{margin-top:34px;font-size:25px;font-weight:600;color:rgba(255,255,255,.8)}}
.chapter{{position:absolute;left:150px;top:96px;display:flex;align-items:center;gap:18px;color:#fff;z-index:60}}
.chnum{{font-size:21px;font-weight:800;color:{Y};letter-spacing:3px}}
.chbar{{width:40px;height:3px;background:rgba(255,255,255,.5)}}
.chtitle{{font-size:21px;font-weight:700;letter-spacing:6px;text-transform:uppercase}}
.stage{{position:absolute;inset:0;background:radial-gradient(90% 80% at 50% 45%,#19191c,#050506);overflow:hidden}}
.persp{{position:absolute;inset:0;perspective:1400px;display:flex;align-items:center;justify-content:center}}
.n98{{position:absolute;top:150px;left:0;right:0;text-align:center;font-size:440px;font-weight:900;letter-spacing:-0.05em;line-height:1;transform-style:preserve-3d}}
.n98 span{{display:block}}
.n98 .back{{color:#7a560e}}
.n98 .gold{{position:absolute;left:0;right:0;top:0;background:linear-gradient(180deg,#FFF1B0 0%,#FEDE5C 35%,#C8961E 70%,#FFE38A 100%);-webkit-background-clip:text;background-clip:text;color:transparent}}
.n98.refl .back{{display:none}}
.n98.refl{{top:auto;bottom:-430px;transform:scaleY(-1);-webkit-mask-image:linear-gradient(0deg,rgba(0,0,0,.6),transparent 45%)}}
.uline{{position:absolute;left:680px;right:680px;top:660px;height:8px;border-radius:4px;background:{Y};transform-origin:left;box-shadow:0 0 30px rgba(254,222,92,.6)}}
.datewrap{{flex-direction:column;align-items:flex-start;left:560px;right:auto;justify-content:center}}
.dbar{{position:absolute;left:-60px;top:345px;width:14px;height:380px;border-radius:8px;background:{Y};transform-origin:top;box-shadow:0 0 40px rgba(254,222,92,.5)}}
.dl1{{font-size:150px;font-weight:900;color:#fff;letter-spacing:-0.03em;line-height:1;transform-origin:50% 100%}}
.dl2{{font-size:200px;font-weight:900;color:{Y};letter-spacing:-0.03em;line-height:1;transform-origin:50% 100%}}
.lbig{{position:absolute;left:50%;top:50%;width:1000px;margin-left:-500px;margin-top:-118px}}
.lsweep{{position:absolute;left:50%;top:0;bottom:0;width:180px;margin-left:-90px;background:linear-gradient(90deg,transparent,rgba(254,222,92,.35),transparent);transform:skewX(-18deg)}}
.lfoot{{position:absolute;left:0;right:0;top:640px;text-align:center;color:rgba(255,255,255,.75);font-size:40px;font-weight:600;letter-spacing:2px}}
.aitag{{position:absolute;right:40px;top:34px;padding:8px 16px;border-radius:999px;background:rgba(0,0,0,.45);
  color:rgba(255,255,255,.7);font-size:18px;font-weight:600;letter-spacing:1px}}
.ytag{{position:absolute;left:70px;top:58px;padding:8px 16px;background:{Y};color:#0a0a0b;font-weight:800;font-size:22px;
  letter-spacing:2px;border-radius:6px}}
.ecg{{position:absolute;left:0;width:1920px;height:200px}}
.rewind{{position:absolute;inset:0;backdrop-filter:grayscale(1) contrast(1.2) brightness(.7)}}
.rwlines{{position:absolute;inset:0;background:repeating-linear-gradient(0deg,rgba(255,255,255,.06) 0 2px,transparent 2px 6px);
  background-size:100% 600px}}
.rwtag{{position:absolute;left:70px;top:58px;color:#fff;font-weight:800;font-size:30px;letter-spacing:4px;font-family:monospace}}
.rwyear{{position:absolute;left:0;right:0;top:380px;text-align:center;color:#fff;font-weight:900;font-size:260px;letter-spacing:-8px}}
.tracker{{position:absolute;left:0;right:0;bottom:70px;display:flex;flex-direction:column;align-items:center;gap:16px}}
.trtitle{{color:rgba(255,255,255,.75);font-weight:700;font-size:20px;letter-spacing:5px}}
.trrow{{display:flex;gap:14px;padding:14px 18px;border-radius:999px;background:rgba(10,10,12,.72);box-shadow:inset 0 0 0 1px rgba(255,255,255,.1)}}
.chip{{min-width:64px;height:64px;padding:0 14px;border-radius:32px;display:flex;align-items:center;justify-content:center;
  font-weight:800;font-size:26px;color:#fff;background:#2a2a2f}}
.chip.w{{background:#ff453a}}.chip.six{{background:{Y};color:#111}}.chip.x{{background:#3a3a40;color:{Y}}}
.chip.win{{background:#30d158;color:#06210f}}
.need{{position:absolute;right:70px;top:58px;padding:12px 22px;border-radius:999px;background:rgba(10,10,12,.78);
  box-shadow:inset 0 0 0 1px rgba(255,255,255,.12);color:#fff;font-weight:700;font-size:28px;letter-spacing:2px}}
.need b{{color:{Y};font-size:34px}}
.mark{{position:absolute;right:70px;bottom:56px;width:210px;opacity:.55;z-index:80}}
"""


def build():
    os.makedirs(MEDIA, exist_ok=True)
    shutil.copy(os.path.join(HERE, "..", "doc_video", "node_modules", "gsap", "dist", "gsap.min.js"), os.path.join(OUT, "gsap.min.js"))
    shutil.copy(os.path.join(HERE, "..", "kohli_countdown", "assets", "logo.png"), os.path.join(MEDIA, "logo.png"))
    if not os.path.exists(os.path.join(MEDIA, "grain.png")):
        import numpy as np
        g = (np.random.default_rng(3).normal(128, 40, (512, 512))).clip(0, 255).astype("uint8")
        Image.fromarray(g, "L").save(os.path.join(MEDIA, "grain.png"))
    body = [f'<div class="bg"></div><div class="glow" id="glow"></div><div class="grain"></div>']
    for start, dur, z, h in sorted(els, key=lambda e: e[0]):
        body.append(h)
    body.append(f'<img class="mark clip" id="mark" src="media/logo.png" data-start="{BEAT["drought_70"][0]}" '
                f'data-duration="{round(TOTAL - BEAT["drought_70"][0] - 5, 2)}">')
    body.append('<div class="vig"></div>')
    page = f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div id="root" data-composition-id="root" data-width="{W}" data-height="{H}" data-fps="{FPS}" data-duration="{TOTAL}">
{chr(10).join(body)}
</div>
<script src="gsap.min.js"></script>
<script>
const tl = gsap.timeline({{paused:true}});
tl.fromTo("#glow",{{x:-200,y:0}},{{x:900,y:200,duration:{TOTAL},ease:"sine.inOut"}},0);
tl.fromTo("#mark",{{opacity:0}},{{opacity:0.55,duration:1}},{BEAT["drought_70"][0]});
{chr(10).join(js)}
tl.set({{}},{{}},{TOTAL});
window.__timelines = window.__timelines || {{}};
window.__timelines["root"] = tl;
</script></body></html>"""
    with open(os.path.join(OUT, "index.html"), "w") as f:
        f.write(page)
    with open(os.path.join(HERE, "out", "events.json"), "w") as f:
        json.dump({"total": TOTAL, "vo_offset": VO_OFFSET, "beats": BEAT, "events": sorted(EVENTS)}, f)
    print(f"{len(els)} elements, {len(js)} animation steps, {TOTAL:.1f}s")


if __name__ == "__main__":
    build()

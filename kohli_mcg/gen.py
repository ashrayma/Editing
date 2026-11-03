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
from footage import ai, clip, stretch  # noqa: E402

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
        src = stretch(src, dur + media_start)
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
    src = stretch(src, dur + media_start)
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


# ----------------------------------------------------------------------------- more components (15-min cut)

def flash(t, z=88, dur=0.32):
    """White flash: hits on sixes, wickets and the win."""
    i = nid("fl")
    add(f'<div id="{i}" class="flash clip" data-start="{t}" data-duration="{dur}" style="z-index:{z}"></div>', t, dur, z)
    anim(f'tl.fromTo("#{i}",{{opacity:0.85}},{{opacity:0,duration:{dur},ease:"power2.out"}},{t})')


def letterbox(start, dur, z=86):
    """Cinematic bars slide in for the slow-motion moments."""
    for k, edge in enumerate(("top", "bottom")):
        i = nid("lb")
        add(f'<div id="{i}" class="lbar clip" data-start="{start}" data-duration="{dur}" style="{edge}:0;z-index:{z}"></div>',
            start, dur, z)
        d = -1 if edge == "top" else 1
        anim(f'tl.fromTo("#{i}",{{yPercent:{d * 100}}},{{yPercent:0,duration:0.6,ease:"expo.out"}},{start})')
        anim(f'tl.to("#{i}",{{yPercent:{d * 100},duration:0.5,ease:"power2.in"}},{round(start + dur - 0.5, 2)})')


def split(left, right, start, dur, llab=None, rlab=None, lgray=False, rgray=False, z=22):
    """Two clips side by side, each sliding in from its own edge, labelled underneath (then vs now, us vs them)."""
    for src, side, lab, gray in ((left, "left", llab, lgray), (right, "right", rlab, rgray)):
        i = nid("sp")
        x = 60 if side == "left" else W / 2 + 15
        is_img = src.lower().endswith((".jpg", ".png"))
        inner = (f'<img src="{media(src)}" style="width:100%;height:100%;object-fit:cover">' if is_img else
                 f'<video id="{i}v" class="clip" src="{media(src)}" muted playsinline data-start="{start}" data-duration="{dur}" '
                 f'data-media-start="0" style="width:100%;height:100%;object-fit:cover"></video>')
        filt = "filter:grayscale(1) contrast(1.1);" if gray else ""
        tag = (f'<div class="tag"><span class="tagbar"></span><b>{html.escape(lab)}</b></div>' if lab else "")
        add(f'<div id="{i}" class="card clip" data-start="{start}" data-duration="{dur}" style="left:{x}px;top:250px;'
            f'width:{W / 2 - 75}px;height:{round((W / 2 - 75) * 9 / 16)}px;z-index:{z};{filt}">'
            f'<div class="frame">{inner}<div class="tagfade"></div></div>{tag}</div>', start, dur, z)
        d = -1 if side == "left" else 1
        anim(f'tl.fromTo("#{i}",{{x:{d * 600},opacity:0}},{{x:0,opacity:1,duration:0.9,ease:"expo.out"}},{start})')
        anim(f'tl.to("#{i}",{{opacity:0,duration:0.4}},{round(start + dur - 0.4, 2)})')
    EVENTS.append((start, "whoosh"))


def freeze(clip_path, at, start, dur, gray=True, z=9):
    """Freeze-frame: one still from a clip, frozen with a flash (for the shot breakdown)."""
    import subprocess
    out = os.path.join(MEDIA, "frz_" + os.path.basename(clip_path).rsplit(".", 1)[0] + f"_{at:.1f}.jpg")
    if not os.path.exists(out):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(at), "-i", os.path.join(HERE, clip_path), "-frames:v", "1",
                        "-q:v", "2", out], check=True)
    i = nid("fz")
    filt = "filter:grayscale(1) contrast(1.15);" if gray else ""
    add(f'<div id="{i}" class="full clip" data-start="{start}" data-duration="{dur}" style="z-index:{z};overflow:hidden;{filt}">'
        f'<img id="{i}i" src="media/{os.path.basename(out)}" style="width:100%;height:100%;object-fit:cover">'
        f'<div class="full" style="background:rgba(5,5,6,.35)"></div></div>', start, dur, z)
    anim(f'tl.fromTo("#{i}i",{{scale:1.0}},{{scale:1.12,duration:{dur},ease:"none"}},{start})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.4}},{round(start + dur - 0.4, 2)})')
    flash(start)
    EVENTS.append((start, "freeze"))


def chasebar(runs, wkts, start, dur, target=160, z=64):
    """Top-centre chase tracker: INDIA runs/wkts, a bar filling toward the target."""
    i = nid("cb")
    pct = runs / target * 100
    add(f'<div id="{i}" class="chase clip" data-start="{start}" data-duration="{dur}" style="z-index:{z}">'
        f'<div class="chtxt"><b>INDIA {runs}/{wkts}</b><span>TARGET {target}</span></div>'
        f'<div class="chtrack"><div class="chfill" id="{i}f" style="width:{pct:.1f}%"></div></div></div>', start, dur, z)
    anim(f'tl.fromTo("#{i}",{{y:-30,opacity:0}},{{y:0,opacity:1,duration:0.6,ease:"expo.out"}},{start})')
    anim(f'tl.fromTo("#{i}f",{{scaleX:0}},{{scaleX:1,duration:1.0,ease:"expo.out"}},{start + 0.2})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.4}},{round(start + dur - 0.4, 2)})')


def bars(rows, start, dur, z=30):
    """Horizontal bar race: (label, value, highlight) rows grow to scale with rolling labels."""
    i = nid("br")
    mx = max(v for _, v, _ in rows)
    parts = []
    for k, (lab, v, hi) in enumerate(rows):
        parts.append(f'<div class="brow"><div class="blab">{html.escape(lab)}</div><div class="btrack">'
                     f'<div class="bfill{" hi" if hi else ""}" id="{i}b{k}" style="width:{v / mx * 100:.1f}%"></div></div>'
                     f'<div class="bval">{v}</div></div>')
        anim(f'tl.fromTo("#{i}b{k}",{{scaleX:0}},{{scaleX:1,duration:1.3,ease:"expo.out"}},{round(start + 0.3 + 0.35 * k, 2)})')
        EVENTS.append((round(start + 0.3 + 0.35 * k, 2), "pop"))
    add(f'<div id="{i}" class="bars clip" data-start="{start}" data-duration="{dur}" style="z-index:{z}">{"".join(parts)}</div>',
        start, dur, z)
    anim(f'tl.fromTo("#{i}",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.6,ease:"expo.out"}},{start})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.4}},{round(start + dur - 0.4, 2)})')


def quote(text, who, start, dur, side="left", z=32):
    """A pulled quote: big yellow quote mark, the words revealed line by line, attribution under it."""
    i = nid("qt")
    x = "left:150px" if side == "left" else f"right:150px;text-align:right"
    add(f'<div id="{i}" class="quote clip" data-start="{start}" data-duration="{dur}" style="{x};z-index:{z}">'
        f'<div class="qmark" id="{i}m">“</div><div class="qtext" id="{i}t">{html.escape(text)}</div>'
        f'<div class="qwho" id="{i}w">{html.escape(who)}</div></div>', start, dur, z)
    EVENTS.append((start, "soft"))
    anim(f'tl.fromTo("#{i}m",{{scale:0.4,opacity:0}},{{scale:1,opacity:1,duration:0.7,ease:"back.out(2)"}},{start})')
    anim(f'tl.fromTo("#{i}t",{{clipPath:"inset(0% 100% 0% 0%)"}},{{clipPath:"inset(0% 0% 0% 0%)",duration:1.4,ease:"power2.inOut"}},{start + 0.3})')
    anim(f'tl.fromTo("#{i}w",{{opacity:0,y:10}},{{opacity:1,y:0,duration:0.6}},{start + 1.4})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.45}},{round(start + dur - 0.45, 2)})')


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


# ----------------------------------------------------------------------------- the film (100 lines)

from footage import lib  # noqa: E402

SHOT = "assets/photos/screenshot_drought.png"
REC = "footage/screenrec_match_centre.mp4"
PH = "assets/photos/user/"


def L(n):
    return f"l{n:03d}"


def at(n, f=0.0):
    """Absolute time a fraction f (0..1) into line n."""
    s, e = BEAT[L(n)]
    return round(s + f * (e - s), 2)


def span(n, a=0.0, b_=1.0, pad=0.2):
    """(start, duration) for fraction a..b of line n. Ending at the line's end, it also covers the pause and any
    breather after the line, so no bare background shows between lines."""
    if b_ >= 1.0:
        from beats import BREATH
        pad = max(pad, 0.55) + BREATH.get(L(n), 0.0)
    return at(n, a), round(at(n, b_) - at(n, a) + pad, 2)


def to_next(n, a=0.0):
    """From a fraction of line n to the start of line n+1 (covers the breather after it)."""
    s = at(n, a)
    nxt = BEAT.get(L(n + 1), (TOTAL - 5.0,))[0]
    return s, round(nxt - s + 0.15, 2)


def hv(c, n, a=0.0, b_=1.0, **kw):
    s, d = span(n, a, b_, kw.pop("pad", 0.25))
    if n == 1 and a == 0.0:
        s, d = 0.0, round(d + s, 2)
    return hero(c, s, d, **kw)


def cd(c, n, side="right", label=None, sub=None, a=0.0, b_=1.0, **kw):
    s, d = span(n, a, b_, kw.pop("pad", 0.25))
    vid = not c.lower().endswith((".jpg", ".png"))
    return card(c, s, d, side, label, sub, video=vid, **kw)


def hd(lines, n, side="left", a=0.0, b_=1.0, size=110, acc=1, **kw):
    s, d = span(n, a, b_, kw.pop("pad", 0.0))
    return headline(lines, round(s + 0.1, 2), d, side, size=size, accent_idx=acc, **kw)


def od(text, n, side="left", label=None, a=0.0, b_=1.0, size=260, **kw):
    s, d = span(n, a, b_, kw.pop("pad", 0.0))
    return odometer(text, round(s + 0.1, 2), d, side, size=size, label=label, **kw)


def pl(items, n, side="left", a=0.0, b_=1.0, **kw):
    s, d = span(n, a, b_, 0.0)
    return pills(items, round(s + 0.1, 2), d, side, gap=kw.pop("gap", d / (len(items) + 1.5)), **kw)


def yt(text, n, m=None):
    s = at(n)
    e = BEAT[L(m or n)][1]
    ytag(text, s, round(e - s + 0.2, 2))


def ch(num, title, n):
    chapter(num, title, at(n))


def black(n, a=0.0, b_=1.0, pad=0.3):
    s, d = span(n, a, b_, pad)
    blackout(round(s - 0.1, 2), d + 0.1)


# COLD OPEN ------------------------------------------------------------------------------------
yt("MCG · 23 OCT 2022", 1, 4)
hv(lib("m_kohli_close"), 1, 0.0, 0.45, dim=0.2, fade=0.01)
hv(lib("m_flags"), 1, 0.45, 1.0, dim=0.4)
hd(["8 balls.", "28 runs."], 1, "left", 0.4, 1.0, size=150)
hv(lib("m_shaheen"), 2, dim=0.55)
cd(lib("m_rauf_watch"), 2, "right", "HARIS RAUF", "3 overs · 21 runs · 2 wickets")
od("21", 2, "left", "RUNS IN 3 OVERS", 0.2)
hv(lib("m_kohli_walk18"), 3, dim=0.35, gray=True)
hd(["“His time", "is over.”"], 3, "left", 0.45, 1.0, size=120)
hv(lib("m_six1_close", slow=True), 4, 0.0, 1.0, dim=0.15)
hd(["“The shot of", "the century.”"], 4, "center", 0.35, 1.0, size=120)
letterbox(*span(4, 0.0, 1.0, 1.2))
rewind(at(5, 0.15), round(at(5, 0.85) - at(5, 0.15), 2), "2019")
hv(lib("m_kohli_walk18"), 5, 0.0, 1.0, dim=0.4, gray=True)
hv(lib("m_lights"), 6, dim=0.45)
hd(["1,020 days of silence.", "One night."], 6, "center", 0.05, 1.0, size=110)
full_video(shot("ball"), round(BEAT[L(6)][1] + 0.15, 2), 0.85, z=78, fade=0.05)
s0 = round(BEAT[L(6)][1] + 0.9, 2)
blackout(s0, round(BEAT[L(7)][0] - s0 + 0.1, 2), z=70)
headline(["31 for 4"], round(s0 + 0.1, 2), round(BEAT[L(7)][0] - s0 - 0.1, 2), "center", size=210, accent_idx=0, z=72,
         sub="The night Kohli came back")

# 01 THE KING -----------------------------------------------------------------------------------
ch("01", "The King", 7)
hd(["How high", "he fell from."], 7, "left", size=120)
cd(PH + "test_bat_raised_close.jpg", 7, "right", "VIRAT KOHLI", "At his peak", maxw=980)
yt("2014 · ENGLAND", 8, 9)
cd(clip("N01"), 8, "right", "ENGLAND 2014", "Swing, and Anderson", gray=True)
od("134", 8, "left", "RUNS IN 10 INNINGS", 0.15, color="#fff")
pl(["New <b>body</b>", "New <b>diet</b>", "New <b>game</b>"], 9, "left")
cd(PH + "test_bat_raised_full.jpg", 9, "right", maxw=700)
yt("2016 · IPL", 10)
cd(clip("N02"), 10, "right", "IPL 2016 · RCB", "4 hundreds in one season")
od("973", 10, "left", "RUNS IN ONE IPL SEASON", 0.1, size=280)
yt("2016 · MOHALI", 11)
cd(clip("N03"), 11, "right", "MOHALI · vs AUSTRALIA", "82* off 51 · must-win")
od("82*", 11, "left", "OFF 51 BALLS", 0.05, 0.5)
quote("This is my best innings.", "VIRAT KOHLI · MOHALI 2016", *span(11, 0.5, 1.0, 0.1))
yt("2018 · ENGLAND", 12)
cd(clip("N04"), 12, "right", "ENGLAND 2018", "Same swing. Same Anderson.")
pl(["2014 · <b>134</b> runs", "2018 · <b>593</b> runs"], 12, "left", 0.2)
yt("NOV 2019", 13, 14)
bars([("Sachin Tendulkar", 100, False), ("Ricky Ponting", 71, False), ("Virat Kohli · age 31", 70, True)], *span(13, 0.0, 1.0, 0.2))
hv(lib("m_kohli_close2"), 14, dim=0.6)
od("100", 14, "center", "SACHIN'S RECORD · THE ONE HE COULD CHASE", 0.05, size=320)
hv(lib("m_lights"), 15, dim=0.5, gray=True)
hd(["Then, after", "No. 70..."], 15, "left", 0.0, 0.7, size=110)
ecg(*to_next(15, 0.45), flat_after=0.6)

# 02 THE SILENCE --------------------------------------------------------------------------------
ch("02", "The Silence", 16)
yt("23 NOV 2019 · KOLKATA", 16)
cd(PH + "test_bat_raised_full.jpg", 16, "right", "CENTURY NO. 70", "136 vs Bangladesh · pink-ball Test", maxw=760)
hd(["Century", "No. 70"], 16, "left", size=140)
full_video(shot("days1020"), at(17, -0.0), round(BEAT[L(17)][1] - BEAT[L(17)][0] + 0.75, 2))
yt("MARCH 2020", 18)
hv(lib("m_lights"), 18, dim=0.45, gray=True, media_start=1.0)
hd(["Covid.", "Cricket stopped."], 18, "left", size=120)
fullimg(ai("ai_lonely_bat"), *span(19, 0.0, 1.0, 0.3), dim=0.35)
pl(["50...", "60...", "70...", "<b>Out.</b>"], 19, "left", 0.25)
yt("DEC 2020 · ADELAIDE", 20)
cd(clip("N05"), 20, "right", "ADELAIDE · DEC 2020", "Kohli 74 · run out", gray=True)
od("36", 20, "left", "ALL OUT · INDIA'S LOWEST IN TESTS", 0.45, size=300, color="#ff453a")
yt("2021", 21)
cd(SHOT, 21, "left", "SCREENSHOT", "Still no No. 71", maxw=900)
hd(["Still no", "century."], 21, "right", 0.2, size=100)
yt("SEP 2021", 22)
cd(clip("N06"), 22, "right", "SEPTEMBER 2021", "Stepping down as T20I captain", gray=True)
hd(["“I'll step down", "as T20 captain.”"], 22, "left", 0.15, size=90)
yt("24 OCT 2021 · DUBAI", 23, 25)
hv(lib("d_pak_fans"), 23, dim=0.35)
hd(["India vs Pakistan.", "Dubai."], 23, "left", size=110)
cd(lib("d_babar"), 24, "right", "BABAR AZAM · 68*", a=0.0, b_=0.5)
cd(lib("d_rizwan"), 24, "right", "MOHAMMAD RIZWAN · 79*", a=0.5)
pl(["Kohli · <b>57</b>", "Pakistan · <b>152/0</b>", "<b>10 wickets</b>"], 24, "left")
hv(lib("d_pak_win"), 25, 0.0, 0.45, dim=0.3, gray=True)
hv(lib("d_kohli_congrats"), 25, 0.45, 1.0, dim=0.3, gray=True)
hd(["First World Cup loss", "to Pakistan."], 25, "left", 0.3, size=96)
yt("DEC 2021 → JAN 2022", 26, 27)
cd(lib("v_ganguly"), 26, "right", "THE HEADLINES", "December 2021")
pl(["DEC 2021 · ODI captaincy <b>gone</b>", "JAN 2022 · Test captaincy <b>gone</b>"], 26, "left", 0.1)
hv(lib("m_kohli_walk18"), 27, dim=0.55, gray=True, media_start=0.5)
hd(["No captaincy.", "No century."], 27, "center", size=130)
yt("IPL 2022", 28)
cd(clip("N07"), 28, "right", "IPL 2022", "Out first ball", gray=True)
pl(["Golden duck", "Golden duck", "Golden duck"], 28, "left", 0.15)
hv(lib("v_headlines"), 29, 0.0, 0.72, dim=0.05)
hv(lib("v_finished"), 29, 0.72, 1.0, dim=0.35, gray=True)
hd(["“Kohli is finished.”"], 29, "center", 0.74, 1.0, size=120, acc=0)
fullimg(PH + "test_bat_raised_close.jpg", *span(30, 0, 1, 0.3), dim=0.7, ai=False)
quote("I was trying to fake my intensity a bit.", "VIRAT KOHLI · AUGUST 2022", *span(30, 0.1, 1.0, 0.0))
cd(clip("N08"), 31, "right", "MS DHONI", "The only message")
hd(["Only one", "message.", "MS Dhoni."], 31, "left", 0.2, size=100, acc=2)
black(32, 0.0, 1.0, 1.8)
hd(["Then he did something", "he'd never done."], 32, "center", 0.0, 1.0, size=100, z=40, pad=1.6)

# 03 THE RETURN ---------------------------------------------------------------------------------
ch("03", "The Return", 33)
hv(lib("m_lights"), 33, dim=0.5, media_start=2.0)
od("30", 33, "center", "DAYS WITHOUT TOUCHING A BAT", size=340)
hv(lib("m_lights"), 34, dim=0.55, media_start=0.5)
cd(PH + "asia22_kiss_chain.jpg", 34, "right", "FAMILY FIRST", a=0.55, maxw=860)
pl(["No nets", "No gym selfies", "No social media"], 34, "left", 0.0, 0.7)
hd(["Just family."], 34, "right", 0.55, 1.0, size=110, acc=0)
yt("AUG 2022 · DUBAI", 35, 37)
split(lib("d_pak_win"), PH + "asia22_bat_smile.jpg", *span(35, 0.0, 1.0, 0.3), llab="DUBAI 2021", rlab="DUBAI 2022", lgray=True)
pl(["vs Pakistan · <b>35</b>", "vs Hong Kong · <b>59*</b>", "vs Pakistan · <b>60</b>"], 36, "left")
cd(PH + "asia22_bat_smile.jpg", 36, "right", "ASIA CUP 2022", maxw=900)
fullimg(PH + "asia22_bat_smile.jpg", *span(37, 0, 1, 0.3), dim=0.25, ai=False, origin="60% 35%", push=1.3, end=1.05)
hd(["Smiling", "again."], 37, "left", 0.2, size=130)
yt("8 SEP 2022 · DUBAI", 38, 41)
cd(PH + "asia22_bat_raised_pant.jpg", 38, "right", "vs AFGHANISTAN", "Opening the batting", maxw=900)
hd(["vs Afghanistan."], 38, "left", 0.1, size=100)
fullimg(PH + "asia22_bat_raised_pant.jpg", *span(39, 0, 1, 0.3), dim=0.45, ai=False, origin="40% 40%")
od("122*", 39, "left", "OFF 61 BALLS · 12 FOURS · 6 SIXES", 0.05, size=300)
black(40, 0.0, 1.0, 0.3)
od("71", 40, "center", "1,020 DAYS LATER", size=380, z=40)
flash(at(40, 0.1))
fullimg(PH + "asia22_kiss_chain.jpg", *span(41, 0, 1, 0.3), dim=0.15, ai=False, origin="45% 25%", push=1.25, end=1.05)
hd(["For Anushka", "& Vamika."], 41, "right", 0.5, size=96)
hv(lib("p_crowd"), 42, dim=0.45)
hd(["Big match.", "Big bowlers."], 42, "left", 0.25, size=120)
fullimg(ai("ai_stadium_night"), *to_next(43), dim=0.35)
hd(["One month", "later."], 43, "left", 0.1, size=120)

# 04 THE STAGE ----------------------------------------------------------------------------------
ch("04", "The Stage", 44)
yt("T20 WORLD CUP 2022", 44, 45)
hv(lib("v_bigscreen"), 44, dim=0.3)
hd(["India", "vs Pakistan."], 44, "left", 0.2, size=130)
split(lib("d_pak_win"), lib("p_huddle"), *span(45, 0.0, 1.0, 0.25), llab="DUBAI 2021", rlab="MCG 2022", lgray=True)
yt("23 OCT 2022 · MCG", 46, 53)
fullimg(ai("ai_stadium_night"), *span(46, 0, 1, 0.3), dim=0.25)
pl(["Diwali eve", "Rain all week", "<b>Clear skies</b>"], 46, "left")
hv(lib("v_aerial"), 47, 0.0, 0.5, dim=0.3)
hv(lib("m_flags"), 47, 0.5, 1.0, dim=0.35)
od("90,293", 47, "left", "IN THE STANDS", 0.2, size=240)
cd(clip("N09"), 48, "right", "NATIONAL ANTHEM", "Rohit Sharma")
hd(["Rohit wins the toss.", "Bowls first."], 48, "left", size=90)
hv(lib("b_arshdeep"), 49, dim=0.15)
od("0", 49, "right", "BABAR AZAM · LBW · FIRST BALL", 0.65, size=300, color="#ff453a")
cd(lib("p_rizwan_out"), 50, "right", "RIZWAN · c BHUVI b ARSHDEEP", "4", media_start=4.0)
od("15/2", 50, "left", "PAKISTAN", 0.3, color="#fff")
hv(lib("p_iftikhar_six"), 51, 0.0, 0.5, dim=0.2)
cd(lib("p_masood50"), 51, "right", "SHAN MASOOD · 52*", a=0.5)
pl(["Iftikhar · <b>51</b> (34)", "Masood · <b>52*</b> (42)"], 51, "left", 0.45)
cd(lib("p_hardik"), 52, "right", "HARDIK 3/30 · ARSHDEEP 3/32")
od("159/8", 52, "left", "PAKISTAN · 20 OVERS", 0.35, color="#fff")
black(53, 0.0, 1.0, 1.4)
cd(lib("v_to_win160"), 53, "center", a=0.0, b_=0.3, maxw=1100, z=45)
od("160", 53, "left", "TARGET", 0.0, 1.0, size=300, z=40, pad=1.3)
hd(["Shaheen.", "Naseem.", "Rauf."], 53, "right", 0.3, 1.0, size=96, acc=2, z=40, pad=1.3)

# 05 31 FOR 4 -----------------------------------------------------------------------------------
ch("05", "31 for 4", 54)
hv(lib("m_lights"), 54, dim=0.5, media_start=0.5)
hd(["Then came", "the nightmare."], 54, "center", size=120)
for n, fid, who, (r, w) in ((55, "N10", "KL RAHUL · b NASEEM · 4", (7, 1)), (56, "N11", "ROHIT · c IFTIKHAR b RAUF · 4", (10, 2)),
                            (57, "N12", "SURYAKUMAR · c RIZWAN b RAUF · 15", (26, 3)), (58, "N13", "AXAR PATEL · RUN OUT · 2", (31, 4))):
    hv(clip(fid), n, dim=0.2, fade=0.12)
    cd(clip(fid), n, "left" if n % 2 else "right", who, maxw=760, media_start=2.0)
    chasebar(r, w, *span(n, 0.0, 1.0, 0.2))
    flash(at(n, 0.55))
full_video(shot("score314"), round(at(59) - 0.15, 2), round(BEAT[L(60)][0] - at(59) + 0.2, 2))
split(lib("m_fan_pray"), lib("m_pak_fans"), *span(60, 0.0, 1.0, 0.3), llab="SILENCE", rlab="CELEBRATION")
hv(lib("m_fan_pray2"), 61, dim=0.45, gray=True)
hd(["Phones checked.", "Phones put down."], 61, "left", size=100)
hv(lib("v_kohli_walkin"), 62, dim=0.3)
ecg(*span(62, 0.35, 1.0, 0.3))
black(63, 0.0, 1.0, 1.4)
hd(["The real drama", "hadn't even begun."], 63, "center", size=110, z=40, pad=1.3)

# 06 THE PLAN -----------------------------------------------------------------------------------
ch("06", "The Plan", 64)
cd(clip("N14"), 64, "right", "KOHLI × PANDYA", "Take it deep")
hd(["No more wickets.", "Take it deep."], 64, "left", 0.15, size=100)
hv(lib("v_kohli_mid"), 65, dim=0.5)
od("45/4", 65, "left", "AFTER 10 OVERS", 0.15, color="#fff")
chasebar(45, 4, *span(65, 0.0, 1.0, 0.2))
pl(["Required rate <b>11+</b>"], 65, "right", 0.6)
cd(lib("m_nawaz"), 66, "right", "MOHAMMAD NAWAZ", "One over saved")
hd(["The hidden plan:", "make Nawaz", "bowl the last."], 66, "left", 0.25, size=96, acc=2)
hv(lib("m_shaheen"), 67, dim=0.55)
od("48", 67, "center", "NEEDED OFF 18 BALLS", size=320)
hv(lib("m_kohli_hit18"), 68, dim=0.2)
cd(lib("m_shaheen"), 68, "right", "SHAHEEN AFRIDI · OVER 18", "17 runs", a=0.3)
od("17", 68, "left", "RUNS OFF THE OVER", 0.35)
black(69, 0.0, 1.0, 1.2)
od("31", 69, "center", "OFF 12 BALLS", size=360, z=40, pad=1.1)

# 07 28 OFF 8 -----------------------------------------------------------------------------------
ch("07", "28 off 8", 70)
hv(lib("m_kohli_close"), 70, dim=0.3, media_start=0.5)
cd(lib("m_rauf_watch"), 70, "right", "HARIS RAUF · OVER 19", "3 runs off the first 4 balls")
full_video(shot("eight28"), round(at(71) - 0.1, 2), round(BEAT[L(71)][1] - at(71) + 0.75, 2))
fullimg(ai("ai_tv_off"), *span(72, 0.0, 0.6, 0.2), dim=0.15)
hv(lib("m_fan_pray"), 72, 0.55, 1.0, dim=0.3)
letterbox(*span(73, 0.0, 1.0, 0.0))
hv(lib("m_kohli_close2"), 73, 0.0, 0.6, dim=0.2)
hv(lib("m_kohli_bat16"), 73, 0.6, 1.0, dim=0.2)
s74, d74 = to_next(74)
hero(lib("m_six1_close", slow=True), s74, round(d74 * 0.55, 2), dim=0.05, fade=0.08)
hero(lib("m_six1_wide"), round(s74 + d74 * 0.55, 2), round(d74 * 0.2, 2), dim=0.05, fade=0.08)
hero(lib("m_rauf_watch"), round(s74 + d74 * 0.75, 2), round(d74 * 0.25, 2), dim=0.2, fade=0.08)
flash(round(s74 + d74 * 0.55, 2))
odometer("6", round(s74 + d74 * 0.6, 2), round(d74 * 0.4, 2), "right", size=420, label="STRAIGHT BACK OVER THE BOWLER")
freeze(lib("m_six1_close"), 1.0, *span(75, 0.0, 1.0, 0.3))
pl(["Back foot", "Straight bat", "Over the bowler's head"], 75, "left", 0.1)
cd(lib("m_six1_close"), 75, "right", "THE REPLAY", "145-ish, back of a length", a=0.45, maxw=900)
hv(lib("m_rauf_watch"), 76, dim=0.6, gray=True)
quote("If DK or Hardik had hit those, it would have hurt. But it was Kohli.", "HARIS RAUF · LATER (PARAPHRASED)",
      *span(76, 0.0, 1.0, 0.0))
s77, d77 = to_next(77)
hero(lib("m_six2", slow=True), s77, round(d77 * 0.7, 2), dim=0.05, fade=0.08)
hero(lib("m_fans_flag"), round(s77 + d77 * 0.7, 2), round(d77 * 0.3, 2), dim=0.2, fade=0.08)
flash(round(s77 + d77 * 0.45, 2))
odometer("6", round(s77 + d77 * 0.5, 2), round(d77 * 0.5, 2), "left", size=420, label="OVER FINE LEG")
split(lib("m_fans_scream"), lib("m_crowd_flags2"), *span(78, 0.0, 1.0, 0.2), llab="MCG", rlab="90,293")
black(79, 0.0, 1.0, 1.4)
od("16", 79, "center", "OFF 6 BALLS", size=360, z=40, pad=1.3)

# 08 THE LAST OVER ------------------------------------------------------------------------------
ch("08", "The Last Over", 80)
L0, L1 = at(80), round(BEAT[L(92)][1] + 2.0, 2)
balls = [("W", "w", at(81, 0.3)), ("1", "n", at(82, 0.25)), ("2", "n", at(82, 0.6)), ("6nb", "six", at(83, 0.6)),
         ("wd", "x", at(85, 0.2)), ("3b", "x", at(86, 0.7)), ("W", "w", at(88, 0.5)), ("wd", "x", at(90, 0.6)),
         ("1", "win", at(91, 0.85))]
tracker("OVER 20 · MOHAMMAD NAWAZ", balls, L0, L1 - L0)
need([(L0, "NEED <b>16</b> OFF 6"), (balls[0][2], "NEED <b>16</b> OFF 5"), (balls[1][2], "NEED <b>15</b> OFF 4"),
      (balls[2][2], "NEED <b>13</b> OFF 3"), (balls[3][2], "NEED <b>6</b> OFF 3 · FREE HIT"), (balls[4][2], "NEED <b>5</b> OFF 3 · FREE HIT"),
      (balls[5][2], "NEED <b>2</b> OFF 2"), (balls[6][2], "NEED <b>2</b> OFF 1"), (balls[7][2], "NEED <b>1</b> OFF 1"),
      (balls[8][2], "<b>INDIA WIN</b>")], L1)
cd(lib("m_nawaz"), 80, "right", "MOHAMMAD NAWAZ", "The over they saved")
hd(["Last over.", "16 to win."], 80, "left", 0.1, size=110)
hv(lib("m_hardik_out", slow=True), 81, 0.0, 0.7, dim=0.1)
cd(lib("m_babar_catch"), 81, "right", "HARDIK · c BABAR · 40", a=0.6)
hv(lib("m_runs"), 82, dim=0.15)
hv(lib("m_noball_six"), 83, dim=0.1)
flash(at(83, 0.6))
hv(lib("m_umpire_nb"), 84, 0.0, 0.4, dim=0.1)
hd(["NO-BALL!"], 84, "left", 0.05, 0.45, size=170, acc=0)
cd(lib("m_protest"), 84, "right", "PAKISTAN PROTEST", "The call stands", a=0.4)
cd(lib("m_wide1"), 85, "right", "WIDE", "Free hit to come")
hd(["Wide."], 85, "left", 0.1, size=150, acc=0)
hv(lib("m_freehit"), 86, dim=0.15)
pl(["Free hit", "Bowled · <b>not out</b>", "Ran <b>3 byes</b>"], 86, "left", 0.25)
cd(lib("m_kohli_umpire"), 87, "right", "THE RULE", "Free hit: can't be bowled")
hd(["The rule", "was clear."], 87, "left", 0.2, size=120)
hv(lib("m_dk_stumped", slow=True), 88, 0.0, 0.75, dim=0.1)
cd(lib("m_scoreboard_out"), 88, "right", "KARTHIK · STUMPED", a=0.6)
hv(lib("m_dk_walk"), 89, 0.0, 0.5, dim=0.2)
hv(lib("m_ashwin_in"), 89, 0.5, 1.0, dim=0.2)
hd(["Enter", "Ashwin."], 89, "left", 0.4, size=130)
hv(lib("m_ashwin_wide", slow=True), 90, dim=0.1)
hd(["Left it.", "Wide."], 90, "left", 0.55, size=120)
letterbox(*span(91, 0.0, 1.0, 0.0))
hv(lib("m_ashwin_ready"), 91, 0.0, 0.5, dim=0.15)
hv(lib("m_win_shot", slow=True), 91, 0.5, 1.0, dim=0.05)
s92, d92 = to_next(92)
hero(lib("m_win_shot"), s92, round(d92 * 0.3, 2), dim=0.05, media_start=2.5)
hero(lib("m_celebrate"), round(s92 + d92 * 0.3, 2), round(d92 * 0.35, 2), dim=0.05)
hero(lib("m_fans_win"), round(s92 + d92 * 0.65, 2), round(d92 * 0.35, 2), dim=0.1)
headline(["INDIA WIN!"], round(s92 + 0.2, 2), round(d92 * 0.6, 2), "center", size=200, accent_idx=0, z=55)
flash(s92)

# 09 THE ANSWER ---------------------------------------------------------------------------------
ch("09", "The Answer", 93)
hv(lib("m_kohli_knees", slow=True), 93, dim=0.1)
s94, d94 = to_next(94)
card(clip("N15"), s94, d94, "right", "ROHIT LIFTS KOHLI", video=True)
hero(lib("m_kohli_roar"), s94, d94, dim=0.55)
headline(["On Rohit's", "shoulders."], round(s94 + 0.2, 2), d94 - 0.2, "left", size=110, accent_idx=1)
full_video(shot("hero82"), round(at(95) - 0.1, 2), 3.1)
phone(REC, round(at(95) + 3.0, 2), round(BEAT[L(95)][1] - at(95) - 2.8, 2), "right")
hd(["82* off 53.", "From 31 for 4."], 95, "left", 0.35, size=100)
cd(clip("N16"), 96, "right", "VIRAT KOHLI", "After the match")
quote("Mohali was my best. Tonight, this is above it.", "VIRAT KOHLI · MCG (PARAPHRASED)", *span(96, 0.05, 1.0, 0.0))
hv(lib("m_kohli_walk18"), 97, dim=0.5, gray=True)
hd(["1,020 days.", "One question."], 97, "center", size=120)
s98, d98 = to_next(98)
hero(lib("v_point_sky"), s98, d98, dim=0.25)
headline(["The MCG", "answered."], round(s98 + 0.2, 2), d98 - 0.3, "left", size=130, accent_idx=1)
black(99)
hd(["MCG or Mohali?"], 99, "center", size=140, acc=0, z=40, sub="Comment below")
hv(lib("m_kohli_roar"), 100, dim=0.6)
cd(clip("N17"), 100, "right", "NEXT STORY", "Hobart 2012 · Kohli vs Malinga", a=0.4)
hd(["Subscribe."], 100, "left", 0.0, 0.5, size=130, acc=0)
logo_sting(round(BEAT[L(100)][1] + 0.3, 2), round(TOTAL - BEAT[L(100)][1] - 0.3, 2), end=True)


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
.odo{{position:absolute;font-variant-numeric:tabular-nums;font-weight:800;letter-spacing:-0.04em;line-height:1}}
.digits{{display:inline-flex}}
.dcol{{display:inline-block;height:1em;overflow:hidden}}
.dstrip{{display:flex;flex-direction:column}}
.dstrip span{{height:1em;line-height:1em;text-align:center}}
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
.flash{{position:absolute;inset:0;background:#fff}}
.lbar{{position:absolute;left:0;right:0;height:110px;background:#000}}
.chase{{position:absolute;left:50%;top:52px;width:620px;margin-left:-310px;padding:14px 22px;border-radius:18px;
  background:rgba(10,10,12,.78);box-shadow:inset 0 0 0 1px rgba(255,255,255,.12)}}
.chtxt{{display:flex;justify-content:space-between;color:#fff;font-weight:700;font-size:24px;letter-spacing:2px}}
.chtxt span{{color:rgba(255,255,255,.6)}}
.chtrack{{margin-top:12px;height:10px;border-radius:5px;background:rgba(255,255,255,.12);overflow:hidden}}
.chfill{{height:100%;border-radius:5px;background:linear-gradient(90deg,#ff453a,{Y});transform-origin:left}}
.bars{{position:absolute;left:150px;right:150px;top:330px;display:flex;flex-direction:column;gap:46px}}
.brow{{display:grid;grid-template-columns:420px 1fr 160px;align-items:center;gap:30px;color:#fff}}
.blab{{font-size:36px;font-weight:700}}
.btrack{{height:56px}}
.bfill{{height:100%;border-radius:12px;background:rgba(255,255,255,.22);transform-origin:left}}
.bfill.hi{{background:{Y};box-shadow:0 0 40px rgba(254,222,92,.45)}}
.bval{{font-size:64px;font-weight:900;letter-spacing:-2px;text-align:right}}
.quote{{position:absolute;top:300px;width:620px;color:#fff}}
.qmark{{font-size:220px;line-height:.6;color:{Y};font-weight:900;height:110px;transform-origin:left bottom}}
.qtext{{font-size:56px;font-weight:700;letter-spacing:-1.5px;line-height:1.12}}
.qwho{{margin-top:30px;font-size:24px;font-weight:700;letter-spacing:5px;color:rgba(255,255,255,.65)}}
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
    body.append(f'<img class="mark clip" id="mark" src="media/logo.png" data-start="{BEAT["l007"][0]}" '
                f'data-duration="{round(TOTAL - BEAT["l007"][0] - 5, 2)}">')
    body.append('<div class="vig"></div>')
    page = f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div id="root" data-composition-id="root" data-width="{W}" data-height="{H}" data-fps="{FPS}" data-duration="{TOTAL}">
{chr(10).join(body)}
</div>
<script src="gsap.min.js"></script>
<script>
const tl = gsap.timeline({{paused:true}});
tl.fromTo("#glow",{{x:-200,y:0}},{{x:900,y:200,duration:{TOTAL},ease:"sine.inOut"}},0);
tl.fromTo("#mark",{{opacity:0}},{{opacity:0.55,duration:1}},{BEAT["l007"][0]});
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

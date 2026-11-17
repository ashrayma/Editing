#!/usr/bin/env python3
"""Build the HyperFrames composition for "303: The Number That Ended Karun Nair" (16:9, ~11.5 min).

    python3 gen.py      ->  hf/index.html (+ media copied into hf/media) and out/events.json (for the sound design)

Visual language = the TheCricketLounge Sachin reel, widened to 16:9: near-black + warm-paper stages, condensed
white type with yellow (#FEDE5C) and red accents, small spaced kicker labels, polaroid photos, ticket labels with
red stamps, rolling gold numbers, a browser-framed screen recording, quote cards, a follow/subscribe card.
Media enters from the left or right and never sits on top of a face: a card always shares the frame with text on
the *other* side, and full-frame footage only carries the caption band at the very bottom.

Rules from the brief, enforced in code: every photo / clip / AI image / screen grab is used exactly once
(`use()` raises on a repeat), and something new lands every ~2-3 seconds.
"""
import html
import json
import os
import shutil

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "hf")
MEDIA = os.path.join(OUT, "media")
W, H, FPS = 1920, 1080, 30
CARD_SCALE = 1.14  # cards, screen recordings: a little bigger than the first cut
LEAD = 0.4          # picture starts this long before the voice
TAIL = 6.0          # end card after the last word
Y, RED, PAPER, INK = "#FEDE5C", "#E5484D", "#D9D5CE", "#121214"

TL = json.load(open(os.path.join(HERE, "out", "vo_timeline.json")))
BEAT = {b["id"]: (round(b["start"] + LEAD, 3), round(b["end"] + LEAD, 3)) for b in TL["beats"]}
ORDER = [b["id"] for b in TL["beats"]]
TOTAL = round(TL["duration"] + LEAD + TAIL, 2)

os.makedirs(MEDIA, exist_ok=True)
els, js, EVENTS, USED, NAT, COVER = [], [], [], set(), [], []
_n = [0]


def nid(p="e"):
    _n[0] += 1
    return f"{p}{_n[0]}"


def b(beat, off=0.0):
    s, e = BEAT[beat]
    return round((e + off) if off < 0 else (s + off), 2)


def pre(beat, x):
    """x seconds BEFORE the beat starts."""
    return round(BEAT[beat][0] - x, 2)


def blen(beat):
    return round(BEAT[beat][1] - BEAT[beat][0], 2)


def until(beat, off=0.0):
    """From this beat's start (+off) to the next beat's start."""
    k = ORDER.index(beat)
    end = BEAT[ORDER[k + 1]][0] if k + 1 < len(ORDER) else TOTAL
    return round(end - b(beat, off), 2)


def use(src):
    """Copy media once. Every asset may appear only once in the film."""
    if src in USED:
        raise SystemExit(f"asset used twice: {src}")
    USED.add(src)
    dst = os.path.join(MEDIA, os.path.basename(src))
    sp = os.path.join(HERE, src)
    if not os.path.exists(dst) or os.path.getmtime(sp) > os.path.getmtime(dst):
        shutil.copy(sp, dst)
    return "media/" + os.path.basename(src)


_DUR = {}


def check_len(src, media_start, dur):
    """Warn when a clip would run out (freeze) before its slot ends."""
    import subprocess
    if src not in _DUR:
        _DUR[src] = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                          os.path.join(HERE, src)], capture_output=True, text=True).stdout.strip())
    if media_start + dur > _DUR[src] + 0.05:
        print(f"SHORT: {src} needs {media_start + dur:.2f}s, has {_DUR[src]:.2f}s")


def size(src):
    if src.endswith((".mp4", ".webm")):
        return 1280, 720
    with Image.open(os.path.join(HERE, src)) as im:
        return im.size


def fit(w, h, mw, mh):
    s = min(mw / w, mh / h)
    return round(w * s), round(h * s)


def add(h, start, dur, z=10):
    els.append((start, dur, z, h))


def anim(line):
    js.append(line)


def out_(i, start, dur, d=0.4, extra=""):
    anim(f'tl.to("#{i}",{{opacity:0,{extra}duration:{d},ease:"power2.in"}},{round(start + dur - d, 2)})')


E = lambda s: html.escape(s)  # noqa: E731

# ============================================================================ components


def card(src, start, dur, side="right", label=None, sub=None, maxw=1000, maxh=640, media_start=0.0, ai=False,
         tilt=0, z=20, focus="50% 40%"):
    """Media card that glides in from its side (slight 3D turn), slow push-in, exits the same way."""
    COVER.append((start, start + dur))
    i = nid("cd")
    video = src.endswith((".mp4", ".webm"))
    w, h = size(src)
    maxw, maxh = min(round(maxw * CARD_SCALE), 1180), min(round(maxh * CARD_SCALE), 700)
    cw, ch = fit(w, h, maxw, maxh)
    cx = {"right": W * 0.685, "left": W * 0.315, "center": W / 2}[side]
    left, top = round(cx - cw / 2), round(H * 0.425 - ch / 2)
    rel = use(src)
    EVENTS.append((start, "whoosh"))
    if video:
        check_len(src, media_start, dur)
        inner = (f'<video id="{i}m" src="{rel}" muted playsinline data-start="{start}" data-duration="{dur}" '
                 f'data-media-start="{media_start}" class="cover" style="object-position:{focus}"></video>')
    else:
        inner = f'<img id="{i}m" src="{rel}" class="cover" style="object-position:{focus}">'
    tag = ""
    if label:
        tag = (f'<div class="tag" id="{i}t"><span class="tagbar"></span><b>{E(label)}</b>'
               + (f'<em>{E(sub)}</em>' if sub else "") + "</div>")
    aitag = '<div class="aitag">AI-GENERATED</div>' if ai else ""
    add(f'<div id="{i}" class="card clip" data-start="{start}" data-duration="{dur}" style="left:{left}px;top:{top}px;'
        f'width:{cw}px;height:{ch}px;z-index:{z};transform:rotate({tilt}deg)"><div class="frame">{inner}'
        f'{"<div class=tagfade></div>" if label else ""}{aitag}</div>{tag}</div>', start, dur, z)
    d = -1 if side == "left" else 1
    anim(f'tl.fromTo("#{i}",{{x:{d * 900},rotationY:{-d * 16},opacity:0}},{{x:0,rotationY:0,opacity:1,duration:0.85,ease:"expo.out"}},{start})')
    anim(f'tl.fromTo("#{i}m",{{scale:1.10}},{{scale:1.0,duration:{dur},ease:"none"}},{start})')
    if label:
        anim(f'tl.fromTo("#{i}t",{{y:24,opacity:0}},{{y:0,opacity:1,duration:0.6,ease:"expo.out"}},{start + 0.35})')
    anim(f'tl.to("#{i}",{{x:{d * 500},opacity:0,duration:0.45,ease:"power2.in"}},{round(start + dur - 0.45, 2)})')
    return i


def polaroid(src, start, dur, side="right", caption="", tilt=-3, maxw=860, maxh=640, z=22, ai=False):
    """The Sachin-reel paper photo: white border, handwritten-ish caption, drops in with a tilt."""
    COVER.append((start, start + dur))
    i = nid("po")
    w, h = size(src)
    cw, ch = fit(w, h, maxw, maxh)
    cx = {"right": W * 0.70, "left": W * 0.30, "center": W / 2}[side]
    EVENTS.append((start, "paper"))
    add(f'<div id="{i}" class="pola clip" data-start="{start}" data-duration="{dur}" style="left:{round(cx - cw / 2 - 18)}px;'
        f'top:{round(H * 0.42 - ch / 2 - 18)}px;z-index:{z}"><div style="width:{cw}px;height:{ch}px;overflow:hidden;position:relative">'
        f'<img id="{i}m" src="{use(src)}" class="cover">{"<div class=aitag>AI-GENERATED</div>" if ai else ""}</div>'
        f'<div class="pcap">{E(caption)}</div></div>', start, dur, z)
    anim(f'tl.fromTo("#{i}",{{y:-120,rotation:{tilt * 3},opacity:0,scale:1.08}},{{y:0,rotation:{tilt},opacity:1,scale:1,duration:0.8,ease:"back.out(1.4)"}},{start})')
    anim(f'tl.fromTo("#{i}m",{{scale:1.08}},{{scale:1,duration:{dur},ease:"none"}},{start})')
    out_(i, start, dur, 0.35, "y:60,")
    return i


def full(src, start, dur, media_start=0.0, dim=0.0, ai=False, push=(1.08, 1.0), z=8, focus="50% 40%", quiet=False):
    """Full-frame clip or still (stills/AI push in slowly). Only the caption band ever sits on top."""
    COVER.append((start, start + dur))
    i = nid("fu")
    video = src.endswith((".mp4", ".webm"))
    rel = use(src)
    if video:
        check_len(src, media_start, dur)
    if not quiet:
        EVENTS.append((start, "cut" if video else "whoosh"))
    if video:
        inner = (f'<video id="{i}m" src="{rel}" muted playsinline data-start="{start}" data-duration="{dur}" '
                 f'data-media-start="{media_start}" class="cover" style="object-position:{focus}"></video>')
    else:
        inner = f'<img id="{i}m" src="{rel}" class="cover" style="object-position:{focus}">'
    add(f'<div id="{i}" class="full clip" data-start="{start}" data-duration="{dur}" style="z-index:{z}">{inner}'
        f'<div class="full" style="background:rgba(6,6,7,{dim})"></div>{"<div class=aitag>AI-GENERATED</div>" if ai else ""}</div>',
        start, dur, z)
    anim(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.18}},{start})')
    anim(f'tl.fromTo("#{i}m",{{scale:{push[0]}}},{{scale:{push[1]},duration:{dur},ease:"none"}},{start})')
    out_(i, start, dur, 0.2)
    if video:
        NAT.append((start, src, media_start, dur))
    return i


def browser(src, start, dur, side="right", url="en.wikipedia.org", maxw=1060, maxh=640, z=22, media_start=0.0, box=False):
    maxw, maxh = min(round(maxw * CARD_SCALE), 1560), min(round(maxh * CARD_SCALE), 720)
    """Screen recording / screenshot inside a clean dark browser window."""
    COVER.append((start, start + dur))
    i = nid("br")
    video = src.endswith((".mp4", ".webm"))
    w, h = size(src)
    if not video:
        w, h = w, h
    cw, ch = (maxw, maxh) if box else (fit(w, h, maxw, maxh) if not video else (maxw, round(maxw * 9 / 16)))
    cx = {"right": W * 0.69, "left": W * 0.31, "center": W / 2}[side]
    rel = use(src)
    EVENTS.append((start, "whoosh"))
    inner = (f'<video src="{rel}" muted playsinline data-start="{start}" data-duration="{dur}" data-media-start="{media_start}" '
             f'class="cover" style="object-position:top"></video>') if video else f'<img src="{rel}" class="cover" style="object-position:top">'
    add(f'<div id="{i}" class="browser clip" data-start="{start}" data-duration="{dur}" style="left:{round(cx - cw / 2)}px;'
        f'top:{round(H * 0.42 - ch / 2 - 22)}px;width:{cw}px;z-index:{z}"><div class="bbar"><i></i><i></i><i></i>'
        f'<span>{E(url)}</span><em>{"SCREEN RECORDING" if video else "SCREENSHOT"}</em></div>'
        f'<div style="height:{ch}px;overflow:hidden;position:relative">{inner}</div></div>', start, dur, z)
    anim(f'tl.fromTo("#{i}",{{y:700,rotationX:22,opacity:0}},{{y:0,rotationX:0,opacity:1,duration:0.9,ease:"expo.out"}},{start})')
    anim(f'tl.to("#{i}",{{y:500,opacity:0,duration:0.45,ease:"power2.in"}},{round(start + dur - 0.45, 2)})')
    return i


def head(lines, start, dur, side="left", size=120, accent=(), y=None, kicker=None, kcolor=RED, sub=None, z=30, dark=True):
    """Condensed headline, each line revealed from behind a mask; small spaced kicker above."""
    i = nid("hd")
    x = {"left": 140, "right": W - 140, "center": W / 2}[side]
    nlines = len(lines)
    top = y if y is not None else H * 0.46 - nlines * size * 0.52 - (34 if kicker else 0)
    rows = []
    for k, ln in enumerate(lines):
        col = Y if k in accent else ("#fff" if dark else INK)
        if isinstance(accent, dict):
            col = accent.get(k, "#fff" if dark else INK)
        rows.append(f'<div class="mask"><div class="ln" id="{i}l{k}" style="color:{col}">{E(ln)}</div></div>')
    kick = f'<div class="kick" id="{i}k" style="color:{kcolor}">{E(kicker)}</div>' if kicker else ""
    subh = f'<div class="hsub" id="{i}s">{E(sub)}</div>' if sub else ""
    pos = {"left": f"left:{x}px;text-align:left", "right": f"right:{W - x}px;text-align:right",
           "center": "left:0;right:0;text-align:center"}[side]
    add(f'<div id="{i}" class="head clip" data-start="{start}" data-duration="{dur}" style="{pos};top:{round(top)}px;'
        f'font-size:{size}px;z-index:{z}">{kick}{"".join(rows)}{subh}</div>', start, dur, z)
    EVENTS.append((start + 0.08, "slam" if size >= 150 else "tick"))
    if kicker:
        anim(f'tl.fromTo("#{i}k",{{opacity:0,letterSpacing:"18px"}},{{opacity:1,letterSpacing:"7px",duration:0.6,ease:"expo.out"}},{start})')
    for k in range(nlines):
        anim(f'tl.fromTo("#{i}l{k}",{{yPercent:110}},{{yPercent:0,duration:0.7,ease:"expo.out"}},{round(start + 0.08 + 0.09 * k, 2)})')
    if sub:
        anim(f'tl.fromTo("#{i}s",{{opacity:0,y:14}},{{opacity:1,y:0,duration:0.6,ease:"expo.out"}},{round(start + 0.3 + 0.09 * nlines, 2)})')
    out_(i, start, dur, 0.3, "y:-16,")
    return i


def num(text, start, dur, side="center", size=300, label=None, color=Y, y=None, z=32, roll=1.1):
    """Gold number rolling into place digit by digit."""
    i = nid("nm")
    EVENTS.append((start + 0.05, "roll"))
    cols = []
    for k, ch in enumerate(text):
        if ch.isdigit():
            strip = "".join(f"<span>{d}</span>" for d in "0123456789")
            cols.append(f'<span class="dcol"><span class="dstrip" id="{i}d{k}">{strip}</span></span>')
            anim(f'tl.fromTo("#{i}d{k}",{{yPercent:0}},{{yPercent:{-int(ch) * 10},duration:{roll + 0.1 * k},ease:"expo.out"}},{start + 0.05})')
        else:
            cols.append(f'<span class="dchar">{E(ch)}</span>')
    x = {"left": 140, "right": W - 140, "center": W / 2}[side]
    pos = {"left": f"left:{x}px;text-align:left", "right": f"right:{W - x}px;text-align:right",
           "center": "left:0;right:0;text-align:center"}[side]
    top = y if y is not None else H * 0.44 - size * 0.55
    lab = f'<div class="nlab" id="{i}lab">{E(label)}</div>' if label else ""
    add(f'<div id="{i}" class="num clip" data-start="{start}" data-duration="{dur}" style="{pos};top:{round(top)}px;'
        f'font-size:{size}px;color:{color};z-index:{z}"><div class="digits">{"".join(cols)}</div>{lab}</div>', start, dur, z)
    anim(f'tl.fromTo("#{i}",{{opacity:0,scale:0.94}},{{opacity:1,scale:1,duration:0.4,ease:"power2.out"}},{start})')
    if label:
        anim(f'tl.fromTo("#{i}lab",{{opacity:0,y:12}},{{opacity:1,y:0,duration:0.5,ease:"expo.out"}},{start + 0.45})')
    out_(i, start, dur, 0.3)
    return i


def chips(items, start, dur, side="left", y=None, gap=0.4, z=30, x=None):
    """Rounded chips popping in one after another. An item may be (text, 'red'|'yellow'|'strike')."""
    i = nid("cp")
    xx = x if x is not None else {"left": 140, "right": W - 140, "center": W / 2}[side]
    pos = f"left:{xx}px" if side == "left" else (f"right:{W - xx}px" if side == "right" else "left:0;right:0")
    top = y if y is not None else H * 0.46 - len(items) * 46
    rows = []
    for k, it in enumerate(items):
        t, kind = (it, "") if isinstance(it, str) else it
        rows.append(f'<div class="chip {kind}" id="{i}c{k}"><span class="dot"></span>{t}</div>')
    al = {"left": "flex-start", "right": "flex-end", "center": "center"}[side]
    add(f'<div id="{i}" class="chips clip" data-start="{start}" data-duration="{dur}" style="{pos};top:{round(top)}px;'
        f'align-items:{al};z-index:{z}">{"".join(rows)}</div>', start, dur, z)
    for k in range(len(items)):
        t0 = round(start + gap * k, 2)
        EVENTS.append((t0, "pop"))
        anim(f'tl.fromTo("#{i}c{k}",{{x:{-50 if side != "right" else 50},opacity:0}},{{x:0,opacity:1,duration:0.55,ease:"expo.out"}},{t0})')
    out_(i, start, dur, 0.3)
    return i


def tickets(items, start, dur, side="left", gap=0.45, z=30, y=None, stamps=None):
    """Typewriter score labels (Sachin reel 'TENDULKAR 114'), optional red stamp on each."""
    i = nid("tk")
    x = {"left": 150, "right": W - 760, "center": W / 2 - 330}[side]
    top = y if y is not None else H * 0.46 - len(items) * 62
    rows = []
    for k, (place, score) in enumerate(items):
        st = ""
        if stamps and stamps[k]:
            st = f'<span class="tstamp" id="{i}s{k}">{E(stamps[k])}</span>'
        rows.append(f'<div class="ticket" id="{i}t{k}" style="margin-left:{(k % 2) * 36}px;transform:rotate({(-1.5, 1.2, -0.8, 1.6)[k % 4]}deg)">'
                    f'<small>{E(place)}</small><b>{E(score)}</b>{st}</div>')
    add(f'<div id="{i}" class="tickets clip" data-start="{start}" data-duration="{dur}" style="left:{x}px;top:{round(top)}px;'
        f'z-index:{z}">{"".join(rows)}</div>', start, dur, z)
    for k in range(len(items)):
        t0 = round(start + gap * k, 2)
        EVENTS.append((t0, "paper"))
        anim(f'tl.fromTo("#{i}t{k}",{{y:-40,opacity:0}},{{y:0,opacity:1,duration:0.5,ease:"back.out(1.6)"}},{t0})')
        if stamps and stamps[k]:
            EVENTS.append((t0 + 0.35, "stamp"))
            anim(f'tl.fromTo("#{i}s{k}",{{scale:2.4,opacity:0}},{{scale:1,opacity:1,duration:0.25,ease:"power4.in"}},{t0 + 0.3})')
    out_(i, start, dur, 0.3)


def stamp(text, start, dur, x, y, rot=-8, color=RED, size=64, z=45):
    i = nid("sp")
    EVENTS.append((start + 0.2, "stamp"))
    add(f'<div id="{i}" class="stamp clip" data-start="{start}" data-duration="{dur}" style="left:{x}px;top:{y}px;'
        f'color:{color};border-color:{color};font-size:{size}px;transform:rotate({rot}deg);z-index:{z}">{E(text)}</div>',
        start, dur, z)
    anim(f'tl.fromTo("#{i}",{{scale:2.6,opacity:0}},{{scale:1,opacity:1,duration:0.22,ease:"power4.in"}},{start})')
    out_(i, start, dur, 0.25)


def quote(text, who, start, dur, side="center", size=60, z=34, mark=True, maxw=1300):
    """Apple-clean quote card: big yellow quote mark, words fade up line-group by line-group."""
    i = nid("qt")
    EVENTS.append((start, "soft"))
    x = {"left": 140, "right": W - 140 - maxw, "center": (W - maxw) / 2}[side]
    words = text.split()
    spans = " ".join(f'<span class="qw" id="{i}w{k}">{E(w)}</span>' for k, w in enumerate(words))
    add(f'<div id="{i}" class="quote clip" data-start="{start}" data-duration="{dur}" style="left:{round(x)}px;width:{maxw}px;'
        f'font-size:{size}px;z-index:{z}">{"<div class=qmark>“</div>" if mark else ""}<div class="qtext">{spans}</div>'
        f'<div class="qwho" id="{i}who"><span></span>{E(who)}</div></div>', start, dur, z)
    anim(f'tl.fromTo("#{i}",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.6,ease:"expo.out"}},{start})')
    per = min(0.09, max(0.03, (dur * 0.45) / max(1, len(words))))
    for k in range(len(words)):
        anim(f'tl.fromTo("#{i}w{k}",{{opacity:0.12}},{{opacity:1,duration:0.3}},{round(start + 0.2 + per * k, 2)})')
    anim(f'tl.fromTo("#{i}who",{{opacity:0,x:-20}},{{opacity:1,x:0,duration:0.5}},{round(start + 0.4 + per * len(words), 2)})')
    out_(i, start, dur, 0.35)


def paper(start, dur, z=5):
    """Warm-paper stage (the reel's light scenes) behind graphics."""
    COVER.append((start, start + dur))
    i = nid("pp")
    add(f'<div id="{i}" class="paper clip" data-start="{start}" data-duration="{dur}" style="z-index:{z}"></div>', start, dur, z)
    anim(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.25}},{start})')
    out_(i, start, dur, 0.25)


def big303(start, dur, z=40, color="gold", label=None):
    """Hero 303: extruded gold digits rising in perspective with a reflection and an underline."""
    COVER.append((start, start + dur))
    i = nid("bg")
    EVENTS.append((start, "boom"))
    depth = ",".join(f"0 {k}px 0 #6b4c0c" for k in range(1, 16)) + ",0 40px 60px rgba(0,0,0,.7)"
    fill = ("background:linear-gradient(180deg,#FFF1B0 0%,#FEDE5C 35%,#C8961E 70%,#FFE38A 100%);-webkit-background-clip:text;"
            "background-clip:text;color:transparent") if color == "gold" else f"color:transparent;-webkit-text-stroke:5px {RED}"
    lab = f'<div class="b3lab" id="{i}lab">{E(label)}</div>' if label else ""
    add(f'<div id="{i}" class="stage clip" data-start="{start}" data-duration="{dur}" style="z-index:{z}">'
        f'<div class="persp"><div class="n303" id="{i}n"><span class="back" style="text-shadow:{depth if color == "gold" else "none"};'
        f'{"" if color == "gold" else "opacity:0"}">303</span><span class="front" style="{fill}">303</span></div></div>'
        f'<div class="uline" id="{i}u"></div>{lab}</div>', start, dur, z)
    anim(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.25}},{start})')
    anim(f'tl.fromTo("#{i}n",{{y:240,rotationX:55,opacity:0}},{{y:0,rotationX:0,opacity:1,duration:1.1,ease:"expo.out"}},{start + 0.05})')
    anim(f'tl.fromTo("#{i}n",{{rotationY:-9}},{{rotationY:7,duration:{dur},ease:"sine.inOut"}},{start})')
    anim(f'tl.fromTo("#{i}u",{{scaleX:0}},{{scaleX:1,duration:0.8,ease:"expo.out"}},{start + 0.7})')
    if label:
        anim(f'tl.fromTo("#{i}lab",{{opacity:0,y:16}},{{opacity:1,y:0,duration:0.6}},{start + 0.9})')
    out_(i, start, dur, 0.35)


def datecard(l1, l2, start, dur, sub=None, z=36):
    """Two-line date that flips down into place next to a yellow bar."""
    i = nid("dt")
    EVENTS.append((start, "flip"))
    s = f'<div class="dsub" id="{i}s">{E(sub)}</div>' if sub else ""
    add(f'<div id="{i}" class="date clip" data-start="{start}" data-duration="{dur}" style="z-index:{z}">'
        f'<div class="dbar" id="{i}b"></div><div class="d1" id="{i}1">{E(l1)}</div><div class="d2" id="{i}2">{E(l2)}</div>{s}</div>',
        start, dur, z)
    anim(f'tl.fromTo("#{i}b",{{scaleY:0}},{{scaleY:1,duration:0.5,ease:"expo.out"}},{start})')
    anim(f'tl.fromTo("#{i}1",{{rotationX:-95,opacity:0}},{{rotationX:0,opacity:1,duration:0.8,ease:"expo.out"}},{start + 0.12})')
    anim(f'tl.fromTo("#{i}2",{{rotationX:-95,opacity:0}},{{rotationX:0,opacity:1,duration:0.8,ease:"expo.out"}},{start + 0.28})')
    if sub:
        anim(f'tl.fromTo("#{i}s",{{opacity:0}},{{opacity:1,duration:0.5}},{start + 0.6})')
    out_(i, start, dur, 0.3)


def chapter(numtxt, title, start, dur=2.4, z=70):
    """Full-frame chapter sting: number, rule, title (Apple keynote style)."""
    COVER.append((start, start + dur))
    i = nid("ch")
    EVENTS.append((start, "swell"))
    add(f'<div id="{i}" class="chap clip" data-start="{start}" data-duration="{dur}" style="z-index:{z}">'
        f'<div class="cnum" id="{i}n">CHAPTER {E(numtxt)}</div><div class="crule" id="{i}r"></div>'
        f'<div class="ctitle" id="{i}t">{E(title)}</div></div>', start, dur, z)
    anim(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.2}},{start})')
    anim(f'tl.fromTo("#{i}n",{{opacity:0,y:10}},{{opacity:1,y:0,duration:0.5}},{start + 0.1})')
    anim(f'tl.fromTo("#{i}r",{{scaleX:0}},{{scaleX:1,duration:0.7,ease:"expo.out"}},{start + 0.2})')
    anim(f'tl.fromTo("#{i}t",{{yPercent:100,opacity:0}},{{yPercent:0,opacity:1,duration:0.8,ease:"expo.out"}},{start + 0.3})')
    out_(i, start, dur, 0.3)


def vs(left, right, start, dur, z=34, lcol="#fff", rcol=Y, ltag="", rtag="", t2=None):
    """Split comparison (reel's VS card): two columns, divider draws, right side lands second."""
    i = nid("vs")
    t2 = t2 if t2 is not None else start + 0.5
    EVENTS.append((start, "whoosh"))
    EVENTS.append((t2, "pop"))
    add(f'<div id="{i}" class="vs clip" data-start="{start}" data-duration="{dur}" style="z-index:{z}">'
        f'<div class="vcol" id="{i}a"><small>{E(ltag)}</small><b style="color:{lcol}">{left}</b></div>'
        f'<div class="vdiv" id="{i}d"></div>'
        f'<div class="vcol" id="{i}b"><small>{E(rtag)}</small><b style="color:{rcol}">{right}</b></div></div>', start, dur, z)
    anim(f'tl.fromTo("#{i}d",{{scaleY:0}},{{scaleY:1,duration:0.6,ease:"expo.out"}},{start})')
    anim(f'tl.fromTo("#{i}a",{{x:-80,opacity:0}},{{x:0,opacity:1,duration:0.6,ease:"expo.out"}},{start + 0.1})')
    anim(f'tl.fromTo("#{i}b",{{x:80,opacity:0}},{{x:0,opacity:1,duration:0.6,ease:"expo.out"}},{t2})')
    out_(i, start, dur, 0.3)


def bars(values, start, dur, labels, hi=None, z=34, line=None, title=None):
    """Innings bar chart: bars grow in sequence; optional dashed benchmark line."""
    i = nid("bc")
    mx = max(values)
    n = len(values)
    bw, gap = 110, 46
    total_w = n * bw + (n - 1) * gap
    x0 = (W - total_w) / 2
    base, hmax = 740, 520
    parts = []
    for k, v in enumerate(values):
        hh = max(6, v / mx * hmax)
        col = Y if (hi is not None and k == hi) else "rgba(255,255,255,.28)"
        parts.append(f'<div class="bar" id="{i}b{k}" style="left:{x0 + k * (bw + gap):.0f}px;top:{base - hh:.0f}px;width:{bw}px;'
                     f'height:{hh:.0f}px;background:{col}"><span class="bv">{v}</span></div>'
                     f'<div class="blab" style="left:{x0 + k * (bw + gap) - 20:.0f}px;top:{base + 16}px;width:{bw + 40}px">{E(labels[k])}</div>')
        anim(f'tl.fromTo("#{i}b{k}",{{scaleY:0}},{{scaleY:1,duration:0.6,ease:"expo.out"}},{round(start + 0.15 + 0.16 * k, 2)})')
        EVENTS.append((round(start + 0.15 + 0.16 * k, 2), "tick"))
    if line:
        y = base - line[0] / mx * hmax
        parts.append(f'<div class="bline" id="{i}ln" style="top:{y:.0f}px"><span>{E(line[1])}</span></div>')
        anim(f'tl.fromTo("#{i}ln",{{scaleX:0}},{{scaleX:1,duration:0.9,ease:"expo.inOut"}},{round(line[2], 2)})')
    tt = f'<div class="btitle">{E(title)}</div>' if title else ""
    add(f'<div id="{i}" class="chart clip" data-start="{start}" data-duration="{dur}" style="z-index:{z}">{tt}{"".join(parts)}</div>',
        start, dur, z)
    anim(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.3}},{start})')
    out_(i, start, dur, 0.3)


def chat(msgs, start, dur, side="right", z=34):
    """A phone-style thread: messages from one side, a 'typing…' that never answers."""
    i = nid("ct")
    x = W * (0.66 if side == "right" else 0.12)
    rows = []
    for k, (who, txt, t) in enumerate(msgs):
        cls = "me" if who == "me" else ("typing" if who == "typing" else "them")
        rows.append(f'<div class="msg {cls}" id="{i}m{k}">{E(txt)}</div>')
        anim(f'tl.fromTo("#{i}m{k}",{{y:20,opacity:0,scale:0.9}},{{y:0,opacity:1,scale:1,duration:0.45,ease:"back.out(1.8)"}},{t})')
        EVENTS.append((t, "msg"))
    add(f'<div id="{i}" class="phonebox clip" data-start="{start}" data-duration="{dur}" style="left:{x:.0f}px;z-index:{z}">'
        f'<div class="ptop">Karun Nair</div>{"".join(rows)}</div>', start, dur, z)
    anim(f'tl.fromTo("#{i}",{{y:600,opacity:0}},{{y:0,opacity:1,duration:0.8,ease:"expo.out"}},{start})')
    out_(i, start, dur, 0.35, "y:300,")


def subscribe_card(start, dur, z=60):
    """Channel card: logo ring, name, Subscribe -> Subscribed + bell (Sachin reel's follow card, YouTube flavour)."""
    i = nid("sb")
    tap = start + 1.6
    EVENTS.append((start, "whoosh"))
    EVENTS.append((tap, "click"))
    EVENTS.append((tap + 0.8, "ding"))
    add(f'<div id="{i}" class="subcard clip" data-start="{start}" data-duration="{dur}" style="z-index:{z}">'
        f'<div class="ring"><img src="media/logo.png" width="104" height="24" style="width:104px;height:24px;display:block"></div><div class="sname">TheCricketLounge</div>'
        f'<div class="sdesc">Cricket stories, records &amp; debates</div>'
        f'<div class="sbtn" id="{i}b"><span id="{i}x">Subscribe</span><span id="{i}y" class="sdone">Subscribed ✓</span></div>'
        f'<div class="bell" id="{i}bell">🔔</div><div class="cursor" id="{i}c"></div></div>', start, dur, z)
    anim(f'tl.fromTo("#{i}",{{y:80,opacity:0,scale:0.92}},{{y:0,opacity:1,scale:1,duration:0.7,ease:"expo.out"}},{start})')
    anim(f'tl.fromTo("#{i}c",{{x:260,y:220,opacity:0}},{{x:0,y:0,opacity:1,duration:0.9,ease:"power3.out"}},{start + 0.6})')
    anim(f'tl.to("#{i}c",{{scale:0.8,duration:0.1,yoyo:true,repeat:1}},{tap})')
    anim(f'tl.to("#{i}b",{{backgroundColor:"#2a2a2d",color:"#fff",duration:0.2}},{tap + 0.05})')
    anim(f'tl.to("#{i}x",{{opacity:0,duration:0.15}},{tap + 0.05})')
    anim(f'tl.fromTo("#{i}y",{{opacity:0}},{{opacity:1,duration:0.2}},{tap + 0.15})')
    anim(f'tl.fromTo("#{i}bell",{{opacity:0,rotation:-30,scale:0.5}},{{opacity:1,rotation:0,scale:1,duration:0.6,ease:"elastic.out(1,0.4)"}},{tap + 0.6})')
    out_(i, start, dur, 0.4)


def cap(text, start, dur):
    """Caption band (Sachin reel): bold white on a dark rounded box at the bottom; key word in yellow via *word*."""
    i = nid("cp")
    import re
    body = re.sub(r"\*([^*]+)\*", lambda m: f'<span style="color:{Y}">{m.group(1)}</span>', E(text))
    add(f'<div id="{i}" class="capw clip" data-start="{start}" data-duration="{dur}"><div class="capb" id="{i}b">{body}</div></div>',
        start, dur, 85)
    anim(f'tl.fromTo("#{i}b",{{y:16,opacity:0}},{{y:0,opacity:1,duration:0.25,ease:"expo.out"}},{start})')
    anim(f'tl.to("#{i}b",{{opacity:0,duration:0.12}},{round(start + dur - 0.12, 2)})')


def strike(target_id, t):
    """Red line drawn through an element (by id)."""
    anim(f'tl.fromTo("#{target_id} .strk",{{scaleX:0}},{{scaleX:1,duration:0.35,ease:"power3.out"}},{t})')
    EVENTS.append((t, "scratch"))


def wall_break(start, dur, z=40):
    """Grid of bricks that blows apart from the centre (the wall breaks)."""
    COVER.append((start, start + dur))
    i = nid("wb")
    EVENTS.append((start + 0.9, "boom"))
    cols, rows_ = 12, 8
    bw, bh = W / cols, H / rows_
    bricks = []
    for r in range(rows_):
        for c in range(cols):
            k = r * cols + c
            bricks.append(f'<div class="brick" id="{i}k{k}" style="left:{c * bw:.0f}px;top:{r * bh:.0f}px;width:{bw - 4:.0f}px;height:{bh - 4:.0f}px"></div>')
            dx, dy = (c - cols / 2 + 0.5) * 160, (r - rows_ / 2 + 0.5) * 160
            anim(f'tl.to("#{i}k{k}",{{x:{dx:.0f},y:{dy + 300:.0f},rotation:{(k * 37) % 120 - 60},opacity:0,duration:1.1,ease:"power3.in"}},{start + 0.9 + ((k * 13) % 7) * 0.02:.2f})')
    add(f'<div id="{i}" class="stage clip" data-start="{start}" data-duration="{dur}" style="z-index:{z};background:transparent">{"".join(bricks)}</div>',
        start, dur, z)
    anim(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.3}},{start})')
    out_(i, start, dur, 0.3)


def endcard(start, dur, z=80):
    COVER.append((start, start + dur))
    i = nid("en")
    EVENTS.append((start, "swell"))
    add(f'<div id="{i}" class="stage clip" data-start="{start}" data-duration="{dur}" style="z-index:{z}">'
        f'<div class="eq" id="{i}q">Team India mein hote?</div>'
        f'<div class="eopts"><span id="{i}a">HAAN</span><i>ya</i><span id="{i}b">NAHI</span></div>'
        f'<div class="ecom" id="{i}c"><span class="eav"></span><span class="etype" id="{i}t">Comment mein likhiye…</span></div>'
        f'<div class="elogo" id="{i}l"><img src="media/logo.png" width="520" height="122" style="width:520px;height:122px;display:block"></div><div class="efoot" id="{i}f">Next: the innings that should have changed everything</div></div>',
        start, dur, z)
    anim(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.4}},{start})')
    anim(f'tl.fromTo("#{i}q",{{y:30,opacity:0}},{{y:0,opacity:1,duration:0.7,ease:"expo.out"}},{start + 0.1})')
    anim(f'tl.fromTo("#{i}a",{{scale:0.6,opacity:0}},{{scale:1,opacity:1,duration:0.5,ease:"back.out(2)"}},{start + 0.5})')
    anim(f'tl.fromTo("#{i}b",{{scale:0.6,opacity:0}},{{scale:1,opacity:1,duration:0.5,ease:"back.out(2)"}},{start + 0.75})')
    anim(f'tl.fromTo("#{i}c",{{y:30,opacity:0}},{{y:0,opacity:1,duration:0.6,ease:"expo.out"}},{start + 1.1})')
    anim(f'tl.fromTo("#{i}l",{{clipPath:"inset(0% 100% 0% 0%)"}},{{clipPath:"inset(0% 0% 0% 0%)",duration:1.0,ease:"expo.inOut"}},{start + 1.6})')
    anim(f'tl.fromTo("#{i}f",{{opacity:0}},{{opacity:1,duration:0.6}},{start + 2.4})')


# ============================================================================ the film

P, C, A, BR = "assets/photos/", "footage/clips/", "assets/ai/", "assets/broll/"
CAP = {}  # beat -> caption text (English, key word in *stars*)


def C_(beat, text, off=0.0, end=None):
    """Caption for a beat (or part of one)."""
    s = b(beat, off)
    e = b(end[0], end[1]) if end else BEAT[beat][1]
    cap(text, s, round(max(0.6, e - s), 2))


# ---------------------------------------------------------------- COLD OPEN
full(C + "walk_off.mp4", 0.0, b("open_300", 3.1), focus="50% 30%")
C_("open_300", "*300* in Test cricket", 0.0, end=("open_300", 3.1))
head(["ONLY TWO INDIANS"], b("open_300", 3.1), 1.6, "left", 110, kicker="TEST TRIPLE HUNDREDS")
chips(["1 · VIRENDER SEHWAG", ("2 · ???????", "yellow")], b("open_300", 3.4), 1.5, "left", y=620)
browser(BR + "rec_triple_list.webm", b("open_300", 4.9), until("open_300", 4.9) + 0.2, "center", maxw=1260, maxh=640, media_start=4.5)
C_("open_300", "A name you might not even *remember*", 5.0)

num("3", b("open_3tests"), until("open_3tests"), "center", 380, label="TESTS AFTER THAT. JUST THREE.")
C_("open_3tests", "Then he played *three* more Tests. Just three.")

card(C + "shot_c.mp4", b("open_381"), 3.0, "right", label="CHENNAI, 2016", sub="381 balls")
num("381", b("open_381"), 3.0, "left", 230, label="BALLS FACED", y=330)
card(C + "cook_face.mp4", b("open_381", 3.0), 2.3, "left", maxw=900)
chips([("DROPPED ✕", "red"), ("DROPPED ✕", "red"), ("DROPPED ✕", "red")], b("open_381", 3.1), 2.2, "right", gap=0.3)
card(C + "stokes_tired.mp4", b("open_381", 5.3), until("open_381", 5.3), "right", maxw=900)
head(["ENGLAND PAID", "FOR EVERY ONE"], b("open_381", 5.4), until("open_381", 5.4), "left", 96, accent=(1,))
C_("open_381", "*381* balls · England dropped him *3* times")

full(A + "ai_tv_night.jpg", b("open_channel"), until("open_channel"), dim=0.45, ai=True)
quote("Ye agle das saal Team India ka number paanch hai.", "EVERY CHANNEL, THAT NIGHT", b("open_channel", 0.3),
      until("open_channel", 0.3) - 0.1, size=64, maxw=1250)
C_("open_channel", "“India's No. 5 for the next *10 years*”")

datecard("3 MONTHS LATER", "LAST TEST", b("open_last"), 2.6, sub="for the next 8 years")
num("8", b("open_last", 2.7), 2.4, "right", 340, label="YEARS OUT", y=260)
full(C + "close_breath.mp4", b("open_last", 5.2), until("open_last", 5.2), focus="50% 30%")
C_("open_last", "His *last* Test for 8 years", 0.0, end=("open_last", 5.2))
C_("open_last", "And he *didn't even know*", 5.2)

big303(pre("num_303", 0.2), until("num_303") + 0.2, label="YOU'VE HEARD THIS NUMBER A HUNDRED TIMES")

paper(b("anyaay"), until("anyaay"))
head(["“KARUN WAS DROPPED.", "A HUGE INJUSTICE.”"], b("anyaay", 0.2), until("anyaay", 0.2) + 1.2, "center", 110, kicker="THE STORY EVERYONE TELLS",
     dark=False, kcolor=RED)
C_("anyaay", "“Karun was dropped. Big *injustice*.”")
stamp("NOT THE WHOLE STORY", b("not_whole", 0.1), 2.0, 600, 650, rot=-6, size=58)
chips([("STEP 1 · DROPPED", "yellow"), "STEP 2 · ?", "STEP 3 · ?"], b("not_whole", 2.0), until("not_whole", 2.0), "center", y=360, gap=0.25)
C_("not_whole", "Being dropped was only *step one*")

vs('<s class="sk">DEFENCE</s>', "SENTENCE", b("saza"), until("saza"), ltag="303 WAS NOT HIS", rtag="303 WAS HIS", rcol=RED, t2=b("saza", 1.7))
C_("saza", "303 wasn't his defence. It was his *sentence*.")

card(P + "karun_arrival_2025.jpg", b("came_back"), until("came_back"), "right", label="2025", sub="8 years later", focus="60% 30%")
head(["8 YEARS LATER,", "303 CAME BACK", "WITH HIM"], b("came_back", 0.3), until("came_back", 0.3), "left", 86, accent=(1,))
C_("came_back", "When he came back, *303* came back too")

# ---------------------------------------------------------------- 01 THE RIVER
chapter("01", "The River", b("river"), 2.1)
full(A + "ai_ghats.jpg", b("river", 2.0), until("river", 2.0), dim=0.3, ai=True)
datecard("JULY 2016", "PAMPA RIVER", b("river", 3.9), until("river", 3.9), sub="Aranmula, Kerala")
C_("river", "It begins with a *river*")

full(A + "ai_snake_boat.jpg", b("boat"), 3.6, dim=0.2, ai=True)
chips(["A SNAKE BOAT TO ARANMULA TEMPLE", ("~100 PEOPLE ON BOARD", "yellow")], b("boat", 0.4), 3.0, "left", y=560, gap=0.9)
full(A + "ai_capsized.jpg", b("boat", 3.6), until("boat", 3.6), dim=0.25, ai=True, push=(1.0, 1.12))
head(["IT CAPSIZED."], b("boat", 3.7), 2.0, "left", 130, y=520)
chips([("2 NEVER CAME BACK", "red")], b("boat", 5.6), until("boat", 5.6), "left", y=690)
C_("boat", "~100 on board · *2* never came back")

polaroid(P + "karnataka_ton.jpg", b("on_boat"), until("on_boat"), "right", caption="Karun Nair, 24", tilt=3)
head(["ALSO ON THAT BOAT:", "A 24-YEAR-OLD", "CRICKETER"], b("on_boat", 0.2), until("on_boat", 0.2), "left", 92, accent=(1,),
     kicker="JULY 2016")
C_("on_boat", "On that boat: *Karun Nair*")

head(["HE WAS", "RESCUED."], b("saved"), until("saved"), "center", 170, accent=(1,))
chips([("FATE × 1", "yellow")], b("saved", 1.6), until("saved", 1.6), "center", y=700)
C_("saved", "Fate saved him *once*")
full(C + "profile_card.mp4", b("chennai_fate"), until("chennai_fate"), media_start=0.3)
C_("chennai_fate", "5 months later, in Chennai, fate stood by him *again*")

# ---------------------------------------------------------------- 02 381 BALLS
chapter("02", "381 Balls", b("debut"), 1.6)
datecard("26 NOV 2016", "TEST DEBUT", b("debut", 1.5), until("debut", 1.5), sub="vs England")
C_("debut", "Nov 2016 · Test *debut*")
tickets([("MOHALI · 2016", "NAIR 4"), ("MUMBAI · 2016", "NAIR 13")], b("mohali"), until("mohali"), "left", gap=0.6)
card(C + "shot_b.mp4", b("mohali"), until("slow"), "right", maxw=900)
C_("mohali", "Mohali *4* · Mumbai *13*")
head(["NOBODY", "NOTICED."], b("slow"), until("slow"), "left", 130)
C_("slow", "A slow start. Nobody *noticed*.")
full(C + "drive_early.mp4", b("december"), until("december"))
C_("december", "Then: *December*. Chennai.")
card(C + "shot_a.mp4", b("fifth_test"), until("fifth_test"), "right", label="5TH TEST", sub="Chennai")
chips(["vs ENGLAND · 5TH TEST", ("RAHANE INJURED", "red"), ("KARUN PLAYS", "yellow")], b("fifth_test", 0.2),
      until("fifth_test", 0.2), "left", gap=0.6)
C_("fifth_test", "Rahane injured, so Karun *played on*")

full(C + "cook_drop.mp4", b("cook_drop"), until("cook_drop") + 0.4, media_start=0.0)
stamp("DROPPED ON 34", b("cook_drop", 1.6), until("cook_drop", 1.6), 1240, 120, rot=-7, size=60)
C_("cook_drop", "On *34*, Alastair Cook drops him at slip")
full(C + "hundred_roar.mp4", b("changed", 1.5), 1.8, focus="50% 25%")
head(["EVERYTHING", "CHANGED"], b("changed"), 1.5, "center", 150, accent=(1,))
full(C + "card_103.mp4", b("changed", 3.3), until("changed", 3.3), media_start=0.0)
C_("changed", "First Test *hundred* in 185 balls", 1.5)

card(P + "rahul_199.jpg", b("rahul"), 3.6, "left", label="KL RAHUL", sub="out for 199", focus="30% 40%")
num("199", b("rahul", 0.2), 3.3, "right", 260, label="ONE RUN SHORT", color=RED)
full(C + "hundred_wide.mp4", b("rahul", 3.6), until("rahul", 3.6))
C_("rahul", "Rahul out on *199*. But Karun *didn't stop*")

full(C + "two_hundred_helmet.mp4", b("root_drop"), 1.3, focus="50% 30%")
full(C + "ashwin_hug.mp4", b("root_drop", 1.3), 0.9, media_start=0.2)
C_("root_drop", "After tea: *double* hundred", 0.0, end=("root_drop", 2.2))
full(C + "root_drop.mp4", b("root_drop", 2.2), until("root_drop", 2.2), media_start=2.0)
stamp("DROPPED ON 217", b("root_drop", 3.4), until("root_drop", 3.4), 1230, 120, rot=6, size=60)
C_("root_drop", "Joe Root drops him on *217*", 2.2)

full(C + "three_hundred_four.mp4", pre("rashid_four", 0.4), until("rashid_four") + 0.4, media_start=0.6)
C_("rashid_four", "Four off Adil Rashid · *300*")
card(C + "arms_up.mp4", b("stats_303"), until("stats_303"), "left", maxw=980, maxh=760, focus="50% 30%")
chips([("381 BALLS", ""), ("303 NOT OUT", "yellow"), ("32 FOURS", ""), ("4 SIXES", "")], b("stats_303", 0.2),
      until("stats_303", 0.2), "right", gap=0.55)
C_("stats_303", "*381* balls · *303* not out · 32 fours · 4 sixes")

card(C + "kohli_claps.mp4", b("declare"), 2.6, "right", maxw=900, focus="50% 30%")
num("759/7", b("declare", 0.1), 2.5, "left", 200, label="INDIA DECLARED", y=320)
card(C + "dressing_200.mp4", b("declare", 2.6), until("declare", 2.6), "left", maxw=820)
head(["INDIA'S HIGHEST", "TEST TOTAL"], b("declare", 2.7), until("declare", 2.7), "right", 96, accent=(1,), kicker="AT THE TIME",
     kcolor=Y)
C_("declare", "*759* declared · India's highest Test total then")

card(C + "three_hundred_run.mp4", b("won"), 2.3, "right", maxw=920, focus="50% 30%")
card(C + "umesh_hug.mp4", b("won", 2.3), until("won", 2.3), "right", maxw=920, focus="50% 30%")
chips([("WON BY AN INNINGS & 75", "yellow"), "SERIES 4–0"], b("won", 0.4), until("won", 0.4), "left", gap=1.6)
C_("won", "Won by an innings & 75 · Series *4–0*")

quote("Welcome to the 300 club. Twelve years and eight months I was alone here.", "VIRENDER SEHWAG · DEC 2016 (paraphrased)",
      b("sehwag"), until("sehwag"), size=62, maxw=1340)
C_("sehwag", "Sehwag: “Welcome to the *300 club*”")
browser(BR + "ss_triple_list.png", b("second"), until("second"), "right", maxw=980)
head(["ONLY THE", "2ND INDIAN"], b("second", 0.2), until("second", 0.2), "left", 120, accent=(1,))
C_("second", "Only the *second* Indian after Sehwag")

head(["MAIDEN TON → 300"], b("sobers"), until("sobers"), "center", 96, y=170, kicker="ONLY THE 3RD BATTER EVER", kcolor=Y)
tickets([("1958 · WEST INDIES", "SOBERS 365*"), ("1964 · AUSTRALIA", "SIMPSON 311"), ("2016 · INDIA", "NAIR 303*")],
        b("sobers", 1.4), until("sobers", 1.4), "center", y=380, gap=0.9)
C_("sobers", "His *first* hundred, turned into 300")

card(C + "card_150.mp4", b("avg160"), until("avg160"), "left", maxw=860)
num("160", b("avg160", 0.1), until("avg160", 0.1), "right", 300, label="TEST AVERAGE AFTER 3 TESTS")
C_("avg160", "Test average after 3 Tests: *160*")

card(C + "pull_close.mp4", b("pressure_q"), until("pressure_q"), "right", maxw=900, focus="50% 30%")
head(["NEAR 300.", "PRESSURE?"], b("pressure_q", 0.2), until("pressure_q", 0.2), "left", 120, accent=(1,))
C_("pressure_q", "Near 300 — no *pressure*?")
quote("Jo aadmi maut ko itne kareeb se dekh chuka ho, uske liye century ka kya pressure?", "KARUN NAIR, AFTER THE 303",
      b("maut"), until("maut"), size=62)
C_("maut", "“After seeing *death* so close, what pressure?”")
full(A + "ai_scoreboard.jpg", b("nadi_free"), until("nadi_free"), dim=0.35, ai=True)
head(["THE RIVER FREED HIM", "FROM FEAR."], b("nadi_free", 0.1), 2.6, "left", 92, y=180)
head(["BUT NOW SOMETHING", "ELSE WAS COMING"], b("nadi_free", 2.8), until("nadi_free", 2.8), "left", 92, accent=(1,), y=180)
C_("nadi_free", "Something new was coming for him: *303*")

# ---------------------------------------------------------------- 03 THE BENCHMARK
chapter("03", "The Benchmark", b("judged"), 1.8)
card(C + "fifty.mp4", b("judged", 1.8), 3.6, "right", maxw=900)
head(["A BATTER IS JUDGED", "BY HIS LAST SCORE"], b("judged", 1.9), 3.5, "left", 92, accent=(1,), kicker="CRICKET'S RULE")
paper(b("judged", 5.5), until("judged", 5.5))
head(["LAST SCORE: 303"], b("judged", 5.6), 2.4, "center", 120, dark=False, y=300)
vs("30?", "303?", b("judged", 8.0), until("judged", 8.0), ltag="NEXT INNINGS COMPARED TO", rtag="…OR", lcol=INK, rcol=RED)
C_("judged", "Judged by the *last* score. His last score: *303*")

vs("A YOUNG<br>BATTER", "“THE 303<br>GUY”", b("before_after"), until("before_after"), ltag="BEFORE CHENNAI", rtag="AFTER CHENNAI",
   t2=b("before_after", 3.4))
C_("before_after", "Before: a young batter. After: *the 303 guy*")
polaroid(P + "karnataka_helmet.jpg", b("young_expect"), until("prove_expect"), "left", caption="Expectations changed", tilt=-3, maxh=700)
head(["YOUNG BATTER:", "SCORE RUNS"], b("young_expect"), until("young_expect"), "right", 100)
head(["303 BATTER:", "PROVE IT WASN'T", "ONE DAY"], b("prove_expect"), until("prove_expect"), "right", 100, accent=(1, 2))
C_("young_expect", "Young batter: *score runs*")
C_("prove_expect", "303 batter: *prove it wasn't one day*")

head(["?"], b("two_q"), until("two_q"), "center", 520, y=40, accent=(0,))
chips([("Q1 · WHY NO RUNS?", ""), ("Q2 · WHY NOT 300?", "red")], b("two_q", 0.5), until("two_q", 0.5), "center", y=560, gap=2.2)
C_("two_q", "Every innings, *two* questions")

bars([4, 13, 303, 26, 0, 23, 5], b("benchmark"), until("touch", 0.0) + blen("touch"), ["MOHALI", "MUMBAI", "CHENNAI", "BLR", "BLR", "RANCHI", "DHARAM."],
     hi=2, line=(303, "THE BENCHMARK", b("touch", 0.0)), title="EVERY TEST INNINGS, 2016–17")
C_("benchmark", "303 wasn't a crown. It was a *benchmark*.")
C_("touch", "One he had to touch *every time*")

head(["RUKIYE."], b("rukiye"), until("rukiye"), "center", 220)
C_("rukiye", "Wait. Think for a *minute*.")
full(A + "ai_office.jpg", b("boss_a"), until("boss_b") + blen("boss_b"), dim=0.4, ai=True)
quote("Your best day, declared “never repeatable”.", "IMAGINE YOUR BOSS SAID THIS", b("boss_a", 0.1), until("boss_a", 0.1), size=66)
head(["TOMORROW,", "AT THE OFFICE?"], b("boss_b"), until("boss_b"), "left", 120, accent=(1,), y=440)
C_("boss_a", "Your best day: *never repeatable*")
C_("boss_b", "How would going to work *feel*?")

# ---------------------------------------------------------------- 04 DROPPED
chapter("04", "Dropped", b("hyderabad"), 1.7)
datecard("FEB 2017", "HYDERABAD", b("hyderabad", 1.6), until("hyderabad", 1.6), sub="vs Bangladesh · the next Test")
C_("hyderabad", "The next Test: Hyderabad, *Feb 2017*")
tickets([("PREVIOUS TEST", "NAIR 303*"), ("NEXT TEST", "NAIR —")], b("not_in_xi"), until("not_in_xi"), "left",
        stamps=[None, "NOT IN XI"], gap=1.4)
head(["303.", "THEN BENCHED."], b("not_in_xi", 0.4), until("not_in_xi", 0.4), "right", 120, accent={1: RED})
C_("not_in_xi", "Right after 303: *not in the XI*")
card(P + "rahane.jpg", b("rahane_back"), 3.4, "left", label="AJINKYA RAHANE", sub="fit again", focus="60% 30%")
head(["RAHANE", "IS BACK"], b("rahane_back", 0.2), 3.2, "right", 130, accent=(1,))
card(P + "kohli_presser.jpg", b("rahane_back", 3.4), until("rahane_back", 3.4), "right", label="CAPTAIN VIRAT KOHLI", sub="before the match",
     focus="50% 30%")
head(["DECIDED", "BEFORE THE", "MATCH"], b("rahane_back", 3.6), until("rahane_back", 3.6), "left", 110, accent=(2,))
C_("rahane_back", "Kohli made it clear: *Rahane* returns")

chips([("LEN HUTTON · INJURED", ""), ("INZAMAM-UL-HAQ · INJURED", "")], b("hutton", 1.0), until("inzamam") + blen("inzamam"), "left", gap=2.6, y=380)
head(["MISSED THE NEXT TEST", "AFTER A TRIPLE"], b("hutton"), until("inzamam") + blen("inzamam"), "right", 80, y=180, accent=(1,))
C_("hutton", "Others missed the next Test after a triple…")
C_("inzamam", "…but they were *injured*")
head(["KARUN:", "FULLY FIT.", "STILL OUT."], b("fit_out"), until("fit_out"), "center", 150, accent={2: RED})
C_("fit_out", "Karun was fit. Still *out*.")

paper(b("rahane_ok"), until("senior") + blen("senior"))
head(["RAHANE DID", "NOTHING WRONG ✓"], b("rahane_ok"), until("rahane_ok"), "center", 130, dark=False, accent={1: "#1e9e5a"})
C_("rahane_ok", "Rahane did *nothing wrong*")
chips([("SENIOR", ""), ("YEARS IN THE TEAM", ""), ("TEAM CHOSE EXPERIENCE", "yellow")], b("senior"), until("senior"), "center", gap=0.9)
C_("senior", "The team chose *experience*. That's it.")
quote("Rahane ko chunna sahi tha.", "KARUN'S FATHER", b("father"), until("father"), size=90, maxw=1200)
C_("father", "Even Karun's *father* said so")
quote("Ek match, kisi aur khiladi ki do saal ki mehnat par bhaari nahi pad sakta.", "KARUN NAIR", b("karun_said"), until("karun_said"), size=62)
C_("karun_said", "“One match can't outweigh *two years* of someone's work”")
head(["NO CONSPIRACY.", "NO VILLAIN."], b("no_villain"), until("no_villain"), "center", 140)
C_("no_villain", "No conspiracy. No *villain*.")
head(["NOBODY HAD TO BE", "WORSE THAN HIM"], b("no_worse"), until("no_worse"), "center", 120, accent=(1,), kicker="TO BENCH THE MAN WHO MADE 303")
C_("no_worse", "To bench him, nobody had to be *worse* than him")
full(A + "ai_hourglass.jpg", b("time"), until("time"), dim=0.3, ai=True)
head(["WHAT HE", "DIDN'T HAVE:", "TIME."], b("time", 0.3), until("time", 0.3), "left", 110, accent=(2,), y=330)
C_("time", "What Karun didn't have: *time*")

# ---------------------------------------------------------------- 05 FOUR INNINGS
chapter("05", "Four Innings", b("australia"), 1.6)
card(P + "bengaluru_bowled.jpg", b("australia", 1.6), until("australia", 1.6), "right", label="BENGALURU", sub="March 2017",
     focus="40% 40%")
tickets([("BENGALURU", "NAIR 26"), ("BENGALURU", "NAIR 0"), ("RANCHI", "NAIR 23"), ("DHARAMSALA", "NAIR 5")],
        b("australia", 2.4), until("australia", 2.4), "left", gap=1.0, y=230)
C_("australia", "vs Australia, 2017 · 4 innings · *54* runs")
head(["INDIA WERE", "WINNING"], b("winning"), 2.6, "left", 130, accent=(1,))
chips([("BENGALURU TEST · WON", ""), ("SERIES · 2–1", "yellow")], b("winning", 2.6), until("winning", 2.6), "center", gap=1.2)
C_("winning", "And the team was *winning*")
head(["WHEN THE TEAM WINS,", "THE FIRST QUESTION GOES TO", "THE BATTER WITHOUT RUNS"], b("first_q"), until("first_q"), "center", 86,
     accent=(2,))
C_("first_q", "The first question goes to the man *without runs*")
head(["DID HE FAIL?", "YES."], b("attention"), until("attention"), "center", 150, accent=(1,))
C_("attention", "He did fail. *Yes.*")
vs("30", "303", b("measured"), until("measured"), ltag="SHOULD HAVE BEEN MEASURED AGAINST", rtag="WAS MEASURED AGAINST", rcol=RED,
   t2=b("measured", 1.4))
C_("measured", "His failure was measured against *303*. Not 30.")
head(["4 QUIET INNINGS", "= NORMAL"], b("four_inn"), until("four_inn"), "center", 130, accent=(1,), kicker="EVERY BATTER HAS THEM")
C_("four_inn", "Four quiet innings: *normal* for anyone")
head(["FOR THE 303 MAN:", "NOT “FORM”"], b("form"), until("form"), "center", 130, accent={1: RED})
C_("form", "For the 303 man, it's not *form*…")
stamp("PROOF", pre("saboot", 0.05), until("saboot") + 0.05, 760, 380, rot=-8, size=130)
C_("saboot", "…it's *proof*")
datecard("25 MARCH 2017", "DHARAMSALA", b("dharamsala", 1.5), until("dharamsala", 1.5), sub="his last Test — for 8 years")
head(["PROOF THAT", "303 WAS ONE DAY"], b("dharamsala"), 1.5, "center", 100, accent={1: RED})
C_("dharamsala", "Dharamsala, 25 March 2017: the *last* Test")

full(A + "ai_storm.jpg", b("not_end"), until("stranger") + blen("stranger"), dim=0.35, ai=True)
head(["THE STORY SHOULD", "HAVE ENDED HERE."], b("not_end"), 2.6, "left", 110)
head(["IT DIDN'T."], b("not_end", 2.6), until("not_end", 2.6), "left", 170, accent=(0,))
head(["WHAT CAME NEXT", "WAS STRANGER"], b("stranger"), until("stranger"), "left", 110, accent=(1,))
C_("not_end", "The story should have ended here. It *didn't*.")
C_("stranger", "What came next was *stranger* than being dropped")

# ---------------------------------------------------------------- 06 THE SQUAD LIST
chapter("06", "The Squad List", b("eng2018"), 1.7)
full(A + "ai_bench.jpg", b("eng2018", 1.6), until("eng2018", 1.6) + blen("whole_tour") + 0.2, dim=0.35, ai=True)
datecard("2018", "ENGLAND TOUR", b("eng2018", 1.7), until("eng2018", 1.7), sub="5 Tests · Karun in the squad")
C_("eng2018", "2018 England tour · *in* the squad")
num("0/5", b("whole_tour"), until("whole_tour"), "center", 300, label="TESTS PLAYED ON THE WHOLE TOUR")
C_("whole_tour", "With the team all tour. Played: *zero*")
card(P + "vihari.jpg", b("vihari"), until("vihari"), "right", label="HANUMA VIHARI", sub="debut, The Oval", focus="50% 30%")
head(["5TH TEST DEBUT:", "THE MAN WHO", "JOINED MID-TOUR"], b("vihari", 0.3), until("vihari", 0.3), "left", 100, accent=(2,))
C_("vihari", "The Oval debut went to *Hanuma Vihari*")
paper(b("wi_squad"), until("wi_squad"))
head(["WEST INDIES SQUAD"], b("wi_squad", 0.1), until("wi_squad", 0.1), "center", 90, dark=False, y=200, kicker="AFTER THE TOUR")
tickets([("SQUAD LIST", "KARUN NAIR")], b("wi_squad", 4.2), until("wi_squad", 4.2), "center", y=470, stamps=["LEFT OUT"])
C_("wi_squad", "West Indies squad: Karun's name *missing* again")
chat([("me", "Why didn't I play?", b("no_talk", 0.4)), ("me", "Why was I dropped?", b("no_answer", 0.2)),
      ("typing", "…", b("no_answer", 1.4))], b("no_talk"), until("no_talk") + blen("no_answer") + 0.3, "right")
head(["NOBODY", "TALKED", "TO HIM"], b("no_talk", 0.2), until("no_talk", 0.2) + blen("no_answer") + 0.2, "left", 140, accent=(2,))
C_("no_talk", "Karun: nobody even *talked* to me")
C_("no_answer", "Why not picked? Why dropped? *No answer.*")
card(P + "msk_kohli.jpg", b("msk"), until("msk"), "left", label="MSK PRASAD", sub="chief selector", focus="25% 30%", maxw=740)
quote("Baat ki gayi thi. Karun abhi bhi plans mein hain.", "MSK PRASAD", b("msk", 0.3), until("msk", 0.3), "right", 52, maxw=700)
C_("msk", "Selector: “We spoke. He's still in *plans*.”")
head(["WHOSE TRUTH?"], b("truth_who"), until("truth_who"), "center", 170, accent=(0,))
C_("truth_who", "Whose truth was it? Maybe *both* know.")
browser(BR + "rec_karun_wiki.webm", b("avg62"), until("avg62"), "right", maxw=1000, media_start=3.2)
num("62", b("avg62", 0.2), until("avg62", 0.2), "left", 300, label="TEST AVERAGE · WATCHING", y=290)
C_("avg62", "Test average *62* — now just watching a tour")
head(["FROM 303'S SHINE", "TO A NAME ON", "A SQUAD LIST"], b("squad_name"), until("squad_name"), "center", 110, accent=(2,))
C_("squad_name", "Just a *name* on a squad list")

# ---------------------------------------------------------------- 07 THE WALL
chapter("07", "The Wall", b("consistency"), 1.6)
num("2019", b("consistency", 1.5), 1.6, "center", 200, color="#fff")
num("2021", b("consistency", 3.1), 1.4, "center", 200, color="#fff")
head(["“CONSISTENCY.”"], b("consistency", 4.5), until("consistency", 4.5), "center", 170, accent=(0,), kicker="EVERY SELECTION ANSWER")
C_("consistency", "Every year, one answer: *consistency*")
full(A + "ai_wall.jpg", b("wall"), until("wall"), dim=0.45, ai=True)
head(["A WORD THAT", "IS A WALL"], b("wall", 0.1), 2.6, "left", 120, accent=(1,), y=220)
chips([("FITNESS? → CONSISTENCY", ""), ("TECHNIQUE? → CONSISTENCY", ""), ("COMBINATION? → CONSISTENCY", "yellow")],
      b("wall", 2.7), until("wall", 2.7), "left", gap=1.2, y=560)
C_("wall", "Anything can hide behind it: *consistency*")
head(["AND SOME YEARS,", "NO RUNS EITHER."], b("no_runs"), until("no_runs"), "center", 120, accent=(1,), kicker="TO BE FAIR")
C_("no_runs", "Truth is, some years he didn't score *either*")
full(A + "ai_phone.jpg", b("dec2022"), until("dec2022"), dim=0.35, ai=True)
datecard("DEC 2022", "DROPPED BY KARNATAKA", b("dec2022", 0.2), until("dec2022", 0.2))
C_("dec2022", "Dec 2022: out of the *Karnataka* team too")
card(P + "dear_cricket.png", pre("dear_cricket", 0.1), until("dear_cricket") + 0.1 + 2.0, "center", maxw=1100, maxh=650)
C_("dear_cricket", "“Dear cricket, give me *one more chance*.”")
head(["A TRIPLE CENTURION,", "ASKING FOR", "ONE CHANCE"], b("sochiye_ask", 2.0),
     until("sochiye_ask", 2.0) + blen("ask_chance"), "center", 120, accent=(2,))
C_("sochiye_ask", "A man with a Test *triple*…")
C_("ask_chance", "…asking cricket for *one chance*")
datecard("ENGLAND", "COUNTY CRICKET", b("county"), until("county"), sub="Northamptonshire")
C_("county", "Cricket sent him to *county* cricket")
card(P + "county_northants.jpg", b("surrey"), until("surrey"), "right", label="NORTHAMPTONSHIRE", sub="vs Surrey", focus="50% 25%")
chips(["OVERSEAS SLOT", "LAST 3 MATCHES ONLY", ("1ST COUNTY 100 vs SURREY", "yellow")], b("surrey", 0.3), until("surrey", 0.3), "left", gap=1.6)
C_("surrey", "Only 3 matches · first county *hundred* vs Surrey")
full(A + "ai_crack.jpg", b("crack"), until("crack"), dim=0.3, ai=True)
head(["THE FIRST CRACK", "IN THE WALL"], b("crack", 0.1), 3.4, "left", 110, accent=(1,), y=460)
head(["THEN CAME", "THE YEAR"], b("crack", 3.6), until("crack", 3.6), "left", 110, accent=(1,), y=460)
C_("crack", "The first *crack* in the wall")
vs("KARNATAKA", "VIDARBHA", b("vidarbha"), until("vidarbha"), ltag="LEFT", rtag="JOINED", t2=b("vidarbha", 1.3))
C_("vidarbha", "He switched states: *Vidarbha*")
num("690", b("year1"), 3.4, "left", 240, label="RUNS · YEAR ONE", y=300)
chips(["RANJI FINAL", ("LOST", "red")], b("year1", 0.8), 2.6, "right", gap=0.8)
head(["2024-25:", "LIKE A FILM"], b("year1", 3.5), until("year1", 3.5), "center", 150, accent=(1,))
C_("year1", "Year one: 690 runs, final *lost*. Then 2024-25…")
num("779", b("vht"), until("vht"), "left", 260, label="VIJAY HAZARE TROPHY", y=280)
chips(["5 HUNDREDS", ("AVERAGE 389", "yellow")], b("vht", 0.6), until("vht", 0.6), "right", gap=0.9)
C_("vht", "*779* runs · 5 hundreds · average *389*")
head(["5 HUNDREDS", "IN ONE SEASON"], b("record"), until("record"), "center", 140, accent=(1,), kicker="EQUALS THE RECORD", kcolor=Y)
C_("record", "Equals the record for one *season*")
card(P + "vidarbha_ton.jpg", b("ranji_final"), until("ranji_final"), "right", label="RANJI FINAL", sub="vs Kerala", focus="45% 25%")
tickets([("FINAL · 1ST INNINGS", "NAIR 86"), ("FINAL · 2ND INNINGS", "NAIR 135")], b("ranji_final", 0.8), until("ranji_final", 0.8),
        "left", gap=1.2, y=280)
chips([("VIDARBHA: CHAMPIONS", "yellow")], b("ranji_final", 4.0), until("ranji_final", 4.0), "left", y=640)
C_("ranji_final", "Ranji final: 86 & *135* · Vidarbha champions")

head(["ANOTHER DOOR", "OPENED"], b("ipl_door"), until("ipl_door"), "center", 150, accent=(1,))
C_("ipl_door", "And then another *door* opened")
num("1,077", b("ipl_1077"), until("ipl_1077"), "right", 240, label="DAYS SINCE HIS LAST IPL GAME", y=270)
datecard("APRIL 2025", "IPL", b("ipl_1077", 0.6), until("ipl_1077", 0.6), sub="Delhi Capitals")
C_("ipl_1077", "1,077 days later, back in the *IPL*")
vs("MUMBAI<br>INDIANS", "BUMRAH", b("bumrah"), until("bumrah"), ltag="OPPONENT", rtag="WITH THE BALL", t2=b("bumrah", 1.7))
C_("bumrah", "vs Mumbai Indians. The ball: *Jasprit Bumrah*")
num("89", b("ipl_89"), until("ipl_89"), "left", 360, label="OFF 40 BALLS", y=230)
chips(["12 FOURS", "5 SIXES", ("18 OFF ONE BUMRAH OVER", "yellow")], b("ipl_89", 0.9), until("ipl_89", 0.9), "right", gap=0.9)
C_("ipl_89", "*89* off 40 · 12 fours · 5 sixes")
head(["NO INDIAN HAD TAKEN", "MORE OFF ONE", "BUMRAH OVER"], b("bumrah_record"), until("bumrah_record"), "center", 110, accent=(1, 2),
     kicker="IPL HISTORY")
C_("bumrah_record", "No Indian took *more* off one Bumrah over")
head(["DELHI LOST", "BY 12 RUNS"], b("dc_lost"), 2.4, "left", 130, accent={1: RED})
quote("Agar team na jeete, toh individual runs ki koi value nahi.", "KARUN NAIR, AFTER THE GAME", b("dc_lost", 2.4), until("dc_lost", 2.4), size=60)
C_("dc_lost", "“If the team doesn't win, my runs have *no value*”")
head(["THE MAN MEASURED", "BY ONE SCORE…"], b("ind_score"), until("ind_score"), "center", 120)
head(["…SAID SCORES", "HAVE NO VALUE"], b("no_value"), until("no_value"), "center", 120, accent=(1,))
C_("ind_score", "The man judged by *one* individual score…")
C_("no_value", "…said individual scores don't *matter*")
wall_break(b("lions_204"), until("lions_204"))
num("204", b("lions_204", 0.2), until("lions_204", 0.2), "center", 330, label="INDIA A vs ENGLAND LIONS", z=45)
C_("lions_204", "*204* for India A. This time the wall *broke*.")

# ---------------------------------------------------------------- 08 THE RETURN
chapter("08", "The Return", pre("headingley", 0.3), 1.6)
datecard("JUNE 2025", "HEADINGLEY", b("headingley", 1.2), until("headingley", 1.2))
C_("headingley", "June 2025 · *Headingley*")
card(P + "karun_nets_2025.jpg", b("cap_3006"), until("cap_3006"), "right", maxw=920, focus="50% 25%")
num("3,006", b("cap_3006", 0.1), until("cap_3006", 0.1), "left", 220, label="DAYS LATER · THE TEST CAP", y=300)
C_("cap_3006", "*3,006* days later, the Test cap again")
card(P + "karun_fence_2025.jpg", b("country_said"), until("country_said"), "left", maxw=640, maxh=640, focus="50% 30%")
head(["“NOW THE STORY", "IS COMPLETE.”"], b("country_said", 0.2), until("country_said", 0.2), "right", 100, accent=(1,), kicker="THE WHOLE COUNTRY")
C_("country_said", "The country said: now the story *completes*")
card(P + "headingley_duck.jpg", b("duck"), until("duck"), "right", label="HEADINGLEY", sub="1st innings", focus="40% 30%")
tickets([("1ST INNINGS · 4 BALLS", "NAIR 0"), ("2ND INNINGS", "NAIR 20")], b("duck", 0.3), until("duck", 0.3), "left", gap=2.6, y=300,
        stamps=["POPE CATCH", None])
C_("duck", "0 off 4 — a great Ollie Pope catch. Then *20*")
card(P + "lords_walk.jpg", b("edgbaston"), until("edgbaston"), "left", label="LORD'S", focus="50% 30%")
tickets([("EDGBASTON", "NAIR 31 & 26"), ("LORD'S", "NAIR 40 & 14")], b("edgbaston", 0.3), until("edgbaston", 0.3), "right", gap=1.4, y=320)
C_("edgbaston", "Edgbaston 31 & 26 · Lord's *40 & 14*")
head(["STARTS.", "EVERY TIME.", "“IS THAT ALL?”"], b("same_q"), until("same_q"), "center", 120, accent={2: Y})
C_("same_q", "A start every time — and the same *question*")
chips([("4TH TEST · LEFT OUT", "red")], b("oval57"), 1.8, "center", y=470)
card(P + "oval_fifty.jpg", b("oval57", 1.8), until("oval57", 1.8), "right", label="THE OVAL", sub="5th Test", focus="45% 30%")
num("57", b("oval57", 2.0), until("oval57", 2.0), "left", 360, label="AT LAST", y=230)
C_("oval57", "Dropped for the 4th Test. Then the Oval: *57*")
head(["FIRST TEST FIFTY", "IN ~9 YEARS"], b("nine_years"), until("nine_years"), "center", 130, accent=(1,))
C_("nine_years", "A Test fifty after nearly *9 years*")
card(P + "karthik.jpg", b("dk"), until("dk"), "left", label="DINESH KARTHIK", sub="on commentary", focus="40% 30%", maxw=740)
quote("Karun ka career ab sach mein wapas aa gaya hai.", "DINESH KARTHIK", b("dk", 0.3), until("dk", 0.3), "right", 52, maxw=700)
C_("dk", "DK: “His career is *truly back*”")
card(P + "walk_off_2025.jpg", b("lbw"), until("lbw"), "right", maxw=600, maxh=700, focus="50% 25%")
tickets([("THE OVAL · 1ST INN.", "LBW · TONGUE"), ("THE OVAL · 2ND INN.", "NAIR 17")], b("lbw", 0.2), until("lbw", 0.2), "left", gap=2.4,
        y=300, stamps=["REVIEW LOST", None])
C_("lbw", "LBW to Josh Tongue · review *lost* · then 17")
browser(BR + "ss_karun_infobox.png", b("avg25"), 5.0, "right", maxw=720, maxh=560, box=True)
chips(["8 INNINGS", "205 RUNS", ("AVERAGE 25", "yellow")], b("avg25", 0.2), 4.8, "left", gap=0.6)
quote("Main kuch saabit karne ki koshish nahi kar raha tha.", "KARUN NAIR, AFTER THE SERIES", b("avg25", 5.0), until("avg25", 5.0), size=60)
C_("avg25", "Not bad. But not *303*.", 0.0, end=("avg25", 5.0))
C_("avg25", "“I wasn't trying to *prove* anything”", 5.0)
head(["BUT EVERYONE", "AROUND HIM WAS", "MAKING HIM PROVE"], b("prove"), until("prove"), "center", 110, accent=(2,))
big303(pre("one_day", 0.1), until("one_day") + 0.1, color="red", label="…WASN'T ONE DAY")
C_("prove", "Everyone kept asking him to *prove* one thing…")
C_("one_day", "…that 303 *wasn't one day*")

paper(b("wi_2025"), until("wi_2025"))
tickets([("WEST INDIES SERIES · 2025", "KARUN NAIR")], b("wi_2025", 0.5), until("wi_2025", 0.5), "center", y=430, stamps=["NOT PICKED"])
C_("wi_2025", "Weeks later: West Indies squad. Name *missing*.")
card(P + "agarkar.jpg", b("agarkar"), until("agarkar") + blen("zyada"), "left", label="AJIT AGARKAR", sub="chief selector", focus="50% 30%", maxw=740)
quote("Humein England mein Karun se zyada ki ummeed thi.", "AJIT AGARKAR", b("agarkar", 0.2), until("agarkar", 0.2), "right", 52, maxw=700)
head(["“ZYADA”", "KI UMMEED."], b("zyada"), until("zyada"), "right", 120, accent={0: RED})
C_("agarkar", "“We expected *more* from Karun in England”")
C_("zyada", "*More*. Did you hear that?")
quote("Main ek series se zyada ka haqdaar tha.", "KARUN NAIR", b("haqdaar"), until("haqdaar"), size=72, maxw=1250)
C_("haqdaar", "“I deserved more than *one series*”")
chips(["BACK TO KARNATAKA", ("2 RANJI 100s IN A ROW", "yellow")], b("back_karnataka"), until("back_karnataka"), "center", gap=1.6)
C_("back_karnataka", "Back to Karnataka · *two* Ranji hundreds in a row")
head(["SAME STORY.", "SAME CYCLE."], b("same_cycle"), until("same_cycle"), "center", 150, accent=(1,))
C_("same_cycle", "Same story. Same *cycle*.")
head(["8 YEARS LATER,", "EVERY INNINGS", "MEASURED BY…"], b("measured_303"), 2.8, "center", 110)
num("303", b("measured_303", 2.8), until("measured_303", 2.8), "center", 380, color=RED)
C_("measured_303", "Every innings, measured by *303*")

# ---------------------------------------------------------------- 09 THE TRUTH
paper(b("villains"), until("villains") + 1.6)
vs("RAHANE", "SELECTORS", b("villains", 0.2), until("villains", 0.2) + 1.4, ltag="VILLAIN #1", rtag="VILLAIN #2", lcol=INK, rcol=INK,
   t2=b("villains", 1.6))
head(["KISMAT"], b("villains", 3.0), until("villains", 3.0) + 1.4, "center", 110, dark=False, y=620, kicker="VILLAIN #3")
stamp("WRONG", b("subscribe", 0.0), 1.4, 300, 360, rot=-9, size=90)
stamp("WRONG", b("subscribe", 0.25), 1.15, 1220, 360, rot=7, size=90)
stamp("WRONG", b("subscribe", 0.5), 0.9, 800, 640, rot=-4, size=90)
C_("villains", "3 villains so far: Rahane, selectors, *fate*")
subscribe_card(b("subscribe", 1.5), until("subscribe", 1.5))
C_("subscribe", "All three are *wrong*. True fan? *Subscribe*.")

chapter("09", "The Truth", pre("truth", 0.2), 1.5)
head(["NOBODY ENDED", "HIS CAREER."], b("truth", 1.3), until("truth", 1.3), "center", 140, accent=(1,), sub="Not Rahane. Not the selectors.")
C_("truth", "Nobody ended his career. Not Rahane. Not *selectors*.")
full(C + "two_hundred_shot.mp4", b("own_innings"), until("own_innings"), media_start=2.0)
C_("own_innings", "His biggest rival: his own *biggest innings*")
chips([("A RIVER ✕", ""), ("A SQUAD LIST ✕", ""), ("8 YEARS ✕", "")], b("number"), 3.6, "left", gap=1.0)
num("303", b("number", 3.8), until("number", 3.8), "right", 300, color=RED, label="WHAT STOPPED HIM: A NUMBER")
C_("number", "Not a river. Not a squad list. A *number*.")
quote("Ye bojh nahi hai.", "KARUN NAIR, YEARS LATER", b("bojh", 2.6), until("bojh", 2.6), size=110, maxw=1100)
head(["HE NEVER CALLED", "303 A BURDEN"], b("bojh"), 2.6, "center", 120, accent=(1,))
C_("bojh", "He never called 303 a *burden*")
quote("Ye kuch aisa hai, jo mujhse kabhi door nahi jaayega.", "KARUN NAIR", b("never_far"), until("never_far"), size=66)
C_("never_far", "“It will never leave me”")
full(C + "shot_d.mp4", b("sahi"), until("sahi"))
C_("sahi", "Maybe he was right. 303 never *left*.")
card(C + "crowd_200.mp4", b("humara"), until("humara"), "right", maxw=980)
head(["IT WASN'T HIS", "ANYMORE.", "IT BECAME OURS."], b("humara", 0.2), until("humara", 0.2), "left", 86, accent=(2,))
C_("humara", "It just wasn't *his* anymore. It became *ours*.")
head(["THE BITTEREST PART"], b("kadvi"), until("kadvi"), "center", 120, kcolor=RED)
C_("kadvi", "And the *bitterest* part…")
full(C + "hundred_crowd.mp4", b("trapped"), 2.6)
head(["WE TRAPPED HIM", "TRYING TO SAVE HIM"], b("trapped", 2.6), until("trapped", 2.6), "center", 120, accent=(1,))
C_("trapped", "Trying to save him, we *trapped* him")
paper(b("character"), until("character"))
tickets([("THE CHARACTER WE BUILT", "“303 WALA AADMI”"), ("", "“ANYAAY KA SHIKAAR”")], b("character", 0.3), until("character", 0.3),
        "center", gap=2.6, y=330)
C_("character", "We built him a character: *the 303 man*")
head(["EVERY INNINGS,", "ONE DEMAND:", "ANOTHER 303"], b("one_thing"), until("one_thing"), "center", 120, accent={2: RED})
C_("one_thing", "And that character owes one thing: *another 303*")
full(C + "shot_e.mp4", b("no_score"), 3.0)
head(["HE DIDN'T NEED", "A SCORE"], b("no_score", 3.0), 2.4, "center", 120)
head(['<s class="sk">303 WALA AADMI</s>'.replace("<", "&lt;") if False else "NOT “THE 303 MAN”", "JUST", "KARUN NAIR"],
     b("no_score", 5.4), until("no_score", 5.4), "center", 120, accent=(2,))
C_("no_score", "He just wanted to be *Karun Nair*")
card(C + "shot_f.mp4", b("aap_bataiye"), until("aap_bataiye"), "right", maxw=980)
head(["IF HE'D MADE 30", "THAT DAY", "IN CHENNAI…"], b("aap_bataiye", 1.0), until("aap_bataiye", 1.0), "left", 86, accent=(0,))
C_("aap_bataiye", "If he'd been out for *30* that day…")
card(C + "hundred_shot.mp4", b("comment"), until("comment") - TAIL + 0.6, "left", maxw=980)
head(["WOULD HE BE", "IN TEAM INDIA", "TODAY?"], b("comment", 0.1), until("comment", 0.1) - TAIL + 0.5, "right", 86, accent=(1, 2))
C_("comment", "…would he be in Team India today? *Comment.*")
endcard(round(BEAT["comment"][1] + 0.2, 2), round(TOTAL - BEAT["comment"][1] - 0.2, 2))


# ---------------------------------------------------------------- match footage behind the text
# Wide shots from the 303 innings (never shown elsewhere) go behind text-only moments, but ONLY on lines that are
# about Chennai / the 303 / "the 303 man", so the picture always matches the words.
BG_OK = ["open_300", "open_3tests", "open_381", "open_last", "anyaay", "not_whole", "saza",
         "december", "fifth_test", "rahul", "stats_303", "declare", "won", "sehwag", "second", "sobers", "avg160",
         "pressure_q", "maut", "judged", "before_after", "young_expect", "prove_expect", "two_q", "benchmark", "touch",
         "measured", "form", "prove", "one_day", "measured_303", "truth", "own_innings", "number", "bojh", "never_far",
         "kadvi", "trapped", "character", "one_thing", "no_score"]
# reviewed by eye: close-ups of faces (6, 8, 36, 39) and a repeat of the 150* graphic (21) are excluded
SKIP = {"bg_006", "bg_008", "bg_021", "bg_036", "bg_039"}
POOL = [p for p in json.load(open(os.path.join(HERE, "out", "bg_pool.json"))) if os.path.basename(p["file"])[:6] not in SKIP]


def gaps_in(t0, t1):
    pieces = [(t0, t1)]
    for c0, c1 in COVER:
        nxt = []
        for p0, p1 in pieces:
            if c1 <= p0 or c0 >= p1:
                nxt.append((p0, p1))
                continue
            if c0 > p0:
                nxt.append((p0, c0))
            if c1 < p1:
                nxt.append((c1, p1))
        pieces = nxt
    return [(round(a, 2), round(e, 2)) for a, e in pieces if e - a >= 0.9]


_pk = [0]
for beat in BG_OK:
    k = ORDER.index(beat)
    t1 = BEAT[ORDER[k + 1]][0] if k + 1 < len(ORDER) else TOTAL
    for g0, g1 in gaps_in(BEAT[beat][0], t1):
        t = g0
        while g1 - t >= 0.9 and _pk[0] < len(POOL):
            shot = POOL[_pk[0]]
            _pk[0] += 1
            d = round(min(shot["dur"], g1 - t, 3.0), 2)
            if g1 - (t + d) < 0.9:      # don't leave a sliver: stretch to the end of the gap if the shot allows
                d = round(min(shot["dur"], g1 - t), 2)
            full(shot["file"], round(t, 2), d, dim=0.58, z=3, quiet=True, push=(1.06, 1.0))
            t += d
print(f"background shots used: {_pk[0]} of {len(POOL)}")

# ============================================================================ page

FONT = "../node_modules/@fontsource"
CSS = f"""
@font-face{{font-family:Anton;src:url(media/anton.woff2) format("woff2")}}
@font-face{{font-family:Inter;font-weight:500;src:url(media/inter500.woff2) format("woff2")}}
@font-face{{font-family:Inter;font-weight:700;src:url(media/inter700.woff2) format("woff2")}}
@font-face{{font-family:Inter;font-weight:800;src:url(media/inter800.woff2) format("woff2")}}
html,body{{margin:0;background:#060607}}
#root{{position:relative;width:{W}px;height:{H}px;overflow:hidden;background:#0b0b0c;font-family:Inter,system-ui,sans-serif;perspective:1600px}}
.bg{{position:absolute;inset:0;background:radial-gradient(120% 90% at 50% 40%,#1c1c1f 0%,#0c0c0d 55%,#050506 100%)}}
.glow{{position:absolute;width:1400px;height:1400px;left:-200px;top:-500px;border-radius:50%;background:radial-gradient(circle,rgba(254,222,92,0.09),rgba(254,222,92,0) 60%)}}
.grain{{position:absolute;inset:0;opacity:.06;mix-blend-mode:overlay;background-image:url(media/grain.png);z-index:88;pointer-events:none}}
.vig{{position:absolute;inset:0;background:radial-gradient(ellipse at center,rgba(0,0,0,0) 60%,rgba(0,0,0,.5) 100%);z-index:89;pointer-events:none}}
.full{{position:absolute;inset:0;width:100%;height:100%;overflow:hidden}}
.cover{{width:100%;height:100%;object-fit:cover;display:block}}
.card{{position:absolute;transform-style:preserve-3d}}
.card .frame{{position:relative;width:100%;height:100%;border-radius:26px;overflow:hidden;box-shadow:0 40px 100px rgba(0,0,0,.6),0 0 0 1px rgba(255,255,255,.09)}}
.tagfade{{position:absolute;left:0;right:0;bottom:0;height:150px;background:linear-gradient(0deg,rgba(0,0,0,.75),rgba(0,0,0,0))}}
.tag{{position:absolute;left:28px;bottom:24px;display:flex;align-items:center;gap:12px;color:#fff;white-space:nowrap}}
.tag b{{font-family:Anton;font-weight:400;font-size:30px;letter-spacing:1.5px}}
.tag em{{font-style:normal;font-weight:500;font-size:20px;color:rgba(255,255,255,.7)}}
.tagbar{{width:6px;height:32px;background:{Y};border-radius:3px}}
.aitag{{position:absolute;right:22px;top:20px;padding:6px 14px;border-radius:999px;background:{Y};color:#111;font-size:15px;font-weight:800;letter-spacing:1.5px;z-index:5}}
.full .aitag{{right:40px;top:110px}}
.pola{{position:absolute;background:#f4f1ea;padding:18px 18px 70px;box-shadow:0 30px 70px rgba(0,0,0,.5)}}
.pcap{{position:absolute;left:24px;bottom:20px;font-size:26px;font-weight:600;color:#333;font-style:italic}}
.browser{{position:absolute;border-radius:16px;overflow:hidden;background:#1d1d20;box-shadow:0 40px 100px rgba(0,0,0,.6),0 0 0 1px rgba(255,255,255,.1);transform-style:preserve-3d}}
.bbar{{height:44px;display:flex;align-items:center;gap:9px;padding:0 18px;background:#2a2a2e;color:rgba(255,255,255,.75);font-size:17px;font-weight:600}}
.bbar i{{width:13px;height:13px;border-radius:50%;background:#555}}
.bbar i:nth-child(1){{background:#ff5f57}}.bbar i:nth-child(2){{background:#febc2e}}.bbar i:nth-child(3){{background:#28c840}}
.bbar span{{margin-left:16px;padding:5px 16px;border-radius:8px;background:#1b1b1e;flex:1;max-width:520px}}
.bbar em{{margin-left:auto;font-style:normal;color:{Y};font-size:14px;letter-spacing:2px;font-weight:800}}
.head{{position:absolute;font-family:Anton;font-weight:400;line-height:1.02;letter-spacing:.5px;color:#fff;text-transform:uppercase}}
.head .mask{{overflow:hidden;padding-bottom:.04em}}
.head .ln{{display:block}}
.kick{{font-family:Inter;font-weight:800;font-size:22px;letter-spacing:7px;margin-bottom:18px}}
.hsub{{font-family:Inter;font-size:30px;font-weight:600;letter-spacing:0;text-transform:none;color:rgba(255,255,255,.72);margin-top:20px}}
.num{{position:absolute;font-family:Anton;line-height:1;font-style:italic}}
.digits{{display:inline-flex}}
.dcol{{display:inline-block;height:1.04em;overflow:hidden}}
.dstrip{{display:flex;flex-direction:column}}
.dstrip span{{height:1.04em;line-height:1.04em}}
.dchar{{display:inline-block}}
.nlab{{font-family:Inter;font-style:normal;font-size:24px;font-weight:800;letter-spacing:6px;color:rgba(255,255,255,.8);margin-top:16px}}
.chips{{position:absolute;display:flex;flex-direction:column;gap:18px}}
.chip{{display:flex;align-items:center;gap:16px;padding:16px 28px;border-radius:999px;background:rgba(18,18,20,.82);box-shadow:inset 0 0 0 1px rgba(255,255,255,.14);
  color:#fff;font-size:30px;font-weight:800;letter-spacing:1px;white-space:nowrap;backdrop-filter:blur(6px)}}
.chip .dot{{width:13px;height:13px;border-radius:50%;background:rgba(255,255,255,.5)}}
.chip.yellow{{background:{Y};color:#111}} .chip.yellow .dot{{background:#111}}
.chip.red{{background:{RED};color:#fff}} .chip.red .dot{{background:#fff}}
.tickets{{position:absolute;display:flex;flex-direction:column;gap:26px}}
.ticket{{position:relative;display:inline-flex;flex-direction:column;background:#efebe2;color:#1a1a1a;padding:12px 26px 14px;font-family:"Courier New",monospace;
  box-shadow:0 14px 30px rgba(0,0,0,.35);width:max-content}}
.ticket small{{font-size:17px;letter-spacing:3px;color:#777}}
.ticket b{{font-size:46px;font-weight:700;letter-spacing:2px}}
.tstamp{{position:absolute;right:-30px;top:-14px;padding:4px 12px;border:4px solid {RED};color:{RED};font-family:Inter;font-weight:900;font-size:22px;
  letter-spacing:2px;transform:rotate(9deg);background:rgba(239,235,226,.9)}}
.stamp{{position:absolute;padding:6px 26px;border:7px solid;border-radius:10px;font-family:Inter;font-weight:900;letter-spacing:4px;white-space:nowrap;
  background:rgba(10,10,10,.25);mix-blend-mode:normal}}
.quote{{position:absolute;top:0;bottom:120px;display:flex;flex-direction:column;justify-content:center;color:#fff;font-weight:700;line-height:1.22;letter-spacing:-.5px}}
.qmark{{font-family:Anton;font-size:2.6em;line-height:.6;color:{Y};height:.55em}}
.qwho{{display:flex;align-items:center;gap:14px;margin-top:30px;font-size:24px;font-weight:800;letter-spacing:5px;color:rgba(255,255,255,.75)}}
.qwho span{{width:44px;height:4px;background:{Y}}}
.paper{{position:absolute;inset:0;background:radial-gradient(120% 100% at 50% 40%,#e3dfd8,#c9c4bc)}}
.paper ~ .head .ln{{}}
.stage{{position:absolute;inset:0;background:radial-gradient(90% 80% at 50% 45%,#19191c,#050506);overflow:hidden}}
.persp{{position:absolute;inset:0;perspective:1400px}}
.n303{{position:absolute;top:120px;left:0;right:0;text-align:center;font-family:Anton;font-size:520px;line-height:1;transform-style:preserve-3d}}
.n303 span{{display:block}} .n303 .back{{color:#7a560e}} .n303 .front{{position:absolute;left:0;right:0;top:0}}
.uline{{position:absolute;left:640px;right:640px;top:790px;height:8px;border-radius:4px;background:{Y};transform-origin:left;box-shadow:0 0 30px rgba(254,222,92,.6)}}
.b3lab{{position:absolute;left:0;right:0;top:830px;text-align:center;font-size:30px;font-weight:800;letter-spacing:7px;color:rgba(255,255,255,.8)}}
.date{{position:absolute;left:150px;top:300px;perspective:1000px}}
.dbar{{position:absolute;left:-44px;top:8px;width:12px;height:300px;border-radius:6px;background:{Y};transform-origin:top;box-shadow:0 0 30px rgba(254,222,92,.45)}}
.d1{{font-family:Anton;font-size:120px;color:#fff;line-height:1.02;transform-origin:50% 100%}}
.d2{{font-family:Anton;font-size:150px;color:{Y};line-height:1.02;transform-origin:50% 100%}}
.dsub{{font-size:30px;font-weight:600;color:rgba(255,255,255,.8);margin-top:14px}}
.chap{{position:absolute;inset:0;background:#08080a;display:flex;flex-direction:column;align-items:center;justify-content:center}}
.cnum{{font-size:24px;font-weight:800;letter-spacing:10px;color:{Y}}}
.crule{{width:120px;height:3px;background:rgba(255,255,255,.4);margin:26px 0 22px}}
.ctitle{{font-family:Anton;font-size:150px;color:#fff;text-transform:uppercase;letter-spacing:2px}}
.vs{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;gap:90px}}
.vcol{{width:640px;text-align:center}}
.vcol small{{display:block;font-size:24px;font-weight:800;letter-spacing:6px;color:{RED};margin-bottom:22px}}
.vcol b{{font-family:Anton;font-weight:400;font-size:150px;line-height:1.02;text-transform:uppercase}}
.vdiv{{width:4px;height:520px;background:rgba(255,255,255,.35);transform-origin:top}}
.paper ~ .vs .vdiv{{background:rgba(0,0,0,.3)}}
s.sk{{text-decoration:line-through;text-decoration-color:{RED};text-decoration-thickness:12px;opacity:.75}}
.chart{{position:absolute;inset:0}}
.btitle{{position:absolute;left:0;right:0;top:90px;text-align:center;font-size:24px;font-weight:800;letter-spacing:7px;color:rgba(255,255,255,.8)}}
.bar{{position:absolute;border-radius:10px 10px 0 0;transform-origin:bottom}}
.bv{{position:absolute;left:0;right:0;top:-54px;text-align:center;font-family:Anton;font-size:44px;color:#fff}}
.blab{{position:absolute;text-align:center;font-size:19px;font-weight:800;letter-spacing:2px;color:rgba(255,255,255,.65)}}
.bline{{position:absolute;left:300px;right:300px;height:0;border-top:4px dashed {RED};transform-origin:left}}
.bline span{{position:absolute;right:0;top:-44px;color:{RED};font-size:22px;font-weight:900;letter-spacing:4px}}
.phonebox{{position:absolute;top:130px;width:500px;height:640px;border-radius:50px;background:#111;box-shadow:0 0 0 3px #2a2a2c,0 50px 100px rgba(0,0,0,.6);
  padding:90px 28px 28px;display:flex;flex-direction:column;gap:18px;box-sizing:border-box}}
.ptop{{position:absolute;left:0;right:0;top:34px;text-align:center;color:#fff;font-weight:700;font-size:22px}}
.msg{{max-width:78%;padding:16px 22px;border-radius:24px;font-size:28px;font-weight:600}}
.msg.me{{align-self:flex-end;background:#2f7cf6;color:#fff}}
.msg.typing{{align-self:flex-start;background:#2a2a2d;color:#aaa;font-size:40px;line-height:.6;padding:16px 26px 26px}}
.subcard{{position:absolute;left:560px;top:300px;width:800px;height:430px;border-radius:36px;background:rgba(22,22,24,.96);box-shadow:0 0 0 1px rgba(255,255,255,.12),0 50px 120px rgba(0,0,0,.6);
  display:flex;flex-direction:column;align-items:center;justify-content:center}}
.ring{{width:120px;height:120px;border-radius:50%;border:4px solid {Y};display:flex;align-items:center;justify-content:center;background:#0b0b0c;overflow:hidden}}
.ring img{{width:104px;height:24px}}
.sname{{font-size:44px;font-weight:800;color:#fff;margin-top:22px}}
.sdesc{{font-size:24px;color:rgba(255,255,255,.6);margin-top:8px}}
.sbtn{{position:relative;margin-top:30px;width:300px;height:68px;border-radius:999px;background:{Y};color:#111;font-size:30px;font-weight:800;display:flex;align-items:center;justify-content:center}}
.sbtn span{{position:absolute}} .sdone{{opacity:0}}
.bell{{position:absolute;right:190px;bottom:62px;font-size:44px}}
.cursor{{position:absolute;left:420px;top:330px;width:34px;height:34px;border-radius:50%;background:rgba(255,255,255,.85);box-shadow:0 0 0 6px rgba(255,255,255,.25)}}
.capw{{position:absolute;left:0;right:0;bottom:196px;display:flex;justify-content:center;z-index:85;pointer-events:none}}
.capb{{padding:12px 26px;border-radius:14px;background:rgba(12,12,14,.86);color:#fff;font-size:34px;font-weight:800;letter-spacing:.3px;
  box-shadow:0 0 0 1px rgba(255,255,255,.08);max-width:1500px;text-align:center}}
.brick{{position:absolute;background:#2a2a2d;border-radius:4px;box-shadow:inset 0 0 0 1px rgba(255,255,255,.05)}}
.logo{{position:absolute;left:46px;top:40px;width:196px;height:46px;overflow:hidden;z-index:86;opacity:.9}}
.eq{{position:absolute;left:0;right:0;top:200px;text-align:center;font-family:Anton;font-size:130px;color:#fff;text-transform:uppercase}}
.eopts{{position:absolute;left:0;right:0;top:400px;display:flex;justify-content:center;align-items:center;gap:40px}}
.eopts span{{font-family:Anton;font-size:120px;color:#111;background:{Y};padding:6px 40px;border-radius:24px}}
.eopts span+i+span{{background:{RED};color:#fff}}
.eopts i{{font-size:40px;color:rgba(255,255,255,.6);font-style:italic;font-weight:600}}
.ecom{{position:absolute;left:660px;top:640px;width:600px;height:76px;border-radius:999px;background:#1e1e21;display:flex;align-items:center;gap:20px;padding:0 24px;box-sizing:border-box}}
.eav{{width:44px;height:44px;border-radius:50%;background:{Y}}}
.etype{{color:rgba(255,255,255,.75);font-size:28px;font-weight:600}}
.elogo{{position:absolute;left:50%;top:800px;width:520px;height:122px;overflow:hidden;margin-left:-260px}}
.efoot{{position:absolute;left:0;right:0;top:960px;text-align:center;color:rgba(255,255,255,.6);font-size:24px;font-weight:600;letter-spacing:2px}}
"""


def build():
    os.makedirs(MEDIA, exist_ok=True)
    shutil.copy(os.path.join(HERE, "node_modules", "gsap", "dist", "gsap.min.js"), os.path.join(OUT, "gsap.min.js"))
    fs = os.path.join(HERE, "node_modules", "@fontsource")
    for src, dst in [("anton/files/anton-latin-400-normal.woff2", "anton.woff2"), ("inter/files/inter-latin-500-normal.woff2", "inter500.woff2"),
                     ("inter/files/inter-latin-700-normal.woff2", "inter700.woff2"), ("inter/files/inter-latin-800-normal.woff2", "inter800.woff2")]:
        shutil.copy(os.path.join(fs, src), os.path.join(MEDIA, dst))
    shutil.copy(os.path.join(HERE, "..", "kohli_countdown", "assets", "logo.png"), os.path.join(MEDIA, "logo.png"))
    if not os.path.exists(os.path.join(MEDIA, "grain.png")):
        import numpy as np
        g = (np.random.default_rng(3).normal(128, 40, (512, 512))).clip(0, 255).astype("uint8")
        Image.fromarray(g, "L").save(os.path.join(MEDIA, "grain.png"))
    body = ['<div class="bg"></div><div class="glow" id="glow"></div>']
    for start, dur, z, h in sorted(els, key=lambda e: e[0]):
        body.append(h)
    # logo in a fixed-size box: a bare <img> with only a height was occasionally drawn stretched across the frame
    body.append(f'<div class="logo clip" id="logo" data-start="0" data-duration="{round(TOTAL - TAIL, 2)}">'
                f'<img src="media/logo.png" width="196" height="46" style="width:196px;height:46px;display:block"></div>')
    body.append('<div class="grain"></div><div class="vig"></div>')
    page = f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div id="root" data-composition-id="root" data-width="{W}" data-height="{H}" data-fps="{FPS}" data-duration="{TOTAL}">
{chr(10).join(body)}
</div>
<script src="gsap.min.js"></script>
<script>
const tl = gsap.timeline({{paused:true}});
tl.fromTo("#glow",{{x:-200,y:0}},{{x:900,y:200,duration:{TOTAL},ease:"sine.inOut"}},0);
{chr(10).join(js)}
tl.set({{}},{{}},{TOTAL});
window.__timelines = window.__timelines || {{}};
window.__timelines["root"] = tl;
</script></body></html>"""
    with open(os.path.join(OUT, "index.html"), "w") as f:
        f.write(page)
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    with open(os.path.join(HERE, "out", "events.json"), "w") as f:
        json.dump({"total": TOTAL, "lead": LEAD, "beats": BEAT, "events": sorted(EVENTS), "nat": NAT}, f)
    # report what's unused, so nothing the user sent gets forgotten
    pool = [os.path.join(d, f) for d in (P, C, A, BR) for f in sorted(os.listdir(os.path.join(HERE, d)))]  # bg shots are optional
    unused = [p for p in pool if p not in USED and not p.endswith(".gif")]
    print(f"{len(els)} elements, {len(js)} animation steps, {TOTAL:.1f}s, {len(USED)} assets used once each")
    if unused:
        print("UNUSED:", unused)


if __name__ == "__main__":
    build()

#!/usr/bin/env python3
"""Virender Sehwag tribute reel (1080x1920, ~73 s), full screen throughout.

    python3 build_clips.py   ->  watermark-free full-screen clips + Ganguly's vocal-only quote (once)
    python3 reel.py          ->  reel/index.html + out/soundtrack.wav, then render with HyperFrames (see make.sh)

Same animation system as the Rajat reel (serif + condensed type, stamps, cards, captions) merged with the
Centurion reel's rolling gold numbers and date flips, but every scene sits on full-screen footage. Timing
comes from out/beats.json (voiceover lines, with Ganguly's own clip inserted after "...sums him up
perfectly"). "True cricket fans follow" runs through the reel: a pulsing badge at the top, three slide-in
pills and the spoken tap-to-follow moment at ~0:39.
"""
import html
import json
import os
import shutil
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "kohli_countdown"))
sys.path.insert(0, os.path.join(ROOT, "doc_video"))
import music  # noqa: E402
import sfx  # noqa: E402
from soundtrack import WARM, arps, norm, pad, pulse, reverb, section  # noqa: E402

OUT = os.path.join(HERE, "reel")
MEDIA = os.path.join(OUT, "media")
ASSETS = os.path.join(HERE, "assets")
W, H, FPS = 1080, 1920, 30
Y, INK, RED = "#FEDE5C", "#121214", "#E5484D"
SR = sfx.SR
LEAD, GAP, END_HOLD = 0.25, 0.3, 1.8
BAND_X, BAND_Y = 64, 1130  # all on-screen text lives in this lower band, clear of faces and the IG buttons

LINES = [
    ("hook", "There was something special about Virender Sehwag."),
    ("manual", "Something no coaching manual could ever explain."),
    ("survive", "Other openers came to survive the new ball."),
    ("destroy", "Viru came to destroy it."),
    ("kid", "For a 2000s kid, it was simple. If Sehwag was batting, nobody left the TV."),
    ("multan", "Multan, 2004. Three hundred and nine. The first Indian ever to score a Test triple hundred."),
    ("chennai", "Chennai, 2008. Three hundred in just 278 balls. The fastest triple century in Test history."),
    ("wc", "The 2011 World Cup. Five matches, and five times the very first ball went for four."),
    ("follow", "If you're a true cricket fan, you must follow this page."),
    ("tease", "Because what Sourav Ganguly said next sums him up perfectly."),
    ("ganguly", ""),
    ("hundred", "And when the hundred came, the helmet came off, the red handkerchief came out, and he smiled like he was batting in his backyard."),
    ("trophies", "Some players give you trophies."),
    ("runs", "Some give you runs."),
    ("childhood", "Viru gave us our childhood."),
    ("vote", "Sehwag or Gayle: who was the most dangerous opener? One word in the comments."),
]

os.makedirs(MEDIA, exist_ok=True)
els, js, events = [], [], []
_n = [0]


def nid(p):
    _n[0] += 1
    return f"{p}{_n[0]}"


def add(h):
    els.append(h)


def anim(a):
    js.append(a)


# ----------------------------------------------------------------------------- timing

NO_VO = set()


def load_times():
    """{line_id: (start, end)} on the reel timeline, plus total length."""
    path = os.path.join(HERE, "out", "beats.json")
    if os.path.exists(path):
        b = json.load(open(path))
        times = {k: tuple(v) for k, v in b["lines"].items()}
        NO_VO.update(b.get("no_vo", []))
        return times, round(b["vo_end"] + END_HOLD, 2), True
    t, times = LEAD, {}
    for lid, txt in LINES:
        d = len(txt.split()) / 2.6 + 0.2
        times[lid] = (round(t, 2), round(t + d, 2))
        t += d + GAP
    return times, round(t - GAP + END_HOLD, 2), False


T, TOTAL, HAS_VO = load_times()


def at(lid, off=0.0):
    s, e = T[lid]
    return round((e + off) if off < 0 else (s + off), 2)


def span(lid, frac):
    s, e = T[lid]
    return round(s + (e - s) * frac, 2)


def until_next(lid):
    """From this line's start to the next line's start (scenes hold through the gap)."""
    ids = [k for k, _ in LINES]
    k = ids.index(lid)
    end = T[ids[k + 1]][0] if k + 1 < len(ids) else TOTAL
    return round(end - T[lid][0], 2)


# ----------------------------------------------------------------------------- assets

def asset(slot):
    for ext in (".mp4", ".png", ".jpg", ".jpeg", ".webp"):
        p = os.path.join(ASSETS, slot + ext)
        if os.path.exists(p):
            dst = os.path.join(MEDIA, slot + ext)
            if not os.path.exists(dst) or os.path.getmtime(p) > os.path.getmtime(dst):
                shutil.copy(p, dst)
            return "media/" + slot + ext, ext == ".mp4"
    return None, False


def media_html(slot, start, dur, hint, cls=""):
    rel, video = asset(slot)
    if rel is None:
        return (f'<div class="ph {cls}"><svg viewBox="0 0 100 100"><circle cx="50" cy="36" r="17"/>'
                f'<path d="M14 100c2-26 18-38 36-38s34 12 36 38z"/></svg><span>{html.escape(hint)}</span></div>')
    if video:
        return (f'<video class="clip {cls}" src="{rel}" muted playsinline data-start="{start}" data-duration="{dur}" '
                f'data-media-start="0"></video>')
    return f'<img class="{cls}" src="{rel}">'


# ----------------------------------------------------------------------------- components

def scene(start, dur, kind="dark"):
    """Background panel. 'yellow' scenes wipe in on a diagonal; dark ones fade."""
    i = nid("bg")
    add(f'<div id="{i}" class="bg {kind} clip" data-start="{start}" data-duration="{dur}"><div class="band"></div></div>')
    if kind == "yellow":
        anim(f'tl.fromTo("#{i}",{{clipPath:"polygon(0 0,0 0,0 100%,0 100%)"}},'
             f'{{clipPath:"polygon(0 0,130% 0,100% 100%,-30% 100%)",duration:0.55,ease:"expo.inOut"}},{start})')
    else:
        anim(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.3}},{start})')


def photo(slot, start, dur, hint, x, y, w, h, tag=None, tilt=0, z=20, enter="up"):
    i = nid("ph")
    events.append((start, "whoosh"))
    tg = f'<div class="ptag">{html.escape(tag)}</div>' if tag else ""
    add(f'<div id="{i}" class="photo clip" data-start="{start}" data-duration="{dur}" '
        f'style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;z-index:{z};transform:rotate({tilt}deg)">'
        f'<div class="pframe">{media_html(slot, start, dur, hint)}</div>{tg}</div>')
    frm = {"up": "y:240,opacity:0", "left": "x:-700,opacity:0", "right": "x:700,opacity:0", "pop": "scale:0.6,opacity:0"}[enter]
    anim(f'tl.fromTo("#{i}",{{{frm}}},{{x:0,y:0,scale:1,opacity:1,duration:0.75,ease:"expo.out"}},{start})')
    anim(f'tl.fromTo("#{i} .pframe > *",{{scale:1.12}},{{scale:1,duration:{dur},ease:"none"}},{start})')
    anim(f'tl.to("#{i}",{{opacity:0,y:-120,duration:0.35,ease:"power2.in"}},{round(start + dur - 0.35, 2)})')
    return i


def fullbleed(slot, start, dur, hint, pos="50% 50%", fg_h=1200, fg_top=270, tag=None, force_front=False, extra=""):
    """Media filling the whole 9:16 frame. Portrait media covers it; landscape media sits large in front of a
    blurred, darkened copy of itself (no upscaling past what the source can hold). Dark fades top and bottom
    keep the logo, text and captions readable."""
    i = nid("fb")
    events.append((start, "whoosh"))
    rel, video = asset(slot)
    portrait = False
    if rel and not video:
        from PIL import Image
        with Image.open(os.path.join(OUT, rel)) as im:
            portrait = im.width / im.height < 0.75 and not force_front
    elif rel and video:
        portrait = True
    tg = f'<div class="fbtag">{html.escape(tag)}</div>' if tag else ""
    if portrait:
        inner = f'<div class="fbcover" id="{i}m">{media_html(slot, start, dur, hint)}</div>'
    else:
        back = f'<img class="fbback" src="{rel}">' if rel else ""
        inner = (f'{back}<div class="fbfront" id="{i}m" style="top:{fg_top}px;height:{fg_h}px">'
                 f'{media_html(slot, start, dur, hint).replace("<img ", f"<img style=\"object-position:{pos}\" ", 1)}</div>')
    shade = "fbshade cover" if portrait else "fbshade"
    add(f'<div id="{i}" class="fb {extra} clip" data-start="{start}" data-duration="{dur}">{inner}<div class="{shade}"></div>{tg}</div>')
    anim(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.35}},{start})')
    anim(f'tl.fromTo("#{i}m",{{scale:1.1}},{{scale:1,duration:{dur},ease:"none"}},{start})')
    if tag:
        anim(f'tl.fromTo("#{i} .fbtag",{{x:-60,opacity:0}},{{x:0,opacity:1,duration:0.5,ease:"expo.out"}},{round(start + 0.3, 2)})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.3}},{round(start + dur - 0.3, 2)})')


def cutout(slot, start, dur, hint, x, y, h, z=15):
    """A player cut-out (assets/<slot>.png with transparency) standing on the bottom of the media area."""
    i = nid("co")
    rel, _ = asset(slot)
    if rel:
        from PIL import Image
        with Image.open(os.path.join(OUT, rel)) as im:
            x = round((W - h * im.width / im.height) / 2)  # centre real cut-outs
    inner = (f'<img src="{rel}" style="height:{h}px">' if rel else
             f'<div class="ph cut" style="height:{h}px;width:{round(h * 0.62)}px"><svg viewBox="0 0 100 100"><circle cx="50" cy="30" r="15"/>'
             f'<path d="M12 100c3-34 18-50 38-50s35 16 38 50z"/></svg><span>{html.escape(hint)}</span></div>')
    add(f'<div id="{i}" class="cutout clip" data-start="{start}" data-duration="{dur}" style="left:{x}px;top:{y}px;z-index:{z}">{inner}</div>')
    anim(f'tl.fromTo("#{i}",{{y:120,opacity:0}},{{y:0,opacity:1,duration:0.8,ease:"expo.out"}},{start})')
    anim(f'tl.fromTo("#{i}",{{scale:1}},{{scale:1.05,duration:{dur},ease:"none"}},{start})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.3}},{round(start + dur - 0.3, 2)})')


def words(lines, start, dur, y, size=120, colors=None, font="anton", align="center", stagger=0.12, z=30, sfx_kind="soft", ink=False):
    """Stacked headline lines that rise in from behind a mask."""
    i = nid("w")
    events.append((start + 0.1, sfx_kind))
    colors = colors or ["#fff"] * len(lines)
    style = lambda c: f"color:transparent;-webkit-text-stroke:6px {INK}" if c == "outline" else f"color:{c}"  # noqa: E731
    rows = "".join(f'<div class="mask"><div class="ln" id="{i}l{k}" style="{style(c)}">{t}</div></div>'
                   for k, (t, c) in enumerate(zip(lines, colors)))
    cls = "tband" if align == "band" else ""
    add(f'<div id="{i}" class="words {font} {cls} clip" data-start="{start}" data-duration="{dur}" '
        f'style="top:{y}px;font-size:{size}px;text-align:{"left" if cls else align};z-index:{z}">{rows}</div>')
    for k in range(len(lines)):
        anim(f'tl.fromTo("#{i}l{k}",{{yPercent:110}},{{yPercent:0,duration:0.7,ease:"expo.out"}},{round(start + 0.05 + stagger * k, 2)})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.3}},{round(start + dur - 0.3, 2)})')
    return i


def label(txt, start, dur, y, color=Y, bg=None, size=34, z=31, band=False):
    i = nid("lb")
    style = (f"left:{BAND_X}px;transform:none;" if band else "") + f"top:{y}px;font-size:{size}px;color:{color};" + (f"background:{bg};padding:10px 22px;border-radius:10px;" if bg else "")
    add(f'<div id="{i}" class="label clip" data-start="{start}" data-duration="{dur}" style="{style}z-index:{z}">{html.escape(txt)}</div>')
    anim(f'tl.fromTo("#{i}",{{opacity:0,y:16}},{{opacity:1,y:0,duration:0.5,ease:"expo.out"}},{start})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.25}},{round(start + dur - 0.25, 2)})')


def squad_card(start, dur, team, event, fmt, rows, y=520, stamp=None, stamp_at=None, tag=None):
    """Paper team-sheet card. rows: list of (text, kind) where kind is name/cap/vc/in/empty."""
    i = nid("sq")
    events.append((start, "whoosh"))
    body = []
    for k, (txt, kind) in enumerate(rows):
        badge = {"cap": '<b class="cb">C</b>', "vc": '<b class="cb">VC</b>', "in": '<b class="cb in">IN</b>'}.get(kind, "")
        body.append(f'<div class="srow {kind}" id="{i}r{k}">{html.escape(txt)}{badge}</div>')
    st = f'<div class="stamp" id="{i}x">{html.escape(stamp)}</div>' if stamp else ""
    tg = f'<div class="sqtag" id="{i}t">{html.escape(tag)}</div>' if tag else ""
    add(f'<div id="{i}" class="squad clip" data-start="{start}" data-duration="{dur}" style="top:{y}px">{tg}'
        f'<div class="shead">{html.escape(team)}</div><div class="sev">{html.escape(event)}</div>'
        f'<div class="sfmt">{html.escape(fmt)}</div><div class="sbody">{"".join(body)}</div>{st}'
        f'<div class="sfoot">SQUAD</div></div>')
    anim(f'tl.fromTo("#{i}",{{y:300,opacity:0,rotation:-4}},{{y:0,opacity:1,rotation:0,duration:0.8,ease:"expo.out"}},{start})')
    if tag:
        anim(f'tl.fromTo("#{i}t",{{scale:0,rotation:-20}},{{scale:1,rotation:-4,duration:0.5,ease:"back.out(2)"}},{round(start + 0.5, 2)})')
    for k in range(len(rows)):
        anim(f'tl.fromTo("#{i}r{k}",{{opacity:0,x:-30}},{{opacity:1,x:0,duration:0.4,ease:"expo.out"}},{round(start + 0.45 + 0.18 * k, 2)})')
    if stamp:
        t = stamp_at or round(start + dur * 0.55, 2)
        events.append((t, "stamp"))
        anim(f'tl.fromTo("#{i}x",{{scale:2.6,opacity:0,rotation:-14}},{{scale:1,opacity:1,rotation:-8,duration:0.35,ease:"power4.in"}},{t})')
        anim(f'tl.to("#{i}",{{x:"+=8",duration:0.05,yoyo:true,repeat:3}},{round(t + 0.33, 2)})')
    anim(f'tl.to("#{i}",{{opacity:0,y:-140,duration:0.35,ease:"power2.in"}},{round(start + dur - 0.35, 2)})')
    return i


def big_number(num, sub, start, dur, y=520, size=520, color="#fff", strike_at=None, outline_at=None):
    i = nid("bn")
    events.append((start + 0.05, "impact"))
    add(f'<div id="{i}" class="bign clip" data-start="{start}" data-duration="{dur}" style="top:{y}px">'
        f'<div class="bnum anton" id="{i}n" style="font-size:{size}px;color:{color}">{num}</div>'
        f'<div class="bsub" id="{i}s">{html.escape(sub)}</div><div class="strike" id="{i}k"></div></div>')
    anim(f'tl.fromTo("#{i}n",{{scale:1.5,opacity:0}},{{scale:1,opacity:1,duration:0.55,ease:"expo.out"}},{start})')
    anim(f'tl.fromTo("#{i}s",{{opacity:0,letterSpacing:"30px"}},{{opacity:1,letterSpacing:"14px",duration:0.8,ease:"expo.out"}},{round(start + 0.2, 2)})')
    if outline_at:
        anim(f'tl.to("#{i}n",{{color:"rgba(0,0,0,0)",webkitTextStroke:"5px #fff",duration:0.3}},{outline_at})')
    if strike_at:
        events.append((strike_at, "pop"))
        anim(f'tl.fromTo("#{i}k",{{scaleX:0}},{{scaleX:1,duration:0.35,ease:"expo.out"}},{strike_at})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.3}},{round(start + dur - 0.3, 2)})')
    return i


def ruler(start, dur, frm, to, y=1120, step_at=None):
    """Age ruler sliding so `to` lands under the centre marker."""
    i = nid("ru")
    events.append((start + 0.1, "roll"))
    lo, hi, px = 24, 40, 170
    ticks = "".join(f'<div class="tk{" maj" if a % 1 == 0 else ""}" style="left:{(a - lo) * px}px"><span>{a}</span></div>'
                    for a in range(lo, hi + 1))
    minor = "".join(f'<div class="tm" style="left:{(a - lo) * px + px * f}px"></div>' for a in range(lo, hi) for f in (0.25, 0.5, 0.75))
    add(f'<div id="{i}" class="ruler clip" data-start="{start}" data-duration="{dur}" style="top:{y}px">'
        f'<div class="rtrack" id="{i}t">{ticks}{minor}</div><div class="rmark"></div></div>')
    pos = lambda a: W / 2 - (a - lo) * px  # noqa: E731
    anim(f'tl.fromTo("#{i}t",{{x:{pos(frm)}}},{{x:{pos(to[0])},duration:1.4,ease:"expo.out"}},{start + 0.1})')
    for k, a in enumerate(to[1:]):
        t = (step_at or [])[k]
        events.append((t, "tick"))
        anim(f'tl.to("#{i}t",{{x:{pos(a)},duration:0.6,ease:"expo.out"}},{t})')
    anim(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.3}},{start})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.3}},{round(start + dur - 0.3, 2)})')


def tiles(start, dur, y=640, hi=None, hi_at=None, door=None, door_at=None, dim_others=True):
    """TEST / ODI / T20 format tiles; `hi` gets the yellow check, `door` swings open like a door."""
    i = nid("ti")
    events.append((start, "whoosh"))
    spec = [("TEST", "5 DAYS"), ("ODI", "50 OVERS"), ("T20", "20 OVERS")]
    cards = "".join(f'<div class="tile" id="{i}{k}"><div class="tt anton">{a}</div><div class="ts">{b}</div>'
                    f'<div class="tick" id="{i}{k}c">✓</div></div>' for k, (a, b) in enumerate(spec))
    add(f'<div id="{i}" class="tiles clip" data-start="{start}" data-duration="{dur}" style="top:{y}px">{cards}</div>')
    for k in range(3):
        anim(f'tl.fromTo("#{i}{k}",{{y:160,opacity:0}},{{y:0,opacity:1,duration:0.6,ease:"expo.out"}},{round(start + 0.1 * k, 2)})')
    if hi is not None:
        t = hi_at or round(start + 0.8, 2)
        events.append((t, "pop"))
        anim(f'tl.to("#{i}{hi}",{{scale:1.12,backgroundColor:"{Y}",color:"{INK}",duration:0.4,ease:"back.out(2)"}},{t})')
        anim(f'tl.fromTo("#{i}{hi}c",{{scale:0}},{{scale:1,duration:0.4,ease:"back.out(3)"}},{round(t + 0.15, 2)})')
        if dim_others:
            for k in range(3):
                if k != hi:
                    anim(f'tl.to("#{i}{k}",{{opacity:0.35,duration:0.4}},{t})')
    if door is not None:
        t = door_at or round(start + 0.9, 2)
        events.append((t, "whoosh"))
        anim(f'tl.to("#{i}{door}",{{opacity:1,boxShadow:"0 0 80px rgba(254,222,92,.9)",duration:0.3}},{t})')
        anim(f'tl.to("#{i}{door}",{{rotationY:-58,duration:0.9,ease:"power3.inOut"}},{round(t + 0.25, 2)})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.3}},{round(start + dur - 0.3, 2)})')
    return i


def checklist(items, start, dur, y, times):
    """items: (text, ok). Each row ticks or crosses at its time."""
    i = nid("ck")
    rows = "".join(f'<div class="crow {"ok" if ok else "no"}" id="{i}{k}"><span class="cm">{"✓" if ok else "✕"}</span>'
                   f'<span class="ct">{html.escape(t)}</span></div>' for k, (t, ok) in enumerate(items))
    add(f'<div id="{i}" class="check clip" data-start="{start}" data-duration="{dur}" style="top:{y}px">{rows}</div>')
    for k, t in enumerate(times):
        events.append((t, "pop"))
        anim(f'tl.fromTo("#{i}{k}",{{x:-120,opacity:0}},{{x:0,opacity:1,duration:0.5,ease:"expo.out"}},{t})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.3}},{round(start + dur - 0.3, 2)})')


def captions(lid):
    """Bottom subtitles: the line split into 2-4 word chunks spread over the spoken time."""
    s, e = T[lid]
    txt = dict(LINES)[lid].upper()
    ws = txt.split()
    chunks, cur = [], []
    for w in ws:
        cur.append(w)
        if len(cur) >= 3 or w.endswith((",", ".", "?")):
            chunks.append(" ".join(cur))
            cur = []
    if cur:
        chunks.append(" ".join(cur))
    total_chars = sum(len(c) for c in chunks)
    t = s
    for c in chunks:
        d = (e - s) * len(c) / total_chars
        i = nid("cap")
        add(f'<div id="{i}" class="subt clip" data-start="{round(t, 2)}" data-duration="{round(d, 2)}">{html.escape(c)}</div>')
        anim(f'tl.fromTo("#{i}",{{scale:0.86,opacity:0}},{{scale:1,opacity:1,duration:0.18,ease:"back.out(2)"}},{round(t, 2)})')
        t += d


# ----------------------------------------------------------------------------- components new in this reel

def fb(slot, start, dur, hint="", pos="50% 50%", tag=None, front=False, blur=False):
    """Full-screen media (see fullbleed). front=True forces the blurred-backdrop + large-front layout for small
    photos; blur=True turns the media into a soft, dark backdrop for graphics."""
    fullbleed(slot, start, dur, hint, pos=pos, tag=tag, force_front=front, extra="blurred" if blur else "")


def date_flip(a, b, start, dur, y=380):
    i = nid("df")
    events.append((start, "tick"))
    add(f'<div id="{i}" class="dflip clip" data-start="{start}" data-duration="{dur}" style="top:{y}px">'
        f'<div class="dbar" id="{i}b"></div><div class="d1" id="{i}a">{html.escape(a)}</div>'
        f'<div class="d2" id="{i}c">{html.escape(b)}</div></div>')
    anim(f'tl.fromTo("#{i}b",{{scaleY:0}},{{scaleY:1,duration:0.45,ease:"expo.out"}},{start})')
    anim(f'tl.fromTo("#{i}a",{{rotationX:-95,opacity:0}},{{rotationX:0,opacity:1,duration:0.8,ease:"expo.out"}},{round(start + 0.1, 2)})')
    anim(f'tl.fromTo("#{i}c",{{rotationX:-95,opacity:0}},{{rotationX:0,opacity:1,duration:0.8,ease:"expo.out"}},{round(start + 0.25, 2)})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.3}},{round(start + dur - 0.3, 2)})')


def odo(num, start, dur, y, size=360, label=None, color=Y, gold=False, band=True):
    """Rolling-digit number (Centurion reel style)."""
    i = nid("od")
    events.append((start + 0.1, "roll"))
    cols = []
    for k, ch in enumerate(num):
        if ch.isdigit():
            strip = "".join(f"<span>{d}</span>" for d in "0123456789")
            cols.append(f'<span class="dcol"><span class="dstrip" id="{i}d{k}">{strip}</span></span>')
            anim(f'tl.fromTo("#{i}d{k}",{{yPercent:0}},{{yPercent:{-int(ch) * 10},duration:{1.1 + 0.15 * k},ease:"expo.out"}},{round(start + 0.1, 2)})')
        else:
            cols.append(f'<span>{html.escape(ch)}</span>')
    lab = f'<div class="olab">{html.escape(label)}</div>' if label else ""
    add(f'<div id="{i}" class="odo anton clip{" gold" if gold else ""}" data-start="{start}" data-duration="{dur}" '
        f'style="top:{y}px;font-size:{size}px;color:{color}{";left:" + str(BAND_X) + "px;text-align:left" if band else ""}"><div class="digits">{"".join(cols)}</div>{lab}</div>')
    anim(f'tl.fromTo("#{i}",{{opacity:0,scale:1.15}},{{opacity:1,scale:1,duration:0.4,ease:"expo.out"}},{start})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.3}},{round(start + dur - 0.3, 2)})')


def stamp(txt, t, dur, y, color=RED, rot=-8, size=120):
    i = nid("st")
    events.append((t, "stamp"))
    add(f'<div id="{i}" class="stampx anton clip" data-start="{t}" data-duration="{dur}" '
        f'style="top:{y}px;color:{color};border-color:{color};font-size:{size}px">{html.escape(txt)}</div>')
    anim(f'tl.fromTo("#{i}",{{scale:2.6,opacity:0,rotation:{rot - 8}}},{{scale:1,opacity:1,rotation:{rot},duration:0.32,ease:"power4.in"}},{t})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.25}},{round(t + dur - 0.25, 2)})')


def manual(start, dur, stamp_at, y=520):
    """The coaching manual: a book card whose rules get stamped 'CAN'T EXPLAIN'."""
    i = nid("mn")
    events.append((start, "whoosh"))
    rules = ["Leave the ball outside off", "See off the new ball", "Respect the first hour", "Never hit in the air early"]
    rows = "".join(f'<div class="mrow" id="{i}r{k}"><b>{k + 1}</b>{html.escape(r)}</div>' for k, r in enumerate(rules))
    add(f'<div id="{i}" class="manual clip" data-start="{start}" data-duration="{dur}" style="top:{y}px">'
        f'<div class="mhead">THE COACHING MANUAL</div><div class="msub">OPENING BATTING · CHAPTER 1</div>{rows}</div>')
    anim(f'tl.fromTo("#{i}",{{rotationY:-70,opacity:0,x:-200}},{{rotationY:0,opacity:1,x:0,duration:0.8,ease:"expo.out"}},{start})')
    for k in range(len(rules)):
        anim(f'tl.fromTo("#{i}r{k}",{{opacity:0,x:-30}},{{opacity:1,x:0,duration:0.35}},{round(start + 0.35 + 0.15 * k, 2)})')
    anim(f'tl.to("#{i}",{{opacity:0,y:-120,duration:0.3}},{round(start + dur - 0.3, 2)})')
    stamp("CAN'T EXPLAIN", stamp_at, start + dur - stamp_at, y + 560, size=96)


def split(top, bottom, start, dur, bottom_at, strike_at):
    """Two stacked clips: the careful opener (grey) and Viru (colour)."""
    i = nid("sp")
    events.append((start, "whoosh"))
    add(f'<div id="{i}" class="split clip" data-start="{start}" data-duration="{dur}">'
        f'<div class="half top">{media_html(top, start, dur, "")}<div class="hshade"></div>'
        f'<div class="htag">OTHER OPENERS</div><div class="hword anton" id="{i}w1">SURVIVE<span class="hstrike" id="{i}k"></span></div></div>'
        f'<div class="half bot" id="{i}b">{media_html(bottom, bottom_at, start + dur - bottom_at, "")}<div class="hshade"></div>'
        f'<div class="htag y">VIRU</div><div class="hword anton y" id="{i}w2">DESTROY</div></div></div>')
    anim(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.3}},{start})')
    anim(f'tl.fromTo("#{i}w1",{{y:60,opacity:0}},{{y:0,opacity:1,duration:0.6,ease:"expo.out"}},{round(start + 0.2, 2)})')
    events.append((bottom_at, "whoosh"))
    anim(f'tl.fromTo("#{i}b",{{clipPath:"inset(100% 0 0 0)"}},{{clipPath:"inset(0% 0 0 0)",duration:0.5,ease:"expo.inOut"}},{bottom_at})')
    anim(f'tl.fromTo("#{i}w2",{{scale:1.6,opacity:0}},{{scale:1,opacity:1,duration:0.45,ease:"expo.out"}},{round(bottom_at + 0.25, 2)})')
    events.append((round(bottom_at + 0.3, 2), "impact"))
    events.append((strike_at, "pop"))
    anim(f'tl.fromTo("#{i}k",{{scaleX:0}},{{scaleX:1,duration:0.35,ease:"expo.out"}},{strike_at})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.3}},{round(start + dur - 0.3, 2)})')


def tv(slot, start, dur, y=520):
    """A 2000s CRT television playing a Sehwag clip."""
    i = nid("tv")
    events.append((start, "whoosh"))
    add(f'<div id="{i}" class="tv clip" data-start="{start}" data-duration="{dur}" style="top:{y}px">'
        f'<div class="tvant"></div><div class="tvbody"><div class="tvscreen">{media_html(slot, start, dur, "")}'
        f'<div class="scan"></div><div class="glare"></div></div><div class="tvknobs"><i></i><i></i></div></div></div>')
    anim(f'tl.fromTo("#{i}",{{scale:0.7,opacity:0,y:120}},{{scale:1,opacity:1,y:0,duration:0.8,ease:"back.out(1.4)"}},{start})')
    anim(f'tl.fromTo("#{i} .tvscreen",{{filter:"brightness(4)"}},{{filter:"brightness(1)",duration:0.5}},{round(start + 0.2, 2)})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.3}},{round(start + dur - 0.3, 2)})')


def wc_strip(start, dur, y, times):
    """2011 World Cup: 8 matches, a four off the first ball in five of them."""
    i = nid("wc")
    teams = ["BAN", "ENG", "IRE", "NED", "SA", "", "", ""]
    cells = "".join(f'<div class="wcell" id="{i}c{k}"><div class="wt">{t or "·"}</div><div class="wball" id="{i}b{k}">4</div></div>'
                    for k, t in enumerate(teams))
    add(f'<div id="{i}" class="wcs clip" data-start="{start}" data-duration="{dur}" style="top:{y}px">'
        f'<div class="wchead">WORLD CUP 2011 · FIRST BALL</div><div class="wgrid">{cells}</div>'
        f'<div class="wcount anton" id="{i}n">5 / 8</div></div>')
    anim(f'tl.fromTo("#{i}",{{y:200,opacity:0}},{{y:0,opacity:1,duration:0.6,ease:"expo.out"}},{start})')
    for k in range(8):
        anim(f'tl.fromTo("#{i}c{k}",{{scale:0.4,opacity:0}},{{scale:1,opacity:1,duration:0.3,ease:"back.out(2)"}},{round(start + 0.2 + 0.05 * k, 2)})')
    for k, t in enumerate(times):
        events.append((t, "pop"))
        anim(f'tl.fromTo("#{i}b{k}",{{scale:0}},{{scale:1,duration:0.35,ease:"back.out(3)"}},{t})')
        anim(f'tl.to("#{i}c{k}",{{backgroundColor:"{Y}",color:"{INK}",duration:0.2}},{t})')
    anim(f'tl.fromTo("#{i}n",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.5,ease:"expo.out"}},{round(times[-1] + 0.3, 2)})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.3}},{round(start + dur - 0.3, 2)})')


def follow_tap(start, dur, y=620):
    """Logo card with a FOLLOW button that gets tapped and turns into FOLLOWING."""
    i = nid("ft")
    events.append((start, "whoosh"))
    tap = round(start + dur * 0.55, 2)
    add(f'<div id="{i}" class="ftap clip" data-start="{start}" data-duration="{dur}" style="top:{y}px">'
        f'<img src="media/logo.png" class="flogo"><div class="fbtn" id="{i}b"><span id="{i}t1">+ FOLLOW</span>'
        f'<span id="{i}t2" class="fdone">FOLLOWING ✓</span></div><div class="finger" id="{i}f">👆</div>'
        f'<div class="fbell" id="{i}l">🔔</div></div>')
    anim(f'tl.fromTo("#{i}",{{scale:0.8,opacity:0}},{{scale:1,opacity:1,duration:0.6,ease:"back.out(1.6)"}},{start})')
    anim(f'tl.fromTo("#{i}f",{{x:260,y:260,opacity:0}},{{x:0,y:0,opacity:1,duration:0.6,ease:"power3.out"}},{round(tap - 0.6, 2)})')
    events.append((tap, "pop"))
    anim(f'tl.to("#{i}b",{{scale:0.9,duration:0.08,yoyo:true,repeat:1}},{tap})')
    anim(f'tl.to("#{i}b",{{backgroundColor:"#2a2a2f",color:"#fff",duration:0.2}},{round(tap + 0.1, 2)})')
    anim(f'tl.to("#{i}t1",{{opacity:0,duration:0.1}},{round(tap + 0.1, 2)})')
    anim(f'tl.fromTo("#{i}t2",{{opacity:0}},{{opacity:1,duration:0.2}},{round(tap + 0.15, 2)})')
    anim(f'tl.to("#{i}f",{{opacity:0,duration:0.3}},{round(tap + 0.4, 2)})')
    events.append((round(tap + 0.3, 2), "ding"))
    anim(f'tl.fromTo("#{i}l",{{scale:0,rotation:0}},{{scale:1,rotation:0,duration:0.3,ease:"back.out(3)"}},{round(tap + 0.3, 2)})')
    anim(f'tl.to("#{i}l",{{rotation:18,duration:0.08,yoyo:true,repeat:5}},{round(tap + 0.6, 2)})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.3}},{round(start + dur - 0.3, 2)})')


def follow_pop(t, dur=2.2):
    """Small 'true cricket fans follow' pill sliding in from the right (no voiceover)."""
    i = nid("fp")
    events.append((t, "pop"))
    add(f'<div id="{i}" class="fpop clip" data-start="{t}" data-duration="{dur}"><span class="fpb">+ FOLLOW</span>'
        f'<span>True cricket fans follow <b>TheCricketLounge</b></span></div>')
    anim(f'tl.fromTo("#{i}",{{x:700}},{{x:0,duration:0.5,ease:"expo.out"}},{t})')
    anim(f'tl.to("#{i}",{{x:700,duration:0.4,ease:"power2.in"}},{round(t + dur - 0.4, 2)})')


def name_tag(name, sub, start, dur, y=1180):
    i = nid("nt")
    events.append((start, "whoosh"))
    add(f'<div id="{i}" class="ntag clip" data-start="{start}" data-duration="{dur}" style="top:{y}px">'
        f'<div class="nbar"></div><div><div class="nn anton">{html.escape(name)}</div><div class="ns">{html.escape(sub)}</div></div></div>')
    anim(f'tl.fromTo("#{i}",{{x:-500,opacity:0}},{{x:0,opacity:1,duration:0.6,ease:"expo.out"}},{start})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.3}},{round(start + dur - 0.3, 2)})')


def subtitle(txt, start, dur, y=1330):
    i = nid("sb")
    add(f'<div id="{i}" class="subtl clip" data-start="{start}" data-duration="{dur}" style="top:{y}px">{txt}</div>')
    anim(f'tl.fromTo("#{i}",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.3}},{start})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.2}},{round(start + dur - 0.2, 2)})')


def vote(left, right, start, dur):
    """Diagonal split: Sehwag vs Gayle with an OR badge."""
    i = nid("vt")
    events.append((start, "whoosh"))
    add(f'<div id="{i}" class="vote clip" data-start="{start}" data-duration="{dur}">'
        f'<div class="vl" id="{i}l">{media_html(left, start, dur, "")}<div class="vname anton">SEHWAG</div></div>'
        f'<div class="vr" id="{i}r">{media_html(right, start, dur, "")}<div class="vname anton">GAYLE</div></div>'
        f'<div class="vor anton" id="{i}o">OR</div></div>')
    anim(f'tl.fromTo("#{i}l",{{x:-600}},{{x:0,duration:0.6,ease:"expo.out"}},{start})')
    anim(f'tl.fromTo("#{i}r",{{x:600}},{{x:0,duration:0.6,ease:"expo.out"}},{round(start + 0.15, 2)})')
    events.append((round(start + 0.55, 2), "impact"))
    anim(f'tl.fromTo("#{i}o",{{scale:0,rotation:-30}},{{scale:1,rotation:0,duration:0.5,ease:"back.out(2.5)"}},{round(start + 0.5, 2)})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.3}},{round(start + dur - 0.3, 2)})')


def end_card(start, dur):
    i = nid("ec")
    add(f'<div id="{i}" class="endc clip" data-start="{start}" data-duration="{dur}"><img src="media/logo.png" class="elogo" id="{i}l">'
        f'<div class="efol" id="{i}f">+ FOLLOW</div><div class="esub" id="{i}s">for every cricket memory</div></div>')
    anim(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.3}},{start})')
    anim(f'tl.fromTo("#{i}l",{{clipPath:"inset(0% 100% 0% 0%)"}},{{clipPath:"inset(0% 0% 0% 0%)",duration:0.8,ease:"expo.inOut"}},{round(start + 0.1, 2)})')
    anim(f'tl.fromTo("#{i}f",{{scale:0}},{{scale:1,duration:0.5,ease:"back.out(2.5)"}},{round(start + 0.6, 2)})')
    anim(f'tl.fromTo("#{i}s",{{opacity:0}},{{opacity:1,duration:0.5}},{round(start + 0.9, 2)})')


# ----------------------------------------------------------------------------- the reel

def glow(start, dur, color):
    """Dark stage with a coloured radial glow behind the player (Kohli 101 reference look)."""
    i = nid("gl")
    add(f'<div id="{i}" class="glow clip" data-start="{start}" data-duration="{dur}" '
        f'style="background:radial-gradient(70% 45% at 55% 55%,{color},rgba(8,8,10,0) 70%),#08080a"></div>')
    anim(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.35}},{start})')


def headline(lines, start, dur, colors=None, size=84, y=300):
    """Top-left two-line headline, revealed line by line."""
    return words(lines, start, dur, y, size=size, colors=colors or ["#fff", Y], align="band", stagger=0.14, z=45)


def player(slot, start, dur, h=1250, x=None, bottom=1750, enter="up", z=30, flip=False):
    """Big cut-out standing on the bottom of the frame; enters with a rise, slow push-in while on screen."""
    i = nid("pl")
    events.append((start, "whoosh"))
    rel, _ = asset(slot)
    from PIL import Image
    with Image.open(os.path.join(OUT, rel)) as im:
        w = round(h * im.width / im.height)
    left = round((W - w) / 2) if x is None else x
    add(f'<div id="{i}" class="player clip" data-start="{start}" data-duration="{dur}" '
        f'style="left:{left}px;top:{bottom - h}px;width:{w}px;height:{h}px;z-index:{z}">'
        f'<img src="{rel}" style="{"transform:scaleX(-1);" if flip else ""}"></div>')
    frm = {"up": "y:260,opacity:0", "left": "x:-500,opacity:0", "right": "x:500,opacity:0"}[enter]
    anim(f'tl.fromTo("#{i}",{{{frm},scale:0.96}},{{x:0,y:0,opacity:1,scale:1,duration:0.8,ease:"expo.out"}},{start})')
    anim(f'tl.to("#{i}",{{scale:1.04,duration:{max(0.5, dur - 0.8)},ease:"none"}},{round(start + 0.8, 2)})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.3}},{round(start + dur - 0.3, 2)})')


def giant(txt, start, dur, y, size=520, color=Y, outline=False, fill_at=None, z=20):
    """Huge word behind the player (the Rajat reel's T20 / BCCI move): slams in, outline can fill later."""
    i = nid("gi")
    events.append((start + 0.05, "impact"))
    st = f"color:transparent;-webkit-text-stroke:5px {color}" if outline else f"color:{color}"
    add(f'<div id="{i}" class="giant anton clip" data-start="{start}" data-duration="{dur}" '
        f'style="top:{y}px;font-size:{size}px;z-index:{z};{st}">{html.escape(txt)}</div>')
    anim(f'tl.fromTo("#{i}",{{scale:1.35,opacity:0}},{{scale:1,opacity:1,duration:0.55,ease:"expo.out"}},{start})')
    if fill_at:
        events.append((fill_at, "pop"))
        anim(f'tl.to("#{i}",{{color:"{color}",duration:0.3}},{fill_at})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.3}},{round(start + dur - 0.3, 2)})')


def tracker(marks):
    """Persistent bottom bar: 'THE VIRU YEARS' with the year of each chapter ticking over (1999-2013)."""
    yrs = "".join(f'<span class="tyr" id="ty{k}">{html.escape(y)}</span>' for k, (t, y) in enumerate(marks))
    add(f'<div class="tracker"><div class="tlab">THE VIRU YEARS</div><div class="tyrs">{yrs}</div>'
        f'<div class="tbar"><div class="tfill" id="tfill"></div></div><div class="tends"><span>1999</span><span>2013</span></div></div>')
    anim('tl.fromTo(".tracker",{y:120,opacity:0},{y:0,opacity:1,duration:0.6,ease:"expo.out"},0.3)')
    prev = None
    for k, (t, y) in enumerate(marks):
        frac = {"2000s": 0.15, "2004": 0.36, "2008": 0.64, "2011": 0.86}.get(y, 0.05)
        if prev is not None:
            anim(f'tl.to("#ty{prev}",{{yPercent:-100,opacity:0,duration:0.3}},{t})')
        anim(f'tl.fromTo("#ty{k}",{{yPercent:100,opacity:0}},{{yPercent:0,opacity:1,duration:0.4,ease:"expo.out"}},{t})')
        anim(f'tl.to("#tfill",{{scaleX:{frac},duration:0.8,ease:"expo.out"}},{t})')
        prev = k


def build_scenes():
    """Full-frame layout (Kohli 101 reference): headline top-left, big Sehwag cut-outs filling the middle and
    lower frame over coloured glows, giant words behind him, cards rising, and a running tracker at the bottom."""
    BLUE, PURPLE, RED_G, GREEN, GOLD, TEAL = ("rgba(40,90,255,.55)", "rgba(140,60,255,.5)", "rgba(230,50,60,.5)",
                                               "rgba(40,180,90,.45)", "rgba(254,190,40,.45)", "rgba(20,170,200,.45)")
    # 0:00 action first, then the claim
    s, d = at("hook"), until_next("hook")
    fb("c_cut_aus", 0.0, 1.95)
    glow(1.9, s + d - 1.9, BLUE)
    giant("VIRU", 1.9, s + d - 1.9, 760, size=600, color="rgba(254,222,92,.9)", outline=True)
    player("cut_drive", 2.0, s + d - 2.0, h=1350)
    words(["There was something", "special about"], s + 0.05, d - 0.05, 300, size=74, font="serif", align="band", z=45, colors=["#fff", "#fff"])
    words(["SEHWAG"], at("hook", 1.0), s + d - at("hook", 1.0), 470, size=150, colors=[Y], align="band", z=45, sfx_kind="impact")

    # no manual could explain him: the manual card rises, gets stamped
    s, d = at("manual"), until_next("manual")
    glow(s, d, PURPLE)
    headline(["No coaching manual", "could explain him."], s, d)
    manual(s + 0.1, d - 0.1, span("manual", 0.62), y=700)

    # survive -> destroy
    s, d = at("survive"), round(at("destroy") - at("survive"), 2)
    glow(s, d, "rgba(120,120,130,.35)")
    headline(["Other openers came", "to survive."], s, d, colors=["#fff", "rgba(255,255,255,.6)"])
    giant("SURVIVE", s + 0.2, d - 0.2, 760, size=300, color="rgba(255,255,255,.55)", outline=True)
    player("cut_latecut", s + 0.1, d - 0.1, h=1050, bottom=1750)
    s, d = at("destroy"), until_next("destroy")
    glow(s, d, RED_G)
    headline(["Viru came", "to destroy it."], s, d, colors=["#fff", Y])
    giant("DESTROY", s + 0.1, d - 0.1, 650, size=290, color=Y)
    player("cut_bighit", s + 0.25, d - 0.25, h=1180)

    # 2000s kid: the TV
    s, d = at("kid"), until_next("kid")
    glow(s, d, GREEN)
    headline(["For a 2000s kid,", "nobody left the TV."], s, d)
    tv("tv_drive_nz", s + 0.3, d - 0.3, y=640)
    giant("2000s", s + 0.6, d - 0.6, 1280, size=300, color="rgba(254,222,92,.8)", outline=True, fill_at=span("kid", 0.6))
    follow_pop(round(at("kid", -1.8), 2), 2.2)

    # Multan 2004: 309 behind him
    s, d = at("multan"), until_next("multan")
    glow(s, d, GOLD)
    headline(["Multan, 2004.", "First Indian Test triple."], s, d)
    odo("309", span("multan", 0.25), s + d - span("multan", 0.25), 700, size=400, color=Y, label="RUNS")
    player("cut_multan", s + 0.2, d - 0.2, h=1150, x=640)

    # Chennai 2008: outline 300 fills, then 278 balls + stamp
    s, d = at("chennai"), until_next("chennai")
    fb("c_test_sweep", s, 2.2, blur=True)
    fb("c_celebrate", round(s + 2.0, 2), round(d - 2.0, 2), blur=True)
    headline(["Chennai, 2008.", "Fastest Test triple ever."], s, d)
    giant("300", span("chennai", 0.12), span("chennai", 0.45) - span("chennai", 0.12), 640, size=520, color=Y, outline=True, fill_at=span("chennai", 0.3))
    odo("278", span("chennai", 0.45), s + d - span("chennai", 0.45), 640, size=460, label="BALLS", color="#fff", band=False)
    stamp("FASTEST EVER", span("chennai", 0.74), s + d - span("chennai", 0.74), 1330, size=84, rot=-5)

    # 2011 World Cup: first-ball fours
    s, d = at("wc"), until_next("wc")
    glow(s, d, BLUE)
    headline(["World Cup 2011.", "First ball? Four."], s, d)
    player("cut_wc2011", s + 0.1, d - 0.1, h=780, bottom=1260, x=330)
    wc_strip(s + 0.5, d - 0.5, 1270, [span("wc", f) for f in (0.42, 0.52, 0.62, 0.72, 0.82)])

    # follow ask (spoken)
    s, d = at("follow"), until_next("follow")
    glow(s, d, GOLD)
    headline(["True cricket fans", "follow this page."], s, d)
    follow_tap(s + 0.2, d - 0.2, y=700)
    for k, t in enumerate(["Throwbacks", "Records", "Stories you grew up with"]):
        label(t, round(s + 0.8 + 0.25 * k, 2), round(d - 0.8 - 0.25 * k, 2), 1340 + 110 * k, color="#fff", bg="rgba(255,255,255,.12)", size=34)

    # Ganguly tease, then his own words full screen
    s, d = at("tease"), until_next("tease")
    fb("ganguly_still", s, d, blur=True)
    headline(["What Sourav Ganguly", "said next..."], s, d)
    name_tag("SOURAV GANGULY", "Former India captain", s + 0.4, d - 0.4, y=1250)
    s, d = at("ganguly"), until_next("ganguly")
    fb("ganguly", s, d)
    g0, g1 = T["ganguly"]
    subtitle("“An opener's job is to keep leaving the ball until it gets old.”", g0 + 0.05, 2.55, y=1420)
    subtitle("“Sehwag's job was to make it old <b>by hitting it.</b>”", g0 + 2.6, g1 - g0 - 2.4, y=1420)

    # the hundred: helmet off, red handkerchief, 100 behind him
    s, d = at("hundred"), until_next("hundred")
    h1 = span("hundred", 0.36)
    glow(s, d, TEAL)
    headline(["When the hundred came,", "the helmet came off."], s, h1 - s)
    giant("100", s + 0.1, h1 - s, 600, size=600, color="rgba(254,222,92,.85)", outline=True, fill_at=round(s + 0.9, 2))
    player("cut_helmet", s + 0.15, h1 - s - 0.1, h=1300)
    glow(h1, s + d - h1, RED_G)
    headline(["The red handkerchief.", "That smile."], h1, s + d - h1, colors=["#fff", Y])
    player("cut_patka", h1, s + d - h1, h=1080)
    words(["Like he was batting in his backyard."], span("hundred", 0.66), s + d - span("hundred", 0.66), 490, size=50, font="serif", align="band", z=45)

    # trophies, runs, childhood
    s = at("trophies")
    fb("c_drive_nz", s, until_next("trophies"))
    headline(["Some players give you", "TROPHIES."], s, until_next("trophies"), colors=["#fff", "#fff"])
    s = at("runs")
    fb("c_cut_aus2", s, until_next("runs"))
    headline(["Some give you", "RUNS."], s, until_next("runs"), colors=["#fff", "#fff"])
    s, d = at("childhood"), until_next("childhood")
    glow(s, d, GOLD)
    words(["Viru gave us", "our childhood."], s, d, 300, size=100, font="serif", colors=["#fff", Y], stagger=0.25, align="band", z=45)
    player("cut_laugh", s + 0.2, d - 0.2, h=1250)

    # the question
    s = at("vote")
    d = round(TOTAL - s - END_HOLD + 0.2, 2)
    glow(s, d, "rgba(120,40,40,.4)")
    headline(["Most dangerous", "opener?"], s, d)
    player("cut_drive", s + 0.1, d - 0.1, h=1100, x=-40, enter="left")
    player("cut_gayle", s + 0.25, d - 0.25, h=1100, x=520, enter="right")
    i = nid("or")
    add(f'<div id="{i}" class="vor anton clip" data-start="{round(s + 0.6, 2)}" data-duration="{round(d - 0.6, 2)}" style="top:900px;z-index:40">OR</div>')
    anim(f'tl.fromTo("#{i}",{{scale:0,rotation:-30}},{{scale:1,rotation:0,duration:0.5,ease:"back.out(2.5)"}},{round(s + 0.6, 2)})')
    events.append((round(s + 0.65, 2), "impact"))
    label("SEHWAG", s + 0.8, d - 0.8, 1560, color="#fff", bg="rgba(18,18,20,.85)", size=34, band=True)
    label("GAYLE", s + 0.9, d - 0.9, 1560, color="#fff", bg="rgba(18,18,20,.85)", size=34)
    label("💬  ONE WORD IN THE COMMENTS", span("vote", 0.72), s + d - span("vote", 0.72), 1660, color=INK, bg=Y, size=32, z=47)
    follow_pop(span("vote", 0.85), 2.2)
    end_card(round(TOTAL - END_HOLD - 0.1, 2), round(END_HOLD + 0.1, 2))

    tracker([(0.4, "1999"), (at("kid"), "2000s"), (at("multan"), "2004"), (at("chennai"), "2008"), (at("wc"), "2011"),
             (at("follow"), "VIRU")])

build_scenes()

FONTS = os.path.join(ROOT, "rajat", "node_modules", "@fontsource")
CSS = f"""
@font-face{{font-family:Anton;src:url(media/anton.woff2)}}
@font-face{{font-family:Playfair;font-style:italic;font-weight:400;src:url(media/playfair-i.woff2)}}
html,body{{margin:0;background:{INK}}}
#root{{position:relative;width:{W}px;height:{H}px;overflow:hidden;background:{INK};font-family:"Inter Display","Inter",sans-serif;perspective:1600px}}
.anton{{font-family:Anton,"Inter Display",sans-serif}}
.bg{{position:absolute;inset:0;z-index:1;overflow:hidden}}
.bg.dark{{background:radial-gradient(120% 75% at 50% 38%,#26262b,#0d0d0f)}}
.bg.yellow{{background:{Y}}}
.band{{position:absolute;left:-20%;right:-20%;top:58%;height:30%;transform:rotate(-8deg);background:rgba(0,0,0,.07)}}
.bg.dark .band{{background:rgba(254,222,92,.05)}}
.brand{{position:absolute;left:50%;top:232px;transform:translateX(-50%);z-index:80;background:rgba(18,18,20,.88);padding:12px 22px;border-radius:12px}}
.brand img{{width:210px;display:block}}
.photo{{position:absolute}}
.pframe{{width:100%;height:100%;border-radius:28px;overflow:hidden;background:#222;box-shadow:0 40px 90px rgba(0,0,0,.55),0 0 0 8px #fff}}
.pframe img,.pframe video{{width:100%;height:100%;object-fit:cover;display:block}}
.ptag{{position:absolute;left:28px;top:-26px;background:{Y};color:{INK};font:900 30px "Inter Display";letter-spacing:2px;padding:10px 18px;border-radius:8px}}
.ph{{width:100%;height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px;
  background:repeating-linear-gradient(45deg,#2a2a2f 0 22px,#232327 22px 44px);color:rgba(255,255,255,.75);font:800 28px "Inter Display";text-align:center;padding:24px;box-sizing:border-box}}
.ph svg{{width:42%;fill:rgba(255,255,255,.18)}}
.ph.cut{{background:rgba(0,0,0,.18);border:4px dashed rgba(0,0,0,.35);border-radius:30px;color:rgba(0,0,0,.6)}}
.ph.cut svg{{fill:rgba(0,0,0,.25)}}
.fb{{position:absolute;inset:0;z-index:12;overflow:hidden;background:#0d0d0f}}
.fbcover{{position:absolute;inset:0}}
.fbcover video,.fbcover img,.fbcover .ph{{width:100%;height:100%;object-fit:cover;display:block}}
.fbback{{position:absolute;inset:-60px;width:calc(100% + 120px);height:calc(100% + 120px);object-fit:cover;filter:blur(38px) brightness(.45) saturate(1.2)}}
.fbfront{{position:absolute;left:0;right:0;-webkit-mask-image:linear-gradient(180deg,transparent 0,#000 9%,#000 72%,transparent 100%)}}
.fbfront img,.fbfront video,.fbfront .ph{{width:100%;height:100%;object-fit:cover;display:block}}
.fbshade{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(13,13,15,.75) 0%,rgba(13,13,15,0) 22%,rgba(13,13,15,0) 52%,rgba(13,13,15,.92) 78%,rgba(13,13,15,.96) 100%)}}
.fbshade.cover{{background:linear-gradient(180deg,rgba(13,13,15,.55) 0%,rgba(13,13,15,0) 18%,rgba(13,13,15,0) 55%,rgba(13,13,15,.55) 75%,rgba(13,13,15,.8) 100%)}}
.fbtag{{position:absolute;left:60px;top:340px;background:{Y};color:{INK};font:900 34px "Inter Display";letter-spacing:2px;padding:12px 20px;border-radius:8px}}
.cutout{{position:absolute;filter:drop-shadow(0 30px 40px rgba(0,0,0,.45))}}
.words{{position:absolute;left:50px;right:50px;line-height:.98;letter-spacing:-0.01em}}
.words.anton{{text-transform:uppercase}}
.words.serif{{font-family:Playfair,serif;font-style:italic;letter-spacing:-0.02em;line-height:1.02}}
.words .mask{{overflow:hidden;padding:0 .04em .06em}}
.words .ln{{display:block}}
.label{{position:absolute;left:50%;transform:translateX(-50%);white-space:nowrap;font-family:"Inter Display";font-weight:900;letter-spacing:4px}}
.squad{{position:absolute;left:110px;width:860px;background:#F4EFE3;border-radius:22px;padding:40px 46px 30px;box-sizing:border-box;
  box-shadow:0 40px 90px rgba(0,0,0,.45);text-align:center;color:{INK};z-index:20}}
.shead{{font:400 110px Anton;line-height:1}}
.sev{{font:900 30px "Inter Display";letter-spacing:3px;margin-top:12px}}
.sfmt{{display:inline-block;margin-top:14px;background:{INK};color:{Y};font:900 26px "Inter Display";letter-spacing:3px;padding:6px 16px;border-radius:6px}}
.sbody{{margin-top:28px;display:flex;flex-direction:column;gap:16px}}
.srow{{border:3px dashed rgba(0,0,0,.35);border-radius:12px;padding:22px;font:400 58px Anton;letter-spacing:2px;position:relative}}
.srow.cap,.srow.vc,.srow.in{{border-style:solid;border-color:{INK}}}
.cb{{position:absolute;right:-22px;top:50%;transform:translateY(-50%);background:{Y};color:{INK};border:4px solid {INK};border-radius:50%;
  min-width:62px;height:62px;line-height:54px;font:900 30px "Inter Display";box-sizing:border-box;padding:0 8px}}
.cb.in{{background:#33c27a;color:#fff;border-radius:31px}}
.stamp{{position:absolute;left:50%;top:58%;margin-left:-330px;width:660px;text-align:center;font:400 120px Anton;color:{RED};
  border:10px solid {RED};border-radius:16px;background:rgba(244,239,227,.92);letter-spacing:4px}}
.sfoot{{margin-top:22px;font:800 22px "Inter Display";letter-spacing:8px;opacity:.45}}
.sqtag{{position:absolute;left:-14px;top:-30px;background:{INK};color:#fff;font:900 30px "Inter Display";letter-spacing:2px;padding:12px 20px;border-radius:10px}}
.bign{{position:absolute;left:0;right:0;text-align:center;z-index:30}}
.bnum{{line-height:1}}
.bsub{{font:900 54px "Inter Display";letter-spacing:14px;color:rgba(255,255,255,.85);margin-top:10px}}
.strike{{position:absolute;left:170px;right:170px;top:46%;height:26px;border-radius:13px;background:{RED};transform-origin:left;transform:scaleX(0) rotate(-8deg)}}
.ruler{{position:absolute;left:0;right:0;height:170px;z-index:30;overflow:hidden}}
.rtrack{{position:absolute;left:0;top:0;height:100%}}
.tk{{position:absolute;top:30px;width:6px;height:70px;background:currentColor;margin-left:-3px;color:#fff}}
.tk span{{position:absolute;top:84px;left:50%;transform:translateX(-50%);font:400 60px Anton}}
.tm{{position:absolute;top:44px;width:4px;height:42px;background:rgba(255,255,255,.45);margin-left:-2px}}
.bg.yellow ~ .ruler .tk{{color:{INK}}}
.rmark{{position:absolute;left:50%;top:0;width:34px;height:34px;margin-left:-17px;border-radius:50%;background:{RED};box-shadow:0 0 0 8px rgba(229,72,77,.25)}}
.tiles{{position:absolute;left:90px;right:90px;display:flex;gap:30px;z-index:30;perspective:1200px}}
.tile{{flex:1;height:420px;border-radius:24px;background:#F4EFE3;color:{INK};display:flex;flex-direction:column;align-items:center;justify-content:center;
  position:relative;transform-origin:left center;box-shadow:0 30px 60px rgba(0,0,0,.4)}}
.tt{{font-size:130px;line-height:1}}
.ts{{font:900 28px "Inter Display";letter-spacing:3px;margin-top:14px;opacity:.7}}
.tick{{position:absolute;top:-30px;right:-24px;width:84px;height:84px;border-radius:50%;background:{INK};color:{Y};font:900 52px "Inter Display";
  display:flex;align-items:center;justify-content:center;transform:scale(0)}}
.check{{position:absolute;left:110px;right:110px;display:flex;flex-direction:column;gap:40px;z-index:30}}
.crow{{display:flex;align-items:center;gap:34px;background:rgba(255,255,255,.07);border-radius:24px;padding:34px 40px}}
.cm{{width:110px;height:110px;border-radius:50%;display:flex;align-items:center;justify-content:center;font:900 70px "Inter Display";flex:none}}
.ct{{font:400 92px Anton;color:#fff;letter-spacing:1px}}
.crow.ok .cm{{background:{Y};color:{INK}}}
.crow.no .cm{{background:{RED};color:#fff}}
.crow.no .ct{{text-decoration:line-through;text-decoration-color:{RED};text-decoration-thickness:10px;color:rgba(255,255,255,.55)}}
.subt{{position:absolute;left:60px;right:60px;top:1395px;text-align:center;z-index:70;font:400 64px Anton;color:#fff;letter-spacing:1px;
  -webkit-text-stroke:3px #000;paint-order:stroke fill;text-shadow:0 6px 18px rgba(0,0,0,.6)}}

.fb.blurred .fbcover > *,.fb.blurred .fbfront{{filter:blur(22px) brightness(.55) saturate(1.25)}}
.brand{{display:flex;align-items:center;gap:14px}}
.bfol{{background:{Y};color:{INK};font:900 22px "Inter Display";letter-spacing:1px;padding:7px 12px;border-radius:7px}}
.dflip{{position:absolute;left:120px;z-index:32;perspective:800px}}
.dflip .dbar{{position:absolute;left:-40px;top:6px;width:14px;height:92%;border-radius:7px;background:{Y};transform-origin:top}}
.dflip .d1{{font:400 120px Anton;color:#fff;line-height:1;transform-origin:50% 100%;text-shadow:0 8px 30px rgba(0,0,0,.6)}}
.dflip .d2{{font:400 170px Anton;color:{Y};line-height:1;transform-origin:50% 100%;text-shadow:0 8px 30px rgba(0,0,0,.6)}}
.odo{{position:absolute;left:0;right:0;text-align:center;line-height:1;z-index:31;text-shadow:0 10px 40px rgba(0,0,0,.65)}}
.odo .digits{{display:inline-flex}}
.odo .dcol{{display:inline-block;height:1.16em;overflow:hidden}}
.odo .dstrip{{display:flex;flex-direction:column}}
.odo .dstrip span{{height:1.16em;line-height:1.16em}}
.odo .olab{{font:900 46px "Inter Display";letter-spacing:14px;color:#fff;margin-top:14px}}
.stampx{{position:absolute;left:50%;margin-left:-420px;width:840px;text-align:center;border:12px solid;border-radius:18px;
  background:rgba(244,239,227,.94);z-index:40;letter-spacing:4px;line-height:1.15}}
.manual{{position:absolute;left:120px;width:840px;background:#F4EFE3;border-radius:16px;padding:46px 50px 40px;box-sizing:border-box;
  color:{INK};z-index:30;box-shadow:0 40px 90px rgba(0,0,0,.6),inset 18px 0 0 #d9d1bd;transform-origin:left center}}
.mhead{{font:400 76px Anton;line-height:1}}
.msub{{font:800 24px "Inter Display";letter-spacing:4px;opacity:.55;margin:10px 0 26px}}
.mrow{{font:700 40px "Inter Display";padding:14px 0;border-top:2px dashed rgba(0,0,0,.2);display:flex;gap:22px}}
.mrow b{{color:{RED}}}
.split{{position:absolute;inset:0;z-index:20}}
.half{{position:absolute;left:0;right:0;height:960px;overflow:hidden}}
.half.top{{top:0}}
.half.bot{{top:960px;border-top:8px solid {Y}}}
.half video,.half img{{width:100%;height:100%;object-fit:cover}}
.half.top video{{filter:grayscale(1) brightness(.7)}}
.hshade{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.1),rgba(0,0,0,.55))}}
.htag{{position:absolute;left:70px;bottom:250px;font:900 40px "Inter Display";letter-spacing:6px;color:#fff}}
.half.top .htag{{bottom:250px}}
.half.bot .htag{{top:90px;bottom:auto}}
.htag.y{{color:{Y}}}
.hword{{position:absolute;left:62px;font-size:200px;color:#fff;line-height:1;bottom:30px}}
.half.bot .hword{{top:150px;bottom:auto}}
.hword.y{{color:{Y}}}
.hstrike{{position:absolute;left:-10px;right:-10px;top:50%;height:22px;background:{RED};border-radius:11px;transform-origin:left;transform:scaleX(0)}}
.tv{{position:absolute;left:110px;width:860px;z-index:30}}
.tvbody{{background:linear-gradient(180deg,#3b3530,#221e1b);border-radius:46px;padding:40px 40px 110px;box-shadow:0 50px 100px rgba(0,0,0,.7);position:relative}}
.tvscreen{{position:relative;height:600px;border-radius:60px/40px;overflow:hidden;background:#000;box-shadow:inset 0 0 60px rgba(0,0,0,.9)}}
.tvscreen video,.tvscreen img{{width:100%;height:100%;object-fit:cover;filter:saturate(.8) contrast(1.1) sepia(.15)}}
.scan{{position:absolute;inset:0;background:repeating-linear-gradient(0deg,rgba(0,0,0,.18) 0 3px,transparent 3px 6px)}}
.glare{{position:absolute;inset:0;background:radial-gradient(80% 60% at 30% 20%,rgba(255,255,255,.18),transparent 60%)}}
.tvknobs{{position:absolute;right:60px;bottom:30px;display:flex;gap:26px}}
.tvknobs i{{width:46px;height:46px;border-radius:50%;background:#111;box-shadow:inset 0 0 0 6px #555}}
.tvant{{position:absolute;left:50%;top:-120px;width:240px;height:130px;margin-left:-120px;
  background:linear-gradient(60deg,transparent 47%,#666 47% 50%,transparent 50%),linear-gradient(-60deg,transparent 47%,#666 47% 50%,transparent 50%)}}
.wcs{{position:absolute;left:80px;right:80px;z-index:30;background:rgba(18,18,20,.88);border-radius:28px;padding:34px;box-shadow:0 40px 90px rgba(0,0,0,.6)}}
.wchead{{font:900 34px "Inter Display";letter-spacing:5px;color:{Y};text-align:center;margin-bottom:24px}}
.wgrid{{display:grid;grid-template-columns:repeat(4,1fr);gap:18px}}
.wcell{{background:#2a2a2f;border-radius:18px;height:170px;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#fff;gap:8px}}
.wt{{font:900 36px "Inter Display";letter-spacing:3px}}
.wball{{width:70px;height:70px;border-radius:50%;background:{INK};color:{Y};font:400 46px Anton;display:flex;align-items:center;justify-content:center;transform:scale(0)}}
.wcount{{text-align:center;font-size:120px;color:#fff;margin-top:18px;line-height:1}}
.ftap{{position:absolute;left:140px;right:140px;z-index:32;background:rgba(18,18,20,.92);border-radius:36px;padding:60px 40px;
  display:flex;flex-direction:column;align-items:center;gap:40px;box-shadow:0 40px 100px rgba(0,0,0,.6)}}
.flogo{{width:560px}}
.fbtn{{position:relative;background:{Y};color:{INK};font:900 64px "Inter Display";letter-spacing:2px;padding:26px 70px;border-radius:20px;min-width:440px;text-align:center}}
.fdone{{position:absolute;left:0;right:0;top:26px;opacity:0}}
.finger{{position:absolute;left:58%;top:300px;font-size:130px}}
.fbell{{position:absolute;right:40px;top:30px;font-size:90px;transform:scale(0)}}
.fpop{{position:absolute;right:0;top:420px;z-index:65;display:flex;align-items:center;gap:16px;background:rgba(18,18,20,.92);
  color:#fff;font:700 32px "Inter Display";padding:16px 26px 16px 18px;border-radius:18px 0 0 18px;border-left:8px solid {Y}}}
.fpop b{{color:{Y}}}
.fpb{{background:{Y};color:{INK};font:900 26px "Inter Display";padding:8px 12px;border-radius:8px}}
.ntag{{position:absolute;left:70px;z-index:32;display:flex;gap:24px;align-items:stretch}}
.nbar{{width:14px;border-radius:7px;background:{Y}}}
.nn{{font-size:110px;color:#fff;line-height:1}}
.ns{{font:800 36px "Inter Display";letter-spacing:4px;color:{Y};margin-top:8px}}
.subtl{{position:absolute;left:60px;right:60px;text-align:center;z-index:60;font:800 62px "Inter Display";color:#fff;line-height:1.2;
  text-shadow:0 4px 18px rgba(0,0,0,.9),0 0 4px #000}}
.subtl b{{color:{Y}}}
.vote{{position:absolute;inset:0;z-index:20;background:#0d0d0f;overflow:hidden}}
.vl,.vr{{position:absolute;top:0;bottom:0;width:62%}}
.vl{{left:0;clip-path:polygon(0 0,100% 0,62% 100%,0 100%)}}
.vr{{right:0;clip-path:polygon(38% 0,100% 0,100% 100%,0 100%)}}
.vl img,.vr img{{width:100%;height:100%;object-fit:cover}}
.vname{{position:absolute;bottom:560px;font-size:120px;color:#fff;text-shadow:0 8px 30px rgba(0,0,0,.8)}}
.vl .vname{{left:60px}}
.vr .vname{{right:60px}}
.vor{{position:absolute;left:50%;top:860px;width:200px;height:200px;margin-left:-100px;border-radius:50%;background:{Y};color:{INK};
  font-size:110px;display:flex;align-items:center;justify-content:center;z-index:5;box-shadow:0 0 0 14px rgba(254,222,92,.25)}}
.endc{{position:absolute;inset:0;z-index:70;background:radial-gradient(90% 60% at 50% 45%,#1d1d21,#08080a);display:flex;flex-direction:column;
  align-items:center;justify-content:center;gap:40px}}
.elogo{{width:800px}}
.efol{{background:{Y};color:{INK};font:900 70px "Inter Display";padding:24px 70px;border-radius:22px}}
.esub{{font:700 40px "Inter Display";color:rgba(255,255,255,.7)}}

/* clean pass: smaller type, one text band, logo top-left */
.brand{{left:44px;top:196px;transform:none;background:rgba(18,18,20,.55);padding:8px 12px;border-radius:10px;gap:10px;opacity:.92}}
.brand img{{width:150px}}
.bfol{{font-size:17px;padding:5px 9px;border-radius:6px}}
.fbshade{{background:linear-gradient(180deg,rgba(13,13,15,.55) 0%,rgba(13,13,15,0) 16%,rgba(13,13,15,0) 46%,rgba(13,13,15,.78) 60%,rgba(13,13,15,.95) 74%,rgba(13,13,15,.97) 100%)}}
.fbshade.cover{{background:linear-gradient(180deg,rgba(13,13,15,.5) 0%,rgba(13,13,15,0) 16%,rgba(13,13,15,0) 46%,rgba(13,13,15,.75) 60%,rgba(13,13,15,.93) 76%,rgba(13,13,15,.96) 100%)}}
.words.tband{{left:{BAND_X}px;right:170px}}
.words{{text-shadow:0 4px 24px rgba(0,0,0,.55)}}
.odo .olab{{font-size:30px;letter-spacing:10px;margin-top:6px}}
.stampx{{left:{BAND_X}px;margin-left:0;width:auto;padding:0 28px;border-width:8px;border-radius:12px}}
.fpop{{top:1680px;left:44px;right:auto;border-radius:10px;border-left:6px solid {Y};font-size:24px;padding:10px 16px 10px 10px;gap:10px}}
.fpb{{font-size:18px;padding:5px 8px}}
.subtl{{left:{BAND_X}px;right:170px;text-align:left;font-size:46px;line-height:1.25}}
.ntag .nn{{font-size:84px}}
.ntag .ns{{font-size:28px}}
.ntag{{left:{BAND_X}px}}
.manual{{left:170px;width:740px;padding:36px 40px 30px}}
.mhead{{font-size:60px}}
.mrow{{font-size:32px;padding:11px 0}}
.wcs{{left:{BAND_X}px;right:170px;padding:22px}}
.wchead{{font-size:24px;margin-bottom:14px;letter-spacing:4px}}
.wgrid{{gap:12px}}
.wcell{{height:104px;border-radius:12px;gap:4px}}
.wt{{font-size:24px}}
.wball{{width:46px;height:46px;font-size:30px}}
.wcount{{font-size:70px;margin-top:10px}}
.hword{{font-size:150px}}
.htag{{font-size:30px}}
.vname{{font-size:70px;bottom:auto;top:330px}}
.vor{{width:150px;height:150px;margin-left:-75px;top:700px;font-size:80px}}
.ftap{{left:200px;right:200px;padding:44px 30px;gap:30px}}
.flogo{{width:420px}}
.fbtn{{font-size:48px;padding:20px 50px;min-width:340px}}
.fdone{{top:20px}}
.finger{{font-size:100px;top:230px}}
.tv{{left:150px;width:780px}}
.tvscreen{{height:520px}}

/* full-frame pass */
.glow{{position:absolute;inset:0;z-index:2}}
.player{{position:absolute;transform-origin:50% 100%;filter:drop-shadow(0 30px 50px rgba(0,0,0,.55))}}
.player img{{width:100%;height:100%;object-fit:contain;object-position:bottom}}
.giant{{position:absolute;left:0;right:0;text-align:center;line-height:.9;letter-spacing:-0.01em}}
.tracker{{position:absolute;left:{BAND_X}px;right:{BAND_X}px;top:1770px;z-index:66}}
.tlab{{font:900 22px "Inter Display";letter-spacing:6px;color:rgba(255,255,255,.75)}}
.tyrs{{position:absolute;right:0;top:-34px;height:64px;width:260px;overflow:hidden;text-align:right}}
.tyr{{position:absolute;right:0;top:0;font:400 60px Anton;color:{Y};line-height:64px;opacity:0}}
.tbar{{margin-top:14px;height:14px;border-radius:7px;background:rgba(255,255,255,.12);overflow:hidden}}
.tfill{{height:100%;width:100%;background:linear-gradient(90deg,#2f6bff,{Y});transform-origin:left;transform:scaleX(0)}}
.tends{{display:flex;justify-content:space-between;font:800 18px "Inter Display";color:rgba(255,255,255,.45);margin-top:6px;letter-spacing:3px}}
.endc{{z-index:75}}
"""


# ----------------------------------------------------------------------------- audio

def load_vo():
    p = os.path.join(HERE, "out", "vo_reel.wav")
    if not os.path.exists(p):
        return np.zeros(int(SR * TOTAL), np.float32)
    with wave.open(p) as w:
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768


def build_audio():
    n = int(SR * TOTAL)
    vo = np.zeros(n, np.float32)
    v = load_vo()
    vo[: min(n, len(v))] = v[:n]
    # nostalgic bed; a pulse lifts it through the records, it drops away under Ganguly, warm again to the close
    m = norm(reverb(pad(WARM, TOTAL + 2, bar=4.0, cutoff=1500), 2.5, 0.4)) * 0.5
    m = m[:n] + norm(reverb(arps(WARM, TOTAL + 2, step=0.5, gain=0.16), 1.5, 0.3))[:n] * 0.35
    t0, t1 = at("multan"), at("follow")
    m += section(norm(pulse(t1 - t0 + 1, 100, lambda t: min(1, t / 6))) * 0.45, t0, TOTAL, 0.8, 1.2)[:n]
    m = section(m, 0.0, TOTAL, 0.4, 1.2)
    g0, g1 = T["ganguly"]
    gd = np.ones(n)
    a, b = int((g0 - 0.6) * SR), int((g1 + 0.3) * SR)
    gd[a:b] = 0.12
    m *= np.convolve(gd, np.ones(int(0.3 * SR)) / int(0.3 * SR), "same")
    hop = 441
    env = np.abs(vo[: len(vo) // hop * hop]).reshape(-1, hop).max(1)
    env = np.convolve(env > 0.03, np.ones(30), "same") > 0
    duck = np.convolve(np.repeat(np.where(env, 0.5, 1.0), hop), np.ones(4410) / 4410, "same")
    m[: len(duck)] *= duck
    fx = np.zeros(n)
    cache = {}

    def put(name, t, g):
        if name not in cache:
            cache[name] = getattr(sfx, name)()
        music.add(fx, cache[name], max(0, t), g)

    # SFX kept low (about half the Centurion reel): user asked for quieter whooshes and drops
    gains = {"whoosh": ("whoosh", -0.12, 0.08), "impact": ("impact", 0.0, 0.13), "soft": ("pop", 0.0, 0.05),
             "pop": ("pop", 0.0, 0.08), "stamp": ("impact", 0.0, 0.16), "tick": ("tick", 0.0, 0.12),
             "ding": ("ding", 0.0, 0.10)}
    for t, kind in events:
        if kind == "roll":
            for k in range(8):
                put("tick", t + 0.05 * k, 0.06)
        else:
            name, off, g = gains[kind]
            put(name, t + off, g)
    mix = vo * 0.95 + m * 0.2 + fx * 0.55
    mix = np.tanh(mix * 1.05) / np.tanh(1.05)
    mix = mix / max(1e-6, np.abs(mix).max()) * 0.9
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    with wave.open(os.path.join(HERE, "out", "soundtrack.wav"), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.stack([mix, mix], 1) * 32767).astype(np.int16).tobytes())


def build_page():
    shutil.copy(os.path.join(ROOT, "doc_video", "node_modules", "gsap", "dist", "gsap.min.js"), os.path.join(OUT, "gsap.min.js"))
    shutil.copy(os.path.join(ROOT, "kohli_countdown", "assets", "logo.png"), os.path.join(MEDIA, "logo.png"))
    shutil.copy(os.path.join(FONTS, "anton", "files", "anton-latin-400-normal.woff2"), os.path.join(MEDIA, "anton.woff2"))
    shutil.copy(os.path.join(FONTS, "playfair-display", "files", "playfair-display-latin-400-italic.woff2"), os.path.join(MEDIA, "playfair-i.woff2"))
    page = f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div id="root" data-composition-id="root" data-width="{W}" data-height="{H}" data-fps="{FPS}" data-duration="{TOTAL}">
<div class="brand"><img src="media/logo.png"><span class="bfol" id="bfol">+ FOLLOW</span></div>
{chr(10).join(els)}
</div>
<script src="gsap.min.js"></script>
<script>
const tl = gsap.timeline({{paused:true}});
{chr(10).join(js)}
for (let t = 3; t < {TOTAL} - 3; t += 6) tl.to("#bfol",{{scale:1.18,duration:0.25,yoyo:true,repeat:1,ease:"power2.out"}},t);
tl.set({{}},{{}},{TOTAL});
window.__timelines = window.__timelines || {{}};
window.__timelines["root"] = tl;
</script></body></html>"""
    with open(os.path.join(OUT, "index.html"), "w") as f:
        f.write(page)


if __name__ == "__main__":
    build_page()
    build_audio()
    print(f"reel {TOTAL:.1f}s ({'voiceover timing' if HAS_VO else 'estimated timing, no voiceover yet'})")
    print(", ".join(f"{k} {v[0]}-{v[1]}" for k, v in T.items()))


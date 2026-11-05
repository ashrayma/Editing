#!/usr/bin/env python3
""""Rohit Sharma is not from this planet" — the five biggest six-hitters. 9:16 reel, HyperFrames composition.

    python3 reel.py   ->  hf/index.html (+ hf/media/) and out/events.json (SFX cue list for soundtrack.py)

Everything is timed off out/timeline.json (build_vo.py), so a new voice take re-times the whole edit.
Look: charcoal + film grain, theCricketLounge yellow, Inter Display. Full-screen photos slide in from the left
or right; cut-out "sticker" players carry the stat screens; Blender 3D shots for the #7, the three ICC trophies,
91*, the stumping and G.O.A.T.; word-by-word captions in the lower third; type is kept off faces (layout.py).
Instagram safe zone: nothing important above ~250 px or below ~1500 px.
"""
import html
import json
import os
import re
import shutil

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "hf")
MEDIA = os.path.join(OUT, "media")
W, H, FPS = 1080, 1920, 30
Y = "#FEDE5C"
TL = json.load(open(os.path.join(HERE, "out", "timeline.json")))
LINE = {ln["id"]: ln for ln in TL["lines"]}
END_CARD = 2.4
TOTAL = round(TL["duration"] + END_CARD, 2)

FACES = json.load(open(os.path.join(HERE, "assets", "faces.json")))
_lp = os.path.join(HERE, "out", "layout.json")
LAYOUT = json.load(open(_lp)) if os.path.exists(_lp) else {"move": {}, "brand_hide": []}

os.makedirs(MEDIA, exist_ok=True)
els, js, events = [], [], []
_n = [0]
_z = [10]


def nid(p):
    _n[0] += 1
    return f"{p}{_n[0]}"


def z():
    _z[0] += 1
    return _z[0]


def s(lid, off=0.0):
    """Start of a line (+offset)."""
    return round(LINE[lid]["start"] + off, 3)


def e(lid, off=0.0):
    return round(LINE[lid]["end"] + off, 3)


def word(lid, k):
    """Start time of the k-th caption word of a line."""
    return LINE[lid]["words"][k][1]


def span(a, b):
    """From the start of line a to the start of line b (or the end of the reel)."""
    return round((s(b) if b else TOTAL) - s(a), 3)


def media(path):
    src = os.path.join(HERE, path)
    name = path.replace("/", "_")
    dst = os.path.join(MEDIA, name)
    if not os.path.exists(dst) or os.path.getmtime(src) > os.path.getmtime(dst):
        shutil.copy(src, dst)
    return "media/" + name


def mv(i, top, left=None):
    """Position of a type element, after any move the face checker (layout.py) decided on."""
    o = LAYOUT["move"].get(i, {})
    return o.get("top", top), o.get("left", left)


def face_marks(key, ox=0.0, oy=0.0, dw=None, dh=None):
    """Invisible boxes over each face of an image drawn at (ox, oy, dw, dh) px inside its transformed wrapper;
    the checker reads their on-screen rects."""
    return "".join(f'<div class="face" style="left:{ox + x * dw:.0f}px;top:{oy + y * dh:.0f}px;width:{w * dw:.0f}px;'
                   f'height:{h * dh:.0f}px"></div>' for x, y, w, h in FACES.get(key, []))


def merge_classes(h):
    """clip_attrs() puts class="clip" on a tag that may carry its own class too: fold them into one attribute."""
    def fix(m):
        tag = m.group(0)
        cls = re.findall(r'\sclass="([^"]*)"', tag)
        if len(cls) < 2:
            return tag
        tag = re.sub(r'\sclass="[^"]*"', "", tag)
        return tag[:-1] + f' class="{" ".join(cls)}">'
    return re.sub(r"<[a-z]+\b[^<>]*>", fix, h)


def add(h):
    els.append(merge_classes(h))


def anim(a):
    js.append(a)


def cue(t, kind, gain=1.0):
    events.append((round(t, 3), kind, gain))


def clip_attrs(start, dur):
    return f'class="clip" data-start="{round(start, 3)}" data-duration="{round(dur, 3)}"'


# ----------------------------------------------------------------------------- layers

def stage(start, dur, tone="#0b0b0c"):
    """An opaque grain panel: resets the frame for cut-outs and type."""
    i = nid("st")
    add(f'<div id="{i}" {clip_attrs(start, dur)} class="layer full" style="position:absolute;inset:0;z-index:{z()};background:{tone}">'
        f'<div class="gridbg" id="{i}g"></div><div class="grain"></div><div class="vig"></div></div>')
    anim(f'tl.fromTo("#{i}g",{{x:0,y:0}},{{x:-60,y:-90,duration:{max(0.5, dur)},ease:"none"}},{start})')
    return i


FOCUS = {}  # manual crop focus (x) for wide photos; otherwise the crop centres on the detected face


def focus_x(name):
    if name in FOCUS:
        return FOCUS[name]
    fs = FACES.get("hi/" + name) or []
    if not fs:
        return 0.5
    x, y, w, h = max(fs, key=lambda f: f[2] * f[3])
    return x + w / 2


def photo(name, start, dur, side="right", push=(1.0, 1.1), origin="50% 40%", fx=None, whoosh=True, band=False):
    """Full-screen photo. Tall photos fill the frame; wide ones sit full-width over a blurred fill of themselves.
    Enters with a fast slide from `side` ("left"/"right"/"up"/None for a hard cut), then a slow push-in."""
    i = nid("ph")
    src = media(f"assets/hi/{name}.png")
    fill = media(f"assets/fill/{name}.jpg")
    with Image.open(os.path.join(HERE, "assets", "hi", name + ".png")) as im:
        tall = im.height / im.width >= 1.25
        ih = round(W * im.height / im.width)
    filt = {"grey": "grayscale(1) contrast(1.1) brightness(.85)", "dim": "brightness(.7)"}.get(fx, "none")
    with Image.open(os.path.join(HERE, "assets", "hi", name + ".png")) as im:
        iw, ihh = im.size
    if tall or not band:
        sc = max(W / iw, H / ihh)
        dw, dh = iw * sc, ihh * sc
        # object-position that puts the focus point (the face) at the centre of the frame, within the image
        fx_ = 0.5 if tall or dw <= W + 1 else min(1.0, max(0.0, (W / 2 - focus_x(name) * dw) / (W - dw)))
        pos = f"{fx_ * 100:.1f}% 30%"
        marks = face_marks("hi/" + name, (W - dw) * fx_, (H - dh) * 0.3, dw, dh)
        inner = (f'<div id="{i}m" style="position:absolute;inset:0;transform-origin:{origin}">'
                 f'<img src="{src}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;'
                 f'object-position:{pos};filter:{filt}">{marks}</div>')
    else:
        top = round(H * 0.42 - ih / 2)
        marks = face_marks("hi/" + name, 0, 0, W, ih)
        inner = (f'<img src="{fill}" style="position:absolute;inset:-40px;width:calc(100% + 80px);height:calc(100% + 80px);object-fit:cover">'
                 f'<div id="{i}m" style="position:absolute;left:0;top:{top}px;width:100%;height:{ih}px;transform-origin:{origin}">'
                 f'<img src="{src}" style="width:100%;height:100%;object-fit:cover;filter:{filt};box-shadow:0 40px 120px rgba(0,0,0,.75)">'
                 f'{marks}</div>')
    add(f'<div id="{i}" {clip_attrs(start, dur)} class="layer full" style="position:absolute;inset:0;z-index:{z()};overflow:hidden;background:#000">'
        f'{inner}<div class="shade"></div><div class="vig"></div></div>')
    if side:
        if whoosh:
            cue(start - 0.1, "whoosh", 0.8)
        fr = {"left": "xPercent:-100", "right": "xPercent:100", "up": "yPercent:100"}[side]
        anim(f'tl.fromTo("#{i}",{{{fr}}},{{xPercent:0,yPercent:0,duration:0.38,ease:"expo.out"}},{start})')
        # motion-blur feel: a short skew while it travels
        anim(f'tl.fromTo("#{i}m",{{skewX:{-6 if side == "right" else 6 if side == "left" else 0}}},{{skewX:0,duration:0.45,ease:"expo.out"}},{start})')
    anim(f'tl.fromTo("#{i}m",{{scale:{push[0]}}},{{scale:{push[1]},duration:{dur},ease:"none"}},{start})')
    return i


def sticker(name, start, dur, side="right", x=None, h=1250, bottom=0, grey=False, flip=False):
    """Cut-out player with a white outline, standing on the bottom edge; slides in, then floats slightly."""
    i = nid("ct")
    src = media(f"assets/cut/{name}.png")
    with Image.open(os.path.join(HERE, "assets", "cut", name + ".png")) as im:
        w = round(h * im.width / im.height)
    if w > 1000:
        h, w = round(h * 1000 / w), 1000
    left = x if x is not None else (W - w - 20 if side == "right" else 20)
    filt = "grayscale(1) brightness(.9)" if grey else "none"
    add(f'<div id="{i}" {clip_attrs(start, dur)} class="layer" style="position:absolute;left:{left}px;bottom:{bottom}px;width:{w}px;height:{h}px;z-index:{z()}">'
        f'<img id="{i}m" src="{src}" style="width:100%;height:100%;filter:{filt} drop-shadow(0 30px 40px rgba(0,0,0,.6));'
        f'transform:{"scaleX(-1)" if flip else "none"}">{face_marks("cut/" + name, 0, 0, w, h)}</div>')
    cue(start - 0.08, "whoosh", 0.55)
    dx = 700 if side == "right" else -700
    anim(f'tl.fromTo("#{i}",{{x:{dx},opacity:0}},{{x:0,opacity:1,duration:0.6,ease:"expo.out"}},{start})')
    anim(f'tl.fromTo("#{i}",{{y:0}},{{y:-18,duration:{dur},ease:"sine.inOut"}},{start})')
    return i


def video3d(name, start, dur):
    """A Blender render, full frame; holds its last frame if the line runs longer than the shot."""
    i = nid("v3")
    src = media(f"blender/renders/{name}.mp4")
    last = media(f"blender/renders/{name}_last.png")
    with open(os.path.join(HERE, "blender", "renders", name + ".len")) as f:
        vlen = float(f.read())
    add(f'<div id="{i}" {clip_attrs(start, dur)} class="layer full" style="position:absolute;inset:0;z-index:{z()};background:#030304">'
        f'<img src="{last}" style="position:absolute;inset:0;width:100%;height:100%">'
        f'<video id="{i}v" class="clip" src="{src}" muted playsinline data-start="{start}" data-duration="{min(dur, vlen)}" '
        f'data-media-start="0" style="position:absolute;inset:0;width:100%;height:100%"></video></div>')
    return i


def screen(rec, start, dur, side="left", focus="50% 30%", zoom=1.45, mstart=0.3):
    """Screen recording in a floating browser window: swings in tilted, flattens, then pushes in on the data."""
    i = nid("sc")
    src = media(f"capture/out/{rec}.mp4")
    add(f'<div id="{i}" {clip_attrs(start, dur)} style="position:absolute;left:40px;top:560px;width:1000px;height:675px;'
        f'z-index:{z()};perspective:1800px">'
        f'<div id="{i}w" class="win" style="transform-origin:{focus}"><div class="bar"><i></i><i></i><i></i>'
        f'<span>thecricketlounge · record book</span></div>'
        f'<video class="clip" src="{src}" muted playsinline data-start="{start}" data-duration="{dur}" data-media-start="{mstart}" '
        f'style="width:1000px;height:625px;display:block"></video></div></div>')
    cue(start - 0.1, "whoosh", 0.8)
    dx, ry = (-1100, 28) if side == "left" else (1100, -28)
    anim(f'tl.fromTo("#{i}w",{{x:{dx},rotationY:{ry},rotationX:8}},{{x:0,rotationY:0,rotationX:0,duration:0.8,ease:"expo.out"}},{start})')
    anim(f'tl.to("#{i}w",{{scale:{zoom},duration:{max(0.5, dur - 1.0)},ease:"power2.inOut"}},{start + 0.9})')
    return i


def screenshot(path, start, dur, side="right", rot=-4, top=600):
    """A screenshot card dropping in with a slight tilt (the camera-shutter moment)."""
    i = nid("ss")
    src = media(path)
    add(f'<div id="{i}" {clip_attrs(start, dur)} style="position:absolute;left:90px;top:{top}px;width:900px;z-index:{z()}">'
        f'<img src="{src}" style="width:900px;border-radius:22px;box-shadow:0 40px 100px rgba(0,0,0,.7),0 0 0 3px rgba(255,255,255,.9)"></div>')
    cue(start, "shutter", 1.0)
    dx = 900 if side == "right" else -900
    anim(f'tl.fromTo("#{i}",{{x:{dx},rotation:{rot * 3},scale:1.15}},{{x:0,rotation:{rot},scale:1,duration:0.55,ease:"back.out(1.4)"}},{start})')
    return i


# ----------------------------------------------------------------------------- type

def title(lines, start, dur, y=330, size=120, color="#fff", accent=(), align="center", italic=False, sfx="soft"):
    """Heavy headline, each line rising out of a mask with a short blur."""
    i = nid("ti")
    cue(start, sfx, 1.0)
    rows = "".join(f'<div class="mask"><div id="{i}l{k}" class="ln" style="color:{Y if k in accent else color}">'
                   f'{html.escape(t)}</div></div>' for k, t in enumerate(lines))
    y, _ = mv(i, y)
    add(f'<div id="{i}" {clip_attrs(start, dur)} style="position:absolute;left:70px;right:70px;top:{y}px;z-index:{z()};'
        f'font-size:{size}px;text-align:{align};font-style:{"italic" if italic else "normal"}" class="title avoid">{rows}</div>')
    for k in range(len(lines)):
        anim(f'tl.fromTo("#{i}l{k}",{{yPercent:105,filter:"blur(12px)"}},{{yPercent:0,filter:"blur(0px)",duration:0.65,ease:"expo.out"}},{start + 0.08 * k})')
    anim(f'tl.fromTo("#{i}",{{y:0,scale:1}},{{y:-16,scale:1.03,duration:{max(0.3, dur)},ease:"none"}},{start})')
    return i


def typed(lines, start, dur, x=70, y=420, header=None, size=56, cps=34, color=Y):
    """A stat block like a terminal: optional italic header, then lines typed out character by character."""
    i = nid("ty")
    rows = []
    t = start
    if header:
        rows.append(f'<div class="thead" id="{i}h">{html.escape(header)}</div>')
        anim(f'tl.fromTo("#{i}h",{{opacity:0,x:-30}},{{opacity:1,x:0,duration:0.4,ease:"expo.out"}},{t})')
        t += 0.3
    for k, ln in enumerate(lines):
        chars = "".join(f'<span class="ch">{html.escape(c) if c != " " else "&nbsp;"}</span>' for c in ln)
        rows.append(f'<div class="tline" id="{i}r{k}" style="font-size:{size}px;color:{color if k == 0 else "#fff"}">{chars}</div>')
        anim(f'tl.fromTo("#{i}r{k} .ch",{{opacity:0}},{{opacity:1,duration:0.01,stagger:{round(1 / cps, 3)}}},{round(t, 3)})')
        for c in range(0, len(ln), 3):
            cue(t + c / cps, "key", 0.5)
        t += len(ln) / cps + 0.12
    y, x = mv(i, y, x)
    add(f'<div id="{i}" {clip_attrs(start, dur)} style="position:absolute;left:{x}px;top:{y}px;z-index:{z()}" class="typed avoid">'
        f'{"".join(rows)}</div>')
    anim(f'tl.fromTo("#{i}",{{y:0}},{{y:-14,duration:{max(0.3, dur)},ease:"none"}},{start})')
    return i


def odo(num, start, dur, y=520, size=330, color=Y, label=None, x=None, sfx=True):
    """Rolling-digit counter."""
    i = nid("od")
    if sfx:
        cue(start, "roll", 1.0)
    cols = []
    for k, ch in enumerate(num):
        if ch.isdigit():
            strip = "".join(f"<span>{d}</span>" for d in "0123456789")
            cols.append(f'<span class="dcol"><span class="dstrip" id="{i}d{k}">{strip}</span></span>')
            anim(f'tl.fromTo("#{i}d{k}",{{yPercent:0}},{{yPercent:{-int(ch) * 10},duration:{0.9 + 0.15 * k},ease:"expo.out"}},{start + 0.05})')
        else:
            cols.append(f'<span>{html.escape(ch)}</span>')
    lab = f'<div class="olabw"><span class="olab"><i></i>{html.escape(label)}</span></div>' if label else ""
    y, x = mv(i, y, x)
    pos = f"left:{x}px" if x is not None else "left:0;right:0;text-align:center"
    gold = " gold" if color == Y else ""
    add(f'<div id="{i}" {clip_attrs(start, dur)} class="odo avoid{gold}" style="{pos};top:{y}px;font-size:{size}px;color:{color};z-index:{z()}">'
        f'<div class="digits">{"".join(cols)}<span class="oshine"></span></div>{lab}</div>')
    anim(f'tl.fromTo("#{i}",{{scale:0.8,opacity:0}},{{scale:1,opacity:1,duration:0.5,ease:"back.out(1.6)"}},{start})')
    land = start + 0.95 + 0.15 * len(num)
    if dur > land - start + 0.2:
        anim(f'tl.fromTo("#{i} .digits",{{scale:1.1}},{{scale:1,duration:0.35,ease:"back.out(3)"}},{land})')
        anim(f'tl.fromTo("#{i} .oshine",{{xPercent:-160}},{{xPercent:260,duration:0.7,ease:"power2.inOut"}},{land})')
        cue(land, "pop", 0.8)
    anim(f'tl.fromTo("#{i}",{{y:0}},{{y:-18,duration:{max(0.3, dur)},ease:"none"}},{start})')
    if label:
        anim(f'tl.fromTo("#{i} .olab",{{y:20,opacity:0}},{{y:0,opacity:1,duration:0.4,ease:"expo.out"}},{start + 0.35})')
    return i


def tag(txt, start, dur, x=70, y=1250, dark=False):
    """Name tag: yellow pill, the name types in."""
    i = nid("tg")
    chars = "".join(f'<span class="ch">{html.escape(c) if c != " " else "&nbsp;"}</span>' for c in txt)
    y, x = mv(i, y, x)
    add(f'<div id="{i}" {clip_attrs(start, dur)} class="tag avoid{" dark" if dark else ""}" style="left:{x}px;top:{y}px;z-index:{z()}">{chars}</div>')
    anim(f'tl.fromTo("#{i}",{{scaleX:0}},{{scaleX:1,duration:0.35,ease:"expo.out"}},{start})')
    anim(f'tl.fromTo("#{i} .ch",{{opacity:0}},{{opacity:1,duration:0.01,stagger:0.035}},{start + 0.2})')
    cue(start, "pop", 0.8)
    return i


def chip(txt, start, dur, x=70, y=300):
    """Small glass label (date / venue)."""
    i = nid("cp")
    y, x = mv(i, y, x)
    pos = f"left:{x}px" if x is not None else "left:0;right:0;margin:0 auto;width:fit-content"
    add(f'<div id="{i}" {clip_attrs(start, dur)} class="chip avoid" style="{pos};top:{y}px;z-index:{z()}"><span class="dot"></span>{html.escape(txt)}</div>')
    anim(f'tl.fromTo("#{i}",{{y:24,opacity:0}},{{y:0,opacity:1,duration:0.5,ease:"expo.out"}},{start})')
    cue(start, "pop", 0.6)


def bars(a, b, la, lb, start, dur, y=440, unit=""):
    """Two 3D columns (Kohli yellow vs Sachin grey) growing to scale, values counting on top."""
    i = nid("br")
    hmax = 620
    ha, hb = hmax, round(hmax * b / a)
    def col(k, v, h, lab, c, x):
        strip = lambda n: "".join(f'<div class="bnum" id="{i}n{k}">{n}{unit}</div>' for _ in [0])
        return (f'<div class="bcol" style="left:{x}px;top:{y}px;height:{hmax + 160}px">'
                f'{strip(v)}<div class="bbody" id="{i}b{k}" style="height:{h}px;background:linear-gradient(90deg,{c[0]},{c[1]})">'
                f'<div class="btop" style="background:{c[2]}"></div></div><div class="blab">{html.escape(lab)}</div></div>')
    add(f'<div id="{i}" {clip_attrs(start, dur)} style="position:absolute;inset:0;z-index:{z()}">'
        f'{col(0, a, ha, la, ("#d9b93c", Y, "#fff2b0"), 190)}{col(1, b, hb, lb, ("#5a5a60", "#8d8d94", "#c9c9cf"), 600)}</div>')
    for k, (v, h) in enumerate(((a, ha), (b, hb))):
        t0 = start + 0.15 + 0.25 * k
        anim(f'tl.fromTo("#{i}b{k}",{{height:0}},{{height:{h},duration:0.9,ease:"expo.out"}},{t0})')
        anim(f'(()=>{{const o={{v:0}};tl.to(o,{{v:{v},duration:0.9,ease:"expo.out",onUpdate:()=>{{document.getElementById("{i}n{k}").textContent=Math.round(o.v)+"{unit}"}}}},{t0})}})()')
        cue(t0, "rise", 0.7)


def stamp(txt, start, dur, y=760, size=300, color=Y, rot=-6):
    """Word slams in from big to size with a shake."""
    i = nid("sm")
    y, _ = mv(i, y)
    add(f'<div id="{i}" {clip_attrs(start, dur)} class="stamp avoid" style="top:{y}px;font-size:{size}px;color:{color};z-index:{z()}">{html.escape(txt)}</div>')
    anim(f'tl.fromTo("#{i}",{{scale:2.6,opacity:0,rotation:{rot * 2}}},{{scale:1,opacity:1,rotation:{rot},duration:0.32,ease:"power4.in"}},{start})')
    shake(start + 0.3)
    cue(start + 0.3, "impact", 1.0)
    return i


# ----------------------------------------------------------------------------- transitions / fx

def shake(t, amp=22, dur=0.35):
    anim(f'tl.fromTo("#world",{{x:0,y:0}},{{keyframes:[{{x:{amp},y:{-amp // 2}}},{{x:{-amp},y:{amp // 2}}},'
         f'{{x:{amp // 2},y:{amp // 3}}},{{x:0,y:0}}],duration:{dur},ease:"none"}},{t})')


def flash(t, color="#fff", peak=0.85):
    i = nid("fl")
    add(f'<div id="{i}" {clip_attrs(t - 0.02, 0.4)} style="position:absolute;inset:0;background:{color};z-index:{z() + 400};pointer-events:none"></div>')
    anim(f'tl.fromTo("#{i}",{{opacity:{peak}}},{{opacity:0,duration:0.32,ease:"power2.out"}},{t})')


def leak(t, dur=0.8):
    """Warm light leak sweeping across (yellow -> orange), screen-blended."""
    i = nid("lk")
    add(f'<div id="{i}" {clip_attrs(t, dur)} class="leak" style="z-index:{z() + 400}"></div>')
    anim(f'tl.fromTo("#{i}",{{xPercent:-80,opacity:0}},{{keyframes:[{{xPercent:-20,opacity:1,duration:{dur * 0.4}}},'
         f'{{xPercent:60,opacity:0,duration:{dur * 0.6}}}],ease:"none"}},{t})')
    cue(t, "swish", 0.7)


def glitch(t, dur=0.45, name=None):
    """RGB-split slices + jitter. With a photo name, a red/cyan offset copy of it flickers over the frame."""
    i = nid("gl")
    split = ""
    if name:
        src = media(f"assets/hi/{name}.png")
        split = (f'<img id="{i}r" src="{src}" class="gimg" style="mix-blend-mode:screen;filter:url(#red)">'
                 f'<img id="{i}c" src="{src}" class="gimg" style="mix-blend-mode:screen;filter:url(#cyan)">')
    slices = "".join(f'<div class="slice" id="{i}s{k}" style="top:{180 + k * 330}px;height:{40 + (k * 37) % 90}px"></div>' for k in range(5))
    add(f'<div id="{i}" {clip_attrs(t, dur)} style="position:absolute;inset:0;z-index:{z() + 400};pointer-events:none">{split}{slices}</div>')
    steps = max(3, int(dur / 0.05))
    if name:
        anim(f'tl.fromTo("#{i}r",{{x:-26,opacity:.7}},{{x:26,opacity:0,duration:{dur},ease:"steps({steps})"}},{t})')
        anim(f'tl.fromTo("#{i}c",{{x:26,opacity:.7}},{{x:-26,opacity:0,duration:{dur},ease:"steps({steps})"}},{t})')
    for k in range(5):
        anim(f'tl.fromTo("#{i}s{k}",{{x:{(-1) ** k * 120}}},{{x:{(-1) ** (k + 1) * 80},duration:{dur},ease:"steps({steps})"}},{t})')
    shake(t, 14, dur)
    cue(t, "glitch", 1.0)


def duo(name, start, dur, side=None):
    """The red duotone treatment: greyscale photo under a deep red wash."""
    i = photo(name, start, dur, side=side, fx="grey", push=(1.08, 1.18))
    j = nid("du")
    add(f'<div id="{j}" {clip_attrs(start, dur)} style="position:absolute;inset:0;z-index:{z()};background:#d0141e;mix-blend-mode:multiply;opacity:.85"></div>')
    return i


def flicker(names, start, dur):
    """Rapid montage: hard cuts every ~0.13 s with a flash on the last one."""
    n = len(names)
    step = dur / n
    for k, nm in enumerate(names):
        photo(nm, start + k * step, step + 0.02, side=None, push=(1.18, 1.1), whoosh=False)
        cue(start + k * step, "tick", 0.9)
    flash(start + dur - 0.02, peak=0.5)


# ----------------------------------------------------------------------------- captions

NO_CAPTION = set(LINE)  # the data-reel style: headlines carry the words, no word captions


def captions():
    """One word at a time in the lower third: heavy white type with a soft shadow, numbers in yellow, a quick pop."""
    for ln in TL["lines"]:
        if ln["id"] in NO_CAPTION:
            continue
        words = ln["words"]
        for k, (w, t0, t1) in enumerate(words):
            t_next = words[k + 1][1] if k + 1 < len(words) else ln["end"] + 0.12
            num = any(c.isdigit() for c in w)
            i = nid("cap")
            cy, _ = mv(i, 1420)
            add(f'<div id="{i}" {clip_attrs(t0, t_next - t0)} class="cap1 avoid{" num" if num else ""}" style="top:{cy}px"><span>{html.escape(w.upper().strip(",.…"))}</span></div>')
            anim(f'tl.fromTo("#{i} span",{{scale:0.7,y:10}},{{scale:1,y:0,duration:0.16,ease:"back.out(2.6)"}},{t0})')


# ----------------------------------------------------------------------------- the edit


def legend(first, last, start, dur, country, k, photo_name=None):
    """A legend's name card: first name small, surname huge, country chip, a fast slide from alternating sides.
    Uses their photo full-screen when one is in assets/hi/, otherwise a type-only card on grain."""
    side = "left" if k % 2 else "right"
    if photo_name and os.path.exists(os.path.join(HERE, "assets", "hi", photo_name + ".png")):
        photo(photo_name, start, dur, side=side, push=(1.0, 1.08), whoosh=False)
    else:
        i = stage(start, dur, tone="#0d0d0f")
        anim(f'tl.fromTo("#{i}",{{xPercent:{-100 if side == "left" else 100}}},{{xPercent:0,duration:0.32,ease:"expo.out"}},{start})')
        num = nid("lg")
        add(f'<div id="{num}" {clip_attrs(start, dur)} class="lgnum" style="z-index:{z()}">{k + 1:02d}</div>')
        anim(f'tl.fromTo("#{num}",{{x:{-200 if side == "left" else 200},opacity:0}},{{x:0,opacity:1,duration:0.5,ease:"expo.out"}},{start})')
    cue(start - 0.06, "whoosh", 0.7)
    title([first], start + 0.02, dur, y=700, size=70, color="rgba(255,255,255,.8)", sfx="soft")
    title([last.upper()], start + 0.06, dur, y=780, size=150 if len(last) < 10 else 112, accent=(0,), sfx="soft")
    chip(country, start + 0.12, dur - 0.12, x=None, y=1000)


def name_wall(start, dur, names, y=300):
    """Every legend at once: surnames tile in as a wall, then hold."""
    i = nid("nw")
    cells = "".join(f'<div class="nwc" id="{i}c{k}"><span>{html.escape(n.upper())}</span></div>' for k, n in enumerate(names))
    add(f'<div id="{i}" {clip_attrs(start, dur)} class="nwall avoid" style="top:{y}px;z-index:{z()}">{cells}</div>')
    for k in range(len(names)):
        anim(f'tl.fromTo("#{i}c{k}",{{scale:0.6,opacity:0,rotationX:-70}},{{scale:1,opacity:1,rotationX:0,duration:0.45,ease:"back.out(1.6)"}},{start + 0.06 * k})')
        cue(start + 0.06 * k, "tick", 0.8)


def quote_card(start, dur, txt, who):
    """'You'll grow out of it.': a big quote typed out between giant quote marks, attribution underneath."""
    i = nid("qt")
    # words stay whole (no line break inside a word or before its full stop)
    chars = " ".join('<span class="wd">' + "".join(f'<span class="ch">{html.escape(c)}</span>' for c in w) + "</span>"
                     for w in txt.split())
    add(f'<div id="{i}" {clip_attrs(start, dur)} class="quote avoid" style="z-index:{z()}"><div class="qm" id="{i}q">“</div>'
        f'<div class="qt">{chars}</div><div class="qw" id="{i}w">— {html.escape(who)}</div></div>')
    anim(f'tl.fromTo("#{i}q",{{scale:0.3,opacity:0}},{{scale:1,opacity:1,duration:0.5,ease:"back.out(1.8)"}},{start})')
    anim(f'tl.fromTo("#{i} .ch",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.1,stagger:0.028}},{start + 0.2})')
    anim(f'tl.fromTo("#{i}w",{{opacity:0}},{{opacity:1,duration:0.4}},{start + 0.2 + 0.028 * len(txt)})')
    for c in range(0, len(txt), 2):
        cue(start + 0.2 + 0.028 * c, "key", 0.6)


def records_fan(start, dur, shots):
    """Screenshots of the record book fly in and fan out like a deck: 'I went through every record'."""
    for k, path in enumerate(shots):
        screenshot(path, start + 0.28 * k, dur - 0.28 * k, side="right" if k % 2 else "left", rot=(-7, 4, -2)[k % 3],
                   top=520 + 120 * k)


def years(start, dur, a, b, label):
    """a ———— b: a line draws across, the year counts up, a label lands underneath."""
    i = nid("yl")
    add(f'<div id="{i}" {clip_attrs(start, dur)} style="position:absolute;inset:0;z-index:{z()}">'
        f'<div class="ylab" style="left:90px">{a}</div><div class="ylab" id="{i}y" style="right:90px;color:{Y}">{a}</div>'
        f'<div class="yline"><div id="{i}f" class="yfill"></div></div>'
        f'<div class="ybig" id="{i}b">{html.escape(label)}</div></div>')
    d = min(1.4, dur * 0.7)
    anim(f'tl.fromTo("#{i}f",{{scaleX:0}},{{scaleX:1,duration:{d},ease:"power2.inOut"}},{start + 0.1})')
    anim(f'(()=>{{const o={{v:{a}}};tl.to(o,{{v:{b},duration:{d},ease:"power2.inOut",onUpdate:()=>{{document.getElementById("{i}y").textContent=Math.round(o.v)}}}},{start + 0.1})}})()')
    anim(f'tl.fromTo("#{i}b",{{scale:0.6,opacity:0}},{{scale:1,opacity:1,duration:0.5,ease:"back.out(1.8)"}},{start + d})')
    cue(start + 0.1, "rise", 0.8)
    for k in range(10):
        cue(start + 0.1 + k * d / 10, "tick", 0.5)


def receipt(n, start, dur, total=8):
    """Proof counter in the corner: PROOF 3/8 — ticks up with every new receipt."""
    i = nid("rc")
    add(f'<div id="{i}" {clip_attrs(start, dur)} class="receipt" style="z-index:{z() + 300}"><span class="rl">PROOF</span>'
        f'<span class="rn">{n}</span><span class="rt">/{total}</span></div>')
    anim(f'tl.fromTo("#{i} .rn",{{yPercent:100,opacity:0}},{{yPercent:0,opacity:1,duration:0.35,ease:"back.out(2)"}},{start})')


def then_now(start, dur, a_photo, b_photo, la="THEN", lb="NOW", grey=True):
    """Split screen: THEN (grey, 2007) on top, NOW (colour) underneath; the divider wipes across."""
    i = nid("tn")
    sa, sb = media(f"assets/hi/{a_photo}.png"), media(f"assets/hi/{b_photo}.png")
    add(f'<div id="{i}" {clip_attrs(start, dur)} class="layer full" style="position:absolute;inset:0;z-index:{z()};background:#000">'
        f'<div class="half" id="{i}a" style="top:0"><img src="{sa}" style="filter:{"grayscale(1) contrast(1.1)" if grey else "none"}"><div class="hl">{html.escape(la)}</div></div>'
        f'<div class="half" id="{i}b" style="top:960px"><img src="{sb}"><div class="hl" style="color:{Y}">{html.escape(lb)}</div></div>'
        f'<div class="hdiv" id="{i}d"></div></div>')
    anim(f'tl.fromTo("#{i}a",{{xPercent:-100}},{{xPercent:0,duration:0.5,ease:"expo.out"}},{start})')
    anim(f'tl.fromTo("#{i}b",{{xPercent:100}},{{xPercent:0,duration:0.5,ease:"expo.out"}},{start + 0.25})')
    anim(f'tl.fromTo("#{i}d",{{scaleX:0}},{{scaleX:1,duration:0.6,ease:"expo.out"}},{start + 0.4})')
    cue(start - 0.08, "whoosh", 0.8)
    cue(start + 0.17, "whoosh", 0.8)


def recap(start, dur, items):
    i = nid("rp")
    rows = "".join(f'<div class="rrow" id="{i}r{k}"><span class="tick" id="{i}t{k}">✓</span>{html.escape(t)}</div>'
                   for k, t in enumerate(items))
    add(f'<div id="{i}" {clip_attrs(start, dur)} class="recap avoid" style="z-index:{z()}">{rows}</div>')
    for k in range(len(items)):
        t0 = start + 0.09 * k
        anim(f'tl.fromTo("#{i}r{k}",{{x:-80,opacity:0}},{{x:0,opacity:1,duration:0.4,ease:"expo.out"}},{t0})')
        anim(f'tl.fromTo("#{i}t{k}",{{scale:0}},{{scale:1,duration:0.3,ease:"back.out(2.5)"}},{t0 + 0.15})')
        cue(t0 + 0.15, "pop", 0.7)


def comment_cta(start, dur):
    i = nid("cm")
    add(f'<div id="{i}" {clip_attrs(start, dur)} class="cta" style="z-index:{z()}">'
        f'<div class="bubble" id="{i}b"><div class="av"></div><div><div class="who">you</div>'
        f'<div class="what" id="{i}w"></div></div></div><div class="cta2">Who was your childhood GOAT?</div></div>')
    anim(f'tl.fromTo("#{i}b",{{y:60,opacity:0,scale:.9}},{{y:0,opacity:1,scale:1,duration:0.6,ease:"back.out(1.6)"}},{start + 0.3})')
    txt = "Dhoni. Always 💛"
    anim(f'(()=>{{const o={{n:0}};const s="{txt}";tl.to(o,{{n:[...s].length,duration:1.0,ease:"none",onUpdate:()=>{{document.getElementById("{i}w").textContent=[...s].slice(0,Math.round(o.n)).join("")}}}},{start + 0.8})}})()')
    cue(start + 0.3, "pop", 1.0)


BOARD = [("ROHIT SHARMA", "India", 650, "650+"), ("CHRIS GAYLE", "West Indies", 553, "553"),
         ("SHAHID AFRIDI", "Pakistan", 476, "476"), ("BRENDON McCULLUM", "New Zealand", 398, "398"),
         ("MARTIN GUPTILL", "New Zealand", 383, "383")]


def leaderboard(start, dur, reveal=False, y=380):
    """The top five as a leaderboard: rows rise in from #5 up, bars grow to scale, numbers count.
    reveal=False keeps #1 as a '???' tease; reveal=True lands Rohit on top with a glow."""
    i = nid("lb")
    rows = []
    for k, (name, team, n, lab) in enumerate(BOARD):
        top = k == 0
        hide = top and not reveal
        w = round(560 * n / 650)
        rows.append(f'<div class="lbr{" lbtop" if top else ""}" id="{i}r{k}"><div class="lbk">{k + 1}</div>'
                    f'<div class="lbm"><div class="lbn">{"? ? ?" if hide else html.escape(name)}</div>'
                    f'<div class="lbbar"><div class="lbf" id="{i}f{k}" style="width:{0 if hide else w}px"></div></div></div>'
                    f'<div class="lbv" id="{i}v{k}">{"???" if hide else "0"}</div></div>')
    add(f'<div id="{i}" {clip_attrs(start, dur)} class="lboard avoid" style="top:{y}px;z-index:{z()}">{"".join(rows)}</div>')
    order = list(range(4, -1, -1))  # #5 first
    for j, k in enumerate(order):
        t0 = start + 0.12 + (0.16 if not reveal else 0.1) * j + (0.35 if reveal and k == 0 else 0)
        anim(f'tl.fromTo("#{i}r{k}",{{x:-120,opacity:0}},{{x:0,opacity:1,duration:0.45,ease:"expo.out"}},{t0})')
        name, team, n, lab = BOARD[k]
        if k == 0 and not reveal:
            cue(t0, "pop", 0.8)
            continue
        anim(f'tl.fromTo("#{i}f{k}",{{scaleX:0}},{{scaleX:1,duration:0.8,ease:"expo.out"}},{t0 + 0.1})')
        plus = "+" if lab.endswith("+") else ""
        anim(f'(()=>{{const o={{v:0}};tl.to(o,{{v:{n},duration:0.8,ease:"expo.out",onUpdate:()=>{{document.getElementById("{i}v{k}").textContent=Math.round(o.v)+(o.v>={n}-0.5?"{plus}":"")}}}},{t0 + 0.1})}})()')
        cue(t0 + 0.1, "rise" if k else "impact", 0.8 if k else 1.0)
    if reveal:
        anim(f'tl.fromTo("#{i}r0",{{boxShadow:"0 0 0 rgba(254,222,92,0)"}},{{boxShadow:"0 0 60px rgba(254,222,92,.55)",duration:0.6,yoyo:true,repeat:3}},{start + 0.9})')
        flash(start + 0.85, peak=0.3)


def versus(start, dur, a, b, la, lb, y=420):
    """Two bars: Rohit 650+ vs Gayle 553 — the gap you can see."""
    i = nid("vs")
    def col(k, n, lab, name, x, gold):
        h = round(640 * n / 650)
        c = ("#d9b93c", Y, "#fff2b0") if gold else ("#5a5a60", "#8d8d94", "#c9c9cf")
        return (f'<div class="bcol" style="left:{x}px;top:{y}px;height:800px"><div class="bnum" id="{i}n{k}">{lab}</div>'
                f'<div class="bbody" id="{i}b{k}" style="height:{h}px;background:linear-gradient(90deg,{c[0]},{c[1]})">'
                f'<div class="btop" style="background:{c[2]}"></div></div><div class="blab">{name}</div></div>')
    add(f'<div id="{i}" {clip_attrs(start, dur)} class="avoid" style="position:absolute;inset:0;z-index:{z()}">'
        f'{col(0, a[0], a[1], la, 190, True)}{col(1, b[0], b[1], lb, 600, False)}</div>')
    for k, n in enumerate((a[0], b[0])):
        t0 = start + 0.1 + 0.2 * k
        anim(f'tl.fromTo("#{i}b{k}",{{height:0}},{{height:{round(640 * n / 650)},duration:0.9,ease:"expo.out"}},{t0})')
        anim(f'tl.fromTo("#{i}n{k}",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.4}},{t0 + 0.5})')
        cue(t0, "rise", 0.8)


def strike_list(start, dur, names, y=560):
    """The reference reel's crossing-out move: names stack in, then a line strikes through each one."""
    i = nid("sl")
    rows = "".join(f'<div class="slr" id="{i}r{k}"><span>{html.escape(n)}</span><i class="sll" id="{i}l{k}"></i></div>'
                   for k, n in enumerate(names))
    add(f'<div id="{i}" {clip_attrs(start, dur)} class="slist avoid" style="top:{y}px;z-index:{z()}">{rows}</div>')
    n = len(names)
    for k in range(n):
        anim(f'tl.fromTo("#{i}r{k}",{{y:40,opacity:0}},{{y:0,opacity:1,duration:0.35,ease:"expo.out"}},{start + 0.08 * k})')
        t1 = start + 0.45 + (dur - 0.8) * k / max(1, n)
        anim(f'tl.fromTo("#{i}l{k}",{{scaleX:0}},{{scaleX:1,duration:0.25,ease:"power2.out"}},{t1})')
        anim(f'tl.to("#{i}r{k} span",{{opacity:.35,duration:0.25}},{t1})')
        cue(t1, "swish", 0.8)


def slowmo(name, start, dur):
    """'Bats like he's in slow motion': a very slow push, ghost echoes trailing behind, SLOW MOTION stretching out."""
    i = photo(name, start, dur, side=None, push=(1.0, 1.05), whoosh=False)
    src = media(f"assets/hi/{name}.png")
    for k in range(3):
        g = nid("gh")
        add(f'<div id="{g}" {clip_attrs(start, dur)} style="position:absolute;inset:0;z-index:{z()};pointer-events:none;mix-blend-mode:screen;opacity:{0.28 - 0.07 * k}">'
            f'<img src="{src}" style="width:100%;height:100%;object-fit:cover;object-position:50% 30%;filter:blur({2 + 2 * k}px)"></div>')
        anim(f'tl.fromTo("#{g}",{{x:0,y:0}},{{x:{-26 * (k + 1)},y:{10 * (k + 1)},duration:{dur},ease:"sine.out"}},{start})')
    t = nid("sm")
    add(f'<div id="{t}" {clip_attrs(start, dur)} class="slowt avoid" style="z-index:{z()}">SLOW MOTION</div>')
    anim(f'tl.fromTo("#{t}",{{letterSpacing:"-0.04em",opacity:0}},{{letterSpacing:"0.22em",opacity:1,duration:{dur},ease:"power1.out"}},{start + 0.1})')
    cue(start, "swish", 0.9)
    return i


def badge(n, start, dur):
    """The rank stays pinned top-left for the player's whole segment (from the new reference)."""
    i = nid("bd")
    add(f'<div id="{i}" {clip_attrs(start, dur)} class="badge" style="z-index:{z() + 350}">{n}</div>')
    anim(f'tl.fromTo("#{i}",{{scale:0,rotation:-90}},{{scale:1,rotation:0,duration:0.45,ease:"back.out(2.2)"}},{start})')
    cue(start, "pop", 0.7)


def hero(cut, lines, start, dur):
    """Cut-out on the grid with a big yellow circle behind and chunky white type underneath (reference hook look)."""
    i = stage(start, dur, tone="#0d0d0f")
    j = nid("hr")
    add(f'<div id="{j}" {clip_attrs(start, dur)} class="hero" style="z-index:{z()}"><div class="circ" id="{j}c"></div></div>')
    anim(f'tl.fromTo("#{j}c",{{scale:0}},{{scale:1,duration:0.55,ease:"back.out(1.6)"}},{start})')
    anim(f'tl.fromTo("#{j}c",{{y:0}},{{y:-30,duration:{dur},ease:"none"}},{start})')
    with Image.open(os.path.join(HERE, "assets", "cut", cut + ".png")) as im:
        cw = min(1000, round(1250 * im.width / im.height))
    sticker(cut, start + 0.05, dur - 0.05, side="right", h=1250, x=round((W - cw) / 2), bottom=0)
    k = nid("hb")
    rows = "<br>".join(html.escape(t) for t in lines)
    add(f'<div id="{k}" {clip_attrs(start, dur)} class="hero avoid" style="z-index:{z()}"><div class="big" id="{k}t">{rows}</div></div>')
    anim(f'tl.fromTo("#{k}t",{{scale:1.6,opacity:0}},{{scale:1,opacity:1,duration:0.22,ease:"power4.in"}},{start + 0.1})')
    anim(f'tl.fromTo("#{k}t",{{y:0}},{{y:-20,duration:{dur},ease:"none"}},{start + 0.32})')
    shake(start + 0.32, 18)
    cue(start + 0.32, "impact", 1.0)
    return i


def pips(cards, start, dur):
    """Small picture-in-picture cards stacking in at the top right, each with a name strip."""
    for k, (name, label) in enumerate(cards):
        i = nid("pp")
        src = media(f"assets/hi/{name}.png")
        add(f'<div id="{i}" {clip_attrs(start + 0.35 * k, dur - 0.35 * k)} class="pip" style="right:{50 + 30 * k}px;top:{290 + 410 * k}px;'
            f'z-index:{z()}"><img src="{src}"><b>{html.escape(label)}</b></div>')
        anim(f'tl.fromTo("#{i}",{{x:420,rotation:8}},{{x:0,rotation:{(-3, 3)[k % 2]},duration:0.5,ease:"back.out(1.5)"}},{start + 0.35 * k})')
        cue(start + 0.35 * k, "whoosh", 0.6)


def depth_number(cut, num, label, start, dur):
    """Depth layer: blurred backdrop, a giant number, and the player's cut-out standing in front of it."""
    i = nid("dp")
    fill = media(f"assets/fill/{cut}.jpg")
    add(f'<div id="{i}" {clip_attrs(start, dur)} class="layer full" style="position:absolute;inset:0;z-index:{z()};background:#000">'
        f'<img id="{i}b" src="{fill}" style="position:absolute;inset:-60px;width:calc(100% + 120px);height:calc(100% + 120px);object-fit:cover;filter:brightness(.8) saturate(1.2)">'
        f'<div class="vig"></div></div>')
    anim(f'tl.fromTo("#{i}b",{{scale:1.15}},{{scale:1.0,duration:{dur},ease:"none"}},{start})')
    j = nid("dn")
    add(f'<div id="{j}" {clip_attrs(start, dur)} class="dnum avoid" style="z-index:{z()}"><div id="{j}n">{html.escape(num)}</div><span>{html.escape(label)}</span></div>')
    anim(f'tl.fromTo("#{j}n",{{yPercent:60,opacity:0,scale:.85}},{{yPercent:0,opacity:1,scale:1,duration:0.6,ease:"expo.out"}},{start + 0.05})')
    anim(f'tl.fromTo("#{j}",{{y:0,scale:1}},{{y:-30,scale:1.05,duration:{dur},ease:"none"}},{start})')
    cue(start + 0.05, "impact", 0.9)
    sticker(cut, start + 0.15, dur - 0.15, side="left", h=1300, x=170)


def band(num, label, start, dur, y=1160):
    """Broadcast lower-third: a yellow band slams across with the number and a label."""
    i = nid("bn")
    add(f'<div id="{i}" {clip_attrs(start, dur)} class="band avoid" style="top:{y}px;z-index:{z()}"><b id="{i}n">{html.escape(num)}</b><span>{html.escape(label)}</span></div>')
    anim(f'tl.fromTo("#{i}",{{xPercent:-110,skewX:-12}},{{xPercent:0,skewX:0,duration:0.42,ease:"expo.out"}},{start})')
    anim(f'tl.fromTo("#{i}n",{{scale:1.5}},{{scale:1,duration:0.3,ease:"back.out(2.4)"}},{start + 0.25})')
    anim(f'tl.fromTo("#{i}",{{x:0}},{{x:-24,duration:{dur},ease:"none"}},{start})')
    shake(start + 0.3, 14)
    cue(start, "whoosh_big", 0.9)
    cue(start + 0.3, "impact", 0.9)


def stat_screen(cut, num, lines, start, dur, x=430, h=1250):
    """The Gayle-style stat screen: outlined cut-out on the right, rolling number + typed descriptor on the left."""
    stage(start, dur)
    sticker(cut, start, dur, side="right", h=h, x=x)
    odo(num, start + 0.1, dur - 0.1, x=70, y=330, size=300)
    typed(lines, start + 0.35, dur - 0.35, y=700, size=58)


def rank_card(num_shot, name, lid, nxt, word_name):
    """'At number N, it's X': the 3D number, then the player's first photo lands on their name."""
    video3d(num_shot, s(lid, -0.1), word(lid, word_name) - s(lid, -0.1) + 0.02)
    cue(s(lid, -0.6), "riser", 0.7)
    cue(s(lid), "boom", 0.9)


def comment_cta(start, dur):
    i = nid("cm")
    add(f'<div id="{i}" {clip_attrs(start, dur)} class="cta" style="z-index:{z()}">'
        f'<div class="mot" id="{i}q"><span>GREATEST</span><i>No. 3</i><span style="color:{Y}">EVER?</span></div>'
        f'<div class="bubble" id="{i}b"><div class="av"></div><div><div class="who">you</div>'
        f'<div class="what" id="{i}w"></div></div></div><div class="cta2">Tell me in the comments 👇</div></div>')
    anim(f'tl.fromTo("#{i}q span,#{i}q i",{{y:40,opacity:0}},{{y:0,opacity:1,duration:0.5,stagger:0.12,ease:"back.out(1.8)"}},{start})')
    anim(f'tl.fromTo("#{i}b",{{y:60,opacity:0,scale:.9}},{{y:0,opacity:1,scale:1,duration:0.6,ease:"back.out(1.6)"}},{start + 0.6})')
    txt = "No contest. King Kohli 👑"
    anim(f'(()=>{{const o={{n:0}};const s="{txt}";tl.to(o,{{n:[...s].length,duration:0.7,ease:"none",onUpdate:()=>{{document.getElementById("{i}w").textContent=[...s].slice(0,Math.round(o.n)).join("")}}}},{start + 1.1})}})()')
    cue(start, "pop", 1.0)


def bg(name, start, dur, grade="dark", credit="PHOTO: BCCI", push=(1.0, 1.08), side=None, origin="50% 35%", tall=False):
    """News look: a big photo, graded dark (or B&W / blue), slow push, photo credit at the bottom.
    tall=True: the photo fills the top 1260 px (for low-res / wide shots), cropped on the face, type sits below it."""
    if tall:
        i = nid("tp")
        src = media(f"assets/hi/{name}.png")
        with Image.open(os.path.join(HERE, "assets", "hi", name + ".png")) as im:
            iw, ih = im.size
        bh = 1260
        dw, dh = max(W, iw * bh / ih), max(bh, ih * W / iw)
        fxp = min(1.0, max(0.0, (W / 2 - focus_x(name) * dw) / (W - dw))) if dw > W + 1 else 0.5
        filt = "grayscale(1) contrast(1.1) brightness(.85)" if grade == "bw" else "none"
        marks = face_marks("hi/" + name, (W - dw) * fxp, (bh - dh) * 0.3, dw, dh)
        add(f'<div id="{i}" {clip_attrs(start, dur)} class="layer full" style="position:absolute;inset:0;z-index:{z()};background:#05070d;overflow:hidden">'
            f'<div id="{i}m" style="position:absolute;left:0;top:0;width:100%;height:{bh}px;transform-origin:{origin}">'
            f'<img src="{src}" style="width:100%;height:100%;object-fit:cover;object-position:{fxp * 100:.1f}% 30%;filter:{filt}">{marks}</div>'
            f'<div class="tfade"></div></div>')
        anim(f'tl.fromTo("#{i}m",{{scale:{push[0]}}},{{scale:{push[1]},duration:{dur},ease:"none"}},{start})')
    else:
        i = photo(name, start, dur, side=side, fx="grey" if grade == "bw" else None, push=push, origin=origin, whoosh=bool(side))
    tint = {"dark": "rgba(0,0,0,0)", "bw": "rgba(0,0,0,.1)", "blue": "rgba(10,30,90,.28)"}[grade]
    g = nid("gr")
    add(f'<div id="{g}" {clip_attrs(start, dur)} class="ngrade" style="z-index:{z()};background-color:{tint}"></div>')
    if credit:
        c = nid("cr")
        add(f'<div id="{c}" {clip_attrs(start, dur)} class="credit" style="z-index:{z() + 150}">{html.escape(credit)}</div>')
    return i


def ntag(txt, start, dur, color="#e3262f"):
    i = nid("tg")
    add(f'<div id="{i}" {clip_attrs(start, dur)} class="ntag" style="z-index:{z() + 150};background:{color}">{html.escape(txt)}</div>')
    anim(f'tl.fromTo("#{i}",{{x:-40,opacity:0}},{{x:0,opacity:1,duration:0.4,ease:"expo.out"}},{start})')


def nbig(lines, start, dur, color="#ff3340", sub=None, y=860, size=190, sfx="impact"):
    """The huge italic headline that blurs in."""
    i = nid("nb")
    cue(start, sfx, 1.0)
    rows = "".join(f'<div>{html.escape(t)}</div>' for t in lines)
    sb = f'<div class="nsub" id="{i}s">{html.escape(sub)}</div>' if sub else ""
    y, _ = mv(i, y)
    add(f'<div id="{i}" {clip_attrs(start, dur)} class="nbig avoid" style="top:{y}px;font-size:{size}px;color:{color};z-index:{z()}">'
        f'<div id="{i}t">{rows}</div>{sb}</div>')
    anim(f'tl.fromTo("#{i}t",{{scale:1.25,opacity:0,filter:"blur(18px)"}},{{scale:1,opacity:1,filter:"blur(0px)",duration:0.45,ease:"expo.out"}},{start})')
    anim(f'tl.fromTo("#{i}",{{scale:1}},{{scale:1.05,duration:{max(0.5, dur)},ease:"none"}},{start})')
    if sub:
        anim(f'tl.fromTo("#{i}s",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.4}},{start + 0.35})')


def sbox(a, b, start, dur, sub=None, pill=None, y=1040, roll=None, gold_sub=False):
    """Dark glass stat box: the number counts a -> b (formatted with commas), sub line under it, optional pill on top."""
    i = nid("sb")
    pl = f'<div class="spill" id="{i}p">{html.escape(pill)}</div>' if pill else ""
    sb = f'<span id="{i}s" class="{"gsub" if gold_sub else ""}">{html.escape(sub)}</span>' if sub else ""
    y, _ = mv(i, y)
    add(f'<div id="{i}" {clip_attrs(start, dur)} class="sbox avoid" style="top:{y}px;z-index:{z()}">{pl}'
        f'<b id="{i}n">{a:,}</b>{sb}</div>')
    anim(f'tl.fromTo("#{i}",{{y:60,opacity:0}},{{y:0,opacity:1,duration:0.45,ease:"expo.out"}},{start})')
    t0 = start + 0.25 if roll is None else roll
    if a != b:
        d = 1.0
        anim(f'(()=>{{const o={{v:{a}}};tl.to(o,{{v:{b},duration:{d},ease:"power2.out",onUpdate:()=>{{document.getElementById("{i}n").textContent=Math.round(o.v).toLocaleString("en-US")}}}},{t0})}})()')
        for k in range(10):
            cue(t0 + k * 0.08, "tick", 0.6)
        anim(f'tl.fromTo("#{i}n",{{scale:1.12}},{{scale:1,duration:0.35,ease:"back.out(3)"}},{t0 + d})')
        cue(t0 + d, "impact", 0.8)
    if pill:
        anim(f'tl.fromTo("#{i}p",{{scale:0,opacity:0}},{{scale:1,opacity:1,duration:0.35,ease:"back.out(2.4)"}},{start + 0.2})')
    return i


def vs_scene(start, dur, cells):
    """Split screen: Kohli on top, Ponting below, a VS badge between; each stat cell lands at its own time.
    cells: [(row 0/1, col 0..2, text, t)]"""
    i = nid("vs")
    ka, pa = media("assets/hi/kohli_hands.png"), media("assets/hi/ponting_bat.png")
    def box(r, name):
        cols = "".join(f'<div class="vc"><i>{lab}</i><b id="{i}v{r}{k}">&nbsp;</b></div>' for k, lab in enumerate(("INNINGS", "AVERAGE", "100s")))
        return f'<div class="vpill">{name}</div><div class="vbox">{cols}</div>'
    add(f'<div id="{i}" {clip_attrs(start, dur)} class="layer full" style="position:absolute;inset:0;z-index:{z()};background:#05070d">'
        f'<div class="vh" id="{i}a" style="top:0"><img src="{ka}" style="object-position:50% 32%"><div class="vsh"></div>'
        f'<div class="vstack" style="top:700px">{box(0, "VIRAT KOHLI · 13,000+ RUNS")}<div class="credit2">PHOTO: BCCI</div></div></div>'
        f'<div class="vh" id="{i}b" style="top:960px"><img src="{pa}" style="object-position:40% 18%"><div class="vsh"></div>'
        f'<div class="vstack" style="top:600px">{box(1, "RICKY PONTING · 12,662 RUNS")}<div class="credit2">PHOTO: GETTY IMAGES</div></div></div>'
        f'<div class="vsb" id="{i}x">VS</div></div>')
    anim(f'tl.fromTo("#{i}a",{{yPercent:-100}},{{yPercent:0,duration:0.5,ease:"expo.out"}},{start})')
    anim(f'tl.fromTo("#{i}b",{{yPercent:100}},{{yPercent:0,duration:0.5,ease:"expo.out"}},{start + 0.1})')
    anim(f'tl.fromTo("#{i}x",{{scale:0,rotation:-90}},{{scale:1,rotation:0,duration:0.45,ease:"back.out(2.2)"}},{start + 0.45})')
    anim(f'tl.fromTo("#{i} .vh img",{{scale:1}},{{scale:1.08,duration:{dur},ease:"none"}},{start})')
    cue(start, "whoosh_big", 0.9)
    for r, c, txt, t in cells:
        anim(f'tl.call(()=>{{document.getElementById("{i}v{r}{c}").textContent={json.dumps(txt)}}},null,{t})')
        anim(f'tl.fromTo("#{i}v{r}{c}",{{scale:1.6,opacity:0}},{{scale:1,opacity:1,duration:0.3,ease:"back.out(2.5)"}},{t})')
        cue(t, "pop", 0.9)


def notebox(top, main, start, dur, t2=None, y=1180):
    i = nid("nt")
    y, _ = mv(i, y)
    add(f'<div id="{i}" {clip_attrs(start, dur)} class="sbox avoid" style="top:{y}px;z-index:{z()}">'
        f'<span style="font-size:30px;color:#aab">{html.escape(top)}</span>'
        f'<span id="{i}m" class="gsub" style="font-size:64px;margin-top:14px">{html.escape(main)}</span></div>')
    anim(f'tl.fromTo("#{i}",{{y:60,opacity:0}},{{y:0,opacity:1,duration:0.45,ease:"expo.out"}},{start})')
    anim(f'tl.fromTo("#{i}m",{{opacity:0,scale:1.2}},{{opacity:1,scale:1,duration:0.4,ease:"back.out(2)"}},{t2 or start + 0.3})')
    cue(t2 or start + 0.3, "impact", 0.8)


RANKS = [("VIRAT KOHLI", 13000, "13,000+"), ("RICKY PONTING", 12662, "12,662"), ("KUMAR SANGAKKARA", 9747, "9,747"),
         ("JACQUES KALLIS", 7774, "7,774"), ("KANE WILLIAMSON", 6504, "6,504")]


def ranks(start, dur):
    i = nid("rk")
    rows = "".join(f'<div class="rr{" rtop" if k == 0 else ""}" id="{i}r{k}"><div class="rl"><span>{n}</span><b>{lab}</b></div>'
                   f'<div class="rt"><div class="rf" id="{i}f{k}" style="width:{v / 13000 * 100:.1f}%"></div></div></div>'
                   for k, (n, v, lab) in enumerate(RANKS))
    add(f'<div id="{i}" {clip_attrs(start, dur)} class="ranks avoid" style="z-index:{z()}"><div class="rh">MOST ODI RUNS AT NO. 3</div>{rows}'
        f'<div class="rfoot">THE GREATEST NO. 3?</div></div>')
    anim(f'tl.fromTo("#{i} .rh",{{x:-60,opacity:0}},{{x:0,opacity:1,duration:0.45,ease:"expo.out"}},{start})')
    for k in range(len(RANKS)):
        t = start + 0.15 + 0.12 * k
        anim(f'tl.fromTo("#{i}r{k}",{{x:-80,opacity:0}},{{x:0,opacity:1,duration:0.4,ease:"expo.out"}},{t})')
        anim(f'tl.fromTo("#{i}f{k}",{{scaleX:0}},{{scaleX:1,duration:0.8,ease:"expo.out"}},{t + 0.1})')
        cue(t, "tick", 0.8)
    anim(f'tl.fromTo("#{i} .rfoot",{{scale:0.7,opacity:0}},{{scale:1,opacity:1,duration:0.45,ease:"back.out(2)"}},{start + 1.2})')


def edit():
    def seg(t0, t1):
        return round(t0, 3), round(t1 - t0, 3)

    # ---------------- 55 years... nobody... at No. 3
    bg("kohli_13k_bat_bw", *seg(0, s("l3", -0.05)), grade="bw", push=(1.12, 1.03), tall=True)
    ntag("ONE-DAY INTERNATIONALS · SINCE 1971", *seg(0.1, s("l3", -0.05)))
    nbig(["55 YEARS"], *seg(0.15, s("l2")), sub="OF ODI CRICKET", y=1180, size=170)
    nbig(["NOBODY"], *seg(s("l2"), word("l2", 5)), sub="HAD EVER DONE THIS", y=1180, size=170)
    nbig(["AT NO. 3"], *seg(word("l2", 5), s("l3", -0.05)), y=1200, size=170)
    # ---------------- 13,000
    flash(s("l3", -0.05), peak=0.7)
    cue(s("l3", -0.05), "boom", 1.0)
    bg("kohli_13k_celebrate", *seg(s("l3", -0.05), s("p1", -0.05)), grade="blue", push=(1.0, 1.08), tall=True)
    ntag("NOV 2026 · ODI · NO. 3", *seg(s("l3"), s("p1", -0.05)), color="#2f6bff")
    sbox(12954, 13000, *seg(s("l3"), s("l4")), sub="ODI RUNS AT NO. 3", pill="THE FIRST EVER", y=1220)
    sbox(13000, 13000, *seg(s("l4"), s("p1", -0.05)), sub="VIRAT KOHLI", pill="THE FIRST EVER", gold_sub=True, y=1220)
    # ---------------- Ponting's record
    bg("ponting_helmet", *seg(s("p1", -0.05), s("p2", -0.05)), credit="PHOTO: GETTY IMAGES", side="right", push=(1.0, 1.1))
    ntag("THE OLD RECORD", *seg(s("p1"), s("p2", -0.05)), color="#e3262f")
    nbig(["RICKY", "PONTING"], *seg(word("p1", 5), s("p2", -0.05)), color="#FFD54A", y=1180, size=150, sfx="soft")
    bg("ponting_bat", *seg(s("p2", -0.05), s("p3", -0.05)), credit="PHOTO: GETTY IMAGES", side="left", push=(1.0, 1.1))
    sbox(0, 12662, *seg(s("p2"), s("p3", -0.05)), sub="RUNS AT NO. 3", y=1100, roll=s("p2", 0.1))
    sbox(330, 330, *seg(word("p2", 3), s("p3", -0.05)), sub="INNINGS", y=1360)
    # ---------------- head to head
    vs_scene(*seg(s("p3", -0.05), s("r1", -0.05)), [
        (1, 0, "330", s("p3")), (0, 0, "251", word("p3", 6)),
        (1, 1, "42.48", word("p4", 2)), (0, 1, "61+", word("p5", 3)),
        (1, 2, "29", word("p6", 2)), (0, 2, "48", word("p7", 2))])
    # ---------------- nobody close / birthday
    stage(*seg(s("r1", -0.05), s("r2", -0.05)), tone="#060a1a")
    sticker("kohli_point_wc", *seg(s("r1", -0.05), s("r2", -0.05)), side="right", h=620, x=560, bottom=0)
    ranks(*seg(s("r1", -0.05), s("r2", -0.05)))
    bg("kohli_cap_glasses", *seg(s("r2", -0.05), s("q1", -0.05)), grade="blue", side="up", push=(1.0, 1.08))
    notebox("ALL OF THIS", "A DAY BEFORE HIS 38TH BIRTHDAY", *seg(word("r2", 2), s("q1", -0.05)), t2=word("r2", 6), y=1260)
    # ---------------- CTA
    video3d("logo", s("q1", -0.05), TOTAL - s("q1", -0.05))
    comment_cta(s("q1", 0.05), TOTAL - s("q1", 0.05))
    for a, b in LAYOUT["brand_hide"]:
        if a >= s("q1", -0.3):
            continue
        anim(f'tl.fromTo("#brand",{{opacity:.85}},{{opacity:0,duration:0.2,immediateRender:false}},{a})')
        if b < s("q1", -0.3):
            anim(f'tl.fromTo("#brand",{{opacity:0}},{{opacity:.85,duration:0.25,immediateRender:false}},{b})')
    anim(f'tl.fromTo("#brand",{{opacity:.85}},{{opacity:0,duration:0.2,immediateRender:false}},{s("q1", -0.3)})')


EXTRA_CSS = f"""
.tfade{{position:absolute;left:0;right:0;top:960px;height:320px;background:linear-gradient(180deg,rgba(5,7,13,0),#05070d)}}
.ngrade{{position:absolute;inset:0;background-image:linear-gradient(180deg,rgba(0,0,0,.55) 0%,rgba(0,0,0,.05) 30%,rgba(0,0,0,.35) 55%,rgba(0,0,0,.92) 100%)}}
.credit{{position:absolute;left:0;right:0;top:1560px;text-align:center;font:600 20px "IDisp";letter-spacing:.16em;color:rgba(255,255,255,.55)}}
.credit2{{text-align:center;font:600 18px "IDisp";letter-spacing:.16em;color:rgba(255,255,255,.55);margin-top:12px}}
.ntag{{position:absolute;left:70px;top:330px;color:#fff;font:800 24px "IDisp";letter-spacing:.1em;padding:9px 18px;border-radius:999px}}
.nbig{{position:absolute;left:30px;right:30px;text-align:center;font-family:"IDisp";font-weight:900;font-style:italic;letter-spacing:-.03em;line-height:.92;text-transform:uppercase;text-shadow:0 0 50px rgba(0,0,0,.6),0 8px 30px rgba(0,0,0,.6)}}
.nsub{{font:700 38px "IDisp";font-style:normal;letter-spacing:.3em;color:#fff;margin-top:22px;text-shadow:none}}
.sbox{{position:absolute;left:80px;right:80px;text-align:center;background:rgba(8,12,26,.84);border:2px solid rgba(255,255,255,.16);border-radius:28px;padding:30px 20px 34px;box-shadow:0 30px 80px rgba(0,0,0,.6)}}
.sbox b{{display:block;font-family:"IDisp";font-weight:900;font-style:italic;font-size:170px;line-height:1;color:#FFD54A;text-shadow:0 4px 0 #C99A10,0 0 40px rgba(255,213,74,.35)}}
.sbox span{{display:block;font:800 40px "IDisp";letter-spacing:.14em;color:#fff;margin-top:10px}}
.sbox span.gsub{{font-style:italic;font-size:84px;letter-spacing:-.01em;color:#FFD54A;font-weight:900}}
.spill{{position:absolute;left:50%;top:-30px;transform:translateX(-50%);background:{Y};color:#111;font:900 26px "IDisp";font-style:italic;letter-spacing:.06em;padding:8px 22px;border-radius:999px;white-space:nowrap}}
.vh{{position:absolute;left:0;right:0;height:960px;overflow:hidden}}
.vh img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}
.vsh{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.2),rgba(0,0,0,.75))}}
.vstack{{position:absolute;left:60px;right:60px}}
.vpill{{display:table;margin:0 auto -18px;position:relative;z-index:2;background:{Y};color:#111;font:900 24px "IDisp";letter-spacing:.06em;padding:8px 20px;border-radius:999px}}
.vbox{{display:flex;background:rgba(8,12,26,.86);border:2px solid rgba(255,255,255,.16);border-radius:24px;padding:34px 30px 22px}}
.vc{{flex:0 0 30%;text-align:left}}.vc:nth-child(2){{flex-basis:40%}}
.vc i{{display:block;font:700 22px "IDisp";font-style:normal;letter-spacing:.14em;color:#aab}}
.vc b{{display:block;font-family:"IDisp";font-weight:900;font-style:italic;font-size:90px;line-height:1.05;color:#FFD54A;text-shadow:0 3px 0 #C99A10}}
.vsb{{position:absolute;left:50%;top:960px;width:120px;height:120px;margin:-60px 0 0 -60px;border-radius:50%;background:#0a1030;border:4px solid {Y};color:{Y};font:900 48px "IDisp";font-style:italic;display:flex;align-items:center;justify-content:center;z-index:5}}
.ranks{{position:absolute;left:70px;right:70px;top:420px}}
.rh{{font-family:"IDisp";font-weight:900;font-style:italic;font-size:68px;color:#FFD54A;line-height:1;margin-bottom:40px}}
.rr{{margin-bottom:34px}}
.rl{{display:flex;justify-content:space-between;font:800 30px "IDisp";letter-spacing:.06em;color:#dfe3ea;margin-bottom:10px}}
.rr.rtop .rl{{color:{Y}}}
.rt{{height:20px;background:rgba(255,255,255,.08);border-radius:6px}}
.rf{{height:100%;background:linear-gradient(90deg,#3a5bd9,#7c95ff);border-radius:6px;transform-origin:0 50%}}
.rr.rtop .rf{{background:linear-gradient(90deg,#e0a800,{Y})}}
.rfoot{{margin-top:60px;font-family:"IDisp";font-weight:900;font-style:italic;font-size:78px;color:#FFD54A;text-align:center}}

@font-face{{font-family:"Bebas";src:url({media("assets/fonts/BebasNeue.woff2")})}}
@font-face{{font-family:"Osw";font-weight:700;src:url({media("assets/fonts/Oswald-700.woff2")})}}
.glow{{position:absolute;left:-200px;right:-200px;top:180px;height:1400px;pointer-events:none}}
.hlw{{position:absolute;left:70px;right:70px;font-family:"Bebas";line-height:.92;letter-spacing:.01em;text-shadow:0 6px 30px rgba(0,0,0,.6)}}
.hln{{display:block}}
.needs{{position:absolute;left:70px;font-family:"Bebas";font-size:84px;color:{Y};border:5px solid {Y};border-radius:10px;padding:2px 22px 0;background:rgba(0,0,0,.55);transform-origin:0 50%}}
.ctr{{position:absolute;left:70px;right:70px;top:1500px;font-family:"Osw"}}
.ctop{{display:flex;justify-content:space-between;align-items:flex-end;color:#cfd3da;font-size:30px;letter-spacing:.14em}}
.ctop b{{font-family:"Bebas";font-size:120px;line-height:.8;color:{Y};letter-spacing:0;font-weight:400}}
.cbar{{position:relative;height:22px;margin-top:14px;background:rgba(255,255,255,.12);border-radius:6px}}
.cfill{{position:absolute;left:0;top:0;bottom:0;background:linear-gradient(90deg,#2f6bff,#4f8bff);border-radius:6px;box-shadow:0 0 24px rgba(79,139,255,.6)}}
.cmark{{position:absolute;top:-14px;bottom:-14px;width:4px;background:#fff}}
.cmark i{{position:absolute;right:10px;top:46px;font-style:normal;font-size:22px;color:#fff;letter-spacing:.1em;white-space:nowrap}}
.chl{{position:absolute;font-family:"Bebas";font-size:84px;color:{Y}}}
.dgrid{{position:absolute;left:110px;top:620px;width:860px;display:grid;grid-template-columns:repeat(10,1fr);gap:22px}}
.dgrid i{{display:block;width:62px;height:62px;border-radius:50%;background:rgba(255,255,255,.18)}}
.yrow{{position:absolute;left:60px;right:60px;top:720px;display:flex;justify-content:space-between}}
.yc{{display:flex;flex-direction:column;align-items:center;gap:10px}}
.yc b{{font-family:"Bebas";font-size:96px;color:#fff;font-weight:400}}
.yc span{{font-family:"Osw";font-size:28px;color:{Y};letter-spacing:.08em}}
.yc:last-child b{{color:#ff3b3b}}
.vbars{{position:absolute;left:70px;right:70px;top:660px}}
.vbh{{font-family:"Osw";font-size:30px;letter-spacing:.16em;color:#cfd3da;margin-bottom:30px}}
.vbr{{display:flex;align-items:center;gap:24px;margin-bottom:56px}}
.vbn{{width:230px;font-family:"Bebas";font-size:84px;color:#fff;line-height:.9}}
.vbn span{{display:block;font-family:"Osw";font-size:24px;color:#9aa0a6;letter-spacing:.06em}}
.vbt{{flex:1;height:64px;background:rgba(255,255,255,.08);border-radius:8px;overflow:hidden}}
.vbf{{height:100%;border-radius:8px;transform-origin:0 50%}}
.vbv{{width:150px;text-align:right;font-family:"Bebas";font-size:100px}}

.pcard{{position:absolute;border-radius:34px;overflow:hidden;box-shadow:0 40px 90px rgba(0,0,0,.65),0 0 0 2px rgba(255,255,255,.08)}}
.pcard img{{width:100%;height:100%;object-fit:cover;display:block}}
.rainl{{position:absolute;left:0;right:0;top:-600px;bottom:-600px;background-image:linear-gradient(100deg,transparent 48%,rgba(220,230,255,.55) 49%,transparent 51%);background-size:90px 200px;transform:rotate(8deg)}}
.odo .digits{{position:relative;transform-origin:50% 60%}}
.odo.gold{{font-style:italic}}
.odo.gold .dstrip span,.odo.gold .digits>span:not(.dcol):not(.oshine){{color:#FFE14D;
  text-shadow:0 2px 0 #F2C21E,0 4px 0 #DDA90F,0 6px 0 #C29008,0 8px 0 #A67A05,0 22px 34px rgba(0,0,0,.55),0 0 46px rgba(254,222,92,.45)}}
.oshine{{position:absolute;top:-10%;bottom:-10%;left:0;width:22%;background:linear-gradient(90deg,rgba(255,255,255,0),rgba(255,255,255,.75),rgba(255,255,255,0));
  transform:skewX(-20deg) translateX(-160%);mix-blend-mode:overlay;pointer-events:none}}
.olabw{{margin-top:14px}}
.odo .olab{{display:inline-flex;align-items:center;gap:14px;padding:10px 22px 10px 16px;border-radius:999px;background:rgba(10,10,12,.55);
  backdrop-filter:blur(12px);box-shadow:inset 0 0 0 2.5px rgba(254,222,92,.75);font-size:42px;font-weight:800;font-style:normal;letter-spacing:.22em;color:#fff}}
.odo .olab i{{width:14px;height:14px;border-radius:50%;background:{Y};box-shadow:0 0 14px {Y}}}
.lbtop .lbv,.bcol:first-child .bnum{{font-style:italic;color:#FFE14D;
  text-shadow:0 2px 0 #F2C21E,0 4px 0 #DDA90F,0 6px 0 #B98806,0 0 30px rgba(254,222,92,.55)}}

.lboard{{position:absolute;left:50px;right:50px}}
.slowt{{position:absolute;left:-200px;right:-200px;top:1150px;text-align:center;font-size:96px;font-weight:900;font-style:italic;color:{Y};
  white-space:nowrap;text-shadow:0 6px 30px rgba(0,0,0,.7)}}
.dnum{{position:absolute;left:0;right:0;top:260px;text-align:center}}
.dnum div{{font-size:560px;font-weight:900;font-style:italic;letter-spacing:-0.06em;line-height:.9;color:#FFE14D;
  text-shadow:0 4px 0 #F2C21E,0 8px 0 #DDA90F,0 12px 0 #B98806,0 40px 60px rgba(0,0,0,.5),0 0 60px rgba(254,222,92,.5)}}
.dnum span{{display:inline-block;margin-top:10px;font-size:44px;font-weight:900;letter-spacing:.3em;color:#fff;text-shadow:0 6px 20px rgba(0,0,0,.6)}}
.band{{position:absolute;left:0;right:60px;display:flex;align-items:baseline;gap:26px;padding:22px 50px 26px 70px;background:{Y};
  border-radius:0 26px 26px 0;box-shadow:0 30px 60px rgba(0,0,0,.5)}}
.band b{{font-size:150px;font-weight:900;font-style:italic;color:#0b0b0c;letter-spacing:-0.05em;line-height:.9;display:inline-block}}
.band span{{font-size:38px;font-weight:900;color:#0b0b0c;letter-spacing:.12em}}
.cap1{{position:absolute;left:0;right:0;text-align:center;z-index:900}}
.cap1 span{{display:inline-block;font-size:78px;font-weight:900;color:#fff;letter-spacing:-0.01em;
  text-shadow:0 4px 0 rgba(0,0,0,.35),0 10px 30px rgba(0,0,0,.75)}}
.cap1.num span{{color:#FFE14D;text-shadow:0 3px 0 #C29008,0 10px 30px rgba(0,0,0,.75)}}
.badge{{position:absolute;left:46px;top:236px;width:118px;height:118px;border-radius:50%;background:{Y};color:#0b0b0c;display:flex;
  align-items:center;justify-content:center;font-size:76px;font-weight:900;box-shadow:0 10px 30px rgba(0,0,0,.5),0 0 0 6px rgba(254,222,92,.25)}}
.hero{{position:absolute;inset:0}}
.hero .circ{{position:absolute;left:50%;top:640px;width:820px;height:820px;margin-left:-410px;border-radius:50%;background:{Y};
  box-shadow:0 0 120px rgba(254,222,92,.45)}}
.hero .big{{position:absolute;left:0;right:0;top:250px;text-align:center;font-size:170px;font-weight:900;color:#fff;letter-spacing:-0.045em;line-height:.9;
  text-shadow:0 6px 0 #c8c8c8,0 12px 0 #8d8d8d,0 30px 50px rgba(0,0,0,.6)}}
.pip{{position:absolute;width:290px;border-radius:22px;overflow:hidden;box-shadow:0 30px 70px rgba(0,0,0,.65),0 0 0 4px #fff}}
.pip img{{width:100%;height:370px;object-fit:cover;object-position:50% 25%;display:block}}
.pip b{{position:absolute;left:0;right:0;bottom:0;padding:10px 14px;background:linear-gradient(0deg,rgba(0,0,0,.85),transparent);color:#fff;font-size:26px;font-weight:800}}
.slist{{position:absolute;left:70px;right:70px}}
.slr{{position:relative;font-size:84px;font-weight:900;color:#fff;letter-spacing:-0.02em;line-height:1.25;white-space:nowrap}}
.sll{{position:absolute;left:-10px;right:-10px;top:52%;height:9px;border-radius:5px;background:{Y};transform-origin:left;box-shadow:0 0 18px {Y}}}
.lbr{{display:flex;align-items:center;gap:22px;height:150px;margin-bottom:18px;padding:0 26px;border-radius:24px;
  background:rgba(255,255,255,.06);box-shadow:inset 0 0 0 1.5px rgba(255,255,255,.1)}}
.lbr.lbtop{{background:rgba(254,222,92,.12);box-shadow:inset 0 0 0 2.5px {Y}}}
.lbk{{width:70px;font-size:76px;font-weight:900;color:rgba(255,255,255,.35);letter-spacing:-0.04em}}
.lbtop .lbk{{color:{Y}}}
.lbm{{flex:1}}
.lbn{{font-size:36px;font-weight:900;color:#fff;letter-spacing:.02em;margin-bottom:12px}}
.lbbar{{height:16px;border-radius:8px;background:rgba(255,255,255,.08);overflow:hidden;width:560px}}
.lbf{{height:100%;border-radius:8px;background:linear-gradient(90deg,#9a9aa2,#d8d8de);transform-origin:left}}
.lbtop .lbf{{background:linear-gradient(90deg,#d9b93c,{Y});box-shadow:0 0 20px {Y}}}
.lbv{{width:200px;text-align:right;font-size:70px;font-weight:900;color:#fff;letter-spacing:-0.03em}}
.lbtop .lbv{{color:{Y}}}
.mot{{position:absolute;left:0;right:0;top:330px;text-align:center;font-size:120px;font-weight:900;color:#fff;letter-spacing:-0.03em;line-height:1}}
.mot span,.mot i{{display:block}}
.mot i{{font-size:54px;font-style:italic;font-weight:700;color:rgba(255,255,255,.6);margin:10px 0}}
.lgnum{{position:absolute;right:50px;top:330px;font-size:300px;font-weight:900;color:rgba(254,222,92,.08);letter-spacing:-0.05em;line-height:1}}
.nwall{{position:absolute;left:60px;right:60px;display:grid;grid-template-columns:1fr 1fr;gap:18px;perspective:1200px}}
.nwc{{height:150px;border-radius:22px;background:rgba(255,255,255,.06);box-shadow:inset 0 0 0 1.5px rgba(255,255,255,.12);
  display:flex;align-items:center;justify-content:center}}
.nwc span{{font-size:46px;font-weight:900;color:#fff;letter-spacing:.02em}}
.nwc:last-child{{grid-column:span 2;background:rgba(254,222,92,.14);box-shadow:inset 0 0 0 2px {Y}}}
.nwc:last-child span{{color:{Y}}}
.quote{{position:absolute;left:70px;right:70px;top:640px;text-align:left}}
.qm{{font-size:340px;line-height:.7;font-weight:900;color:{Y};height:200px;transform-origin:left top}}
.qt{{font-size:108px;font-weight:800;font-style:italic;color:#fff;letter-spacing:-0.03em;line-height:1.02}}
.qt .ch{{display:inline-block}}
.qt .wd{{white-space:nowrap}}
.qw{{margin-top:34px;font-size:40px;font-weight:600;color:rgba(255,255,255,.6)}}
.receipt{{position:absolute;right:50px;top:232px;display:flex;align-items:baseline;gap:8px;padding:12px 20px;border-radius:14px;
  background:rgba(10,10,12,.6);backdrop-filter:blur(14px);box-shadow:inset 0 0 0 1.5px rgba(254,222,92,.5);overflow:hidden}}
.receipt .rl{{font-size:22px;font-weight:800;letter-spacing:.2em;color:rgba(255,255,255,.7);margin-right:6px}}
.receipt .rn{{display:inline-block;font-size:44px;font-weight:900;color:{Y}}}
.receipt .rt{{font-size:28px;font-weight:800;color:rgba(255,255,255,.6)}}
.half{{position:absolute;left:0;width:1080px;height:960px;overflow:hidden}}
.half img{{width:100%;height:100%;object-fit:cover;object-position:50% 30%}}
.hl{{position:absolute;left:60px;bottom:50px;font-size:150px;font-weight:900;color:#fff;letter-spacing:-0.04em;text-shadow:0 10px 50px rgba(0,0,0,.6)}}
.hdiv{{position:absolute;left:0;right:0;top:955px;height:10px;background:{Y};box-shadow:0 0 30px {Y};transform-origin:left}}
.recap .rrow{{font-size:64px;margin-bottom:16px;gap:20px}}
.recap .tick{{width:64px;height:64px;font-size:42px}}
"""


FONTS = {400: "Regular", 600: "SemiBold", 700: "Bold", 800: "ExtraBold", 900: "Black"}
FONT_CSS = "".join(f'@font-face{{font-family:"IDisp";font-weight:{w};font-style:{st};src:url(media/InterDisplay-{n}{"Italic" if st == "italic" else ""}.otf)}}'
                   for w, n in FONTS.items() for st in ("normal", "italic"))

CSS = FONT_CSS + EXTRA_CSS + f"""
html,body{{margin:0;background:#000}}
#root{{position:relative;width:{W}px;height:{H}px;overflow:hidden;background:#0b0b0c;font-family:"IDisp","Inter Display",system-ui,sans-serif}}
#cam{{position:absolute;inset:-30px;transform-origin:50% 50%}}
#world{{position:absolute;inset:30px}}
.gridbg{{position:absolute;inset:-120px;background-image:linear-gradient(rgba(255,255,255,.045) 2px,transparent 2px),linear-gradient(90deg,rgba(255,255,255,.045) 2px,transparent 2px);
  background-size:120px 120px}}
.clip{{}}
.grain{{position:absolute;inset:-60px;background:url(media/assets_grain.png);opacity:.09;mix-blend-mode:overlay}}
#grainTop{{position:absolute;inset:-60px;background:url(media/assets_grain.png);opacity:.05;z-index:880;pointer-events:none;mix-blend-mode:overlay}}
.shade{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.62) 0%,rgba(0,0,0,.15) 34%,rgba(0,0,0,0) 55%,rgba(0,0,0,.35) 100%);pointer-events:none}}
.vig{{position:absolute;inset:0;background:radial-gradient(120% 80% at 50% 45%,rgba(0,0,0,0) 55%,rgba(0,0,0,.55) 100%);pointer-events:none}}
.title{{font-weight:900;letter-spacing:-0.035em;line-height:.98;color:#fff;text-shadow:0 8px 40px rgba(0,0,0,.55)}}
.title .mask{{overflow:hidden;padding:0 .04em .06em}}
.title .ln{{display:block}}
.typed{{font-weight:800;letter-spacing:-0.01em;line-height:1.1}}
.thead{{font-size:34px;font-weight:600;font-style:italic;color:rgba(255,255,255,.8);margin-bottom:16px}}
.tline{{white-space:nowrap;text-shadow:0 4px 24px rgba(0,0,0,.6)}}
.odo{{position:absolute;font-weight:900;letter-spacing:-0.05em;line-height:1;text-shadow:0 10px 50px rgba(0,0,0,.5)}}
.digits{{display:inline-flex}}
.dcol{{display:inline-block;height:1em;line-height:1em;overflow:hidden}}
.dstrip{{display:flex;flex-direction:column}}
.dstrip span{{display:block;height:1em;line-height:1em}}
.olab{{font-size:40px;font-weight:800;letter-spacing:.18em;color:#fff;margin-top:6px}}
.tag{{position:absolute;padding:14px 26px;border-radius:14px;background:{Y};color:#0b0b0c;font-size:44px;font-weight:900;letter-spacing:.02em;transform-origin:left;white-space:nowrap}}
.tag.dark{{background:#fff}}
.chip{{position:absolute;display:flex;align-items:center;gap:14px;padding:16px 28px;border-radius:999px;background:rgba(20,20,22,.6);
  backdrop-filter:blur(18px);box-shadow:inset 0 0 0 1.5px rgba(255,255,255,.18);color:#fff;font-size:36px;font-weight:700;white-space:nowrap}}
.chip .dot{{width:14px;height:14px;border-radius:50%;background:{Y};box-shadow:0 0 14px {Y}}}
.face{{position:absolute;pointer-events:none}}
.cap{{position:absolute;left:0;right:0;top:1420px;text-align:center;z-index:900}}
.cap span{{display:inline-block;padding:10px 22px;border-radius:12px;background:#fff;color:#0b0b0c;font-size:58px;font-weight:900;letter-spacing:-0.01em;
  box-shadow:0 10px 30px rgba(0,0,0,.45)}}
.cap.num span{{background:{Y}}}
.win{{width:1000px;border-radius:22px;overflow:hidden;background:#111;box-shadow:0 60px 140px rgba(0,0,0,.8),0 0 0 1.5px rgba(255,255,255,.12)}}
.win .bar{{height:50px;display:flex;align-items:center;gap:10px;padding:0 20px;background:#1c1c20;color:#8d8d94;font-size:20px;font-weight:600}}
.win .bar i{{width:14px;height:14px;border-radius:50%;background:#ff5f57}}
.win .bar i:nth-child(2){{background:#febc2e}}.win .bar i:nth-child(3){{background:#28c840}}
.win .bar span{{margin-left:16px}}
.bcol{{position:absolute;width:300px;display:flex;flex-direction:column;justify-content:flex-end;align-items:center}}
.bnum{{font-size:120px;font-weight:900;color:#fff;letter-spacing:-0.04em;margin-bottom:18px}}
.bbody{{position:relative;width:240px;border-radius:6px 6px 0 0;box-shadow:30px 0 0 rgba(0,0,0,.25)}}
.btop{{position:absolute;left:0;right:0;top:-18px;height:18px;transform:skewX(-45deg);transform-origin:bottom}}
.blab{{margin-top:22px;font-size:42px;font-weight:900;letter-spacing:.12em;color:#fff}}
.stamp{{position:absolute;left:0;right:0;text-align:center;font-weight:900;letter-spacing:-0.05em;line-height:1;text-shadow:0 20px 80px rgba(0,0,0,.6)}}
.leak{{position:absolute;inset:-200px;background:radial-gradient(40% 55% at 50% 50%,rgba(255,170,40,.95),rgba(254,222,92,.5) 45%,rgba(0,0,0,0) 75%);mix-blend-mode:screen;pointer-events:none}}
.gimg{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}
.slice{{position:absolute;left:-200px;right:-200px;background:rgba(254,222,92,.18);mix-blend-mode:difference;border-top:2px solid rgba(255,40,60,.7)}}
.ylab{{position:absolute;top:640px;font-size:110px;font-weight:900;color:#fff;letter-spacing:-0.03em}}
.yline{{position:absolute;left:90px;right:90px;top:820px;height:10px;border-radius:5px;background:rgba(255,255,255,.15);overflow:hidden}}
.yfill{{position:absolute;inset:0;background:{Y};transform-origin:left;box-shadow:0 0 24px {Y}}}
.ybig{{position:absolute;left:0;right:0;top:930px;text-align:center;font-size:150px;font-weight:900;color:{Y};letter-spacing:-0.04em}}
.recap{{position:absolute;left:70px;top:330px}}
.rrow{{display:flex;align-items:center;gap:22px;font-size:84px;font-weight:900;color:#fff;letter-spacing:-0.03em;margin-bottom:26px;white-space:nowrap}}
.rnum{{color:{Y};width:90px}}
.tick{{display:inline-flex;align-items:center;justify-content:center;width:84px;height:84px;border-radius:50%;background:{Y};color:#0b0b0c;font-size:56px}}
.cta{{position:absolute;inset:0}}
.bubble{{position:absolute;left:110px;right:110px;top:1080px;display:flex;gap:22px;align-items:center;padding:28px 32px;border-radius:30px;
  background:rgba(30,30,34,.85);box-shadow:inset 0 0 0 1.5px rgba(255,255,255,.12),0 30px 80px rgba(0,0,0,.6)}}
.av{{width:84px;height:84px;border-radius:50%;background:linear-gradient(135deg,{Y},#f39c12);flex:none}}
.who{{font-size:30px;font-weight:700;color:rgba(255,255,255,.6)}}
.what{{font-size:46px;font-weight:800;color:#fff;min-height:56px}}
.cta2{{position:absolute;left:0;right:0;top:1290px;text-align:center;font-size:40px;font-weight:700;color:rgba(255,255,255,.75)}}
.brand{{position:absolute;left:0;right:0;top:230px;text-align:center;z-index:950;opacity:.85}}
.brand img{{width:230px}}
"""

SVG_FILTERS = """<svg width="0" height="0" style="position:absolute"><filter id="red"><feColorMatrix type="matrix"
values="1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0"/></filter><filter id="cyan"><feColorMatrix type="matrix"
values="0 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 1 0"/></filter></svg>"""


def build():
    edit()
    captions()
    gsap = os.path.join(HERE, "..", "doc_video", "node_modules", "gsap", "dist", "gsap.min.js")
    shutil.copy(gsap, os.path.join(OUT, "gsap.min.js"))
    media("assets/grain.png")
    for w, n in FONTS.items():
        for it in ("", "Italic"):
            f = f"InterDisplay-{n}{it}.otf".replace("RegularItalic", "Italic")
            shutil.copy(f"/usr/share/fonts/opentype/inter/{f}", os.path.join(MEDIA, f"InterDisplay-{n}{it}.otf"))
    shutil.copy(os.path.join(HERE, "..", "kohli_countdown", "assets", "logo.png"), os.path.join(MEDIA, "logo.png"))
    # grain crawl: jumps every frame (steps), like film
    # the camera never stops: a slow breathing zoom and drift over the whole reel
    anim(f'tl.fromTo("#cam",{{scale:1.025,rotation:-0.35,x:-6}},{{scale:1.055,rotation:0.35,x:6,duration:3.2,ease:"sine.inOut",repeat:{int(TOTAL / 3.2) + 1},yoyo:true}},0)')
    anim(f'tl.fromTo("#grainTop",{{x:0,y:0}},{{x:-48,y:-36,duration:{TOTAL},ease:"steps({int(TOTAL * 12)})"}},0)')
    page = f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
{SVG_FILTERS}
<div id="root" data-composition-id="root" data-width="{W}" data-height="{H}" data-fps="{FPS}" data-duration="{TOTAL}">
<div id="cam"><div id="world">
{chr(10).join(els)}
</div></div>
<div id="grainTop"></div>
<div class="brand" id="brand"><img src="media/logo.png"></div>
</div>
<script src="gsap.min.js"></script>
<script>
const tl = gsap.timeline({{paused:true}});
{(";" + chr(10)).join(js)};
tl.set({{}},{{}},{TOTAL});
window.__timelines = window.__timelines || {{}};
window.__timelines["root"] = tl;
</script></body></html>"""
    with open(os.path.join(OUT, "index.html"), "w") as f:
        f.write(page)
    json.dump({"total": TOTAL, "events": sorted(events)}, open(os.path.join(HERE, "out", "events.json"), "w"))
    print(f"reel {TOTAL:.1f}s, {len(els)} layers, {len(events)} sfx cues")


if __name__ == "__main__":
    build()

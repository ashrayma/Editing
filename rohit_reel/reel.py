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


FOCUS = {"mccullum_drive": 0.58}  # manual crop focus (x) for wide photos; otherwise the crop centres on the detected face


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

NO_CAPTION = {"n1", "r4"}  # the 3D #1 card carries it


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


def then_now(start, dur, a_photo, b_photo):
    """Split screen: THEN (grey, 2007) on top, NOW (colour) underneath; the divider wipes across."""
    i = nid("tn")
    sa, sb = media(f"assets/hi/{a_photo}.png"), media(f"assets/hi/{b_photo}.png")
    add(f'<div id="{i}" {clip_attrs(start, dur)} class="layer full" style="position:absolute;inset:0;z-index:{z()};background:#000">'
        f'<div class="half" id="{i}a" style="top:0"><img src="{sa}" style="filter:grayscale(1) contrast(1.1)"><div class="hl">THEN</div></div>'
        f'<div class="half" id="{i}b" style="top:960px"><img src="{sb}"><div class="hl" style="color:{Y}">NOW</div></div>'
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
    anim(f'tl.fromTo("#{k}t",{{scale:1.6,opacity:0}},{{scale:1,opacity:1,duration:0.35,ease:"power4.in"}},{start + 0.25})')
    anim(f'tl.fromTo("#{k}t",{{y:0}},{{y:-20,duration:{dur},ease:"none"}},{start + 0.6})')
    shake(start + 0.6, 18)
    cue(start + 0.6, "impact", 1.0)
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
        f'<div class="mot" id="{i}q"><span>MUSCLE</span><i>or</i><span style="color:{Y}">TIMING?</span></div>'
        f'<div class="bubble" id="{i}b"><div class="av"></div><div><div class="who">you</div>'
        f'<div class="what" id="{i}w"></div></div></div><div class="cta2">Drop one word below 👇</div></div>')
    anim(f'tl.fromTo("#{i}q span,#{i}q i",{{y:40,opacity:0}},{{y:0,opacity:1,duration:0.5,stagger:0.12,ease:"back.out(1.8)"}},{start})')
    anim(f'tl.fromTo("#{i}b",{{y:60,opacity:0,scale:.9}},{{y:0,opacity:1,scale:1,duration:0.6,ease:"back.out(1.6)"}},{start + 0.6})')
    txt = "Timing 🎯"
    anim(f'(()=>{{const o={{n:0}};const s="{txt}";tl.to(o,{{n:[...s].length,duration:0.7,ease:"none",onUpdate:()=>{{document.getElementById("{i}w").textContent=[...s].slice(0,Math.round(o.n)).join("")}}}},{start + 1.1})}})()')
    cue(start, "pop", 1.0)


def edit():
    # ---------------- HOOK: a star mid-six on frame one, the claim, then the promise
    photo("rohit_t20_six", 0, word("i1", 9) + 0.02, side=None, push=(1.18, 1.05), origin="50% 30%")
    flash(0.02, peak=0.5)
    title(["NOT FROM", "THIS PLANET"], word("i1", 4) - 0.05, word("i1", 9) - word("i1", 4) + 0.05, y=300, size=124, accent=(1,), sfx="impact")
    photo("rohit_pull_mcg", word("i1", 9), span("i1", "i2") - word("i1", 9) + s("i1"), side="right", push=(1.02, 1.1))
    chip("Stay till the end", word("i1", 9) + 0.1, span("i1", "i2") - (word("i1", 9) + 0.1 - s("i1")), y=300)
    tag("ROHIT SHARMA", s("i1", 0.2), word("i1", 9) - s("i1", 0.2), y=1300)
    stage(s("i2", -0.05), span("i2", "n5") + 0.05)
    title(["THE BIGGEST", "SIX-HITTERS EVER"], s("i2", 0.05), span("i2", "n5") - 0.05, y=250, size=84, accent=(1,))
    leaderboard(s("i2", 0.3), span("i2", "n5") - 0.3, reveal=False, y=520)

    # ---------------- #5 GUPTILL
    rank_card("num5", "Martin Guptill", "n5", "g5", 5)
    badge(5, word("n5", 5), span("n5", "n4") - (word("n5", 5) - s("n5")))
    photo("guptill_wc2015", word("n5", 5), span("n5", "g5") - (word("n5", 5) - s("n5")), side="left", push=(1.0, 1.1))
    tag("MARTIN GUPTILL", word("n5", 5) + 0.05, span("n5", "g5") - (word("n5", 5) + 0.05 - s("n5")), y=1300)
    photo("guptill_t20", s("g5", -0.05), word("g5", 8) - s("g5", -0.05), side="right", push=(1.0, 1.12))
    chip("New Zealand", s("g5", 0.1), word("g5", 8) - s("g5", 0.1), y=300)
    stat_screen("guptill_t20", "383", ["SIXES", "tall, strong,", "enormous reach"], word("g5", 8), span("g5", "n4") - (word("g5", 8) - s("g5")))
    flash(word("g5", 8), peak=0.4)

    # ---------------- #4 McCULLUM
    rank_card("num4", "Brendon McCullum", "n4", "g4a", 6)
    badge(4, word("n4", 6), span("n4", "n3") - (word("n4", 6) - s("n4")))
    photo("mccullum_drive", word("n4", 6), span("n4", "g4a") - (word("n4", 6) - s("n4")), side="right", push=(1.0, 1.1))
    tag("BRENDON McCULLUM", word("n4", 6) + 0.05, span("n4", "g4a") - (word("n4", 6) + 0.05 - s("n4")), y=1300)
    photo("mccullum_six", s("g4a", -0.05), span("g4a", "g4b") + 0.05, side="left", push=(1.0, 1.12))
    title(["PURE", "AGGRESSION"], word("g4a", 3), span("g4a", "g4b") - (word("g4a", 3) - s("g4a")), y=1150, size=100, accent=(1,), sfx="impact")
    depth_number("mccullum_six", "398", "SIXES", s("g4b", -0.05), span("g4b", "n3") + 0.05)

    # ---------------- #3 AFRIDI
    video3d("num3", s("n3", -0.1), span("n3", "a3a") + 0.1)
    cue(s("n3", -0.6), "riser", 0.7)
    cue(s("n3"), "boom", 0.9)
    title(["THE BIG LEAGUES"], word("n3", 4), span("n3", "a3a") - (word("n3", 4) - s("n3")), y=1215, size=90, accent=(0,))
    photo("afridi_six", s("a3a", -0.05), span("a3a", "n2") + 0.05, side="up", push=(1.0, 1.14))
    badge(3, s("a3a"), span("a3a", "n2"))
    tag("SHAHID AFRIDI", s("a3a", 0.05), span("a3a", "a3b") - 0.05 + 0.2, y=1300)
    stamp("BOOM BOOM", word("a3b", 5), span("a3b", "a3c") - (word("a3b", 5) - s("a3b")), y=300, size=150, rot=-5)
    glitch(word("a3c", 4), 0.3, "afridi_six")
    band("476", "SIXES · PURE MUSCLE", word("a3c", 6), span("a3c", "n2") - (word("a3c", 6) - s("a3c")))

    # ---------------- #2 GAYLE
    rank_card("num2", "Chris Gayle", "n2", "c2a", 8)
    photo("gayle_six", word("n2", 8), span("n2", "c2a") - (word("n2", 8) - s("n2")), side="right", push=(1.0, 1.1))
    badge(2, word("n2", 8), span("n2", "n1") - (word("n2", 8) - s("n2")))
    tag("CHRIS GAYLE", word("n2", 8) + 0.05, span("n2", "c2a") - (word("n2", 8) + 0.05 - s("n2")), y=1300)
    chip("The Universe Boss", word("n2", 5), span("n2", "c2a") - (word("n2", 5) - s("n2")), y=300)
    stage(s("c2a", -0.05), span("c2a", "c2b") + 0.05)
    sticker("gayle_six", s("c2a", -0.05), span("c2a", "c2b") + 0.05, side="right", h=1250, x=430)
    odo("553", s("c2a", 0.05), span("c2a", "c2b") - 0.05, x=70, y=330, size=300)
    typed(["6'2\"", "built like a", "heavyweight"], s("c2a", 0.3), span("c2a", "c2b") - 0.3, y=700, size=58)
    duo("gayle_six", s("c2b", -0.05), span("c2b", "n1") + 0.05)
    title(["NEVER", "BE BROKEN?"], word("c2b", 6), span("c2b", "n1") - (word("c2b", 6) - s("c2b")), y=300, size=130, accent=(1,), sfx="impact")
    glitch(e("c2b", 0.1), 0.35, "gayle_six")

    # ---------------- #1 ... the reveal
    video3d("num1", s("n1", -0.1), span("n1", "r1") + 0.1)
    cue(s("n1", -1.0), "riser", 1.0)
    cue(s("n1"), "boom", 1.0)
    # your photo of Rohit eating dal chawal goes here when it arrives (assets/photos/rohit_dal_chawal.jpg)
    if os.path.exists(os.path.join(HERE, "assets", "hi", "rohit_dal_chawal.png")):
        photo("rohit_dal_chawal", s("r1", -0.05), span("r1", "r2") + 0.05, side="right", push=(1.0, 1.1))
        stamp("DAL CHAWAL", word("r1", 5) - 0.1, span("r1", "r2") - (word("r1", 5) - 0.1 - s("r1")), y=1150, size=130, rot=-4)
    else:
        stage(s("r1", -0.05), span("r1", "r2") + 0.05, tone="#0d0d0f")
        stamp("DAL CHAWAL", word("r1", 5) - 0.1, span("r1", "r2") - (word("r1", 5) - 0.1 - s("r1")), y=760, size=150, rot=-4)
        title(["LOVES HIS…"], s("r1", 0.05), word("r1", 5) - s("r1", 0.05) + 1.0, y=520, size=100)
    stage(s("r2", -0.05), span("r2", "r4") + 0.05)
    sticker("rohit_raise_bat", s("r2", -0.05), span("r2", "r3") + 0.05, side="right", h=1250, x=360)
    title(["NEVER IN", "A HURRY"], s("r2", 0.05), span("r2", "r3") - 0.05, y=300, size=110, accent=(1,))
    photo("rohit_t20wc_trophy", s("r3", -0.05), span("r3", "r4") + 0.05, side="left", push=(1.0, 1.08))
    title(["JUST A", "REGULAR GUY"], word("r3", 6), span("r3", "r4") - (word("r3", 6) - s("r3")), y=300, size=110, accent=(1,))
    hero("rohit_pull_mcg", ["ROHIT", "SHARMA"], s("r4", -0.05), span("r4", "r5") + 0.05)
    badge(1, s("r4", -0.05), span("r4", "s1") + 0.05)
    flash(s("r4"), peak=0.6)
    cue(s("r4"), "boom", 1.0)
    stage(s("r5", -0.05), span("r5", "r6") + 0.05)
    versus(s("r5", -0.05), span("r5", "r6") + 0.05, (650, "650+"), (553, "553"), "ROHIT", "GAYLE", y=330)
    stage(s("r6", -0.05), span("r6", "s1") + 0.05, tone="#0e0e10")
    screen("screen_sixes", s("r6", -0.05), span("r6", "s1") + 0.05, side="left", focus="85% 30%", zoom=1.3)
    title(["MOST SIXES", "PER INNINGS TOO"], s("r6", 0.1), span("r6", "s1") - 0.1, y=280, size=84, accent=(1,))

    # ---------------- WHY: muscle vs timing
    leak(s("s1", -0.3), 0.9)
    stage(s("s1", -0.05), span("s1", "s2") + 0.05)
    title(["HERE'S WHAT", "MAKES IT", "SPECIAL"], s("s1", 0.05), span("s1", "s2") - 0.05, y=640, size=120, accent=(2,))
    flicker(["afridi_six", "gayle_six", "mccullum_six", "guptill_t20", "afridi_six", "gayle_six"], s("s2", -0.02), span("s2", "s3") + 0.02)
    stamp("MUSCLE.", word("s2", 8) - 0.1, span("s2", "s3") - (word("s2", 8) - 0.1 - s("s2")), y=360, size=200, color="#fff", rot=-4)
    photo("dravid_drive", s("s3", -0.05), word("s4", 6) - s("s3", -0.05), side="left", push=(1.0, 1.08))
    title(["TIMING:", "THE GENTLE ART"], word("s3", 2), word("s4", 4) - word("s3", 2), y=1150, size=88, accent=(1,))
    tag("RAHUL DRAVID", word("s4", 3), word("s4", 6) - word("s4", 3), y=1300)
    photo("williamson_drive", word("s4", 6), span("s4", "s5") - (word("s4", 6) - s("s4")), side="right", push=(1.0, 1.1))
    tag("KANE WILLIAMSON", word("s4", 6) + 0.05, span("s4", "s5") - (word("s4", 6) + 0.05 - s("s4")), y=1300)
    chip("Along the ground, for four", word("s4", 12), span("s4", "s5") - (word("s4", 12) - s("s4")), y=300)
    photo("rohit_mi_pull", s("s5", -0.05), word("s5", 6) - s("s5", -0.05), side="up", push=(1.0, 1.1))
    title(["SAME SOFT TIMING…"], s("s5", 0.1), word("s5", 6) - s("s5", 0.1), y=1150, size=92, accent=(0,))
    pips([("dravid_drive", "Rahul Dravid"), ("williamson_drive", "Kane Williamson")], s("s5", 0.1), word("s5", 6) - s("s5", 0.1))
    video3d("six", word("s5", 6), span("s5", "s6") - (word("s5", 6) - s("s5")))
    cue(word("s5", 6), "whoosh_big", 1.0)
    title(["…AIMED AT", "THE SKY"], word("s5", 7), span("s5", "s6") - (word("s5", 7) - s("s5")), y=1150, size=110, accent=(1,), sfx="impact")
    photo("rohit_pull_mcg", s("s6", -0.05), span("s6", "e1") + 0.05, side=None, push=(1.25, 1.1), origin="60% 25%")
    title(["A SIX-HITTING", "WEAPON"], word("s6", 9), span("s6", "e1") - (word("s6", 9) - s("s6")), y=300, size=110, accent=(1,), sfx="impact")

    # ---------------- THE PROOF: the full list, now with #1 revealed
    stage(s("e1", -0.05), span("e1", "e2") + 0.05)
    title(["THE GIANTS…"], s("e1", 0.05), span("e1", "e2") - 0.05, y=300, size=120)
    strike_list(s("e1", 0.1), span("e1", "e2") - 0.1, ["CHRIS GAYLE", "SHAHID AFRIDI", "BRENDON McCULLUM", "MARTIN GUPTILL"], y=560)
    for k, (cutn, x) in enumerate((("guptill_t20", -80), ("mccullum_six", 170), ("afridi_six", 420), ("gayle_six", 640))):
        sticker(cutn, s("e1", 0.15 + 0.08 * k), span("e1", "e2") - 0.15 - 0.08 * k, side="right" if k % 2 else "left", h=640, x=x, grey=True)
    stage(s("e2", -0.05), span("e2", "e3") + 0.05)
    title(["BEAT EVERY", "ONE OF THEM"], s("e2", 0.05), span("e2", "e3") - 0.05, y=250, size=84, accent=(1,))
    leaderboard(s("e2", 0.15), span("e2", "e3") - 0.15, reveal=True, y=520)
    video3d("planet", s("e3", -0.05), span("e3", "q1") + 0.05)
    cue(s("e3"), "boom", 0.8)
    title(["NOT FROM", "THIS PLANET"], word("e3", 4), span("e3", "q1") - (word("e3", 4) - s("e3")), y=300, size=124, accent=(1,), sfx="impact")
    photo("rohit_ct_kiss", e("e3", -0.6), span("e3", "q1") - (e("e3", -0.6) - s("e3")), side="up", push=(1.0, 1.06))

    # ---------------- CTA
    video3d("logo", s("q1", -0.05), TOTAL - s("q1", -0.05))
    comment_cta(s("q1", 0.05), TOTAL - s("q1", 0.05))
    for a, b in LAYOUT["brand_hide"] + [[s("q1", -0.3), TOTAL + 1]]:
        anim(f'tl.fromTo("#brand",{{opacity:.85}},{{opacity:0,duration:0.2,immediateRender:false}},{a})')
        if b < TOTAL:
            anim(f'tl.fromTo("#brand",{{opacity:0}},{{opacity:.85,duration:0.25,immediateRender:false}},{b})')


EXTRA_CSS = f"""
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
.hero .big{{position:absolute;left:0;right:0;top:1130px;text-align:center;font-size:170px;font-weight:900;color:#fff;letter-spacing:-0.045em;line-height:.9;
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

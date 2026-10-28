#!/usr/bin/env python3
""""I didn't grow out of it" — MS Dhoni, greatest of all time. 9:16 reel, HyperFrames composition.

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
        f'<div class="grain"></div><div class="vig"></div></div>')
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
        anim(f'tl.fromTo("#{i}",{{{fr}}},{{xPercent:0,yPercent:0,duration:0.5,ease:"expo.out"}},{start})')
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
    lab = f'<div class="olab">{html.escape(label)}</div>' if label else ""
    y, x = mv(i, y, x)
    pos = f"left:{x}px" if x is not None else "left:0;right:0;text-align:center"
    add(f'<div id="{i}" {clip_attrs(start, dur)} class="odo avoid" style="{pos};top:{y}px;font-size:{size}px;color:{color};z-index:{z()}">'
        f'<div class="digits">{"".join(cols)}</div>{lab}</div>')
    anim(f'tl.fromTo("#{i}",{{scale:0.8,opacity:0}},{{scale:1,opacity:1,duration:0.5,ease:"back.out(1.6)"}},{start})')
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

NO_CAPTION = {"l2", "l3", "l4", "l5", "l6", "l7", "h4", "t1"}  # the name cards / quote / twist spell these out


def captions():
    """Lower-third captions, 1-3 words at a time: white box, black heavy caps; numbers get a yellow box."""
    for ln in TL["lines"]:
        if ln["id"] in NO_CAPTION:
            continue
        words = ln["words"]
        groups, cur = [], []
        for w in words:
            cur.append(w)
            short = len(w[0]) <= 3
            if len(cur) >= 3 or (len(cur) == 2 and not short) or w[0][-1] in ".,?!…:":
                groups.append(cur)
                cur = []
        if cur:
            groups.append(cur)
        for g, grp in enumerate(groups):
            t0 = grp[0][1]
            t1 = groups[g + 1][0][1] if g + 1 < len(groups) else ln["end"] + 0.12
            txt = " ".join(w[0] for w in grp).upper()
            num = any(any(c.isdigit() for c in w[0]) for w in grp)
            i = nid("cap")
            cy, _ = mv(i, 1420)
            add(f'<div id="{i}" {clip_attrs(t0, t1 - t0)} class="cap avoid{" num" if num else ""}" style="top:{cy}px"><span>{html.escape(txt)}</span></div>')
            anim(f'tl.fromTo("#{i} span",{{scale:0.82,y:14}},{{scale:1,y:0,duration:0.22,ease:"back.out(2.2)"}},{t0})')


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


LEGENDS = [("l2", "Jacques", "Kallis", "South Africa", "kallis"), ("l3", "Shane", "Warne", "Australia", "warne"),
           ("l4", "Muttiah", "Muralitharan", "Sri Lanka", "murali"), ("l5", "Rahul", "Dravid", "India", "dravid"),
           ("l6", "Brian", "Lara", "West Indies", "lara"), ("l7", "Dale", "Steyn", "South Africa", "steyn")]


def edit():
    # ---------------- HOOK
    photo("csk_back_7", 0, span("h1", "h2"), side=None, push=(1.16, 1.04), origin="50% 30%")
    title(["ONE HOT TAKE"], word("h1", 4), span("h1", "h2") - (word("h1", 4) - s("h1")), y=300, size=120, accent=(0,), sfx="impact")
    chip("Growing up", s("h1", 0.2), word("h1", 4) - s("h1", 0.2) + 0.3, y=300)
    photo("india_helmet_smile", s("h2", -0.05), span("h2", "h3") + 0.05, side="right", push=(1.0, 1.04), origin="50% 15%")
    tag("MS DHONI", s("h2", 0.1), span("h2", "h3") - 0.1, y=1330)
    title(["GREATEST", "OF ALL TIME"], word("h2", 4), span("h2", "h3") - (word("h2", 4) - s("h2")), y=1100, size=92, accent=(1,), sfx="impact")
    flash(word("h2", 4), peak=0.4)
    stage(s("h3", -0.05), span("h3", "l1") + 0.05, tone="#0c0c0e")
    title(["EVERY ADULT", "TOLD ME…"], s("h3", 0.05), span("h3", "h4") - 0.05, y=330, size=100, accent=(1,))
    quote_card(s("h4", -0.1), span("h4", "l1") + 0.1, "You'll grow out of it.", "every adult, ever")

    # ---------------- THE LEGENDS
    leak(s("l1", -0.3), 0.9)
    stage(s("l1", -0.05), span("l1", "l2") + 0.05)
    chip("Back then", s("l1", 0.05), span("l1", "l2") - 0.05, y=300)
    title(["LOOK WHO", "ELSE WAS", "PLAYING"], s("l1", 0.15), span("l1", "l2") - 0.15, y=600, size=130, accent=(2,))
    for k, (lid, first, last, country, ph) in enumerate(LEGENDS):
        nxt = LEGENDS[k + 1][0] if k + 1 < len(LEGENDS) else "l8"
        legend(first, last, s(lid, -0.05), span(lid, nxt) + 0.05, country, k, ph)
    legend("Ricky", "Ponting", s("l8", -0.05), word("l8", 3) - s("l8", -0.05), "Australia", 6, "ponting")
    stage(word("l8", 3), span("l8", "l9") - (word("l8", 3) - s("l8")))
    odo("2", word("l8", 3), span("l8", "l9") - (word("l8", 3) - s("l8")), y=420, size=420, label="WORLD CUPS AS CAPTAIN")
    chip("2003 · 2007", word("l8", 4), span("l8", "l9") - (word("l8", 4) - s("l8")), x=None, y=1000)
    stage(s("l9", -0.05), span("l9", "b1") + 0.05, tone="#0d0d0f")
    name_wall(s("l9", -0.05), span("l9", "b1") + 0.05, [l[2] for l in LEGENDS] + ["Ponting"], y=330)
    title(["ANY ALL-TIME XI"], s("l10", 0.1), span("l10", "b1") - 0.1, y=1080, size=96, accent=(0,), sfx="impact")
    glitch(e("l10", 0.1), 0.3)

    # ---------------- THE BUILD
    stage(s("b1", -0.05), span("b1", "b2") + 0.05)
    years(s("b1"), span("b1", "b2"), 2007, 2026, "SO I GREW UP")
    stage(s("b2", -0.05), span("b2", "b3") + 0.05, tone="#0e0e10")
    title(["I WENT THROUGH", "EVERY RECORD"], s("b2", 0.05), span("b2", "b3") - 0.05, y=300, size=92, accent=(1,))
    records_fan(word("b2", 6), span("b2", "b3") - (word("b2", 6) - s("b2")),
                ["capture/out/shot_stumpings.png", "capture/out/shot_notouts.png", "capture/out/shot_icc.png"])
    stage(s("b3", -0.05), span("b3", "b4") + 0.05)
    title(["I TRIED TO", "CHANGE MY MIND"], s("b3", 0.05), span("b3", "b4") - 0.05, y=700, size=104, accent=(1,))
    glitch(word("b3", 5), 0.35)
    photo("csk_helmet_lookup", s("b4", -0.05), span("b4", "t1") + 0.05, side=None, push=(1.02, 1.2), fx="dim")
    title(["AND NOW…"], s("b4", 0.05), span("b4", "t1") - 0.05, y=300, size=110)
    cue(e("b4", -0.6), "riser", 1.0)
    # the pause: a beat of black
    stage(e("b4", 0.05), s("t1") - e("b4", 0.05) + 0.02, tone="#000")

    # ---------------- THE TWIST
    video3d("seven", s("t1", -0.05), span("t1", "p1") + 0.05)
    cue(s("t1"), "boom", 1.0)
    flash(s("t1"), peak=0.5)
    title(["I DIDN'T", "GROW OUT OF IT."], s("t1", 0.15), span("t1", "p1") - 0.15, y=300, size=92, accent=(1,), sfx="impact")
    leak(e("t1", 0.3), 0.9)

    # ---------------- THE PROOF
    photo("t20wc2007_champagne", s("p1", -0.05), span("p1", "p2") + 0.05, side="left", push=(1.0, 1.1))
    receipt(1, s("p1"), span("p1", "p2"))
    title(["FIRST TOURNAMENT", "AS CAPTAIN"], s("p1", 0.05), word("p1", 4) - s("p1", 0.05), y=300, size=88, accent=(1,))
    chip("T20 World Cup · 2007", word("p1", 4), span("p1", "p2") - (word("p1", 4) - s("p1")), y=300)
    title(["CHAMPION."], word("p1", 6), span("p1", "p2") - (word("p1", 6) - s("p1")), y=380, size=130, accent=(0,), sfx="impact")
    photo("test_mace_smile", s("p2", -0.05), span("p2", "p3") + 0.05, side="right", push=(1.0, 1.08), origin="50% 30%")
    receipt(2, s("p2"), span("p2", "p3"))
    stamp("No.1", word("p2", 6), span("p2", "p3") - (word("p2", 6) - s("p2")), y=300, size=260)
    chip("Test rankings · Dec 2009", word("p2", 6) + 0.2, span("p2", "p3") - (word("p2", 6) + 0.2 - s("p2")), y=1080)
    photo("wc2011_six", s("p3", -0.05), word("p3", 4) - s("p3", -0.05), side="up", push=(1.0, 1.1))
    receipt(3, s("p3"), span("p3", "p4"))
    chip("World Cup final · Wankhede · 2011", s("p3", 0.1), word("p3", 4) - s("p3", 0.1), y=300)
    video3d("n91", word("p3", 4), word("p3", 8) - word("p3", 4))
    photo("wc2011_six", word("p3", 8), span("p3", "p4") - (word("p3", 8) - s("p3")), side=None, push=(1.15, 1.3), origin="60% 15%")
    flash(word("p3", 11), peak=0.7)
    cue(word("p3", 11), "crowd", 1.2)
    title(["…WITH A SIX."], word("p3", 9), span("p3", "p4") - (word("p3", 9) - s("p3")), y=300, size=118, accent=(0,), sfx="impact")
    photo("ct2013_blazer", s("p4", -0.05), span("p4", "p5") + 0.05, side="right", push=(1.0, 1.1))
    receipt(4, s("p4"), span("p4", "p5"))
    chip("Champions Trophy · 2013", s("p4", 0.15), span("p4", "p5") - 0.15, y=300)
    video3d("trophies", s("p5", -0.05), word("p5", 8) - s("p5", -0.05) + 0.3)
    receipt(5, s("p5"), span("p5", "p6"))
    title(["THE ONLY", "CAPTAIN EVER"], s("p5", 0.1), word("p5", 8) - s("p5", 0.1) + 0.3, y=300, size=110, accent=(1,), sfx="impact")
    stage(word("p5", 8) + 0.3, span("p5", "p6") - (word("p5", 8) + 0.3 - s("p5")), tone="#0e0e10")
    screen("screen_icc", word("p5", 8) + 0.3, span("p5", "p6") - (word("p5", 8) + 0.3 - s("p5")), side="left", focus="50% 45%", zoom=1.25)
    title(["ALL 3 ICC", "WHITE-BALL TROPHIES"], word("p5", 8) + 0.4, span("p5", "p6") - (word("p5", 8) + 0.4 - s("p5")), y=300, size=80, accent=(1,))
    photo("ipl_trophy_portrait", s("p6", -0.05), span("p6", "p7") + 0.05, side="left", push=(1.0, 1.1), origin="50% 30%")
    receipt(6, s("p6"), span("p6", "p7"))
    odo("5", s("p6", 0.05), span("p6", "p7") - 0.05, y=300, size=360, label="IPL TITLES AS CAPTAIN")
    flicker(["ipl_2021_trophy_walk", "ipl_trophy_portrait", "ipl_2021_trophy_walk"], e("p6", -0.25), 0.4)
    video3d("stumps", s("p7", -0.05), word("p7", 2) - s("p7", -0.05) + 0.25)
    receipt(7, s("p7"), span("p7", "p8"))
    photo("stumping_india", word("p7", 2) + 0.25, span("p7", "p8") - (word("p7", 2) + 0.25 - s("p7")), side="right", push=(1.0, 1.1))
    odo("195", word("p7", 2) + 0.3, span("p7", "p8") - (word("p7", 2) + 0.3 - s("p7")), y=300, size=300, label="STUMPINGS · MOST EVER")
    stage(s("p8", -0.05), span("p8", "p9") + 0.05)
    receipt(8, s("p8"), span("p9", "o1") + (s("p9") - s("p8")))
    sticker("csk_back_7", s("p8", -0.05), span("p8", "p9") + 0.05, side="right", h=1250, x=430)
    odo("84", s("p8", 0.05), span("p8", "p9") - 0.05, x=70, y=330, size=330)
    typed(["ODI", "NOT-OUTS", "most ever"], s("p8", 0.4), span("p8", "p9") - 0.4, y=700, size=58)
    photo("csk_six", s("p9", -0.05), word("p9", 6) - s("p9", -0.05), side="up", push=(1.0, 1.12))
    photo("stumping_csk", word("p9", 6), span("p9", "o1") - (word("p9", 6) - s("p9")), side=None, push=(1.1, 1.2))
    duo("csk_back_7", word("p9", 8) - 0.1, span("p9", "o1") - (word("p9", 8) - 0.1 - s("p9")))
    glitch(word("p9", 8) - 0.1, 0.35, "csk_back_7")
    stamp("OVER.", word("p9", 10) - 0.1, span("p9", "o1") - (word("p9", 10) - 0.1 - s("p9")), y=360, size=190, color="#fff", rot=-4)

    # ---------------- OUTRO
    leak(s("o1", -0.3), 0.9)
    stage(s("o1", -0.05), span("o1", "o2") + 0.05)
    sticker("wc2011_gateway", s("o1", -0.05), span("o1", "o2") + 0.05, side="right", h=1250, x=480)
    recap(s("o1", 0.05), span("o1", "o2") - 0.05,
          ["T20 World Cup", "No.1 in Tests", "World Cup 2011", "Champions Trophy", "5× IPL", "195 stumpings", "84 not-outs"])
    video3d("goat", s("o2", -0.05), span("o2", "o3") + 0.05)
    cue(s("o2"), "boom", 1.0)
    title(["MS DHONI"], s("o2", 0.1), span("o2", "o3") - 0.1, y=620, size=120, sfx="soft")
    then_now(s("o3", -0.05), span("o3", "o4") + 0.05, "t20wc2007_champagne", "csk_helmet_lookup")
    video3d("logo", s("o4", -0.05), TOTAL - s("o4", -0.05))
    comment_cta(s("o4", 0.1), TOTAL - s("o4", 0.1))
    # the logo steps aside whenever a face is under it (windows found by layout.py)
    for a, b in LAYOUT["brand_hide"] + [[s("o4", -0.3), TOTAL + 1]]:
        anim(f'tl.fromTo("#brand",{{opacity:.85}},{{opacity:0,duration:0.2,immediateRender:false}},{a})')
        if b < TOTAL:
            anim(f'tl.fromTo("#brand",{{opacity:0}},{{opacity:.85,duration:0.25,immediateRender:false}},{b})')


EXTRA_CSS = f"""
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
.receipt{{position:absolute;right:50px;top:300px;display:flex;align-items:baseline;gap:8px;padding:12px 20px;border-radius:14px;
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
#world{{position:absolute;inset:0}}
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
    anim(f'tl.fromTo("#grainTop",{{x:0,y:0}},{{x:-48,y:-36,duration:{TOTAL},ease:"steps({int(TOTAL * 12)})"}},0)')
    page = f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
{SVG_FILTERS}
<div id="root" data-composition-id="root" data-width="{W}" data-height="{H}" data-fps="{FPS}" data-duration="{TOTAL}">
<div id="world">
{chr(10).join(els)}
</div>
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

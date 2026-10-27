#!/usr/bin/env python3
""""3 Records Kohli Owns That Sachin Never Touched" — 9:16 reel, HyperFrames composition.

    python3 reel.py   ->  hf/index.html (+ hf/media/) and out/events.json (SFX cue list for soundtrack.py)

Everything is timed off out/timeline.json (build_vo.py), so a new voice take re-times the whole edit.
Look: charcoal + film grain, theCricketLounge yellow, Inter Display. Full-screen photos slide in from the left
or right over a blurred fill of themselves; cut-out "sticker" players carry the stat screens; Blender 3D shots
for the chapter numbers, the ball, 49 -> 50 and the logo; word-by-word captions in the lower third.
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
    add(f'<div id="{i}" {clip_attrs(start, dur)} style="position:absolute;inset:0;z-index:{z()};background:{tone}">'
        f'<div class="grain"></div><div class="vig"></div></div>')
    return i


FOCUS = {"sachin_100th_lookup": "50%", "kohli_trophy_kiss": "42%", "kohli_odi_helmet_bat": "50%",
         "sachin_helmet_close": "48%", "sachin_test_bat_helmet": "55%", "kohli_test_roar": "62%",
         "kohli_odi_celebrate_wide": "50%"}


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
    if tall or not band:
        pos = f"{FOCUS.get(name, '50%')} 30%" if not tall else "50% 30%"
        inner = (f'<img id="{i}m" src="{src}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;'
                 f'object-position:{pos};transform-origin:{origin};filter:{filt}">')
    else:
        top = round(H * 0.42 - ih / 2)
        inner = (f'<img src="{fill}" style="position:absolute;inset:-40px;width:calc(100% + 80px);height:calc(100% + 80px);object-fit:cover">'
                 f'<img id="{i}m" src="{src}" style="position:absolute;left:0;top:{top}px;width:100%;height:{ih}px;object-fit:cover;'
                 f'transform-origin:{origin};filter:{filt};box-shadow:0 40px 120px rgba(0,0,0,.75)">')
    add(f'<div id="{i}" {clip_attrs(start, dur)} style="position:absolute;inset:0;z-index:{z()};overflow:hidden;background:#000">'
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
    add(f'<div id="{i}" {clip_attrs(start, dur)} style="position:absolute;left:{left}px;bottom:{bottom}px;width:{w}px;height:{h}px;z-index:{z()}">'
        f'<img id="{i}m" src="{src}" style="width:100%;height:100%;filter:{filt} drop-shadow(0 30px 40px rgba(0,0,0,.6));'
        f'transform:{"scaleX(-1)" if flip else "none"}"></div>')
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
    add(f'<div id="{i}" {clip_attrs(start, dur)} style="position:absolute;inset:0;z-index:{z()};background:#030304">'
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
    add(f'<div id="{i}" {clip_attrs(start, dur)} style="position:absolute;left:70px;right:70px;top:{y}px;z-index:{z()};'
        f'font-size:{size}px;text-align:{align};font-style:{"italic" if italic else "normal"}" class="title">{rows}</div>')
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
    add(f'<div id="{i}" {clip_attrs(start, dur)} style="position:absolute;left:{x}px;top:{y}px;z-index:{z()}" class="typed">'
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
    pos = f"left:{x}px" if x is not None else "left:0;right:0;text-align:center"
    add(f'<div id="{i}" {clip_attrs(start, dur)} class="odo" style="{pos};top:{y}px;font-size:{size}px;color:{color};z-index:{z()}">'
        f'<div class="digits">{"".join(cols)}</div>{lab}</div>')
    anim(f'tl.fromTo("#{i}",{{scale:0.8,opacity:0}},{{scale:1,opacity:1,duration:0.5,ease:"back.out(1.6)"}},{start})')
    return i


def tag(txt, start, dur, x=70, y=1250, dark=False):
    """Name tag: yellow pill, the name types in."""
    i = nid("tg")
    chars = "".join(f'<span class="ch">{html.escape(c) if c != " " else "&nbsp;"}</span>' for c in txt)
    add(f'<div id="{i}" {clip_attrs(start, dur)} class="tag{" dark" if dark else ""}" style="left:{x}px;top:{y}px;z-index:{z()}">{chars}</div>')
    anim(f'tl.fromTo("#{i}",{{scaleX:0}},{{scaleX:1,duration:0.35,ease:"expo.out"}},{start})')
    anim(f'tl.fromTo("#{i} .ch",{{opacity:0}},{{opacity:1,duration:0.01,stagger:0.035}},{start + 0.2})')
    cue(start, "pop", 0.8)
    return i


def chip(txt, start, dur, x=70, y=300):
    """Small glass label (date / venue)."""
    i = nid("cp")
    add(f'<div id="{i}" {clip_attrs(start, dur)} class="chip" style="left:{x}px;top:{y}px;z-index:{z()}"><span class="dot"></span>{html.escape(txt)}</div>')
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
    add(f'<div id="{i}" {clip_attrs(start, dur)} class="stamp" style="top:{y}px;font-size:{size}px;color:{color};z-index:{z()}">{html.escape(txt)}</div>')
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

NO_CAPTION = {"n1a", "n1b", "n2a", "n2b", "n3a", "n3b"}  # the 3D chapter cards spell these out already


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
            add(f'<div id="{i}" {clip_attrs(t0, t1 - t0)} class="cap{" num" if num else ""}"><span>{html.escape(txt)}</span></div>')
            anim(f'tl.fromTo("#{i} span",{{scale:0.82,y:14}},{{scale:1,y:0,duration:0.22,ease:"back.out(2.2)"}},{t0})')


# ----------------------------------------------------------------------------- the edit

def edit():
    # ---------------- HOOK
    photo("sachin_test_celebrate", 0, span("h1", "h2"), side=None, push=(1.18, 1.05), origin="50% 25%")
    title(["THE GOD", "OF CRICKET"], s("h1", 0.15), span("h1", "h2") - 0.15, y=300, size=128, accent=(1,), sfx="impact")
    tag("SACHIN TENDULKAR", s("h1", 0.5), span("h1", "h2") - 0.5, y=1230)
    photo("sachin_100th_lookup", s("h2"), span("h2", "h3"), side="right", push=(1.0, 1.12))
    chip("100th international hundred · 2012", s("h2", 0.15), span("h2", "h3") - 0.15, y=1180)
    # the ball flies in on "But" -> three records
    video3d("ball", s("h3"), word("h3", 3) - s("h3"))
    cue(s("h3") - 0.05, "whoosh_big", 1.0)
    stage(word("h3", 3), e("h3") - word("h3", 3) + 0.3)
    odo("3", word("h3", 3), e("h3") - word("h3", 3) + 0.3, y=300, size=420, sfx=False)
    cue(word("h3", 3), "impact", 0.8)
    title(["RECORDS"], word("h3", 3) + 0.15, e("h3") - word("h3", 3) + 0.15, y=760, size=120)
    sticker("kohli_2023_hands", word("h3", 5) - 0.1, e("h3") - word("h3", 5) + 0.4, side="right", h=900)
    # split: Kohli in colour, Sachin in grey
    stage(s("h4", -0.2), span("h4", "n1a") + 0.2)
    sticker("kohli_odi_bat_raise", s("h4", -0.2), span("h4", "n1a") + 0.2, side="left", h=1150, x=-60)
    sticker("sachin_odi_walk", s("h4", -0.1), span("h4", "n1a") + 0.1, side="right", h=1150, x=560, grey=True)
    title(["NEVER", "TOUCHED"], word("h4", 3), span("h4", "n1a") - (word("h4", 3) - s("h4")), y=300, size=130, accent=(1,), sfx="impact")
    glitch(e("h4", 0.1), 0.3)

    # ---------------- 1. THE CHASE MASTER
    cue(s("n1a", -1.0), "riser", 1.0)
    video3d("num1", s("n1a", -0.1), span("n1a", "c1") + 0.1)
    cue(s("n1a"), "boom", 1.0)
    title(["The Chase", "Master"], s("n1b"), span("n1b", "c1"), y=1215, size=96, accent=(1,), sfx="soft")
    # chasing: Kohli in a different gear
    photo("kohli_odi_celebrate_wide", s("c1", -0.05), word("c1", 5) - s("c1", -0.05), side="left", push=(1.0, 1.1), band=True)
    chip("ODI run chases", s("c1", 0.1), word("c1", 5) - s("c1", 0.1), y=1110)
    duo("kohli_t20_lookup", word("c1", 5), e("c1") - word("c1", 5) + 0.25)
    glitch(word("c1", 5), 0.35, "kohli_t20_lookup")
    title(["DIFFERENT", "PLAYER"], word("c1", 6), e("c1") - word("c1", 6) + 0.25, y=320, size=130, sfx="soft")
    # 25 hundreds: stat screen
    stage(s("c2", -0.05), span("c2", "c3") + 0.05)
    sticker("kohli_odi_bat_raise", s("c2", -0.05), span("c2", "c3") + 0.05, side="right", h=1180, x=430)
    odo("25", s("c2", 0.05), span("c2", "c3") - 0.05, x=70, y=300, size=360)
    typed(["ODI HUNDREDS", "in successful", "chases"], s("c2", 0.4), span("c2", "c3") - 0.4, y=700, size=54)
    # the screen recording proves it
    stage(s("c3", -0.05), span("c3", "c4") + 0.05, tone="#0e0e10")
    screen("screen_chase", s("c3", -0.05), span("c3", "c4") + 0.05, side="left", focus="40% 55%", zoom=1.35)
    title(["#1 ALL-TIME"], s("c3", 0.1), span("c3", "c4") - 0.1, y=330, size=104, accent=(0,))
    # Sachin? 14.  -> 25 vs 14
    stage(s("c4", -0.05), span("c4", "c5") + 0.05)
    bars(25, 14, "KOHLI", "SACHIN", s("c4", -0.05), span("c4", "c5") + 0.05, y=380)
    # average 90+
    photo("kohli_odi_helmet_bat", s("c5", -0.05), span("c5", "c6") + 0.05, side="right", push=(1.02, 1.12))
    typed(["AVG 90+", "in won chases"], word("c5", 4), span("c5", "c6") - (word("c5", 4) - s("c5")), y=300, size=64)
    # NINETY.
    stage(s("c6", -0.05), span("c6", "c7") + 0.05, tone="#060606")
    stamp("90", s("c6", -0.05), span("c6", "c7") + 0.05, y=560, size=560, rot=-4)
    # not batting -> cheat code
    photo("kohli_test_roar", s("c7"), span("c7", "n2a"), side="up", push=(1.05, 1.15))
    title(["NOT BATTING"], s("c7", 0.05), word("c7", 3) - s("c7", 0.05), y=320, size=110)
    glitch(word("c7", 3) - 0.05, 0.5, "kohli_test_roar")
    title(["CHEAT", "CODE"], word("c7", 3), e("c7") - word("c7", 3) + 0.5, y=300, size=170, accent=(0, 1), sfx="impact")
    leak(e("c7", 0.2), 0.9)

    # ---------------- 2. THE CAPTAIN
    cue(s("n2a", -1.0), "riser", 1.0)
    video3d("num2", s("n2a", -0.1), span("n2a", "k1") + 0.1)
    cue(s("n2a"), "boom", 1.0)
    title(["The", "Captain"], s("n2b"), span("n2b", "k1"), y=1215, size=96, accent=(1,))
    photo("kohli_test_lookup", s("k1", -0.05), span("k1", "k3") + 0.05, side="left", push=(1.0, 1.1), origin="50% 30%")
    typed(["68 TESTS", "as captain"], s("k1", 0.4), span("k1", "k2") - 0.4, y=300, size=64)
    odo("40", s("k2"), span("k2", "k3"), x=70, y=440, size=300, label="WINS")
    stage(s("k3", -0.05), span("k3", "k4") + 0.05, tone="#0e0e10")
    screen("screen_capt", s("k3", -0.05), span("k3", "k4") + 0.05, side="right", focus="55% 40%", zoom=1.2, mstart=1.3)
    title(["MOST BY AN", "INDIAN CAPTAIN"], s("k3", 0.1), span("k3", "k4") - 0.1, y=300, size=84, accent=(1,))
    photo("kohli_trophy_kiss", s("k4", -0.05), span("k4", "k5") + 0.05, side="right", push=(1.0, 1.12))
    chip("Australia · 2018–19", s("k4", 0.2), span("k4", "k5") - 0.2, y=1110)
    title(["FIRST EVER", "SERIES WIN", "IN AUSTRALIA"], word("k4", 4), span("k4", "k5") - (word("k4", 4) - s("k4")), y=280, size=96, accent=(0,))
    flash(word("k4", 9) if len(LINE["k4"]["words"]) > 9 else e("k4"), peak=0.35)
    # Sachin as captain
    stage(s("k5", -0.05), span("k5", "k7") + 0.05)
    sticker("sachin_test_raise_bat", s("k5", -0.05), span("k5", "k7") + 0.05, side="right", h=1180, x=430, grey=True)
    typed(["25 TESTS", "as captain"], s("k5", 0.3), span("k5", "k6") - 0.3, y=300, size=64, color="#d9d9de")
    odo("4", s("k6"), span("k6", "k7"), x=70, y=560, size=330, color="#bdbdc4", label="WINS")
    # bars 40 vs 4 on "Different job? Sure."
    stage(s("k7", -0.05), span("k7", "k8") + 0.05)
    bars(40, 4, "KOHLI", "SACHIN", s("k7", -0.05), span("k7", "k8") + 0.05, y=380)
    # built a team -> flicker of Test Kohli
    photo("kohli_test_shush", s("k8", -0.05), word("k8", 5) - s("k8", -0.05), side="left", push=(1.0, 1.1))
    flicker(["kohli_test_roar", "kohli_trophy_kiss", "kohli_test_lookup", "kohli_test_shush", "kohli_test_roar",
             "kohli_trophy_kiss"], word("k8", 5), 0.8)
    photo("kohli_trophy_kiss", word("k8", 5) + 0.8, e("k8") - word("k8", 5) - 0.8 + 0.5, side=None, push=(1.1, 1.2))
    title(["WIN AWAY", "FROM HOME"], word("k8", 7), e("k8") - word("k8", 7) + 0.5, y=300, size=118, accent=(1,))
    leak(e("k8", 0.2), 0.9)

    # ---------------- 3. THE BIGGEST STAGE
    cue(s("n3a", -1.0), "riser", 1.0)
    video3d("num3", s("n3a", -0.1), span("n3a", "w1") + 0.1)
    cue(s("n3a"), "boom", 1.0)
    title(["The Biggest", "Stage"], s("n3b"), span("n3b", "w1"), y=1215, size=96, accent=(1,))
    photo("sachin_2003_trophy", s("w1", -0.05), span("w1", "w2") + 0.05, side="left", push=(1.0, 1.1), origin="40% 30%")
    chip("World Cup 2003", s("w1", 0.1), span("w1", "w2") - 0.1, y=300)
    odo("673", word("w1", 5) - 0.1, span("w1", "w2") - (word("w1", 5) - 0.1 - s("w1")), y=380, size=300, label="RUNS")
    # 20 years: a timeline 2003 -> 2023
    stage(s("w2", -0.05), span("w2", "w3") + 0.05)
    tl_line(s("w2"), span("w2", "w3"))
    photo("kohli_2023_hands", s("w3", -0.05), span("w3", "w4") + 0.05, side="right", push=(1.0, 1.1), origin="50% 25%")
    chip("World Cup 2023", s("w3", 0.1), span("w3", "w4") - 0.1, y=300)
    odo("765", word("w3", 4) - 0.1, span("w3", "w4") - (word("w3", 4) - 0.1 - s("w3")), y=380, size=300, label="RUNS")
    stage(s("w4", -0.05), span("w4", "w6") + 0.05, tone="#0e0e10")
    sw = screen("screen_wc", s("w4", -0.05), span("w4", "w6") + 0.05, side="left", focus="80% 30%", zoom=1.3, mstart=1.1)
    anim(f'tl.to("#{sw}",{{opacity:.3,filter:"blur(6px)",duration:0.3}},{s("w5", 0.05)})')
    flash(s("w5", 0.05), peak=0.5)
    chip("Semi-final · Wankhede · 15 Nov 2023", s("w4", 0.1), span("w4", "w6") - 0.1, y=300)
    screenshot("capture/out/shot_wc.png", s("w5", 0.05), span("w5", "w6") - 0.05, side="right", top=1180 - 420)
    # the 50th
    photo("kohli_odi_helmet_bat", s("w6", -0.05), span("w6", "w7") + 0.05, side="up", push=(1.12, 1.0))
    flash(word("w6", 3), peak=0.6)
    cue(word("w6", 3), "crowd", 1.0)
    video3d("fifty", s("w7", -0.1), span("w7", "w8") + 0.1)
    cue(s("w7"), "boom", 0.9)
    # 55 now
    stage(s("w8", -0.05), span("w8", "o1") + 0.05)
    sticker("kohli_t20_lookup", s("w8", -0.05), span("w8", "o1") + 0.05, side="right", h=1250, x=440)
    odo("55", word("w8", 2) - 0.1, span("w8", "o1") - (word("w8", 2) - 0.1 - s("w8")), x=70, y=360, size=360)
    typed(["ODI", "HUNDREDS", "& counting"], word("w8", 2) + 0.3, span("w8", "o1") - (word("w8", 2) + 0.3 - s("w8")), y=760, size=56)

    # ---------------- OUTRO
    stage(s("o1", -0.05), span("o1", "o2") + 0.05)
    sticker("kohli_odi_celebrate_wide", s("o1", -0.05), span("o1", "o2") + 0.05, side="left", h=820, x=-120, bottom=520)
    sticker("sachin_test_celebrate", s("o1", 0.05), span("o1", "o2") - 0.05, side="right", h=1300, x=520)
    title(["BETTER", "THAN SACHIN?"], s("o1", 0.1), word("o1", 6) - s("o1", 0.1), y=300, size=104, accent=(1,))
    stamp("NO.", word("o1", 6) - 0.15, e("o1") - word("o1", 6) + 0.5, y=330, size=330, color="#fff")
    photo("sachin_odi_bat_raise", s("o2", -0.05), span("o2", "o3") + 0.05, side="up", push=(1.0, 1.1), origin="50% 20%")
    odo("100", s("o2", 0.05), word("o2", 3) - s("o2", 0.05) + 0.2, y=300, size=300, label="INTERNATIONAL HUNDREDS")
    odo("24", word("o2", 3), e("o2") - word("o2", 3) + 0.25, y=300, size=300, label="YEARS")
    photo("sachin_young_cut", s("o3", -0.05), span("o3", "o4") + 0.05, side="right", push=(1.0, 1.12))
    title(["THE", "BENCHMARK"], word("o3", 3), span("o3", "o4") - (word("o3", 3) - s("o3")), y=300, size=128, accent=(1,), sfx="impact")
    # recap: the three, ticked off
    stage(s("o4", -0.05), span("o4", "o5") + 0.05)
    sticker("kohli_2023_hands", s("o4", -0.05), span("o4", "o5") + 0.05, side="right", h=950, x=380)
    recap(s("o4"), span("o4", "o5"))
    # CTA + logo
    video3d("logo", s("o5", -0.05), TOTAL - s("o5", -0.05))
    comment_cta(s("o5", 0.1), TOTAL - s("o5", 0.1))
    anim(f'tl.to(".brand",{{opacity:0,duration:0.3}},{s("o5", -0.3)})')


def tl_line(start, dur):
    """2003 ———— 2023: a line draws across, the year counts up, a '20 YEARS' label lands."""
    i = nid("yl")
    add(f'<div id="{i}" {clip_attrs(start, dur)} style="position:absolute;inset:0;z-index:{z()}">'
        f'<div class="ylab" style="left:90px">2003</div><div class="ylab" id="{i}y" style="right:90px;color:{Y}">2003</div>'
        f'<div class="yline"><div id="{i}f" class="yfill"></div></div>'
        f'<div class="ybig" id="{i}b">20 YEARS</div></div>')
    anim(f'tl.fromTo("#{i}f",{{scaleX:0}},{{scaleX:1,duration:{min(1.4, dur * 0.7)},ease:"power2.inOut"}},{start + 0.1})')
    anim(f'(()=>{{const o={{v:2003}};tl.to(o,{{v:2023,duration:{min(1.4, dur * 0.7)},ease:"power2.inOut",onUpdate:()=>{{document.getElementById("{i}y").textContent=Math.round(o.v)}}}},{start + 0.1})}})()')
    anim(f'tl.fromTo("#{i}b",{{scale:0.6,opacity:0}},{{scale:1,opacity:1,duration:0.5,ease:"back.out(1.8)"}},{start + min(1.4, dur * 0.7)})')
    cue(start + 0.1, "rise", 0.8)
    for k in range(10):
        cue(start + 0.1 + k * min(1.4, dur * 0.7) / 10, "tick", 0.5)


def recap(start, dur):
    """Three record titles drop in; each gets a yellow tick on the beat."""
    i = nid("rc")
    items = ["Chase Master", "The Captain", "Biggest Stage"]
    rows = "".join(f'<div class="rrow" id="{i}r{k}"><span class="rnum">{k + 1}.</span>{t}<span class="tick" id="{i}t{k}">✓</span></div>'
                   for k, t in enumerate(items))
    add(f'<div id="{i}" {clip_attrs(start, dur)} class="recap" style="z-index:{z()}">{rows}</div>')
    for k in range(3):
        t0 = start + 0.12 * k
        anim(f'tl.fromTo("#{i}r{k}",{{x:-80,opacity:0}},{{x:0,opacity:1,duration:0.5,ease:"expo.out"}},{t0})')
        t1 = start + min(dur - 0.4, 1.1 + 0.25 * k)
        anim(f'tl.fromTo("#{i}t{k}",{{scale:0,rotation:-30}},{{scale:1,rotation:0,duration:0.35,ease:"back.out(2.5)"}},{t1})')
        cue(t1, "pop", 1.0)


def comment_cta(start, dur):
    i = nid("cm")
    add(f'<div id="{i}" {clip_attrs(start, dur)} class="cta" style="z-index:{z()}">'
        f'<div class="bubble" id="{i}b"><div class="av"></div><div><div class="who">you</div>'
        f'<div class="what" id="{i}w"></div></div></div><div class="cta2">Which one surprised you most?</div></div>')
    anim(f'tl.fromTo("#{i}b",{{y:60,opacity:0,scale:.9}},{{y:0,opacity:1,scale:1,duration:0.6,ease:"back.out(1.6)"}},{start + 0.3})')
    txt = "Number 1, no doubt 🔥"
    anim(f'(()=>{{const o={{n:0}};const s="{txt}";tl.to(o,{{n:s.length,duration:1.2,ease:"none",onUpdate:()=>{{document.getElementById("{i}w").textContent=[...s].slice(0,Math.round(o.n)).join("")}}}},{start + 0.8})}})()')
    cue(start + 0.3, "pop", 1.0)


# ----------------------------------------------------------------------------- page

FONTS = {400: "Regular", 600: "SemiBold", 700: "Bold", 800: "ExtraBold", 900: "Black"}
FONT_CSS = "".join(f'@font-face{{font-family:"IDisp";font-weight:{w};font-style:{st};src:url(media/InterDisplay-{n}{"Italic" if st == "italic" else ""}.otf)}}'
                   for w, n in FONTS.items() for st in ("normal", "italic"))

CSS = FONT_CSS + f"""
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
<div class="brand"><img src="media/logo.png"></div>
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

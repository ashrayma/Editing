#!/usr/bin/env python3
"""Build the HyperFrames composition for "Centurion 2003: The 98" from the narration timeline.

    python3 gen.py            ->  hf_main/index.html (+ copies media into hf_main/media)
    cd hf_main && npx hyperframes render -o ../out/video_silent.mp4

Visual language (Apple-clean, theCricketLounge brand): charcoal stage, white type, #FEDE5C accent.
Media cards glide in from the left or right with a slight 3D turn and a slow push-in; headlines reveal
line by line behind a mask; numbers roll like an odometer; 3D hero shots play full frame.
"""
import html
import json
import os
import shutil

from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "hf_main")
MEDIA = os.path.join(OUT, "media")
W, H, FPS = 1920, 1080, 30
VO_OFFSET = 0.6          # narration starts this many seconds into the film
TAIL = 4.5               # logo end card after the last line
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
    if not os.path.exists(dst) or os.path.getmtime(srcp) > os.path.getmtime(dst):
        shutil.copy(srcp, dst)
    return "media/" + os.path.basename(src)


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

def card(src, start, dur, side="right", label=None, sub=None, video=False, maxw=1060, maxh=700, z=20, kb=True):
    """A media card that glides in from `side`, pushes in slowly, and exits the other way."""
    i = nid("card")
    if video:
        w, h = 716, 780
    else:
        w, h = img_size(src)
    cw, ch = fit(w, h, maxw, maxh)
    cx = W * (0.67 if side == "right" else 0.33) if side != "center" else W / 2
    EVENTS.append((start, "whoosh"))
    left, top = round(cx - cw / 2), round(H / 2 - ch / 2 + 10)
    rel = media(src)
    if video:
        inner = (f'<video id="{i}v" class="clip" src="{rel}" muted playsinline data-start="{start}" '
                 f'data-duration="{dur}" data-media-start="0" style="width:100%;height:100%;object-fit:cover"></video>')
    else:
        inner = f'<img id="{i}i" src="{rel}" style="width:100%;height:100%;object-fit:cover">'
    tag = ""
    if label:
        tag = (f'<div class="tag" id="{i}t"><span class="tagbar"></span><b>{html.escape(label)}</b>'
               + (f'<em>{html.escape(sub)}</em>' if sub else "") + "</div>")
    add(f'<div id="{i}" class="card clip" data-start="{start}" data-duration="{dur}" '
        f'style="left:{left}px;top:{top}px;width:{cw}px;height:{ch}px;z-index:{z}">'
        f'<div class="frame">{inner}</div>{tag}</div>', start, dur, z)
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


def phone(src, start, dur, side="right", z=25):
    """The scorecard screen recording inside a clean phone frame."""
    i = nid("ph")
    EVENTS.append((start, "whoosh"))
    cx = W * (0.7 if side == "right" else 0.3)
    pw, ph_ = 380, 822
    add(f'<div id="{i}" class="phone clip" data-start="{start}" data-duration="{dur}" '
        f'style="left:{round(cx - pw / 2)}px;top:{round(H / 2 - ph_ / 2)}px;width:{pw}px;height:{ph_}px;z-index:{z}">'
        f'<video class="clip" src="{media(src)}" muted playsinline data-start="{start}" data-duration="{dur}" '
        f'data-media-start="0"></video></div>', start, dur, z)
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


# ----------------------------------------------------------------------------- the film

P = "assets/photos/"
C = "footage/clips/"
R3 = "blender/renders/"

# CHAPTER 1 - THE FASTEST BALL (hook)
card(P + "shoaib_bowling.jpg", 0.3, 3.4, "right", "SHOAIB AKHTAR", "Cricket World Cup 2003")
backdrop(P + "shoaib_bowling.jpg", 0.0, 3.8)
headline(["161.3", "KM/H"], 0.5, 3.0, "left", size=150, accent_idx=0)
full_video(R3 + "speed.mp4", b("hook_fastest", 3.0), 3.6)
headline(["The fastest ball", "ever recorded."], b("hook_fastest", 6.4), 2.3, "center", size=92, accent_idx=1)
date_card(b("hook_first_ball", 0.2), 2.5)
card(C + "shoaib_run.mp4", b("hook_first_ball", 2.7), 3.6, "left", "THE FIRST BALL", "Shoaib to Sachin", video=True, maxh=740)
headline(["Shoaib", "vs", "Sachin"], b("hook_first_ball", 2.9), 3.4, "right", size=110, accent_idx=1)
card(C + "six_close.mp4", b("hook_six", 0.0), 3.6, "right", "OFF STUMP, WIDE", "Over third man", video=True, maxh=740)
odometer("6", b("hook_six", 0.6), 3.0, "left", size=320, label="OVER THIRD MAN")
card(C + "crowd_flags.mp4", b("hook_six", 3.6), 3.3, "center", video=True, maxw=1300, maxh=760, kb=True)
headline(["This isn't the story", "of one shot."], b("not_one_shot", 0.1), 4.0, "center", size=96, accent_idx=1)
odometer("12", b("not_one_shot", 4.4), 3.9, "center", size=260, label="NIGHTS WITHOUT SLEEP")
pills(["Cramps", "A runner", "<b>98</b> runs"], b("cramps_98", 0.3), 5.6, "left", gap=0.9)
card(P + "sachin_crouch_cramps.jpg", b("cramps_98", 0.3), 5.6, "right", "SACHIN TENDULKAR", "Centurion, 1 March 2003")
big98(b("cramps_98", 6.0), 3.0)
logo_sting(b("cramps_98", -1.2), 2.5)

# CHAPTER 2 - THE PRESSURE
chapter("01", "The Pressure", b("kargil", 0.4))
timeline_graphic([("1999", "World Cup during Kargil", b("kargil", 3.0)),
                  ("1999", "India beat Pakistan", b("parliament", 0.2)),
                  ("2001", "Parliament attack", b("parliament", 2.6)),
                  ("2002", "Troops face off at the border", b("parliament", 5.6))],
                 b("kargil", 0.6), BEAT["parliament"][1] - BEAT["kargil"][0] - 0.4)
headline(["No bilateral", "cricket."], b("no_cricket", 0.1), 3.6, "left", size=110, accent_idx=1)
headline(["World Cup 2003", "India vs Pakistan"], b("no_cricket", 3.8), BEAT["no_cricket"][1] - b("no_cricket", 3.8), "right",
         size=86, accent_idx=1, sub="Centurion, South Africa")
headline(["Not just", "a cricket match."], b("not_just_match", 0.0), 2.6, "center", size=110, accent_idx=1)
odometer("12", b("months_talk", 0.6), 6.2, "left", size=240, label="MONTHS OF BUILD-UP")
card(P + "collage_three_bowlers.jpg", b("months_talk", 0.4), 6.6, "right")
headline(["“Jeetna hi hai.”"], b("phone_calls", 0.2), 4.6, "center", size=120, sub="Phone calls to the team, every day")
odometer("13", b("phone_calls", 5.0), 5.4, "center", size=240, label="RESTLESS NIGHTS BEFORE THE MATCH")
card(P + "toss_handshake.jpg", b("toss_ties", 0.3), 6.0, "left", "SOURAV GANGULY × WAQAR YOUNIS", "Before the toss")
backdrop(P + "toss_handshake.jpg", b("toss_ties", 0.0), 6.4)
card(P + "handshake_hires.jpg", b("toss_ties", 6.2), BEAT["toss_ties"][1] - b("toss_ties", 6.2) + 0.2, "right", maxh=760)
headline(["A handshake.", "For a moment,", "it felt calm."], b("toss_ties", 6.4), BEAT["toss_ties"][1] - b("toss_ties", 6.4), "left",
         size=78, accent_idx=0)
card(C + "stadium.mp4", b("match_starts", 0.0), 5.2, "center", video=True, maxw=1300, maxh=760)
headline(["Match 36", "SuperSport Park"], b("match_starts", 0.6), 4.4, "left", size=90, accent_idx=1)

# Pakistan bat first
chapter("02", "The Target", b("saeed_anwar", 0.0))
card(P + "saeed_anwar.jpg", b("saeed_anwar", 0.2), 7.6, "right", "SAEED ANWAR", "Opener, Pakistan")
headline(["Saeed Anwar", "194 vs India", "in 1997"], b("saeed_anwar", 2.0), 5.6, "left", size=96, accent_idx=1)
odometer("101", b("saeed_101", 0.2), 4.4, "left", size=260, label="OFF 126 BALLS")
card(P + "harbhajan_celebrates.jpg", b("saeed_101", 0.1), 4.6, "right")
phone(C + "scorecard_phone.mp4", b("target_274", 0.0), 6.9, "right")
odometer("273/7", b("target_274", 0.3), 3.2, "left", size=200, label="PAKISTAN, 50 OVERS", color="#fff")
odometer("274", b("target_274", 3.6), 3.2, "left", size=240, label="TARGET")
pills(["Wasim Akram", "Waqar Younis", f"Shoaib Akhtar <b>161.3</b>"], b("bowling_attack", 0.6), 11.2, "left", gap=1.1)
card(P + "shoaib_bowling.jpg", b("bowling_attack", 0.2), 6.0, "right")
card(P + "collage_three_bowlers.jpg", b("bowling_attack", 6.2), 5.8, "right")
headline(["The plan?", "Just bat."], b("sachin_plan", 0.2), 7.0, "left", size=120, accent_idx=1)
card(P + "sachin_drive_keeper.jpg", b("sachin_plan", 0.1), 7.2, "right", "SACHIN TENDULKAR")

# CHAPTER 3 - THE ASSAULT
chapter("03", "The Assault", b("wasim_over", 0.0))
card(C + "wasim.mp4", b("wasim_over", 0.0), 6.6, "right", "OVER 1 · WASIM AKRAM", "Front-foot punch, four", video=True, maxh=760)
headline(["Ball 3.", "Four."], b("wasim_over", 2.6), 4.0, "left", size=130, accent_idx=1)
card(C + "shoaib_run.mp4", b("shoaib_runup", 0.0), 4.0, "left", "OVER 2 · SHOAIB AKHTAR", video=True, maxh=760)
card(P + "shoaib_bowling.jpg", b("shoaib_runup", 4.0), 4.2, "right")
headline(["The whole", "stadium held", "its breath."], b("shoaib_runup", 4.2), 4.0, "left", size=88, accent_idx=2)
card(C + "six_close.mp4", b("the_six", 0.6), 4.2, "right", video=True, maxh=760)
odometer("6", b("the_six", 4.6), 4.1, "center", size=420, label="OVER THIRD MAN")
card(C + "four_speed.mp4", b("two_fours", 0.0), 7.3, "right", "154.1 KPH", "And Sachin still found the gap", video=True, maxh=760)
pills(["Ball 1 · <b>SIX</b>", "Ball 2 · <b>FOUR</b> square leg", "Ball 3 · <b>FOUR</b> off side"], b("two_fours", 0.3), 6.9, "left", gap=1.6)
card(P + "bowling_card_sachin.jpg", b("three_balls", 0.0), 6.2, "right", maxh=760)
headline(["3 balls.", "3 boundaries."], b("three_balls", 0.2), 6.0, "left", size=110, accent_idx=1)
odometer("18", b("eighteen", 0.0), 3.6, "center", size=300, label="RUNS OFF THE OVER")
card(C + "crowd_celebrate.mp4", b("that_feeling", 0.0), 5.4, "center", video=True, maxw=1300, maxh=760)
odometer("53", b("sehwag_53", 0.8), 8.0, "left", size=260, label="IN 5.4 OVERS · RUN RATE 9+")
card(C + "crowd_flags.mp4", b("sehwag_53", 0.4), 8.4, "right", video=True, maxh=760)
card(C + "wicket_over.mp4", b("two_wickets", 0.0), 7.9, "right", "WAQAR YOUNIS", "Two wickets in two balls", video=True, maxh=760)
pills(["Sehwag · c Afridi b Waqar · <b>21</b>", "Ganguly · lbw b Waqar · <b>0</b>"], b("two_wickets", 2.4), 5.4, "left", gap=2.6)
odometer("53/2", b("53_for_2", 0.2), 4.2, "center", size=280, label="FROM 53/0 IN TWO BALLS", color="#fff")
card(C + "head_down.mp4", b("if_sachin_out", 0.0), 4.1, "right", video=True, maxh=760)
headline(["If Sachin goes,", "the match goes."], b("if_sachin_out", 0.2), 3.9, "left", size=90, accent_idx=1)

# CHAPTER 4 - THE 98
chapter("04", "The 98", b("kaif", 0.0))
card(C + "kaif_back.mp4", b("kaif", 0.2), 6.6, "right", "MOHAMMAD KAIF · 22", "Give Sachin the strike", video=True, maxh=760)
headline(["Job:", "rotate strike,", "don't get out."], b("kaif", 1.0), 5.8, "left", size=84, accent_idx=0)
card(P + "sachin_kaif_hug.jpg", b("partnership", 0.0), 5.5, "right", "TENDULKAR & KAIF")
odometer("102", b("partnership", 0.3), 5.2, "left", size=260, label="RUN PARTNERSHIP")
pills(["Kaif · <b>35</b> (60)", "India · <b>155/3</b>"], b("kaif_out", 0.3), 4.9, "left", gap=1.2)
card(C + "running.mp4", b("kaif_out", 0.0), 5.2, "right", video=True, maxh=760)
card(C + "drinks.mp4", b("cramps", 0.0), 7.3, "right", "CRAMPS", "Every run a struggle", video=True, maxh=760)
headline(["Cramps."], b("cramps", 1.0), 6.3, "left", size=150, accent_idx=0)
headline(["A runner", "for Sachin."], b("runner", 0.1), 4.0, "left", size=110, accent_idx=1, sub="Virender Sehwag")
card(P + "sachin_crouch_cramps.jpg", b("runner", 0.0), 4.1, "right")
card(P + "sachin_running_shoaib_face.jpg", b("nineties", 0.0), 9.7, "right", maxh=760)
odometer("98", b("nineties", 4.6), 5.1, "left", size=300, label="TWO SHOTS FROM A HUNDRED", roll=3.0)
card(P + "shoaib_bowling.jpg", b("bouncer", 0.0), 6.0, "left", "SHOAIB AKHTAR", "Back for more")
card(C + "shoaib_back.mp4", b("bouncer", 6.0), 4.0, "right", video=True, maxh=760)
headline(["Bouncer."], b("bouncer", 5.8), 4.0, "left", size=170, accent_idx=0)
pills(["Gloved to point", "c Younis Khan b Shoaib Akhtar"], b("bouncer", 10.4), BEAT["bouncer"][1] - b("bouncer", 10.4), "left", gap=1.6)
card(C + "sachin_late.mp4", b("bouncer", 10.2), BEAT["bouncer"][1] - b("bouncer", 10.2), "right", video=True, maxh=760)
big98(b("out_98", 0.0), 3.0)
pills(["<b>98</b> off 75 balls", "<b>12</b> fours · <b>1</b> six", "Two runs short."], b("out_98", 3.0), 4.3, "left", gap=0.9)
card(P + "collage_three_bowlers.jpg", b("out_98", 3.0), 4.3, "right")
odometer("97", b("97_needed", 0.4), 10.0, "left", size=260, label="NEEDED · 22 OVERS LEFT · 177/4")
card(P + "ganguly_waqar_after.jpg", b("97_needed", 0.2), 10.4, "right")

# CHAPTER 5 - THE FINISH
chapter("05", "The Finish", b("dravid_yuvraj", 0.0))
headline(["Rahul Dravid", "Yuvraj Singh, 21"], b("dravid_yuvraj", 0.0), 4.1, "center", size=100, accent_idx=1)
card(P + "dravid_yuvraj_win.jpg", b("finish", 0.0), 8.9, "right", "DRAVID & YUVRAJ", "Finished it off")
pills(["Yuvraj · <b>50*</b> (53)", "Dravid · <b>44*</b>"], b("finish", 1.0), 7.9, "left", gap=1.8)
card(C + "dressing_room.mp4", b("won", 0.0), 6.4, "right", video=True, maxh=760)
headline(["India won", "by 6 wickets."], b("won", 0.2), 6.2, "left", size=104, accent_idx=1, sub="276/4 in 45.4 overs")
phone(C + "scorecard_phone.mp4", b("aftermath", 0.2), 8.0, "right")
pills(["Pakistan · out in the group stage", "India · into the final",
       "Sachin · <b>673</b> runs · Player of the Tournament"], b("aftermath", 0.6), 7.6, "left", gap=1.6)
card(P + "india_team_walk.jpg", b("aftermath", 8.2), 9.0, "left")
headline(["The innings fans", "remember most?"], b("aftermath", 8.6), 8.6, "right", size=86, accent_idx=1)
big98(b("aftermath", 17.6), 3.0)
headline(["The 98", "at Centurion."], b("aftermath", 20.6), BEAT["aftermath"][1] - b("aftermath", 20.6), "center", size=130, accent_idx=0)
card(P + "handshake_hires.jpg", b("two_points", 0.0), 3.0, "center", maxh=760)
headline(["Belief."], b("belief", 0.3), 10.0, "left", size=170, accent_idx=0)
card(C + "crowd_celebrate.mp4", b("belief", 0.0), 10.3, "right", video=True, maxh=760)
headline(["Pride."], b("pride", 0.3), 6.6, "left", size=170, accent_idx=0)
card(P + "india_team_walk.jpg", b("pride", 0.0), 6.9, "right")
card(P + "ganguly_waqar_after.jpg", b("crores", 0.0), 7.2, "center", maxw=1240, maxh=740)
headline(["Some matches are won", "on the scoreboard."], b("hearts", 0.0), 3.4, "center", size=86, accent_idx=1)
headline(["Some, in the heart."], b("hearts", 3.4), 2.4, "center", size=96, accent_idx=0)
headline(["Centurion was", "won in both."], b("hearts", 5.6), BEAT["hearts"][1] - b("hearts", 5.6) + 0.4, "center", size=110, accent_idx=1)
card(P + "shoaib_sachin_rivalry.jpg", b("cta", 0.0), 9.0, "right", "SACHIN vs SHOAIB", "The full rivalry?")
headline(["Comment", "“2003”"], b("cta", 0.6), 8.4, "left", size=130, accent_idx=1, sub="…and we'll make the full rivalry video")
logo_sting(b("cta", 9.2), TOTAL - b("cta", 9.2), end=True)

# ----------------------------------------------------------------------------- page

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
.tag{{position:absolute;left:28px;bottom:-74px;display:flex;align-items:center;gap:14px;color:#fff;white-space:nowrap}}
.tag b{{font-weight:800;font-size:28px;letter-spacing:2px}}
.tag em{{font-style:normal;font-weight:500;font-size:24px;color:rgba(255,255,255,.62)}}
.tagbar{{width:6px;height:34px;background:{Y};border-radius:3px}}
.hl{{position:absolute;font-weight:800;letter-spacing:-0.03em;line-height:1.04;color:#fff}}
.hl .mask{{overflow:hidden;padding-bottom:.06em}}
.hl .ln{{display:block}}
.hbar{{position:absolute;left:-46px;top:.08em;width:10px;height:calc(100% - .16em);background:{Y};border-radius:5px;transform-origin:top}}
.hsub{{font-size:34px;font-weight:500;letter-spacing:0;color:rgba(255,255,255,.66);margin-top:22px}}
.odo{{position:absolute;font-weight:800;letter-spacing:-0.04em;line-height:1}}
.digits{{display:inline-flex}}
.dcol{{display:inline-block;height:1em;overflow:hidden}}
.dstrip{{display:flex;flex-direction:column}}
.dstrip span{{height:1em;line-height:1em}}
.dchar{{display:inline-block}}
.olab{{font-size:30px;font-weight:700;letter-spacing:6px;color:rgba(255,255,255,.72);margin-top:22px}}
.pills{{position:absolute;display:flex;flex-direction:column;gap:22px}}
.pill{{display:flex;align-items:center;gap:18px;padding:22px 34px;border-radius:999px;background:rgba(255,255,255,.07);
  box-shadow:inset 0 0 0 1px rgba(255,255,255,.10);color:#fff;font-size:40px;font-weight:600;white-space:nowrap}}
.pill b{{color:{Y};font-weight:800}}
.pill .dot{{width:14px;height:14px;border-radius:50%;background:{Y}}}
.phone{{position:absolute;border-radius:56px;padding:14px;background:#111;box-shadow:0 0 0 2px #2a2a2c,0 60px 120px rgba(0,0,0,.7);transform-style:preserve-3d}}
.phone video{{width:100%;height:100%;object-fit:cover;object-position:top;border-radius:44px}}
.tgraph{{position:absolute;inset:0}}
.tline{{position:absolute;left:230px;right:230px;top:540px;height:4px;background:linear-gradient(90deg,{Y},rgba(254,222,92,.25));transform-origin:left}}
.tnode{{position:absolute;top:470px;transform:translateX(-50%);text-align:center;width:340px}}
.tdot{{width:30px;height:30px;border-radius:50%;margin:56px auto 0}}
.tyear{{position:absolute;top:-70px;left:0;right:0;font-size:84px;font-weight:800;color:#fff;letter-spacing:-2px}}
.tlab{{margin-top:34px;font-size:30px;font-weight:600;color:rgba(255,255,255,.8)}}
.chapter{{position:absolute;left:150px;top:96px;display:flex;align-items:center;gap:18px;color:#fff;z-index:60}}
.chnum{{font-size:26px;font-weight:800;color:{Y};letter-spacing:3px}}
.chbar{{width:40px;height:3px;background:rgba(255,255,255,.5)}}
.chtitle{{font-size:26px;font-weight:700;letter-spacing:6px;text-transform:uppercase}}
.stage{{position:absolute;inset:0;background:radial-gradient(90% 80% at 50% 45%,#19191c,#050506);overflow:hidden}}
.persp{{position:absolute;inset:0;perspective:1400px;display:flex;align-items:center;justify-content:center}}
.n98{{position:absolute;top:150px;left:0;right:0;text-align:center;font-size:560px;font-weight:900;letter-spacing:-0.05em;line-height:1;transform-style:preserve-3d}}
.n98 span{{display:block}}
.n98 .back{{color:#7a560e}}
.n98 .gold{{position:absolute;left:0;right:0;top:0;background:linear-gradient(180deg,#FFF1B0 0%,#FEDE5C 35%,#C8961E 70%,#FFE38A 100%);-webkit-background-clip:text;background-clip:text;color:transparent}}
.n98.refl .back{{display:none}}
.n98.refl{{top:auto;bottom:-430px;transform:scaleY(-1);-webkit-mask-image:linear-gradient(0deg,rgba(0,0,0,.6),transparent 45%)}}
.uline{{position:absolute;left:610px;right:610px;top:760px;height:8px;border-radius:4px;background:{Y};transform-origin:left;box-shadow:0 0 30px rgba(254,222,92,.6)}}
.datewrap{{flex-direction:column;align-items:flex-start;left:560px;right:auto;justify-content:center}}
.dbar{{position:absolute;left:-60px;top:300px;width:16px;height:470px;border-radius:8px;background:{Y};transform-origin:top;box-shadow:0 0 40px rgba(254,222,92,.5)}}
.dl1{{font-size:190px;font-weight:900;color:#fff;letter-spacing:-0.03em;line-height:1;transform-origin:50% 100%}}
.dl2{{font-size:250px;font-weight:900;color:{Y};letter-spacing:-0.03em;line-height:1;transform-origin:50% 100%}}
.lbig{{position:absolute;left:50%;top:50%;width:1000px;margin-left:-500px;margin-top:-118px}}
.lsweep{{position:absolute;left:50%;top:0;bottom:0;width:180px;margin-left:-90px;background:linear-gradient(90deg,transparent,rgba(254,222,92,.35),transparent);transform:skewX(-18deg)}}
.lfoot{{position:absolute;left:0;right:0;top:640px;text-align:center;color:rgba(255,255,255,.75);font-size:40px;font-weight:600;letter-spacing:2px}}
.mark{{position:absolute;right:70px;bottom:56px;width:210px;opacity:.55;z-index:80}}
"""


def build():
    os.makedirs(MEDIA, exist_ok=True)
    shutil.copy(os.path.join(HERE, "node_modules", "gsap", "dist", "gsap.min.js"), os.path.join(OUT, "gsap.min.js"))
    shutil.copy(os.path.join(HERE, "..", "kohli_countdown", "assets", "logo.png"), os.path.join(MEDIA, "logo.png"))
    if not os.path.exists(os.path.join(MEDIA, "grain.png")):
        import numpy as np
        g = (np.random.default_rng(3).normal(128, 40, (512, 512))).clip(0, 255).astype("uint8")
        Image.fromarray(g, "L").save(os.path.join(MEDIA, "grain.png"))
    body = [f'<div class="bg"></div><div class="glow" id="glow"></div><div class="grain"></div>']
    for start, dur, z, h in sorted(els, key=lambda e: e[0]):
        body.append(h)
    body.append(f'<img class="mark clip" id="mark" src="media/logo.png" data-start="{BEAT["kargil"][0]}" '
                f'data-duration="{round(TOTAL - BEAT["kargil"][0] - 5, 2)}">')
    body.append('<div class="vig"></div>')
    page = f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div id="root" data-composition-id="root" data-width="{W}" data-height="{H}" data-fps="{FPS}" data-duration="{TOTAL}">
{chr(10).join(body)}
</div>
<script src="gsap.min.js"></script>
<script>
const tl = gsap.timeline({{paused:true}});
tl.fromTo("#glow",{{x:-200,y:0}},{{x:900,y:200,duration:{TOTAL},ease:"sine.inOut"}},0);
tl.fromTo("#mark",{{opacity:0}},{{opacity:0.55,duration:1}},{BEAT["kargil"][0]});
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

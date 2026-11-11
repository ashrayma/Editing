#!/usr/bin/env python3
""""Dear Rajat" reel (1080x1920, ~60 s): a letter to Rajat Patidar after he pulled out of India A (Nov 2026).

    python3 reel.py   ->  reel/index.html + out/soundtrack.wav, then render with HyperFrames (see make.sh)

Layout follows the "Dear <player>" letter format (squad cards, big numbers, format tiles, cut-outs) in
TheCricketLounge colours: charcoal and brand-yellow scenes. Timing comes from out/beats.json (one entry per
script line, from the cleaned voiceover); without it, line lengths are estimated from the script so the
graphics can be built before the voiceover exists. Photos and clips go in assets/<slot>.(mp4|jpg|png);
a missing one renders as a labelled placeholder.
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
LEAD, GAP, END_HOLD = 0.25, 0.3, 1.6

LINES = [
    ("dear", "Dear Rajat, I hope you know what you're doing."),
    ("bcci", "Because this decision might just upset a few people at the BCCI."),
    ("fifty", "You've asked them not to pick you for fifty-over cricket while you manage your injuries."),
    ("respect", "And honestly? I respect that. Your body comes first."),
    ("t20", "But a few days later, you'll be leading Madhya Pradesh in a T20 tournament, and people will notice that."),
    ("advice", "So here's a little advice from a fan."),
    ("clear", "Make it clear this is about fitness, not about choosing formats."),
    ("age", "You're thirty-three."),
    ("trophy", "You've lifted the IPL trophy as RCB captain."),
    ("suits", "T20 clearly suits you, and that's okay."),
    ("door", "But keep one door open for India."),
    ("wait", "Because selectors don't wait for anyone."),
    ("rinku", "Rinku is already vice-captain, and Badoni already has your spot."),
    ("cap", "You worked so hard for that India cap, Rajat."),
    ("callback", "Get fit, score big, and make them call you back."),
    ("plan", "I really hope this is a plan that pays off,"),
    ("time", "because at thirty-three, time isn't on your side."),
    ("ask", "Good advice, or should he just focus on T20? Tell me in the comments, and follow for the next letter."),
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
    add(f'<div id="{i}" class="words {font} clip" data-start="{start}" data-duration="{dur}" '
        f'style="top:{y}px;font-size:{size}px;text-align:{align};z-index:{z}">{rows}</div>')
    for k in range(len(lines)):
        anim(f'tl.fromTo("#{i}l{k}",{{yPercent:110}},{{yPercent:0,duration:0.7,ease:"expo.out"}},{round(start + 0.05 + stagger * k, 2)})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.3}},{round(start + dur - 0.3, 2)})')
    return i


def label(txt, start, dur, y, color=Y, bg=None, size=34, z=31):
    i = nid("lb")
    style = f"top:{y}px;font-size:{size}px;color:{color};" + (f"background:{bg};padding:10px 22px;border-radius:10px;" if bg else "")
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


# ----------------------------------------------------------------------------- the reel

def build_scenes():
    # 1. Dear Rajat (face first, per the playbook: open on the star, never a title card)
    s, d = 0.0, until_next("dear")
    scene(s, d, "dark")
    photo("rajat_face", s, d, "RAJAT FACE CLIP (celebration / interview)", 170, 360, 740, 820, tag="RCB CAPTAIN", tilt=-3, enter="pop")
    words(["Dear Rajat,"], at("dear", 0.15), d - 0.15, 1230, size=150, font="serif", colors=["#fff"], stagger=0)

    # 2. a few people at the BCCI
    s, d = at("bcci"), until_next("bcci")
    scene(s, d, "yellow")
    words(["BCCI"], s, d, 330, size=380, colors=["outline"], z=21, sfx_kind="impact")
    photo("bcci_post", s + 0.25, d - 0.25, "GAUTAM GAMBHIR (BCCI)", 130, 600, 820, 620, tilt=2)
    label("A FEW PEOPLE AT THE BCCI", span("bcci", 0.45), d - span("bcci", 0.45) + s, 1320, color=INK, bg="#fff", size=40)

    # 3. India A card, WITHDRAWN stamp + injury pill
    s, d = at("fifty"), until_next("fifty")
    scene(s, d, "dark")
    label("FOR CONTEXT", s, d, 360, size=34)
    s2 = span("fifty", 0.38)
    photo("news_cricinfo", s, s2 - s + 0.2, "NEWS HEADLINE", 70, 520, 940, 597, tag="8 NOV 2026", tilt=-1)
    squad_card(s2, s + d - s2, "INDIA A", "RISING STARS ASIA CUP 2026", "50 OVERS", [("RAJAT PATIDAR", "name")],
               y=470, stamp="WITHDRAWN", stamp_at=span("fifty", 0.58))
    label("✚  MANAGING INJURIES", span("fifty", 0.75), d - span("fifty", 0.75) + s, 1200, color="#fff", bg="rgba(229,72,77,.9)", size=40)

    # 4. honestly? I respect that. Your body comes first.
    s, d = at("respect"), until_next("respect")
    scene(s, d, "dark")
    big_number("50", "OVERS", s, span("respect", 0.4) - s + 0.2, y=430, size=560, outline_at=round(s + 0.5, 2), strike_at=round(s + 0.75, 2))
    words(["HONESTLY?", "I RESPECT THAT."], span("respect", 0.38), d - span("respect", 0.38) + s, 560, size=120, colors=["rgba(255,255,255,.55)", "#fff"])
    words(["YOUR BODY", "COMES FIRST."], span("respect", 0.62), d - span("respect", 0.62) + s, 900, size=130, colors=[Y, Y])

    # 5. a few days later: MP captain, T20, people will notice
    s, d = at("t20"), until_next("t20")
    scene(s, d, "yellow")
    label("A FEW DAYS LATER", s, span("t20", 0.5) - s, 360, color=INK, size=36)
    squad_card(s, span("t20", 0.5) - s, "MADHYA PRADESH", "SYED MUSHTAQ ALI TROPHY", "T20", [("RAJAT PATIDAR", "cap")], y=470)
    s2 = span("t20", 0.5)
    words(["T20"], s2, s + d - s2, 330, size=620, colors=[INK], z=12, sfx_kind="impact")
    cutout("rajat_mp_cut", s2 + 0.1, s + d - s2 - 0.1, "RAJAT CUT-OUT (MP / RCB kit)", 230, 560, 840)
    label("PEOPLE WILL NOTICE", span("t20", 0.82), s + d - span("t20", 0.82), 1300, color="#fff", bg=INK, size=42)

    # 6. a little advice from a fan
    s, d = at("advice"), until_next("advice")
    scene(s, d, "dark")
    words(["a little", "advice"], s, d, 560, size=190, font="serif", colors=["#fff", Y])
    words(["FROM A FAN"], s + 0.5, d - 0.5, 1040, size=70, colors=["rgba(255,255,255,.7)"], sfx_kind="pop")

    # 7. fitness, not formats
    s, d = at("clear"), until_next("clear")
    scene(s, d, "dark")
    label("MAKE IT CLEAR", s, d, 420, size=38)
    checklist([("FITNESS", True), ("CHOOSING FORMATS", False)], s, d, 600, [round(s + 0.2, 2), span("clear", 0.6)])

    # 8. 33 (the shareable number)
    s, d = at("age"), until_next("age")
    scene(s, d, "yellow")
    label("AGE", s, d, 400, color=INK, size=40)
    big_number("33", "", s, d, y=470, size=560, color=INK)
    ruler(s, d, 26, [33], y=1130)

    # 9. IPL trophy
    s, d = at("trophy"), until_next("trophy")
    scene(s, d, "dark")
    photo("ipl_trophy", s, d, "RCB IPL TROPHY LIFT (clip or photo)", 90, 420, 900, 760, tag="RCB · IPL CHAMPIONS 2025", tilt=-2)
    label("FIRST TITLE IN 18 SEASONS", span("trophy", 0.45), s + d - span("trophy", 0.45), 1250, color=INK, bg=Y, size=40)

    # 10. T20 suits you
    s, d = at("suits"), until_next("suits")
    scene(s, d, "dark")
    label("EVERY FORMAT", s, d, 470, size=36)
    tiles(s, d, y=620, hi=2, hi_at=span("suits", 0.3))
    words(["AND THAT'S OKAY."], span("suits", 0.62), s + d - span("suits", 0.62), 1180, size=96, colors=["#fff"])

    # 11. keep one door open
    s, d = at("door"), until_next("door")
    scene(s, d, "dark")
    label("KEEP ONE DOOR OPEN", s, d, 470, size=40)
    tiles(s, d, y=620, door=1, door_at=span("door", 0.45), dim_others=False)
    words(["FOR INDIA."], span("door", 0.5), s + d - span("door", 0.5), 1180, size=110, colors=[Y])

    # 12. selectors don't wait
    s, d = at("wait"), until_next("wait")
    scene(s, d, "yellow")
    label("SELECTORS", s, d, 470, color=INK, size=44)
    words(["DON'T", "WAIT."], s + 0.15, d - 0.15, 560, size=330, colors=[INK, RED], sfx_kind="impact")

    # 13. Rinku VC, Badoni in
    s, d = at("rinku"), until_next("rinku")
    scene(s, d, "dark")
    squad_card(s, d, "INDIA A", "RISING STARS ASIA CUP 2026", "UPDATED", [("RINKU SINGH", "vc"), ("AYUSH BADONI", "in")], y=440)
    photo("rinku", span("rinku", 0.1), d - span("rinku", 0.1) + s, "RINKU", 170, 1120, 260, 260, z=25, enter="left")
    photo("badoni", span("rinku", 0.5), d - span("rinku", 0.5) + s, "BADONI", 650, 1120, 260, 260, z=25, enter="right")

    # 14. the India cap
    s, d = at("cap"), until_next("cap")
    scene(s, d, "dark")
    photo("rajat_india", s, d, "RAJAT IN INDIA KIT (debut)", 140, 400, 800, 840, tag="INDIA DEBUT · 2023", tilt=2)

    # 15. get fit, score big, make them call you back
    s, d = at("callback"), until_next("callback")
    scene(s, d, "yellow")
    for k, (txt, f) in enumerate([("GET FIT.", 0.0), ("SCORE BIG.", 0.28), ("MAKE THEM", 0.55)]):
        words([txt], span("callback", f), s + d - span("callback", f), 470 + 210 * k, size=190, colors=[INK], sfx_kind="pop")
    words(["CALL YOU BACK."], span("callback", 0.72), s + d - span("callback", 0.72), 1100, size=150, colors=[RED], sfx_kind="impact")

    # 16. a plan that pays off
    s, d = at("plan"), until_next("plan")
    scene(s, d, "dark")
    cutout("rajat_smile_cut", s, d, "RAJAT CUT-OUT (smiling / clapping)", 250, 700, 780)
    words(["a plan that", "pays off"], s + 0.1, d - 0.1, 400, size=140, font="serif", colors=["#fff", Y], z=31)

    # 17. time isn't on your side
    s, d = at("time"), until_next("time")
    scene(s, d, "dark")
    label("AGE", s, d, 420, size=40)
    big_number("33", "", s, span("time", 0.5) - s, y=480, size=520)
    ruler(s, d, 31, [33, 34, 35], y=1030, step_at=[span("time", 0.5), span("time", 0.68)])
    words(["TIME ISN'T", "ON YOUR SIDE."], span("time", 0.5), s + d - span("time", 0.5), 520, size=130, colors=["#fff", Y])

    # 18. the question + sign-off
    s = at("ask")
    d = TOTAL - s
    scene(s, d, "yellow")
    q = span("ask", 0.77)  # "and follow for the next letter"
    words(["GOOD ADVICE?"], s, q - s, 560, size=170, colors=[INK], sfx_kind="impact")
    words(["OR JUST T20?"], span("ask", 0.19), q - span("ask", 0.19), 790, size=170, colors=[RED], sfx_kind="impact")
    label("💬  TELL ME IN THE COMMENTS", span("ask", 0.59), q - span("ask", 0.59), 1060, color="#fff", bg=INK, size=40)
    words(["FOLLOW", "FOR THE NEXT", "LETTER"], q, TOTAL - q, 470, size=170, colors=[INK, INK, RED])
    words(["Yours,", "TheCricketLounge"], q + 0.6, TOTAL - q - 0.6, 1130, size=80, font="serif", colors=[INK, INK], stagger=0.2, sfx_kind="pop")

    for lid, _ in LINES:
        if lid not in NO_VO:
            captions(lid)


build_scenes()

FONTS = os.path.join(HERE, "node_modules", "@fontsource")
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
    # warm, reflective bed for a letter; lifts with a soft pulse from "selectors don't wait" to the close
    m = norm(reverb(pad(WARM, TOTAL + 2, bar=4.0, cutoff=1500), 2.5, 0.4)) * 0.5
    m = m[:n] + norm(reverb(arps(WARM, TOTAL + 2, step=0.5, gain=0.16), 1.5, 0.3))[:n] * 0.35
    t_w = at("wait")
    m += section(norm(pulse(TOTAL - t_w + 1, 92, lambda t: min(1, t / 8))) * 0.4, t_w, TOTAL, 0.8, 1.5)
    m = section(m, 0.0, TOTAL, 0.4, 1.2)
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
             "pop": ("pop", 0.0, 0.08), "stamp": ("impact", 0.0, 0.16), "tick": ("tick", 0.0, 0.12)}
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
<div class="brand"><img src="media/logo.png"></div>
{chr(10).join(els)}
</div>
<script src="gsap.min.js"></script>
<script>
const tl = gsap.timeline({{paused:true}});
{chr(10).join(js)}
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

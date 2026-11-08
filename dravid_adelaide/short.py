#!/usr/bin/env python3
"""Adelaide 2003 Short (1080x1920): HyperFrames composition timed to the narration.

    python3 short.py      ->  hf/index.html (+ media), out/events.json
    python3 soundtrack.py ->  out/soundtrack.wav
    cd hf && npx hyperframes render ...   (see make_short.sh)

theCricketLounge look: charcoal, white type, #FEDE5C accent, full-screen pictures that whip in with motion blur,
drift and push in; numbers roll; zoom punches on every landing; shake + flash on the big hits. Text stays inside
the Shorts/Reels safe zone (clear of the top ~250 px and bottom ~420 px).
"""
import html
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from beats import IDS  # noqa: E402

OUT = os.path.join(HERE, "hf")
MEDIA = os.path.join(OUT, "media")
W, H, FPS = 1080, 1920, 30
Y = "#FEDE5C"
RED = "#ff453a"
TAIL = 3.0
VO_OFFSET = 0.0
P = "assets/photos/"
R3 = "blender/renders/"

os.makedirs(MEDIA, exist_ok=True)
TL = json.load(open(os.path.join(HERE, "out", "vo_timeline.json")))
BEAT = {b["id"]: (b["start"], b["end"]) for b in TL["beats"]}
ORDER = [b["id"] for b in TL["beats"]]          # lines in the edit (dropped lines are absent)
TOTAL = round(TL["duration"] + TAIL, 2)
els, js, EVENTS, SHOTS = [], [], [], []
_n, _whip = [0], [1]


def nid(p):
    _n[0] += 1
    return f"{p}{_n[0]}"


def add(h):
    els.append(h)


def anim(a):
    js.append(a)


def media(rel):
    src = os.path.join(HERE, rel)
    dst = os.path.join(MEDIA, rel.replace("/", "_"))
    if not os.path.exists(dst) or os.path.getmtime(src) > os.path.getmtime(dst):
        shutil.copy(src, dst)
    return "media/" + os.path.basename(dst)


def L(n):
    return n if isinstance(n, str) else f"l{n:02d}"


def at(n, f=0.0):
    s, e = BEAT[L(n)]
    return round(s + f * (e - s), 2)


def span(n, a=0.0, b=1.0):
    """(start, duration) for fraction a..b of line n; ending at the line's end it runs to the next line's start."""
    s = at(n, a)
    if b >= 1.0:
        k = ORDER.index(L(n))
        e = BEAT[ORDER[k + 1]][0] + 0.15 if k + 1 < len(ORDER) else TOTAL
    else:
        e = at(n, b)
    return s, round(e - s, 2)


# ----------------------------------------------------------------------------- components

def photo(src, n, a=0.0, b=1.0, label=None, sub=None, gray=False, origin="50% 40%", push=1.18, z=5, fit=None):
    """A picture full screen: blurred copy fills the frame, the picture itself whips in (motion blur), then drifts
    and pushes in; soft shade at the bottom for type; optional lower-third tag."""
    s, d = span(n, a, b)
    i = nid("ph")
    EVENTS.append((s, "whoosh"))
    filt = "filter:grayscale(1) contrast(1.12);" if gray else ""
    tag = (f'<div class="tag" id="{i}t"><span class="tagbar"></span><b>{html.escape(label)}</b>'
           + (f"<em>{html.escape(sub)}</em>" if sub else "") + "</div>") if label else ""
    rel = media(src)
    from PIL import Image
    with Image.open(os.path.join(HERE, src)) as im:
        portrait = im.height / im.width > 1.05
    fit = fit or "cover"                            # always fill the 9:16 frame
    base = 1.0 if fit == "cover" else 1.45          # landscape pictures start larger, so they fill more of the frame
    add(f'<div id="{i}" class="full clip" data-start="{s}" data-duration="{d}" style="z-index:{z};{filt}">'
        f'<img src="{rel}" class="full" style="object-fit:cover;filter:blur(34px) brightness(.5);transform:scale(1.2)">'
        f'<img id="{i}i" src="{rel}" class="full" style="object-fit:{fit};object-position:{origin};transform-origin:{origin}">'
        f'<div class="scrim"></div>{tag}</div>')
    dd = _whip[0]
    _whip[0] = -dd
    anim(f'tl.fromTo("#{i}",{{opacity:0,x:{120 * dd},filter:"blur(14px)"}},{{opacity:1,x:0,filter:"blur(0px)",duration:0.28,ease:"expo.out"}},{s})')
    anim(f'tl.fromTo("#{i}i",{{scale:{base},x:{-18 * dd}}},{{scale:{round(base * push, 3)},x:{18 * dd},duration:{d},ease:"sine.inOut"}},{s})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.15}},{round(s + d - 0.15, 2)})')
    if label:
        anim(f'tl.fromTo("#{i}t",{{x:-40,opacity:0}},{{x:0,opacity:1,duration:0.6,ease:"expo.out"}},{round(s + 0.3, 2)})')
    SHOTS.append((s, s + d, i))


def shot3d(name, n, a=0.0, b=1.0, z=6):
    s, d = span(n, a, b)
    i = nid("v")
    EVENTS.append((s, "hit"))
    src = R3 + name + ".mp4" if os.path.exists(os.path.join(HERE, R3 + name + ".mp4")) else R3 + name + ".stub.mp4"
    add(f'<video id="{i}" class="full clip" src="{media(src)}" muted playsinline data-start="{s}" '
        f'data-duration="{d}" data-media-start="0" style="z-index:{z}"></video>')
    anim(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.15}},{s})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.25}},{round(s + d - 0.25, 2)})')


def stage(n, a=0.0, b=1.0, z=4):
    """Dark branded stage (for graphics-only lines)."""
    s, d = span(n, a, b)
    i = nid("st")
    add(f'<div id="{i}" class="stage clip" data-start="{s}" data-duration="{d}" style="z-index:{z}"></div>')
    anim(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.2}},{s})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.25}},{round(s + d - 0.25, 2)})')


def headline(lines, n, a=0.0, b=1.0, size=110, acc=(), y=1180, sub=None, z=30, stamp=False):
    """Centred headline, lines revealed from behind a mask (or stamped in with a hit)."""
    s, d = span(n, a, b)
    s = round(s + 0.05, 2)
    i = nid("h")
    EVENTS.append((s + 0.1, "impact" if (size >= 130 or stamp) else "soft"))
    PUNCHES.append(s + 0.15)
    rows = "".join(f'<div class="mask"><div class="ln" id="{i}l{k}" style="color:{Y if k in acc else "#fff"}">'
                   f"{html.escape(t)}</div></div>" for k, t in enumerate(lines))
    subh = f'<div class="sub" id="{i}s">{html.escape(sub)}</div>' if sub else ""
    add(f'<div id="{i}" class="hl clip" data-start="{s}" data-duration="{d}" style="top:{y}px;font-size:{size}px;z-index:{z}">'
        f"{rows}{subh}</div>")
    if stamp:
        anim(f'tl.fromTo("#{i}",{{scale:2.2,opacity:0}},{{scale:1,opacity:1,duration:0.35,ease:"power4.in"}},{s})')
        SHAKES.append(s + 0.35)
    else:
        for k in range(len(lines)):
            anim(f'tl.fromTo("#{i}l{k}",{{yPercent:110}},{{yPercent:0,duration:0.5,ease:"expo.out"}},{round(s + 0.05 + 0.08 * k, 2)})')
    if sub:
        anim(f'tl.fromTo("#{i}s",{{opacity:0,y:14}},{{opacity:1,y:0,duration:0.6}},{round(s + 0.4, 2)})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.15}},{round(s + d - 0.15, 2)})')


def odo(num, n, a=0.0, b=1.0, label=None, y=1100, size=300, color=Y, z=30):
    s, d = span(n, a, b)
    s = round(s + 0.05, 2)
    i = nid("o")
    EVENTS.append((s + 0.1, "roll"))
    PUNCHES.append(s + 1.1)
    cols = []
    for k, ch in enumerate(num):
        if ch.isdigit():
            strip = "".join(f"<span>{q}</span>" for q in "0123456789")
            cols.append(f'<span class="dcol"><span class="dstrip" id="{i}d{k}">{strip}</span></span>')
            anim(f'tl.fromTo("#{i}d{k}",{{yPercent:0}},{{yPercent:{-int(ch) * 10},duration:{0.7 + 0.08 * k},ease:"expo.out"}},{s + 0.05})')
        else:
            cols.append(f'<span class="dchar">{html.escape(ch)}</span>')
    lab = f'<div class="olab" id="{i}lb">{html.escape(label)}</div>' if label else ""
    add(f'<div id="{i}" class="odo clip" data-start="{s}" data-duration="{d}" style="top:{y}px;font-size:{size}px;color:{color};z-index:{z}">'
        f'<div class="digits">{"".join(cols)}</div>{lab}</div>')
    anim(f'tl.fromTo("#{i}",{{opacity:0,scale:0.92}},{{opacity:1,scale:1,duration:0.4}},{s})')
    if label:
        anim(f'tl.fromTo("#{i}lb",{{opacity:0,y:12}},{{opacity:1,y:0,duration:0.35}},{s + 0.35})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.15}},{round(s + d - 0.15, 2)})')


def pills(items, n, a=0.0, b=1.0, y=1080, z=30):
    s, d = span(n, a, b)
    i = nid("p")
    rows = "".join(f'<div class="pill" id="{i}p{k}"><span class="dot"></span>{t}</div>' for k, t in enumerate(items))
    add(f'<div id="{i}" class="pills clip" data-start="{s}" data-duration="{d}" style="top:{y}px;z-index:{z}">{rows}</div>')
    gap = max(0.25, (d - 0.8) / (len(items) + 0.5))
    for k in range(len(items)):
        EVENTS.append((round(s + 0.1 + gap * k, 2), "pop"))
        anim(f'tl.fromTo("#{i}p{k}",{{y:30,opacity:0}},{{y:0,opacity:1,duration:0.5,ease:"expo.out"}},{round(s + 0.1 + gap * k, 2)})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.15}},{round(s + d - 0.15, 2)})')


def ytag(text, n, m):
    s = at(n)
    d = round(BEAT[L(m)][1] - s + 0.3, 2)
    i = nid("y")
    add(f'<div id="{i}" class="ytag clip" data-start="{s}" data-duration="{d}">{html.escape(text)}</div>')
    anim(f'tl.fromTo("#{i}",{{clipPath:"inset(0% 100% 0% 0%)"}},{{clipPath:"inset(0% 0% 0% 0%)",duration:0.5,ease:"expo.out"}},{s})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.15}},{round(s + d - 0.15, 2)})')


def flash(t):
    i = nid("x")
    EVENTS.append((t, "hit"))
    SHAKES.append(t)
    add(f'<div id="{i}" class="flash clip" data-start="{round(t, 2)}" data-duration="0.4" style="z-index:88"></div>')
    anim(f'tl.fromTo("#{i}",{{opacity:0.8}},{{opacity:0,duration:0.35,ease:"power2.out"}},{t})')


def bars(rows, n, a=0.0, b=1.0, y=1000, z=30):
    """Two or three horizontal bars growing to scale, value on the right."""
    s, d = span(n, a, b)
    i = nid("b")
    mx = max(v for _, v, _ in rows)
    parts = []
    for k, (lab, v, c) in enumerate(rows):
        parts.append(f'<div class="brow"><div class="blab">{html.escape(lab)}</div><div class="btrack">'
                     f'<div class="bfill" id="{i}f{k}" style="width:{v / mx * 100:.1f}%;background:{c}"></div></div>'
                     f'<div class="bval">{v}</div></div>')
        anim(f'tl.fromTo("#{i}f{k}",{{scaleX:0}},{{scaleX:1,duration:0.8,ease:"expo.out"}},{round(s + 0.1 + 0.2 * k, 2)})')
        EVENTS.append((round(s + 0.2 + 0.3 * k, 2), "pop"))
    add(f'<div id="{i}" class="bars clip" data-start="{s}" data-duration="{d}" style="top:{y}px;z-index:{z}">{"".join(parts)}</div>')
    anim(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.3}},{s})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.15}},{round(s + d - 0.15, 2)})')


def clock(hours, n, a=0.0, b=1.0, y=760, z=30):
    """A dial whose hand sweeps round `hours` times while the hours count up underneath."""
    s, d = span(n, a, b)
    i = nid("ck")
    EVENTS.append((s, "tick_run"))
    ticks = "".join(f'<div class="ctk" style="transform:rotate({k * 30}deg)"></div>' for k in range(12))
    add(f'<div id="{i}" class="clock clip" data-start="{s}" data-duration="{d}" style="top:{y}px;z-index:{z}">'
        f'<div class="dial">{ticks}<div class="hand" id="{i}h"></div><div class="hub"></div></div>'
        f'<div class="clab"><span id="{i}n">0</span>+ HOURS</div></div>')
    anim(f'tl.fromTo("#{i}",{{opacity:0,scale:0.9}},{{opacity:1,scale:1,duration:0.5,ease:"expo.out"}},{s})')
    anim(f'tl.fromTo("#{i}h",{{rotation:0}},{{rotation:{360 * hours},duration:{min(d - 0.6, 3.2)},ease:"power2.inOut"}},{s + 0.2})')
    anim(f'tl.fromTo("#{i}n",{{innerText:0}},{{innerText:{hours},duration:{min(d - 0.6, 3.2)},snap:{{innerText:1}},ease:"power2.inOut"}},{s + 0.2})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.15}},{round(s + d - 0.15, 2)})')


def chase(runs, target, n, a=0.0, b=1.0, y=300, z=60, label="INDIA"):
    s, d = span(n, a, b)
    i = nid("cb")
    add(f'<div id="{i}" class="chase clip" data-start="{s}" data-duration="{d}" style="top:{y}px;z-index:{z}">'
        f'<div class="chtxt"><b>{label} {runs}</b><span>TARGET {target}</span></div>'
        f'<div class="chtrack"><div class="chfill" id="{i}f" style="width:{runs / target * 100:.1f}%"></div></div></div>')
    anim(f'tl.fromTo("#{i}",{{y:-30,opacity:0}},{{y:0,opacity:1,duration:0.5,ease:"expo.out"}},{s})')
    anim(f'tl.fromTo("#{i}f",{{scaleX:0}},{{scaleX:1,duration:0.9,ease:"expo.out"}},{s + 0.1})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.15}},{round(s + d - 0.15, 2)})')


def faceoff(cards, n, a=0.0, b=1.0, y=520, z=30, reveal=None):
    """Stat cards stacked down the screen (picture + name + numbers); each lands on its own cue time."""
    s, d = span(n, a, b)
    i = nid("fo")
    parts = []
    for k, (img, name, stat, sub) in enumerate(cards):
        parts.append(f'<div class="fcard" id="{i}c{k}"><img src="{media(img)}"><div class="fname">{html.escape(name)}</div>'
                     f'<div class="fstat">{html.escape(stat)}</div><div class="fsub">{html.escape(sub)}</div></div>')
        t = (reveal[k] if reveal else s + 0.2 + 0.5 * k)
        EVENTS.append((t, "impact"))
        anim(f'tl.fromTo("#{i}c{k}",{{x:{-500 if k % 2 == 0 else 500},opacity:0}},{{x:0,opacity:1,duration:0.6,ease:"expo.out"}},{round(t, 2)})')
    add(f'<div id="{i}" class="faceoff clip" data-start="{s}" data-duration="{d}" style="top:{y}px;z-index:{z}">{"".join(parts)}</div>')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.15}},{round(s + d - 0.15, 2)})')
    return i


def poll(options, n, a=0.0, b=1.0, y=900, z=40):
    s, d = span(n, a, b)
    i = nid("pl")
    rows = "".join(f'<div class="popt" id="{i}o{k}"><span class="pnum">{k + 1}</span>{html.escape(o)}</div>'
                   for k, o in enumerate(options))
    add(f'<div id="{i}" class="poll clip" data-start="{s}" data-duration="{d}" style="top:{y}px;z-index:{z}">'
        f'<div class="pq">WHO WAS THE REAL HERO?</div>{rows}<div class="pc">Comment your pick</div></div>')
    for k in range(len(options)):
        EVENTS.append((round(s + 0.5 + 0.35 * k, 2), "pop"))
        anim(f'tl.fromTo("#{i}o{k}",{{x:-80,opacity:0}},{{x:0,opacity:1,duration:0.4,ease:"expo.out"}},{round(s + 0.3 + 0.25 * k, 2)})')
    anim(f'tl.fromTo("#{i}",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.5,ease:"expo.out"}},{s})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.15}},{round(s + d - 0.15, 2)})')


def date_card(top, bottom, n, a=0.0, b=1.0, z=30):
    s, d = span(n, a, b)
    i = nid("dc")
    EVENTS.append((s, "impact"))
    add(f'<div id="{i}" class="datec clip" data-start="{s}" data-duration="{d}" style="z-index:{z}">'
        f'<div class="dbar" id="{i}b"></div><div class="d1" id="{i}a">{html.escape(top)}</div>'
        f'<div class="d2" id="{i}c">{html.escape(bottom)}</div></div>')
    anim(f'tl.fromTo("#{i}b",{{scaleY:0}},{{scaleY:1,duration:0.5,ease:"expo.out"}},{s})')
    anim(f'tl.fromTo("#{i}a",{{rotationX:-95,opacity:0}},{{rotationX:0,opacity:1,duration:0.8,ease:"expo.out"}},{s + 0.15})')
    anim(f'tl.fromTo("#{i}c",{{rotationX:-95,opacity:0}},{{rotationX:0,opacity:1,duration:0.8,ease:"expo.out"}},{s + 0.35})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.15}},{round(s + d - 0.15, 2)})')


def end_card(start, dur):
    i = nid("end")
    add(f'<div id="{i}" class="stage clip" data-start="{start}" data-duration="{dur}" style="z-index:70">'
        f'<img class="logo" id="{i}l" src="media/logo.png"><div class="follow" id="{i}f">Follow for more cricket stories</div></div>')
    anim(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.3}},{start})')
    anim(f'tl.fromTo("#{i}l",{{clipPath:"inset(0% 100% 0% 0%)"}},{{clipPath:"inset(0% 0% 0% 0%)",duration:0.9,ease:"expo.inOut"}},{start + 0.1})')
    anim(f'tl.fromTo("#{i}f",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.6}},{start + 0.7})')


PUNCHES, SHAKES = [], []

# ----------------------------------------------------------------------------- the Short

# Photo slots. Each slot is one picture; drop a new file into assets/photos/ under the slot's name (any of
# .jpg/.jpeg/.png/.webp) and it replaces the fallback still from the reference reel.
FALLBACK = {"travis_head": "dravid_handshake", "dravid_laxman": "dravid_handshake", "dravid_closeup": "dravid_bat_gloves",
            "adelaide_oval": "adelaide_oval", "ponting": "ponting_242", "aus_team": "aus_2003_team",
            "laxman": "dravid_handshake", "dravid_bat": "dravid_bat_gloves", "agarkar_bowl": "agarkar",
            "agarkar_wicket": "agarkar", "dravid_win": "dravid_arms_raised", "india_celebrate": "dravid_arms_raised",
            "ponting_jump": "aus_2003_team", "ponting_roar": "aus_2003_team", "adelaide_oval2": "adelaide_oval"}


def PH(slot):
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        if os.path.exists(os.path.join(HERE, P + slot + ext)):
            return P + slot + ext
    return P + FALLBACK[slot] + ".png"


# HOOK: Travis Head is to India what Dravid & Laxman were to Australia (two cuts)
photo(PH("travis_head"), "h1", 0.0, 0.5, origin="50% 35%", push=1.2)
photo(PH("dravid_laxman"), "h1", 0.5, 1.0, origin="50% 35%", push=1.2)
pills(["TRAVIS HEAD <b>→ INDIA</b>", "DRAVID & LAXMAN <b>→ AUSTRALIA</b>"], "h1", 0.1, 1.0, y=1080)
photo(PH("dravid_closeup"), "h2", push=1.2, origin="40% 8%")
headline(["A different", "plan."], "h2", 0.3, 1.0, size=130, acc=(1,), y=1130)
photo(PH("adelaide_oval"), "h3", origin="45% 55%", push=1.2)
headline(["Adelaide 2003."], "h3", 0.1, 1.0, size=120, acc=(0,), y=1150)

# 1-2: 556, Ponting 242 ... and Australia LOST
shot3d("s556", 1, 0.0, 0.4)
photo(PH("ponting"), 1, 0.4, 1.0, origin="50% 30%", push=1.25)
odo("242", 1, 0.45, 1.0, label="PONTING ALONE", y=1150, size=260)
photo(PH("ponting_jump"), 2, gray=True, origin="50% 30%", push=1.25)
headline(["And yet…"], 2, 0.0, 0.35, size=90, y=1150)
headline(["LOST."], 2, 0.3, 1.0, size=260, acc=(0,), y=1050, stamp=True)

# 4-5 THE SETTING
ytag("ADELAIDE · DEC 2003", 4, 9)
photo(PH("ponting_roar"), 4, origin="50% 30%", push=1.3)
pills(["Hayden", "Langer", "Ponting", "Martyn", "Gilchrist", "Steve Waugh"], 4, 0.05, 1.0, y=1020)
stage(5)
odo("556", 5, 0.0, 1.0, label="AUSTRALIA · 1ST INNINGS", y=760, size=300, color="#fff")
headline(["Enormous", "pressure."], 5, 0.35, 1.0, size=110, acc=(1,), y=1200)

# 6-9 DRAVID & LAXMAN
photo(PH("laxman"), 6, 0.0, 0.5, push=1.25)
photo(PH("dravid_bat"), 6, 0.5, 1.0, push=1.25)
headline(["Dravid", "& Laxman."], 6, 0.15, 1.0, size=120, acc=(0,), y=1150)
photo(PH("laxman"), 7, push=1.3, origin="40% 35%")
odo("148", 7, 0.0, 1.0, label="VVS LAXMAN", y=1100, size=300)
stage(8, 0.0, 0.45)
clock(10, 8, 0.0, 0.45, y=620)
photo(PH("dravid_bat"), 8, 0.45, 1.0, push=1.25, origin="45% 35%")
odo("233", 8, 0.45, 1.0, label="RAHUL DRAVID", y=1150, size=300)
stage(9)
bars([("AUSTRALIA", 556, "rgba(255,255,255,.35)"), ("INDIA", 523, Y)], 9, 0.0, 1.0, y=820)
headline(["Just 33 behind."], 9, 0.35, 1.0, size=100, acc=(0,), y=1420)

# 10-13 THE TWIST: AGARKAR
stage(10)
headline(["But the real twist", "was still coming."], 10, 0.0, 1.0, size=96, acc=(1,), y=860)
ytag("2ND INNINGS", 11, 13)
photo(PH("agarkar_bowl"), 11, label="AJIT AGARKAR", sub="Spell of his life", origin="40% 40%", push=1.15)
photo(PH("agarkar_wicket"), 12, push=1.3, origin="40% 45%")
odo("6/41", 12, 0.0, 1.0, label="AGARKAR", y=1380, size=300)
shot3d("s196", 13)
flash(at(13, 0.45))

# 14-17 THE CHASE
stage(14)
odo("230", 14, 0.0, 1.0, label="TO WIN", y=760, size=340)
photo(PH("dravid_closeup"), 15, 0.0, 0.5, push=1.2, origin="40% 8%")
photo(PH("dravid_bat"), 15, 0.5, 1.0, push=1.3, origin="60% 35%")
chase(160, 230, 15, label="INDIA")
headline(["Dravid stood", "in the way."], 15, 0.2, 1.0, size=100, acc=(0,), y=1180)
shot3d("s72", 16)
photo(PH("dravid_win"), 17, label="INDIA WIN", sub="by 4 wickets", origin="50% 35%", push=1.25)
flash(at(17, 0.05))
chase(233, 230, 17, label="INDIA")

# 18, 22-24 THINK ABOUT IT
stage(18, 0.0, 1.0)
headline(["Think about it."], 18, 0.0, 1.0, size=110, y=900)
photo(PH("india_celebrate"), 22, origin="40% 8%", push=1.15)
headline(["India beat Australia", "in Australia."], 22, 0.05, 1.0, size=96, acc=(1,), y=1180)
photo(PH("adelaide_oval2"), 23, gray=True, push=1.2, origin="50% 55%")
headline(["Not just a", "Test victory."], 23, 0.0, 1.0, size=110, acc=(1,), y=1150)
photo(PH("dravid_laxman"), 24, push=1.3)
headline(["Indian cricket", "had arrived."], 24, 0.0, 1.0, size=110, acc=(1,), y=1150)
flash(at(24, 0.1))

# 25 CTA
stage(25)
poll(["Rahul Dravid · 233 & 72*", "VVS Laxman · 148", "Ajit Agarkar · 6/41"], 25, y=640)
end_card(round(BEAT[L(25)][1] + 0.3, 2), round(TOTAL - BEAT[L(25)][1] - 0.3, 2))

# ----------------------------------------------------------------------------- punches / shakes on the shot on screen
for t in PUNCHES:
    for a, b_, sid in SHOTS:
        if a + 0.45 < t < b_ - 0.5:
            anim(f'tl.fromTo("#{sid}",{{scale:1}},{{scale:1.05,duration:0.12,ease:"power2.out",yoyo:true,repeat:1}},{round(t, 2)})')
for t in SHAKES:
    for a, b_, sid in SHOTS:
        if a + 0.45 < t < b_ - 0.4:
            anim(f'tl.fromTo("#{sid}",{{y:0,rotation:0}},{{keyframes:[{{y:-16,rotation:-0.7,duration:0.05}},{{y:12,rotation:0.6,duration:0.05}},'
                 f'{{y:-6,rotation:-0.2,duration:0.06}},{{y:0,rotation:0,duration:0.1}}]}},{round(t, 2)})')

CSS = f"""
html,body{{margin:0;background:#060607}}
#root{{position:relative;width:{W}px;height:{H}px;overflow:hidden;background:#0a0a0b;font-family:"Inter Display","Inter",system-ui,sans-serif}}
.bg{{position:absolute;inset:0;background:radial-gradient(120% 80% at 50% 40%,#1b1b1e 0%,#0b0b0c 55%,#050506 100%)}}
.grain{{position:absolute;inset:0;opacity:.07;mix-blend-mode:overlay;background-image:url(media/grain.png);z-index:95}}
.vig{{position:absolute;inset:0;background:radial-gradient(ellipse at center,rgba(0,0,0,0) 55%,rgba(0,0,0,.6) 100%);z-index:90}}
.full{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;overflow:hidden}}
.stage{{position:absolute;inset:0;background:radial-gradient(90% 70% at 50% 45%,#1a1a1d,#050506)}}
.scrim{{position:absolute;inset:0;background:linear-gradient(0deg,rgba(0,0,0,.75) 0%,rgba(0,0,0,.35) 38%,rgba(0,0,0,0) 60%),
  linear-gradient(180deg,rgba(0,0,0,.45) 0%,rgba(0,0,0,0) 18%)}}
.tag{{position:absolute;left:60px;bottom:470px;display:flex;align-items:center;gap:14px;color:#fff}}
.tag b{{font-weight:800;font-size:30px;letter-spacing:3px}}
.tag em{{font-style:normal;font-weight:500;font-size:28px;color:rgba(255,255,255,.7)}}
.tagbar{{width:7px;height:40px;background:{Y};border-radius:3px}}
.hl{{position:absolute;left:60px;right:60px;text-align:center;font-weight:800;letter-spacing:-0.03em;line-height:1.04;color:#fff;
  text-shadow:0 6px 40px rgba(0,0,0,.6)}}
.hl .mask{{overflow:hidden;padding-bottom:.06em}}
.hl .ln{{display:block}}
.sub{{font-size:34px;font-weight:600;color:rgba(255,255,255,.75);margin-top:20px;letter-spacing:0}}
.odo{{position:absolute;left:0;right:0;text-align:center;font-weight:900;letter-spacing:-0.04em;line-height:1;
  font-variant-numeric:tabular-nums;text-shadow:0 10px 50px rgba(0,0,0,.6)}}
.digits{{display:inline-flex}}
.dcol{{display:inline-block;height:1em;overflow:hidden}}
.dstrip{{display:flex;flex-direction:column}}
.dstrip span{{height:1em;line-height:1em;text-align:center}}
.dchar{{display:inline-block}}
.olab{{font-size:34px;font-weight:700;letter-spacing:7px;color:rgba(255,255,255,.8);margin-top:24px}}
.pills{{position:absolute;left:0;right:0;display:flex;flex-wrap:wrap;justify-content:center;gap:18px;padding:0 70px}}
.pill{{display:flex;align-items:center;gap:14px;padding:18px 30px;border-radius:999px;background:rgba(10,10,12,.72);
  box-shadow:inset 0 0 0 1px rgba(255,255,255,.14);color:#fff;font-size:40px;font-weight:700}}
.pill b{{color:{Y}}}
.pill .dot{{width:14px;height:14px;border-radius:50%;background:{Y}}}
.ytag{{position:absolute;left:60px;top:270px;padding:10px 20px;background:{Y};color:#0a0a0b;font-weight:800;font-size:30px;
  letter-spacing:3px;border-radius:8px;z-index:85}}
.flash{{position:absolute;inset:0;background:#fff}}
.bars{{position:absolute;left:70px;right:70px;display:flex;flex-direction:column;gap:50px}}
.brow{{display:flex;flex-direction:column;gap:14px;color:#fff}}
.blab{{font-size:38px;font-weight:800;letter-spacing:5px}}
.btrack{{height:70px}}
.bfill{{height:100%;border-radius:14px;transform-origin:left}}
.bval{{font-size:90px;font-weight:900;letter-spacing:-3px}}
.clock{{position:absolute;left:0;right:0;display:flex;flex-direction:column;align-items:center;gap:30px}}
.dial{{position:relative;width:420px;height:420px;border-radius:50%;box-shadow:inset 0 0 0 6px rgba(255,255,255,.85),0 0 60px rgba(254,222,92,.2)}}
.ctk{{position:absolute;left:207px;top:12px;width:6px;height:30px;background:rgba(255,255,255,.7);transform-origin:3px 198px}}
.hand{{position:absolute;left:204px;top:50px;width:12px;height:160px;background:{Y};border-radius:6px;transform-origin:6px 160px;
  box-shadow:0 0 20px rgba(254,222,92,.6)}}
.hub{{position:absolute;left:192px;top:192px;width:36px;height:36px;border-radius:50%;background:#fff}}
.clab{{color:#fff;font-weight:900;font-size:120px;letter-spacing:-2px}}
.clab span{{color:{Y}}}
.chase{{position:absolute;left:70px;right:70px;padding:22px 30px;border-radius:24px;background:rgba(10,10,12,.8);
  box-shadow:inset 0 0 0 1px rgba(255,255,255,.14)}}
.chtxt{{display:flex;justify-content:space-between;color:#fff;font-size:36px;font-weight:800;letter-spacing:3px}}
.chtxt span{{color:rgba(255,255,255,.6)}}
.chtrack{{margin-top:16px;height:16px;border-radius:8px;background:rgba(255,255,255,.12);overflow:hidden}}
.chfill{{height:100%;background:linear-gradient(90deg,{RED},{Y});transform-origin:left;max-width:100%}}
.faceoff{{position:absolute;left:60px;right:60px;display:flex;flex-direction:column;gap:34px}}
.fcard{{display:flex;align-items:center;gap:30px;padding:22px;border-radius:30px;background:rgba(18,18,20,.92);
  box-shadow:inset 0 0 0 1px rgba(255,255,255,.12)}}
.fcard img{{width:250px;height:250px;object-fit:cover;object-position:50% 25%;border-radius:20px}}
.fname{{color:rgba(255,255,255,.75);font-size:34px;font-weight:800;letter-spacing:6px}}
.fstat{{color:{Y};font-size:100px;font-weight:900;letter-spacing:-3px;line-height:1.05}}
.fsub{{color:rgba(255,255,255,.7);font-size:30px;font-weight:600}}
.poll{{position:absolute;left:70px;right:70px;display:flex;flex-direction:column;gap:26px}}
.pq{{color:#fff;font-size:64px;font-weight:900;letter-spacing:-1px;text-align:center;margin-bottom:20px}}
.popt{{display:flex;align-items:center;gap:24px;padding:30px 34px;border-radius:26px;background:rgba(255,255,255,.08);
  box-shadow:inset 0 0 0 2px rgba(254,222,92,.35);color:#fff;font-size:46px;font-weight:800}}
.pnum{{width:64px;height:64px;border-radius:50%;background:{Y};color:#111;display:flex;align-items:center;justify-content:center;font-size:36px}}
.pc{{color:rgba(255,255,255,.7);font-size:36px;font-weight:600;text-align:center;margin-top:16px}}
.datec{{position:absolute;left:110px;top:700px;perspective:1200px}}
.dbar{{position:absolute;left:-40px;top:10px;width:14px;height:330px;border-radius:7px;background:{Y};transform-origin:top}}
.d1{{font-size:110px;font-weight:900;color:#fff;letter-spacing:-2px;line-height:1.05}}
.d2{{font-size:170px;font-weight:900;color:{Y};letter-spacing:-4px;line-height:1}}
.logo{{position:absolute;left:90px;width:900px;top:820px}}
.follow{{position:absolute;left:0;right:0;top:1050px;text-align:center;color:rgba(255,255,255,.8);font-size:44px;font-weight:600}}
.mark{{position:absolute;right:50px;top:280px;width:200px;opacity:.5;z-index:80}}
"""


def build():
    os.makedirs(MEDIA, exist_ok=True)
    shutil.copy(os.path.join(HERE, "..", "doc_video", "node_modules", "gsap", "dist", "gsap.min.js"), os.path.join(OUT, "gsap.min.js"))
    shutil.copy(os.path.join(HERE, "..", "kohli_countdown", "assets", "logo.png"), os.path.join(MEDIA, "logo.png"))
    g = os.path.join(MEDIA, "grain.png")
    if not os.path.exists(g):
        import numpy as np
        from PIL import Image
        Image.fromarray((np.random.default_rng(3).normal(128, 40, (512, 512))).clip(0, 255).astype("uint8"), "L").save(g)
    page = f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div id="root" data-composition-id="root" data-width="{W}" data-height="{H}" data-fps="{FPS}" data-duration="{TOTAL}">
<div class="bg"></div>
{chr(10).join(els)}
<img class="mark clip" id="mark" src="media/logo.png" data-start="0.2" data-duration="{round(BEAT[L(25)][1], 2)}">
<div class="vig"></div><div class="grain"></div>
</div>
<script src="gsap.min.js"></script>
<script>
const tl = gsap.timeline({{paused:true}});
{chr(10).join(js)}
tl.set({{}},{{}},{TOTAL});
window.__timelines = window.__timelines || {{}};
window.__timelines["root"] = tl;
</script></body></html>"""
    open(os.path.join(OUT, "index.html"), "w").write(page)
    json.dump({"total": TOTAL, "vo_offset": VO_OFFSET, "beats": BEAT, "events": sorted(EVENTS)},
              open(os.path.join(HERE, "out", "events.json"), "w"))
    print(f"{len(els)} elements, {len(js)} animation steps, {TOTAL:.1f}s")


if __name__ == "__main__":
    build()

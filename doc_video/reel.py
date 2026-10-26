#!/usr/bin/env python3
"""60-second Instagram reel cut (1080x1920) of "Centurion 2003: The 98".

    python3 reel.py   ->  reel/index.html + out/reel_vo.wav + out/reel_soundtrack.wav
    then render with HyperFrames and mux (see make_reel.sh)

Story in 60 s: fastest ball ever -> Sachin's six off Shoaib's first ball -> 18 off the over -> the bouncer,
out on 98 -> "some matches are won in the heart" -> logo + comment CTA. Everything sits inside Instagram's
safe zone (top ~250 px and bottom ~420 px stay clear of text).
"""
import html
import json
import os
import shutil
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "kohli_countdown"))
import music  # noqa: E402
import sfx  # noqa: E402
from soundtrack import A_MINOR, D_MINOR, WARM, arps, norm, pad, pulse, reverb, section, ticker  # noqa: E402

OUT = os.path.join(HERE, "reel")
MEDIA = os.path.join(OUT, "media")
W, H, FPS = 1080, 1920, 30
Y = "#FEDE5C"
SR = sfx.SR
BEATS = ["hook_fastest", "hook_first_ball", "hook_six", "eighteen", "bouncer", "out_98", "hearts"]
GAP = 0.35
LEAD, END_CARD = 0.3, 2.6

os.makedirs(MEDIA, exist_ok=True)
els, js, events = [], [], []
_n = [0]


def nid(p):
    _n[0] += 1
    return f"{p}{_n[0]}"


def media(rel):
    src = os.path.join(HERE, rel)
    dst = os.path.join(MEDIA, os.path.basename(rel))
    if not os.path.exists(dst) or os.path.getmtime(src) > os.path.getmtime(dst):
        shutil.copy(src, dst)
    return "media/" + os.path.basename(rel)


def add(h):
    els.append(h)


def anim(a):
    js.append(a)


# ----------------------------------------------------------------------------- narration

def build_vo():
    tl = json.load(open(os.path.join(HERE, "out", "vo_timeline.json")))["beats"]
    beat = {b["id"]: b for b in tl}
    with wave.open(os.path.join(HERE, "out", "vo_final.wav")) as w:
        v = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    parts, times, t = [np.zeros(int(LEAD * SR), np.float32)], {}, LEAD
    for k, bid in enumerate(BEATS):
        b = beat[bid]
        seg = v[int(b["start"] * SR): int(b["end"] * SR)]
        times[bid] = (round(t, 2), round(t + len(seg) / SR, 2))
        parts.append(seg)
        t += len(seg) / SR
        if k < len(BEATS) - 1:
            parts.append(np.zeros(int(GAP * SR), np.float32))
            t += GAP
    vo = np.concatenate(parts)
    return vo, times, round(t + END_CARD, 2)


VO, T, TOTAL = build_vo()


def at(bid, off=0.0):
    s, e = T[bid]
    return round((e + off) if off < 0 else (s + off), 2)


def length(bid):
    return round(T[bid][1] - T[bid][0], 2)


# ----------------------------------------------------------------------------- components (vertical)

MEDIA_TOP, MEDIA_H, TEXT_Y = 330, 900, 1290


def card(src, start, dur, label=None, video=False, w=None, h=None):
    """Media card centred in the upper two-thirds; slides up into place, slow push-in, slides away."""
    i = nid("c")
    events.append((start, "whoosh"))
    if video:
        mw, mh = 716, 780
    else:
        from PIL import Image
        with Image.open(os.path.join(HERE, src)) as im:
            mw, mh = im.size
    s = min((w or 960) / mw, (h or MEDIA_H) / mh)
    cw, ch = round(mw * s), round(mh * s)
    left, top = round(W / 2 - cw / 2), round(MEDIA_TOP + (MEDIA_H - ch) / 2)
    rel = media(src)
    inner = (f'<video id="{i}m" class="clip" src="{rel}" muted playsinline data-start="{start}" data-duration="{dur}" '
             f'data-media-start="0"></video>') if video else f'<img id="{i}m" src="{rel}">'
    tag = (f'<div class="tag"><span class="tagbar"></span>{html.escape(label)}</div>') if label else ""
    add(f'<div id="{i}" class="card clip" data-start="{start}" data-duration="{dur}" '
        f'style="left:{left}px;top:{top}px;width:{cw}px;height:{ch}px"><div class="frame">{inner}'
        f'{"<div class=tagfade></div>" if label else ""}</div>{tag}</div>')
    anim(f'tl.fromTo("#{i}",{{y:260,opacity:0,scale:0.94}},{{y:0,opacity:1,scale:1,duration:0.8,ease:"expo.out"}},{start})')
    anim(f'tl.fromTo("#{i}m",{{scale:1.1}},{{scale:1,duration:{dur},ease:"none"}},{start})')
    anim(f'tl.to("#{i}",{{y:-160,opacity:0,duration:0.45,ease:"power2.in"}},{round(start + dur - 0.45, 2)})')


def full(src, start, dur, dim=0.3, video=False, origin="50% 50%", push=1.12, end=1.0, ai=False):
    i = nid("f")
    events.append((start, "whoosh"))
    rel = media(src)
    inner = (f'<video id="{i}m" class="clip" src="{rel}" muted playsinline data-start="{start}" data-duration="{dur}" '
             f'data-media-start="0" style="transform-origin:{origin}"></video>') if video else \
        f'<img id="{i}m" src="{rel}" style="transform-origin:{origin}">'
    tag = '<div class="aitag">AI illustration</div>' if ai else ""
    add(f'<div id="{i}" class="full clip" data-start="{start}" data-duration="{dur}">{inner}'
        f'<div class="dim" style="background:rgba(5,5,6,{dim})"></div>{tag}</div>')
    anim(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.4}},{start})')
    anim(f'tl.fromTo("#{i}m",{{scale:{push}}},{{scale:{end},duration:{dur},ease:"none"}},{start})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.4}},{round(start + dur - 0.4, 2)})')


def text(lines, start, dur, size=96, accent=None, y=TEXT_Y, sub=None):
    """Centred headline revealed line by line from behind a mask."""
    i = nid("t")
    events.append((start + 0.1, "impact" if size >= 120 else "soft"))
    acc = accent if isinstance(accent, (list, tuple)) else ([accent] if accent is not None else [])
    rows = "".join(f'<div class="mask"><div class="ln" id="{i}l{k}" style="color:{Y if k in acc else "#fff"}">'
                   f'{html.escape(t)}</div></div>' for k, t in enumerate(lines))
    subh = f'<div class="sub" id="{i}s">{html.escape(sub)}</div>' if sub else ""
    add(f'<div id="{i}" class="txt clip" data-start="{start}" data-duration="{dur}" style="top:{y}px;font-size:{size}px">'
        f'{rows}{subh}</div>')
    for k in range(len(lines)):
        anim(f'tl.fromTo("#{i}l{k}",{{yPercent:110}},{{yPercent:0,duration:0.8,ease:"expo.out"}},{round(start + 0.1 + 0.1 * k, 2)})')
    if sub:
        anim(f'tl.fromTo("#{i}s",{{opacity:0,y:14}},{{opacity:1,y:0,duration:0.7}},{round(start + 0.4, 2)})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.35}},{round(start + dur - 0.35, 2)})')


def odo(num, start, dur, size=300, label=None, y=None, color=Y):
    i = nid("o")
    events.append((start + 0.1, "roll"))
    cols = []
    for k, ch in enumerate(num):
        if ch.isdigit():
            strip = "".join(f"<span>{d}</span>" for d in "0123456789")
            cols.append(f'<span class="dcol"><span class="dstrip" id="{i}d{k}">{strip}</span></span>')
            anim(f'tl.fromTo("#{i}d{k}",{{yPercent:0}},{{yPercent:{-int(ch) * 10},duration:{1.2 + 0.12 * k},ease:"expo.out"}},{start + 0.1})')
        else:
            cols.append(f'<span>{html.escape(ch)}</span>')
    lab = f'<div class="olab">{html.escape(label)}</div>' if label else ""
    add(f'<div id="{i}" class="odo clip" data-start="{start}" data-duration="{dur}" '
        f'style="top:{y if y is not None else TEXT_Y - 40}px;font-size:{size}px;color:{color}"><div class="digits">{"".join(cols)}</div>{lab}</div>')
    anim(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.3}},{start})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.35}},{round(start + dur - 0.35, 2)})')


def pill(txt, start, dur, y):
    i = nid("p")
    events.append((start, "pop"))
    add(f'<div id="{i}" class="pill clip" data-start="{start}" data-duration="{dur}" style="top:{y}px">'
        f'<span class="dot"></span>{txt}</div>')
    anim(f'tl.fromTo("#{i}",{{y:30,opacity:0}},{{y:0,opacity:1,duration:0.6,ease:"expo.out"}},{start})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.3}},{round(start + dur - 0.3, 2)})')


def stage(start, dur, z=40):
    i = nid("s")
    events.append((start, "hit"))
    anim(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.25}},{start})')
    anim(f'tl.to("#{i}",{{opacity:0,duration:0.3}},{round(start + dur - 0.3, 2)})')
    return i


def gold98(start, dur):
    i = stage(start, dur)
    depth = ",".join(f"0 {k}px 0 #6b4c0c" for k in range(1, 15)) + ",0 40px 60px rgba(0,0,0,.7)"
    add(f'<div id="{i}" class="stage clip" data-start="{start}" data-duration="{dur}"><div class="n98" id="{i}n">'
        f'<span class="back" style="text-shadow:{depth}">98</span><span class="gold">98</span></div>'
        f'<div class="uline" id="{i}u"></div></div>')
    anim(f'tl.fromTo("#{i}n",{{y:220,rotationX:55,opacity:0}},{{y:0,rotationX:0,opacity:1,duration:1.1,ease:"expo.out"}},{start + 0.05})')
    anim(f'tl.fromTo("#{i}u",{{scaleX:0}},{{scaleX:1,duration:0.8,ease:"expo.out"}},{start + 0.7})')


def date_card(start, dur):
    i = stage(start, dur)
    add(f'<div id="{i}" class="stage clip" data-start="{start}" data-duration="{dur}"><div class="date">'
        f'<div class="dbar" id="{i}b"></div><div class="d1" id="{i}a">1 MARCH</div><div class="d2" id="{i}c">2003</div></div></div>')
    anim(f'tl.fromTo("#{i}b",{{scaleY:0}},{{scaleY:1,duration:0.5,ease:"expo.out"}},{start})')
    anim(f'tl.fromTo("#{i}a",{{rotationX:-95,opacity:0}},{{rotationX:0,opacity:1,duration:0.9,ease:"expo.out"}},{start + 0.2})')
    anim(f'tl.fromTo("#{i}c",{{rotationX:-95,opacity:0}},{{rotationX:0,opacity:1,duration:0.9,ease:"expo.out"}},{start + 0.4})')


def end_card(start, dur):
    i = stage(start, dur, z=50)
    add(f'<div id="{i}" class="stage clip" data-start="{start}" data-duration="{dur}" style="z-index:50">'
        f'<img class="lbig" id="{i}l" src="media/logo.png"><div class="cta" id="{i}c">Comment <b>“2003”</b></div>'
        f'<div class="cta2" id="{i}d">Full story on YouTube</div></div>')
    anim(f'tl.fromTo("#{i}l",{{clipPath:"inset(0% 100% 0% 0%)"}},{{clipPath:"inset(0% 0% 0% 0%)",duration:0.9,ease:"expo.inOut"}},{start + 0.1})')
    anim(f'tl.fromTo("#{i}c",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.6}},{start + 0.6})')
    anim(f'tl.fromTo("#{i}d",{{opacity:0}},{{opacity:1,duration:0.6}},{start + 0.9})')


# ----------------------------------------------------------------------------- the reel

C = "footage/clips/"
P = "assets/photos/"
A = "assets/ai/"
R3 = "blender/renders/"

# 1. fastest ball ever
full(A + "ai_ball.png", at("hook_fastest", 0.0) - LEAD, 3.4 + LEAD, dim=0.25, origin="45% 50%", push=1.25, end=1.05, ai=True)
text(["161.3", "KM/H"], at("hook_fastest", 0.2), 3.0, size=170, accent=0, y=1180)
full(R3 + "speed.mp4", at("hook_fastest", 3.0), 3.5, dim=0.0, video=True, push=1.0, end=1.0)
card(P + "shoaib_bowling.jpg", at("hook_fastest", 6.4), length("hook_fastest") - 6.4 + GAP, label="SHOAIB AKHTAR")
text(["Fastest ball", "ever recorded."], at("hook_fastest", 6.5), length("hook_fastest") - 6.5 + GAP, size=84, accent=1)
# 2. a few days later: Shoaib's first ball to Sachin
date_card(at("hook_first_ball", 0.1), 2.4)
card(C + "m_stance_close.mp4", at("hook_first_ball", 2.5), length("hook_first_ball") - 2.5 + GAP, label="SACHIN TENDULKAR", video=True)
text(["Shoaib vs Sachin"], at("hook_first_ball", 2.7), length("hook_first_ball") - 2.7, size=92, accent=None, sub="First ball")
# 3. the six
card(C + "m_six_shot.mp4", at("hook_six", 0.0), 3.3, label="OVER THIRD MAN", video=True)
odo("6", at("hook_six", 0.4), 2.9, size=280, label="SIX")
card(C + "m_crowd_six.mp4", at("hook_six", 3.3), length("hook_six") - 3.3 + GAP, video=True)
text(["Off Shoaib's", "first ball."], at("hook_six", 3.4), length("hook_six") - 3.4, size=92, accent=1)
# 4. 18 off the over
card(C + "m_four_154.mp4", at("eighteen", -1.6), 1.6 + GAP + 0.6, label="154.1 KPH", video=True)
odo("18", at("eighteen", 0.0), length("eighteen") + 0.6, size=260, label="RUNS OFF THE OVER")
# 5. the bouncer
b0 = at("bouncer", 0.0)
card(C + "m_shoaib_turn.mp4", b0, 4.4, label="SHOAIB AKHTAR", video=True)
text(["Then, at 98…"], b0 + 0.2, 4.0, size=96, accent=None)
text(["Bouncer."], b0 + 4.6, 3.6, size=200, accent=0, y=820)
card(C + "m_dismissal.mp4", b0 + 8.4, 5.8, label="GLOVED TO POINT", video=True)
pill("c Younis Khan b Shoaib Akhtar", b0 + 9.6, 4.6, TEXT_Y + 20)
card(C + "m_walk_off.mp4", b0 + 14.2, length("bouncer") - 14.2 + GAP, label="OUT FOR 98", video=True)
# 6. out for 98
o0 = at("out_98", 0.0)
gold98(o0, 3.0)
card(C + "m_replay.mp4", o0 + 3.0, length("out_98") - 3.0 + GAP, video=True)
text(["2 runs short."], o0 + 3.1, length("out_98") - 3.1, size=96, accent=0, sub="98 off 75 · 12 fours · 1 six")
# 7. won in the heart
h0 = at("hearts", 0.0)
full(A + "ai_tv_family.png", h0, 3.5, dim=0.25, ai=True)
text(["Some matches are won", "on the scoreboard."], h0 + 0.1, 3.3, size=72, accent=1, y=1180)
card(C + "m_bench.mp4", h0 + 3.4, length("hearts") - 3.4 + 0.2, label="INDIA WON BY 6 WICKETS", video=True)
text(["Some, in the heart."], h0 + 3.5, 2.2, size=84, accent=0)
text(["Centurion was", "won in both."], h0 + 5.7, length("hearts") - 5.7 + 0.1, size=92, accent=1)
end_card(round(TOTAL - END_CARD, 2), END_CARD)

CSS = f"""
html,body{{margin:0;background:#060607}}
#root{{position:relative;width:{W}px;height:{H}px;overflow:hidden;background:radial-gradient(110% 70% at 50% 40%,#1b1b1e,#060607);
  font-family:"Inter Display","Inter",system-ui,sans-serif;perspective:1600px}}
.brand{{position:absolute;left:0;right:0;top:250px;text-align:center;z-index:60}}
.brand img{{width:250px;opacity:.9}}
.full{{position:absolute;inset:0;overflow:hidden;z-index:5}}
.full img,.full video{{width:100%;height:100%;object-fit:cover}}
.dim{{position:absolute;inset:0}}
.aitag{{position:absolute;right:36px;top:330px;padding:8px 16px;border-radius:999px;background:rgba(0,0,0,.45);color:rgba(255,255,255,.7);font-size:22px;font-weight:600}}
.card{{position:absolute;z-index:20}}
.card .frame{{position:relative;width:100%;height:100%;border-radius:36px;overflow:hidden;box-shadow:0 50px 110px rgba(0,0,0,.7),0 0 0 1px rgba(255,255,255,.08)}}
.card img,.card video{{width:100%;height:100%;object-fit:cover}}
.tagfade{{position:absolute;left:0;right:0;bottom:0;height:170px;background:linear-gradient(0deg,rgba(0,0,0,.8),rgba(0,0,0,0))}}
.tag{{position:absolute;left:34px;bottom:30px;display:flex;align-items:center;gap:14px;color:#fff;font-size:30px;font-weight:800;letter-spacing:2px}}
.tagbar{{width:7px;height:36px;border-radius:4px;background:{Y}}}
.txt{{position:absolute;left:60px;right:60px;text-align:center;font-weight:900;letter-spacing:-0.03em;line-height:1.04;color:#fff;z-index:30;
  text-shadow:0 6px 30px rgba(0,0,0,.6)}}
.txt .mask{{overflow:hidden;padding-bottom:.05em}}
.txt .ln{{display:block}}
.sub{{font-size:36px;font-weight:600;letter-spacing:0;color:rgba(255,255,255,.75);margin-top:18px}}
.odo{{position:absolute;left:0;right:0;text-align:center;font-weight:900;letter-spacing:-0.04em;line-height:1;z-index:30}}
.digits{{display:inline-flex}}
.dcol{{display:inline-block;height:1em;overflow:hidden}}
.dstrip{{display:flex;flex-direction:column}}
.dstrip span{{height:1em}}
.olab{{font-size:34px;font-weight:800;letter-spacing:6px;color:rgba(255,255,255,.85);margin-top:16px}}
.pill{{position:absolute;left:50%;transform:translateX(-50%);display:flex;align-items:center;gap:16px;padding:20px 34px;border-radius:999px;
  background:rgba(255,255,255,.1);box-shadow:inset 0 0 0 1px rgba(255,255,255,.14);color:#fff;font-size:40px;font-weight:700;white-space:nowrap;z-index:30}}
.pill .dot{{width:16px;height:16px;border-radius:50%;background:{Y}}}
.stage{{position:absolute;inset:0;background:radial-gradient(90% 60% at 50% 45%,#1a1a1d,#050506);z-index:40}}
.n98{{position:absolute;left:0;right:0;top:600px;text-align:center;font-size:520px;font-weight:900;letter-spacing:-0.05em;line-height:1}}
.n98 span{{display:block}}
.n98 .back{{color:#7a560e}}
.n98 .gold{{position:absolute;left:0;right:0;top:0;background:linear-gradient(180deg,#FFF1B0 0%,{Y} 35%,#C8961E 70%,#FFE38A 100%);
  -webkit-background-clip:text;background-clip:text;color:transparent}}
.uline{{position:absolute;left:300px;right:300px;top:1180px;height:10px;border-radius:5px;background:{Y};transform-origin:left;box-shadow:0 0 30px rgba(254,222,92,.6)}}
.date{{position:absolute;left:190px;top:720px}}
.dbar{{position:absolute;left:-50px;top:10px;width:16px;height:420px;border-radius:8px;background:{Y};transform-origin:top}}
.d1{{font-size:170px;font-weight:900;color:#fff;letter-spacing:-0.03em;line-height:1;transform-origin:50% 100%}}
.d2{{font-size:240px;font-weight:900;color:{Y};letter-spacing:-0.03em;line-height:1;transform-origin:50% 100%}}
.lbig{{position:absolute;left:90px;width:900px;top:760px}}
.cta{{position:absolute;left:0;right:0;top:1030px;text-align:center;color:#fff;font-size:74px;font-weight:900}}
.cta b{{color:{Y}}}
.cta2{{position:absolute;left:0;right:0;top:1140px;text-align:center;color:rgba(255,255,255,.7);font-size:40px;font-weight:600}}
"""


def build_audio():
    n = int(SR * TOTAL)
    vo = np.zeros(n, np.float32)
    vo[: len(VO)] = VO[:n]
    m = np.zeros(n)
    t_b = at("bouncer", 0.0) - 0.4
    m += section(norm(music.track(t_b + 1.5)) * 0.62, 0.0, TOTAL, 0.3, 1.2)
    t_h = at("hearts", 0.0) - 0.3
    d = t_h - t_b
    tens = norm(reverb(pad(D_MINOR, d + 2, bar=4.0, cutoff=900), 2.0, 0.35)) * 0.45 + \
        norm(pulse(d + 2, 96, lambda t: min(1, t / d))) * 0.5 + norm(ticker(d + 2, 120)) * 0.25
    m += section(tens, t_b, TOTAL, 0.8, 0.6)
    close = norm(reverb(pad(WARM, TOTAL - t_h + 2, bar=4.0, cutoff=1600), 2.5, 0.4)) * 0.45 + \
        norm(reverb(arps(WARM, TOTAL - t_h + 2), 1.5, 0.3)) * 0.35
    m += section(close, t_h, TOTAL, 1.5, 1.5)
    hop = 441
    env = np.abs(vo[: len(vo) // hop * hop]).reshape(-1, hop).max(1)
    env = np.convolve(env > 0.03, np.ones(30), "same") > 0
    duck = np.convolve(np.repeat(np.where(env, 0.45, 1.0), hop), np.ones(4410) / 4410, "same")
    m[: len(duck)] *= duck
    fx = np.zeros(n)
    cache = {}

    def put(name, t, g):
        if name not in cache:
            cache[name] = getattr(sfx, name)()
        music.add(fx, cache[name], max(0, t), g)

    for t, kind in events:
        {"whoosh": lambda: put("whoosh", t - 0.12, 0.16), "impact": lambda: put("impact", t, 0.28),
         "soft": lambda: put("pop", t, 0.10), "pop": lambda: put("pop", t, 0.16),
         "hit": lambda: put("impact", t, 0.34),
         "roll": lambda: [put("tick", t + 0.05 * k, 0.1) for k in range(8)]}[kind]()
    put("crowd", at("hook_six", 0.5), 0.4)
    put("riser", at("bouncer", 2.6), 0.32)
    put("heartbeat", at("bouncer", 8.6), 0.45)
    mix = vo * 0.95 + m * 0.24 + fx * 0.55
    mix = np.tanh(mix * 1.05) / np.tanh(1.05)
    mix = mix / max(1e-6, np.abs(mix).max()) * 0.9
    with wave.open(os.path.join(HERE, "out", "reel_soundtrack.wav"), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.stack([mix, mix], 1) * 32767).astype(np.int16).tobytes())


def build_page():
    shutil.copy(os.path.join(HERE, "node_modules", "gsap", "dist", "gsap.min.js"), os.path.join(OUT, "gsap.min.js"))
    shutil.copy(os.path.join(HERE, "..", "kohli_countdown", "assets", "logo.png"), os.path.join(MEDIA, "logo.png"))
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
    print(f"reel {TOTAL:.1f}s, beats: " + ", ".join(f"{k} {v[0]}-{v[1]}" for k, v in T.items()))

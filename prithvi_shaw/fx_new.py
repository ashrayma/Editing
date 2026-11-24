# New components for the Prithvi Shaw documentary (inserted into gen.py by make_gen.py).
# Looks taken from the two references: cut-out player with a giant word behind him (Shehzad doc), and the
# "creator" look, recoloured to the TheCricketLounge brand (glow counters, a smooth roadmap curve, 3D depth-of-field lists, glass panels).

CYAN, NAVY = "#FEDE5C", "#0b0b0c"   # brand: TheCricketLounge yellow on near-black (CYAN kept as the accent name)


def space(start, dur, z=4, tone="navy"):
    """Deep navy stage with slow-drifting bokeh orbs (the reel's background)."""
    i = nid("sp")
    COVER.append((start, start + dur))
    bg = {"navy": "radial-gradient(120% 90% at 50% 35%,#1d1d20 0%,#0c0c0d 45%,#050506 100%)",
          "red": "radial-gradient(120% 90% at 50% 35%,#5a1418 0%,#2a080b 50%,#0c0203 100%)"}[tone]
    orbs = "".join(f'<div class="orb" id="{i}o{k}" style="left:{x}px;top:{y}px;width:{r}px;height:{r}px"></div>'
                   for k, (x, y, r) in enumerate([(120, 140, 420), (1380, 520, 560), (760, 760, 300)]))
    add(f'<div id="{i}" class="space clip" data-start="{start}" data-duration="{dur}" style="z-index:{z};background:{bg}">{orbs}</div>',
        start, dur, z)
    anim(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.25}},{start})')
    for k in range(3):
        anim(f'tl.fromTo("#{i}o{k}",{{x:0,y:0}},{{x:{(-1) ** k * 120},y:{60 - 40 * k},duration:{dur},ease:"sine.inOut"}},{start})')
    out_(i, start, dur, 0.25)


def glow(text, start, dur, side="center", size=300, label=None, y=None, z=34):
    """Cyan glowing number that rolls in, with a few twinkling sparkles around it."""
    i = num(text, start, dur, side, size, label, CYAN, y, z, cls="glowc")
    j = nid("gs")
    cx = {"left": 140 + size * 0.32 * len(text), "right": W - 140 - size * 0.32 * len(text), "center": W / 2}[side]
    cy = (y if y is not None else H * 0.44 - size * 0.55) + size * 0.5
    dots = "".join(f'<i id="{j}d{k}" style="left:{cx + dx:.0f}px;top:{cy + dy:.0f}px"></i>'
                   for k, (dx, dy) in enumerate([(-size * 0.9, -size * 0.45), (size * 0.85, -size * 0.55), (size * 1.0, size * 0.3),
                                                 (-size * 1.05, size * 0.35), (-size * 0.2, -size * 0.75), (size * 0.3, size * 0.7)]))
    add(f'<div id="{j}" class="spark clip" data-start="{start}" data-duration="{dur}" style="z-index:{z + 1}">{dots}</div>',
        start, dur, z + 1)
    for k in range(6):
        anim(f'tl.fromTo("#{j}d{k}",{{scale:0,opacity:0}},{{scale:1,opacity:1,duration:0.35,yoyo:true,repeat:{int(dur // 0.9)},'
             f'repeatDelay:0.2,ease:"sine.inOut"}},{round(start + 0.3 + k * 0.13, 2)})')
    out_(j, start, dur, 0.3)
    return i


def cutword(png, word, start, dur, side="center", tone="navy", wcolor=None, sub=None, z=40, h=960):
    """Shehzad-doc shot: textured stage, a giant word BEHIND the cut-out player, the player rising in front."""
    i = nid("cw")
    COVER.append((start, start + dur))
    EVENTS.append((start, "boom"))
    w0, h0 = size(png)
    ph = h
    pw = round(w0 * ph / h0)
    if pw > 1500:
        pw = 1500
        ph = round(h0 * pw / w0)
    cx = {"center": W / 2, "left": W * 0.30, "right": W * 0.70}[side]
    bg = {"navy": "radial-gradient(110% 90% at 50% 30%,#26262a 0%,#111113 50%,#050506 100%)",
          "red": "radial-gradient(110% 90% at 50% 30%,#7a1a1f 0%,#3a0a0e 55%,#0d0203 100%)",
          "gold": "radial-gradient(110% 90% at 50% 30%,#6b5214 0%,#2b2006 55%,#0b0802 100%)"}[tone]
    wc = wcolor or {"navy": CYAN, "red": "#ff5a5f", "gold": Y}[tone]
    fs = 430 if len(word) <= 5 else (300 if len(word) <= 9 else 210)
    # with the player off to one side, the word sits on the other side so it reads in full
    walign = {"right": "left:110px;right:auto;text-align:left", "left": "left:auto;right:110px;text-align:right",
              "center": ""}[side]
    subh = f'<div class="cwsub" id="{i}s">{E(sub)}</div>' if sub else ""
    add(f'<div id="{i}" class="cwstage clip" data-start="{start}" data-duration="{dur}" style="z-index:{z};background:{bg}">'
        f'<div class="cwgrain"></div>'
        f'<div class="cwword" id="{i}w" style="font-size:{fs}px;color:{wc};{walign}">{E(word)}</div>'
        f'<img class="cwimg" id="{i}p" src="{use(png)}" style="left:{round(cx - pw / 2)}px;width:{pw}px;height:{ph}px">'
        f'{subh}</div>', start, dur, z)
    anim(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.2}},{start})')
    anim(f'tl.fromTo("#{i}w",{{scale:1.25,opacity:0,letterSpacing:"40px"}},{{scale:1,opacity:0.92,letterSpacing:"6px",duration:0.9,ease:"expo.out"}},{start + 0.05})')
    anim(f'tl.to("#{i}w",{{x:-60,duration:{dur},ease:"none"}},{start})')
    anim(f'tl.fromTo("#{i}p",{{y:160,opacity:0,scale:1.06}},{{y:0,opacity:1,scale:1,duration:0.9,ease:"expo.out"}},{start + 0.15})')
    anim(f'tl.to("#{i}p",{{scale:1.04,duration:{dur},ease:"none"}},{start + 1.0})')
    if sub:
        anim(f'tl.fromTo("#{i}s",{{opacity:0,y:14}},{{opacity:1,y:0,duration:0.5}},{start + 0.7})')
    out_(i, start, dur, 0.25)


# Career curve: (year, label, height 0..1). One device reused at every chapter, drawing a little further each time.
CURVE = [("2013", "546 · HARRIS SHIELD", 0.70), ("2018", "U19 WORLD CUP", 0.80), ("2018", "DEBUT 134", 0.95),
         ("NOV 2018", "ANKLE INJURY", 0.55), ("2019", "SUSPENSION", 0.33), ("2020", "ADELAIDE 0 & 4", 0.12),
         ("2021", "827 · VIJAY HAZARE", 0.58), ("2023", "244 · NORTHANTS", 0.66), ("2023", "CONTROVERSY", 0.40),
         ("2024", "DROPPED · UNSOLD", 0.16), ("2025", "MAHARASHTRA", 0.42)]


def roadmap(upto, start, dur, title=None, z=60):
    """Smooth glowing career curve; reveals left->right up to node `upto` (the turning point we're entering)."""
    i = nid("rm")
    COVER.append((start, start + dur))
    EVENTS.append((start, "swell"))
    x0, x1, yt, yb = 170, W - 170, 250, 840
    pts = [(x0 + (x1 - x0) * k / (len(CURVE) - 1), yb - (yb - yt) * hgt) for k, (_, _, hgt) in enumerate(CURVE)]
    d = f"M{pts[0][0]:.0f},{pts[0][1]:.0f}"
    for k in range(len(pts) - 1):            # Catmull-Rom -> cubic Bezier
        p0, p1, p2, p3 = pts[max(0, k - 1)], pts[k], pts[k + 1], pts[min(len(pts) - 1, k + 2)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{c1[0]:.0f},{c1[1]:.0f} {c2[0]:.0f},{c2[1]:.0f} {p2[0]:.0f},{p2[1]:.0f}"
    prev = pts[max(0, upto - 1)][0] + 6
    cur = pts[upto][0] + 6
    nodes = []
    for k, ((yr, lab, _), (x, y)) in enumerate(zip(CURVE, pts)):
        if k > upto:
            continue
        on = k == upto
        nodes.append(f'<div class="rmnode{" on" if on else ""}" id="{i}n{k}" style="left:{x:.0f}px;top:{y:.0f}px"><b></b>'
                     f'<span class="rml {"up" if y > 520 else "dn"}"><em>{E(yr)}</em>{E(lab)}</span></div>')
    tt = f'<div class="rmtitle" id="{i}t">{E(title)}</div>' if title else ""
    add(f'<div id="{i}" class="space clip" data-start="{start}" data-duration="{dur}" style="z-index:{z};'
        f'background:radial-gradient(120% 90% at 50% 35%,#1d1d20 0%,#0c0c0d 45%,#050506 100%)">'
        f'<svg class="rmsvg" viewBox="0 0 {W} {H}"><defs><clipPath id="{i}c"><rect id="{i}r" x="0" y="0" width="{prev:.0f}" height="{H}"/></clipPath>'
        f'<linearGradient id="{i}g" x1="0" x2="1"><stop offset="0" stop-color="{Y}"/><stop offset="0.35" stop-color="{CYAN}"/>'
        f'<stop offset="0.6" stop-color="#ff5a5f"/><stop offset="1" stop-color="{CYAN}"/></linearGradient></defs>'
        f'<line x1="{x0}" x2="{x1}" y1="{yb + 40}" y2="{yb + 40}" class="rmaxis"/>'
        f'<path d="{d}" class="rmghost"/><path d="{d}" class="rmpath" stroke="url(#{i}g)" clip-path="url(#{i}c)"/></svg>'
        f'{"".join(nodes)}{tt}</div>', start, dur, z)
    anim(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.25}},{start})')
    anim(f'tl.fromTo("#{i}r",{{attr:{{width:{prev:.0f}}}}},{{attr:{{width:{cur:.0f}}},duration:{min(1.4, dur * 0.5):.2f},ease:"power2.inOut"}},{start + 0.2})')
    anim(f'tl.fromTo("#{i}n{upto}",{{scale:0,opacity:0}},{{scale:1,opacity:1,duration:0.5,ease:"back.out(2.5)"}},{round(start + 0.2 + min(1.4, dur * 0.5), 2)})')
    if title:
        anim(f'tl.fromTo("#{i}t",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.6,ease:"expo.out"}},{start + 0.1})')
    out_(i, start, dur, 0.3)


def depthlist(items, start, dur, times, z=36):
    """Reel-style 3D list: tilted in perspective, the active line sharp and glowing, the rest blurred."""
    i = nid("dl")
    rows = "".join(f'<div class="dli" id="{i}i{k}">{E(t)}</div>' for k, t in enumerate(items))
    add(f'<div id="{i}" class="dlist clip" data-start="{start}" data-duration="{dur}" style="z-index:{z}">'
        f'<div class="dlin" id="{i}in">{rows}</div></div>', start, dur, z)
    anim(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.4}},{start})')
    for k in range(len(items)):
        anim(f'tl.set("#{i}i{k}",{{opacity:0.25,filter:"blur(6px)"}},{start})')
    for k, t in enumerate(times):
        EVENTS.append((t, "tick"))
        anim(f'tl.to("#{i}in",{{y:{-k * 118},duration:0.6,ease:"expo.out"}},{t})')
        anim(f'tl.to("#{i}i{k}",{{opacity:1,filter:"blur(0px)",color:"{CYAN}",duration:0.4}},{t})')
        if k:
            anim(f'tl.to("#{i}i{k - 1}",{{opacity:0.35,filter:"blur(5px)",color:"#ffffff",duration:0.4}},{t})')
    out_(i, start, dur, 0.3)


def glass(title, lines, start, dur, side="right", badge=None, z=36, w=820):
    """Floating glass panel (frosted, thin border) with a badge, lines appearing one by one."""
    i = nid("gl")
    x = {"right": W - 140 - w, "left": 140, "center": (W - w) / 2}[side]
    rows = "".join(f'<div class="glr" id="{i}l{k}"><span></span><div>{t}</div></div>' for k, t in enumerate(lines))
    bd = f'<div class="glb">{E(badge)}</div>' if badge else ""
    add(f'<div id="{i}" class="glass clip" data-start="{start}" data-duration="{dur}" style="left:{x:.0f}px;width:{w}px;z-index:{z}">'
        f'{bd}<div class="glt">{E(title)}</div>{rows}</div>', start, dur, z)
    EVENTS.append((start, "whoosh"))
    anim(f'tl.fromTo("#{i}",{{y:80,rotationX:18,opacity:0}},{{y:0,rotationX:0,opacity:1,duration:0.8,ease:"expo.out"}},{start})')
    anim(f'tl.to("#{i}",{{y:-14,duration:{dur},ease:"sine.inOut"}},{start + 0.8})')
    per = min(1.4, max(0.5, (dur - 1.2) / max(1, len(lines))))
    for k in range(len(lines)):
        EVENTS.append((round(start + 0.6 + per * k, 2), "pop"))
        anim(f'tl.fromTo("#{i}l{k}",{{x:-24,opacity:0}},{{x:0,opacity:1,duration:0.5,ease:"expo.out"}},{round(start + 0.6 + per * k, 2)})')
    out_(i, start, dur, 0.35)


def yearcard(year, start, dur, sub=None, kicker=None, z=50):
    """Shehzad-doc year card: black, flickering grain, a big year, a short line under it."""
    i = nid("yc")
    COVER.append((start, start + dur))
    EVENTS.append((start, "flip"))
    k = f'<div class="yck">{E(kicker)}</div>' if kicker else ""
    s = f'<div class="ycs" id="{i}s">{E(sub)}</div>' if sub else ""
    add(f'<div id="{i}" class="ycard clip" data-start="{start}" data-duration="{dur}" style="z-index:{z}">{k}'
        f'<div class="ycy" id="{i}y">{E(year)}</div>{s}</div>', start, dur, z)
    anim(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.15}},{start})')
    anim(f'tl.fromTo("#{i}y",{{scale:1.18,opacity:0,filter:"blur(12px)"}},{{scale:1,opacity:1,filter:"blur(0px)",duration:0.8,ease:"expo.out"}},{start + 0.05})')
    anim(f'tl.to("#{i}y",{{opacity:0.85,duration:0.06,yoyo:true,repeat:{int(dur * 4)}}},{start + 0.9})')
    if sub:
        anim(f'tl.fromTo("#{i}s",{{opacity:0}},{{opacity:1,duration:0.5}},{start + 0.6})')
    out_(i, start, dur, 0.25)


def diverge(start, dur, split_t, z=36):
    """Same start, different journeys: one point that splits into two lines (GILL up, SHAW down)."""
    i = nid("dv")
    add(f'<div id="{i}" class="clip" data-start="{start}" data-duration="{dur}" style="position:absolute;inset:0;z-index:{z}">'
        f'<svg class="rmsvg" viewBox="0 0 {W} {H}"><path id="{i}a" d="M300,560 L760,560" class="dvl" stroke="#fff"/>'
        f'<path id="{i}u" d="M760,560 C1100,560 1250,260 1640,230" class="dvl" stroke="{CYAN}"/>'
        f'<path id="{i}d" d="M760,560 C1100,560 1250,820 1640,860" class="dvl" stroke="#ff5a5f"/></svg>'
        f'<div class="dvt" style="left:300px;top:600px" id="{i}t0">2018 · U19 WORLD CUP</div>'
        f'<div class="dvt big" style="left:1660px;top:190px;color:{CYAN}" id="{i}t1">GILL</div>'
        f'<div class="dvt big" style="left:1660px;top:820px;color:#ff5a5f" id="{i}t2">SHAW</div>'
        f'<div class="dvw" id="{i}w">SAME GENERATION · SAME START · <b>DIFFERENT JOURNEYS</b></div></div>', start, dur, z)
    for p in ("a", "u", "d"):
        anim(f'tl.set("#{i}{p}",{{strokeDasharray:1400,strokeDashoffset:1400}},{start})')
    anim(f'tl.to("#{i}a",{{strokeDashoffset:0,duration:0.8,ease:"power2.out"}},{start + 0.2})')
    anim(f'tl.fromTo("#{i}t0",{{opacity:0}},{{opacity:1,duration:0.4}},{start + 0.4})')
    anim(f'tl.to("#{i}u",{{strokeDashoffset:0,duration:1.2,ease:"power2.inOut"}},{split_t})')
    anim(f'tl.to("#{i}d",{{strokeDashoffset:0,duration:1.2,ease:"power2.inOut"}},{split_t})')
    anim(f'tl.fromTo("#{i}t1",{{opacity:0,x:-20}},{{opacity:1,x:0,duration:0.5}},{split_t + 1.0})')
    anim(f'tl.fromTo("#{i}t2",{{opacity:0,x:-20}},{{opacity:1,x:0,duration:0.5}},{split_t + 1.1})')
    anim(f'tl.fromTo("#{i}w",{{opacity:0,y:16}},{{opacity:1,y:0,duration:0.6}},{split_t + 1.4})')
    EVENTS.append((split_t, "whoosh"))
    out_(i, start, dur, 0.3)


def phoneimg(src, start, dur, side="right", z=24):
    """A screenshot inside a phone frame that slides up into place."""
    i = nid("pi")
    cx = W * (0.70 if side == "right" else 0.30)
    pw, ph = 430, 860
    EVENTS.append((start, "whoosh"))
    add(f'<div id="{i}" class="phoneimg clip" data-start="{start}" data-duration="{dur}" style="left:{cx - pw / 2:.0f}px;'
        f'top:{H * 0.43 - ph / 2:.0f}px;width:{pw}px;height:{ph}px;z-index:{z}"><img src="{use(src)}"></div>', start, dur, z)
    anim(f'tl.fromTo("#{i}",{{y:700,rotation:{6 if side == "right" else -6},opacity:0}},{{y:0,rotation:{2 if side == "right" else -2},opacity:1,duration:0.9,ease:"expo.out"}},{start})')
    out_(i, start, dur, 0.4, "y:300,")

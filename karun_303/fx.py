"""Motion-graphics kit for the Karun 303 long-form (v2): frame styles, in/out animations, word styles, number styles,
transitions. Everything draws onto a 1920x1080 RGBA PIL canvas at a given time; no state between frames.
"""
import math

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

import make_long as L

W, H = L.W, L.H
Y, RED, WHITE, GREY, INK, GREEN = L.Y, L.RED, L.WHITE, L.GREY, L.INK, L.GREEN
ANTON, BLACK, BOLD = L.ANTON, L.BLACK, L.BOLD
font, ease = L.font, L.ease


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def back(x):                      # ease-out-back (overshoot)
    x = clamp(x)
    c = 1.70158
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def bounce(x):
    x = clamp(x)
    if x < 1 / 2.75:
        return 7.5625 * x * x
    if x < 2 / 2.75:
        x -= 1.5 / 2.75
        return 7.5625 * x * x + 0.75
    if x < 2.5 / 2.75:
        x -= 2.25 / 2.75
        return 7.5625 * x * x + 0.9375
    x -= 2.625 / 2.75
    return 7.5625 * x * x + 0.984375


# ============================================================================ element animation

def place(base, im, cx, cy, t, t0, t1, ins="pop", outs="fade", d_in=0.35, d_out=0.25, rot=0.0):
    """Composite element `im` centred at (cx, cy) with an IN style over d_in and an OUT style over d_out."""
    if t < t0 or t > t1:
        return
    p = (t - t0) / d_in
    q = clamp((t - (t1 - d_out)) / d_out) if outs else 0.0
    sc, dx, dy, a, blur, wipe, r = 1.0, 0.0, 0.0, 1.0, 0.0, 1.0, rot
    if ins == "pop":
        sc *= 0.4 + 0.6 * back(p)
        a *= clamp(p * 3)
    elif ins == "slam":
        sc *= 1.6 - 0.6 * ease(p * 1.6)
        a *= clamp(p * 4)
    elif ins == "slide_l":
        dx -= (1 - ease(p)) * 260
        a *= clamp(p * 2)
    elif ins == "slide_r":
        dx += (1 - ease(p)) * 260
        a *= clamp(p * 2)
    elif ins == "rise":
        dy += (1 - ease(p)) * 90
        a *= clamp(p * 2)
    elif ins == "drop":
        dy -= (1 - bounce(p)) * 420
        a *= clamp(p * 4)
    elif ins == "blur":
        blur = 18 * (1 - ease(p))
        sc *= 1.08 - 0.08 * ease(p)
        a *= clamp(p * 1.5)
    elif ins == "wipe":
        wipe = ease(p)
    elif ins == "spin":
        r += (1 - back(p)) * -14
        sc *= 0.6 + 0.4 * back(p)
        a *= clamp(p * 3)
    elif ins == "glitch":
        a *= clamp(p * 3)
    if outs == "fade":
        a *= 1 - q
    elif outs == "zoom":
        sc *= 1 + 0.35 * ease(q)
        a *= 1 - q
    elif outs == "slide":
        dx += ease(q) * 300
        a *= 1 - q
    elif outs == "blur":
        blur += 16 * q
        a *= 1 - q
    elif outs == "drop":
        dy += ease(q) * 300
        a *= 1 - q
    if a <= 0.01:
        return
    e = im
    if wipe < 1:
        e = e.crop((0, 0, max(1, int(e.width * wipe)), e.height))
        cx -= (im.width - e.width) / 2 * (1 if True else 0)
    if r:
        e = e.rotate(r, expand=True, resample=Image.BICUBIC)
    if sc != 1.0:
        e = e.resize((max(1, int(e.width * sc)), max(1, int(e.height * sc))), Image.BILINEAR)
    if blur > 0.5:
        e = e.filter(ImageFilter.GaussianBlur(blur))
    if a < 1:
        e = e.copy()
        e.putalpha(e.getchannel("A").point(lambda v, a=a: int(v * a)))
    if ins == "glitch" and p < 1.2:
        k = int(18 * (1 - clamp(p)))
        if k:
            rr, gg, bb, aa = e.split()
            e = Image.merge("RGBA", (ImageChops.offset(rr, k, 0), gg, ImageChops.offset(bb, -k, 0), aa))
    base.alpha_composite(e, (int(cx + dx - e.width / 2), int(cy + dy - e.height / 2)))


# ============================================================================ word styles

def word_img(txt, size, col=WHITE, path=ANTON, stroke=0, stroke_col=INK):
    f = font(path, size)
    l, t, r, b = f.getbbox(txt)
    pad = 30 + stroke
    im = Image.new("RGBA", (r - l + 2 * pad, b - t + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((pad - l, pad - t), txt, font=f, fill=col, stroke_width=stroke, stroke_fill=stroke_col)
    return im


def shadowed(im, blur=12, k=0.8):
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * k)))
    out = Image.new("RGBA", (im.width + 8, im.height + 10), (0, 0, 0, 0))
    out.alpha_composite(sh, (6, 9))
    out.alpha_composite(im)
    return out


def kinetic(base, t, t0, t1, text, size=120, cy=520, step=0.13, ins="pop", box=True, outs="blur", maxw=1640):
    """Word-by-word pop. Words wrapped in *...* are yellow (with a highlighter box if box=True)."""
    words = text.split()
    imgs = []
    for w_ in words:
        hot = w_.startswith("*") and w_.endswith("*")
        w2 = w_.strip("*")
        if hot and box:
            wi = word_img(w2, size, INK)
            bx = Image.new("RGBA", (wi.width + 6, wi.height - 30), Y + (255,))
            fr = Image.new("RGBA", wi.size, (0, 0, 0, 0))
            fr.alpha_composite(bx, (-3, 18))
            fr.alpha_composite(wi)
            imgs.append(fr)
        else:
            imgs.append(shadowed(word_img(w2, size, Y if hot else WHITE)))
    sp = size * 0.28
    rows, cur, cw = [], [], 0
    for im in imgs:
        if cur and cw + im.width + sp > maxw:
            rows.append(cur)
            cur, cw = [], 0
        cur.append(im)
        cw += im.width + sp
    rows.append(cur)
    lh = size * 1.18
    y0 = cy - (len(rows) - 1) * lh / 2
    k = 0
    for ri, row in enumerate(rows):
        tw = sum(i.width for i in row) + sp * (len(row) - 1) - 60 * len(row)
        x = W / 2 - tw / 2
        for im in row:
            wv = im.width - 60
            place(base, im, x + wv / 2, y0 + ri * lh, t, t0 + k * step, t1, ins, outs, 0.32, 0.22)
            x += wv + sp
            k += 1


def boxline(base, t, t0, t1, text, size=70, cx=W / 2, cy=860, col=Y, fg=INK, ins="wipe"):
    wi = word_img(text, size, fg, BLACK)
    bx = Image.new("RGBA", (wi.width + 30, wi.height - 10), (0, 0, 0, 0))
    ImageDraw.Draw(bx).rounded_rectangle((0, 0, bx.width - 1, bx.height - 1), 14, fill=col + (255,))
    bx.alpha_composite(wi, (15, -5))
    place(base, bx, cx, cy, t, t0, t1, ins, "slide", 0.35, 0.25)


def outline_fill(base, t, t0, t1, text, size=260, cy=500, col=Y):
    """Outline text whose fill rises from the bottom."""
    o = word_img(text, size, (0, 0, 0, 0), ANTON, 4, col)
    f = word_img(text, size, col, ANTON, 4, col)
    p = ease((t - t0 - 0.25) / 0.9)
    h = int(f.height * p)
    comp = o.copy()
    if h > 0:
        comp.alpha_composite(f.crop((0, f.height - h, f.width, f.height)), (0, f.height - h))
    place(base, shadowed(comp, 14, 0.6), W / 2, cy, t, t0, t1, "blur", "zoom", 0.3, 0.25)


def typewriter(base, t, t0, t1, text, size=72, cy=520, col=WHITE, cps=26):
    n = int(clamp((t - t0) * cps / max(1, len(text))) * len(text))
    if t < t0 or t > t1:
        return
    shown = text[:max(1, n)]
    cursor = "|" if int(t * 3) % 2 == 0 or n < len(text) else ""
    im = shadowed(word_img(shown + cursor, size, col, BOLD))
    place(base, im, W / 2, cy, t, t0, t1, "blur", "fade", 0.15, 0.25)


def stack(base, t, t0, t1, rows, cy=520, step=0.3):
    """rows: [(text, size, colour)], each slides in from alternating sides."""
    hs = [s * 1.12 for _, s, _ in rows]
    y = cy - sum(hs) / 2
    for k, (txt, s, c) in enumerate(rows):
        im = shadowed(word_img(txt, s, c))
        place(base, im, W / 2, y + hs[k] / 2, t, t0 + k * step, t1, "slide_l" if k % 2 == 0 else "slide_r", "slide", 0.35, 0.22)
        y += hs[k]


def lower_third(base, t, t0, t1, name, role):
    a = clamp((t - t0) / 0.35)
    q = clamp((t - (t1 - 0.3)) / 0.3)
    if t < t0 or t > t1:
        return
    lay = Image.new("RGBA", (900, 150), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    w1 = int(880 * ease(a) * (1 - ease(q)))
    d.rectangle((0, 0, w1, 84), fill=(14, 14, 18, 235))
    d.rectangle((0, 84, int(w1 * 0.7), 140), fill=Y + (255,))
    d.rectangle((0, 0, 10, 140), fill=Y + (255,))
    if w1 > 200:
        d.text((34, 42), name, font=font(ANTON, 58), fill=WHITE, anchor="lm")
        d.text((34, 113), role, font=font(BOLD, 34), fill=INK, anchor="lm")
    base.alpha_composite(lay, (90, 760))


def quote_card(base, t, t0, t1, who, text, cy=520, ins="rise"):
    f = font(BOLD, 76)
    words, rows, cur = text.split(), [], ""
    for w_ in words:
        if f.getlength(cur + " " + w_) > 1360 and cur:
            rows.append(cur)
            cur = w_
        else:
            cur = (cur + " " + w_).strip()
    rows.append(cur)
    hgt = 104 * len(rows) + 130
    card = Image.new("RGBA", (1600, hgt + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle((0, 0, 1599, hgt + 39), 30, fill=(16, 16, 22, 230), outline=Y + (255,), width=4)
    d.text((44, -14), "“", font=font(ANTON, 190), fill=Y)
    for k, r in enumerate(rows):
        d.text((140, 50 + k * 104), r, font=f, fill=WHITE)
    d.text((140, 66 + len(rows) * 104), "— " + who, font=font(BOLD, 48), fill=Y)
    place(base, shadowed(card, 20, 0.7), W / 2, cy, t, t0, t1, ins, "zoom", 0.4, 0.25)


def stamp(base, t, t0, t1, word, cx=W / 2, cy=540, color=RED, angle=-8, size=150):
    f = font(BLACK, size)
    l, tt, r, b = f.getbbox(word)
    im = Image.new("RGBA", (r - l + 90, b - tt + 80), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((7, 7, im.width - 8, im.height - 8), outline=color + (255,), width=14)
    d.text((45 - l, 40 - tt), word, font=f, fill=color + (255,))
    al = np.asarray(im.getchannel("A"), np.float32) * np.where(
        np.random.default_rng(len(word)).random((im.height, im.width)) > 0.88, 0.35, 1)
    im.putalpha(Image.fromarray(al.astype(np.uint8)))
    place(base, im, cx, cy, t, t0, t1, "slam", "fade", 0.12, 0.2, angle)


# ============================================================================ number styles

def count_up(base, t, t0, t1, value, sub=None, size=300, cy=470, col=Y, dur=1.0, prefix="", suffix="", fmt=","):
    if t < t0 or t > t1:
        return
    p = ease((t - t0) / dur)
    v = value * p
    s = (f"{v:,.0f}" if fmt == "," else f"{v:.{fmt}f}") if isinstance(value, (int, float)) else str(value)
    im = shadowed(word_img(prefix + s + suffix, size, col))
    place(base, im, W / 2, cy, t, t0, t1, "pop", "zoom", 0.3, 0.25)
    if sub:
        place(base, shadowed(word_img(sub, 58, WHITE, BOLD)), W / 2, cy + size * 0.62, t, t0 + 0.4, t1, "rise", "fade")


def odometer(base, t, t0, t1, text, size=280, cy=470, col=Y, sub=None):
    """Each digit rolls up through 0-9 into place, staggered."""
    if t < t0 or t > t1:
        return
    f = font(ANTON, size)
    cw = [f.getlength(c) for c in text]
    x = W / 2 - sum(cw) / 2
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for k, c in enumerate(text):
        p = ease((t - t0 - 0.08 * k) / 0.75)
        if c.isdigit():
            target = int(c)
            roll = (1 - p) * (10 + target)
            d0 = int(target - roll) % 10
            frac = (target - roll) - math.floor(target - roll)
            cell = Image.new("RGBA", (int(cw[k]) + 4, int(size * 1.25)), (0, 0, 0, 0))
            dd = ImageDraw.Draw(cell)
            for j, dv in enumerate([d0, (d0 + 1) % 10]):
                dd.text((2, -frac * size * 1.05 + j * size * 1.05 + size * 0.05), str(dv), font=f, fill=col)
            lay.alpha_composite(cell, (int(x), int(cy - size * 0.6)))
        else:
            ImageDraw.Draw(lay).text((x, cy - size * 0.55), c, font=f, fill=col)
        x += cw[k]
    a = clamp((t - t0) / 0.2) * (1 - clamp((t - (t1 - 0.25)) / 0.25))
    lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
    base.alpha_composite(shadowed(lay, 14, 0.7).crop((0, 0, W, H)))
    if sub:
        place(base, shadowed(word_img(sub, 56, WHITE, BOLD)), W / 2, cy + size * 0.75, t, t0 + 0.6, t1, "rise", "fade")


def flip_board(base, t, t0, t1, text, cy=470, sub=None, cell=(150, 210)):
    """Scoreboard flip tiles; each tile flips in turn."""
    if t < t0 or t > t1:
        return
    n = len(text)
    gap = 14
    x0 = W / 2 - (n * cell[0] + (n - 1) * gap) / 2
    f = font(ANTON, int(cell[1] * 0.78))
    a = 1 - clamp((t - (t1 - 0.25)) / 0.25)
    for k, c in enumerate(text):
        p = clamp((t - t0 - 0.09 * k) / 0.32)
        if p <= 0:
            continue
        tile = Image.new("RGBA", cell, (0, 0, 0, 0))
        d = ImageDraw.Draw(tile)
        d.rounded_rectangle((0, 0, cell[0] - 1, cell[1] - 1), 12, fill=(22, 22, 28, int(245 * a)))
        d.line((0, cell[1] / 2, cell[0], cell[1] / 2), fill=(0, 0, 0, int(200 * a)), width=3)
        d.text((cell[0] / 2, cell[1] / 2), c, font=f, fill=Y + (int(255 * a),), anchor="mm")
        hh = max(2, int(cell[1] * abs(math.cos(math.pi * (1 - p) / 2))))
        tile = tile.resize((cell[0], hh), Image.BILINEAR)
        base.alpha_composite(tile, (int(x0 + k * (cell[0] + gap)), int(cy - hh / 2)))
    if sub:
        place(base, shadowed(word_img(sub, 54, WHITE, BOLD)), W / 2, cy + cell[1] * 0.85, t, t0 + 0.5, t1, "rise", "fade")


def bars(base, t, t0, t1, vals, labels, hot=None, title=None, maxv=None, cy=600, hmax=560, bw=150, gap=60, col=WHITE):
    """Bar chart that grows bar by bar; `hot` index in yellow (the 303 spike)."""
    if t < t0 or t > t1:
        return
    n = len(vals)
    maxv = maxv or max(vals)
    x0 = W / 2 - (n * bw + (n - 1) * gap) / 2
    a = 1 - clamp((t - (t1 - 0.3)) / 0.3)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    base_y = cy + hmax / 2
    d.line((x0 - 40, base_y, x0 + n * (bw + gap), base_y), fill=(120, 122, 132, int(255 * a)), width=3)
    for k, v in enumerate(vals):
        p = ease((t - t0 - 0.12 * k) / 0.6)
        if p <= 0:
            continue
        h = max(4, hmax * v / maxv * p)
        x = x0 + k * (bw + gap)
        c = Y if k == hot else col
        d.rectangle((x, base_y - h, x + bw, base_y), fill=c + (int(235 * a),))
        d.text((x + bw / 2, base_y - h - 40), f"{int(v * p)}", font=font(ANTON, 60), fill=c + (int(255 * a),), anchor="mm")
        d.text((x + bw / 2, base_y + 40), labels[k], font=font(BOLD, 30), fill=GREY + (int(255 * a),), anchor="mm")
    base.alpha_composite(lay)
    if title:
        place(base, shadowed(word_img(title, 64, Y, BOLD)), W / 2, 170, t, t0, t1, "slide_l", "fade")


def ticker_pop(base, t, t0, t1, vals, label=None, cy=500, col=WHITE, last=None):
    n = len(vals)
    gapx = 240 if n < 6 else 190
    x0 = W / 2 - (n - 1) * gapx / 2
    for k, v in enumerate(vals):
        c = last if (last and k == n - 1) else col
        place(base, shadowed(word_img(str(v), 170 if n < 6 else 140, c)), x0 + k * gapx, cy, t, t0 + 0.28 * k, t1, "drop", "fade", 0.45)
    if label:
        boxline(base, t, t0 + 0.28 * n, t1, label, 60, W / 2, cy + 170)


# ============================================================================ frame styles (backgrounds) -> float RGB array

def _push(im, lt, dur, z0=1.04, z1=1.16, f=(0.5, 0.35), f2=None):
    f2 = f2 or f
    k = ease(lt / dur)
    return L.cover(im, z0 + (z1 - z0) * lt / dur, f[0] + (f2[0] - f[0]) * k, f[1] + (f2[1] - f[1]) * k)


def blurred_bg(im, dark=0.38):
    return Image.fromarray((np.asarray(L.cover(im, 1.0, 0.5, 0.5).filter(ImageFilter.GaussianBlur(26)), np.float32) * dark).astype(np.uint8))


def fs_full(src, lt, dur, **k):
    return L.grade(_push(src, lt, dur, **{x: k[x] for x in ("z0", "z1", "f", "f2") if x in k}), k.get("gray", 0), k.get("dark", 1))


def fs_polaroid(src, lt, dur, tilt=-4, **k):
    base = blurred_bg(src).convert("RGBA")
    pw = 1000
    ph = int(pw * 0.72)
    pic = L.cover(src, 1.06 + 0.06 * lt / dur, 0.5, k.get("fy", 0.35), pw, ph)
    card = Image.new("RGBA", (pw + 50, ph + 140), (246, 244, 238, 255))
    card.paste(pic, (25, 25))
    if k.get("label"):
        ImageDraw.Draw(card).text((card.width / 2, ph + 82), k["label"], font=font(BOLD, 44), fill=(40, 40, 46), anchor="mm")
    p = ease(lt / 0.5)
    rot = tilt * (0.4 + 0.6 * p)
    c = card.rotate(rot, expand=True, resample=Image.BICUBIC)
    sh = Image.new("RGBA", c.size, (0, 0, 0, 0))
    sh.putalpha(c.getchannel("A").filter(ImageFilter.GaussianBlur(22)).point(lambda v: int(v * 0.7)))
    dy = int((1 - p) * 160)
    base.alpha_composite(sh, ((W - c.width) // 2 + 14, (H - c.height) // 2 + 20 + dy))
    base.alpha_composite(c, ((W - c.width) // 2, (H - c.height) // 2 + dy))
    return np.asarray(base.convert("RGB"), np.float32) * L.VIG


def fs_card(src, lt, dur, **k):
    base = Image.fromarray(L.plate(lt * 3 + 7).astype(np.uint8)).convert("RGBA")
    cw, ch = 1480, 832
    p = ease(lt / 0.45)
    s = 0.86 + 0.14 * p + 0.03 * lt / dur
    pic = L.cover(src, 1.05 + 0.05 * lt / dur, k.get("fx", 0.5), k.get("fy", 0.4), cw, ch).convert("RGBA")
    m = Image.new("L", (cw, ch), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, cw - 1, ch - 1), 36, fill=255)
    pic.putalpha(m)
    fr = Image.new("RGBA", (cw + 12, ch + 12), (0, 0, 0, 0))
    ImageDraw.Draw(fr).rounded_rectangle((0, 0, cw + 11, ch + 11), 40, fill=Y + (255,))
    fr.alpha_composite(pic, (6, 6))
    fr = fr.resize((int(fr.width * s), int(fr.height * s)), Image.BILINEAR)
    base.alpha_composite(fr, ((W - fr.width) // 2, (H - fr.height) // 2))
    return np.asarray(base.convert("RGB"), np.float32)


def fs_split(srcs, lt, dur, labels=None, **k):
    base = Image.new("RGB", (W, H), INK)
    n = len(srcs)
    pw = W // n
    for i, s in enumerate(srcs):
        p = ease((lt - 0.12 * i) / 0.45)
        pane = L.cover(s, 1.06 + 0.06 * lt / dur, 0.5, 0.35, pw, H)
        g = Image.fromarray(np.clip(L.grade(pane.resize((W, H)), 0.0, 0.95), 0, 255).astype(np.uint8)).resize((pw, H))
        y = int((1 - p) * (H if i % 2 == 0 else -H))
        base.paste(g, (i * pw, y))
    d = ImageDraw.Draw(base)
    for i in range(1, n):
        hh = int(H * ease(lt / 0.5))
        d.rectangle((i * pw - 4, 0, i * pw + 4, hh), fill=Y)
    out = base.convert("RGBA")
    if labels:
        for i, lab in enumerate(labels):
            if lab:
                place(out, shadowed(word_img(lab, 90, Y if i else WHITE)), i * pw + pw / 2, 840, lt, 0.35 + 0.15 * i, dur + 9, "rise", None)
    return np.asarray(out.convert("RGB"), np.float32)


def fs_circle(src, lt, dur, **k):
    base = Image.fromarray(L.plate(lt * 2 + 3).astype(np.uint8)).convert("RGBA")
    r = 360
    p = back(lt / 0.5)
    rr = max(10, int(r * p))
    pic = L.cover(src, 1.0 + 0.08 * lt / dur, k.get("fx", 0.5), k.get("fy", 0.3), 2 * rr, 2 * rr).convert("RGBA")
    m = Image.new("L", (2 * rr, 2 * rr), 0)
    ImageDraw.Draw(m).ellipse((0, 0, 2 * rr - 1, 2 * rr - 1), fill=255)
    pic.putalpha(m)
    cx, cy = k.get("cx", W / 2), 520
    base.alpha_composite(pic, (int(cx - rr), int(cy - rr)))
    ring = Image.new("RGBA", (2 * r + 60, 2 * r + 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(ring)
    a0 = (lt * 90) % 360
    d.arc((10, 10, 2 * r + 50, 2 * r + 50), a0, a0 + 260 * ease(lt / 0.7), fill=Y, width=10)
    base.alpha_composite(ring, (int(cx - r - 30), int(cy - r - 30)))
    return np.asarray(base.convert("RGB"), np.float32)


def fs_film(srcs, lt, dur, **k):
    """Film strip scrolling left with several frames."""
    base = Image.new("RGBA", (W, H), (8, 8, 10, 255))
    fh, fw = 560, 760
    strip = Image.new("RGBA", ((fw + 40) * len(srcs) + 40, fh + 160), (20, 20, 22, 255))
    d = ImageDraw.Draw(strip)
    for x in range(0, strip.width, 46):
        d.rounded_rectangle((x + 8, 22, x + 32, 50), 4, fill=(230, 230, 230, 255))
        d.rounded_rectangle((x + 8, strip.height - 50, x + 32, strip.height - 22), 4, fill=(230, 230, 230, 255))
    for i, s in enumerate(srcs):
        g = Image.fromarray(np.clip(L.grade(L.cover(s, 1.05, 0.5, 0.35).resize((W, H)), 0.15), 0, 255).astype(np.uint8))
        strip.paste(g.resize((fw, fh)), (40 + i * (fw + 40), 80))
    x = int(W * 0.05 - (strip.width - W) * clamp(lt / dur))
    base.alpha_composite(strip.rotate(-3, expand=True, resample=Image.BICUBIC), (x, (H - strip.height) // 2 - 40))
    return np.asarray(base.convert("RGB"), np.float32) * L.VIG


def fs_cutout(name, src, lt, dur, word="303", col=Y, size=640, tx=None, **k):
    """Blurred backdrop, giant word BEHIND the subject cutout, subject slowly scales."""
    import os
    cutp = os.path.join(L.HERE, "cut", name + ".png")
    base = blurred_bg(src, 0.42).convert("RGBA")
    wd = word_img(word, size, col)
    p = ease(lt / 0.6)
    place(base, wd, W * (tx if tx is not None else 0.5), 470 + 80 * (1 - p), lt, 0, dur + 9, "blur", None, 0.6)
    if os.path.exists(cutp):
        cut = Image.open(cutp).convert("RGBA")
        s = (H * 0.98) / cut.height * (1.0 + 0.04 * lt / dur)
        c2 = cut.resize((int(cut.width * s), int(cut.height * s)), Image.BILINEAR)
        base.alpha_composite(c2, (int(W * k.get("x", 0.5) - c2.width / 2), H - c2.height + int(40 * (1 - p))))
    return np.asarray(base.convert("RGB"), np.float32) * L.VIG


def fs_tv(src, lt, dur, tag="REPLAY", **k):
    """Broadcast replay frame: inset picture, REPLAY tag, scan lines."""
    base = Image.fromarray(L.plate(lt + 11).astype(np.uint8)).convert("RGBA")
    pw, ph = 1560, 878
    pic = Image.fromarray(np.clip(L.grade(L.cover(src, 1.05 + 0.05 * lt / dur, 0.5, k.get("fy", 0.4)).resize((W, H))), 0, 255).astype(np.uint8)).resize((pw, ph))
    sc = np.asarray(pic, np.float32)
    sc[::4] *= 0.86
    pic = Image.fromarray(sc.astype(np.uint8)).convert("RGBA")
    base.alpha_composite(pic, ((W - pw) // 2, (H - ph) // 2))
    d = ImageDraw.Draw(base)
    x0, y0 = (W - pw) // 2, (H - ph) // 2
    d.rectangle((x0, y0, x0 + pw, y0 + ph), outline=(200, 200, 205), width=3)
    if int(lt * 2) % 2 == 0:
        d.ellipse((x0 + 34, y0 + 34, x0 + 58, y0 + 58), fill=RED)
    d.rounded_rectangle((x0 + 70, y0 + 26, x0 + 70 + 230, y0 + 68), 8, fill=(14, 14, 18))
    d.text((x0 + 185, y0 + 47), tag, font=font(BLACK, 30), fill=WHITE, anchor="mm")
    return np.asarray(base.convert("RGB"), np.float32)


# ============================================================================ transitions (applied to the frame array at a cut)

def transition(a, kind, lt, prev=None):
    d = 0.28
    if lt >= d or kind in (None, "none"):
        return a
    p = lt / d
    if kind == "flash":
        return a + 255 * 0.65 * (1 - p)
    if kind == "zoom":
        im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
        s = 1 + 0.18 * (1 - ease(p))
        big = im.resize((int(W * s), int(H * s)), Image.BILINEAR)
        ox, oy = (big.width - W) // 2, (big.height - H) // 2
        im = big.crop((ox, oy, ox + W, oy + H)).filter(ImageFilter.GaussianBlur(10 * (1 - p)))
        return np.asarray(im, np.float32)
    if kind == "whip":
        im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
        shift = int((1 - ease(p)) * 520)
        im = ImageChops.offset(im, shift, 0)
        blur = im.filter(ImageFilter.BoxBlur(int(28 * (1 - p)) + 1))
        return np.asarray(blur, np.float32)
    if kind == "glitch":
        out = a.copy()
        rng = np.random.default_rng(int(lt * 1000))
        for _ in range(8):
            y = rng.integers(0, H - 60)
            h = rng.integers(10, 60)
            out[y:y + h] = np.roll(out[y:y + h], rng.integers(-120, 120), axis=1)
        out[..., 0] = np.roll(out[..., 0], 12, axis=1)
        out[..., 2] = np.roll(out[..., 2], -12, axis=1)
        return out
    if kind == "black":
        return a * ease(p)
    return a


def shake(base_arr, t, t_hit, amp=14):
    k = t - t_hit
    if not (0 <= k < 0.35):
        return base_arr
    s = amp * (1 - k / 0.35)
    dx, dy = int(s * math.sin(k * 90)), int(s * math.cos(k * 70))
    return np.roll(np.roll(base_arr, dx, axis=1), dy, axis=0)

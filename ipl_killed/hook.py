#!/usr/bin/env python3
"""Cold-open hook for "IPL Ko Kisne Maara?" (~14 s), joined in front of the finished video.

VO (vo/hook_raw.mp3): "17 November, retention lists out. Crores ki deals, bade naam release... par ek sawal koi
nahi pooch raha: kya IPL dheere dheere mar raha hai?"

    python3 hook.py          ->  out/hook.mp4, then out/IPL_Ko_Kisne_Maara_hook.mp4 (+ _upload.mp4, 5 Mbit/s)
    python3 hook.py --sheet  ->  out/chk/hook_sheet.jpg (contact sheet only)

Same look as the main video (moving case-file plate, Anton, brand yellow). No photos, so nothing repeats; no real
player is named or shown as released.
"""
import math
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv, _args = sys.argv[:1], sys.argv[1:]
import make_ipl as m  # noqa: E402  (plate, fonts, text helpers, sfx kit)

W, H, FPS = m.W, m.H, m.FPS
Y, RED, WHITE, GREY, INK = m.Y, m.RED, m.WHITE, m.GREY, m.INK
GREEN = (60, 200, 110)
SR = 48000
OFF = 0.35  # VO starts here
# phrase starts / ends in hook time (silencedetect on vo/hook_raw.mp3 + OFF)
A, B, C1, C2, D, E = 0.35, 1.86, 4.14, 5.44, 7.31, 9.97
E_END = 12.85
FLAT = 12.95
DUR = 14.1
BEATS = [10.05, 10.75, 11.55, 12.45]       # heartbeat, slowing
STAMP_AT = 6.15                            # "...release"
ease = m.ease


def ein(t, t0, d=0.25):
    return ease((t - t0) / d)


def eout(t, t1, d=0.25):
    return 1 - ease((t - (t1 - d)) / d)


# ----------------------------------------------------------------------------- graphics

def calendar():
    im = Image.new("RGBA", (460, 520), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 20, 450, 510), 34, fill=(246, 244, 238, 255))
    d.rounded_rectangle((10, 20, 450, 150), 34, fill=RED + (255,))
    d.rectangle((10, 110, 450, 150), fill=RED + (255,))
    for x in (120, 340):
        d.rounded_rectangle((x - 14, 0, x + 14, 60), 10, fill=(60, 62, 70, 255))
    d.text((230, 88), "NOVEMBER", font=m.font(m.ANTON, 70), fill=WHITE, anchor="mm")
    d.text((230, 330), "17", font=m.font(m.ANTON, 300), fill=INK, anchor="mm")
    sh = Image.new("RGBA", (560, 620), (0, 0, 0, 0))
    sh.alpha_composite(im, (50, 50))
    blur = Image.new("RGBA", sh.size, (0, 0, 0, 0))
    blur.putalpha(sh.getchannel("A").filter(ImageFilter.GaussianBlur(22)).point(lambda v: v * 0.7))
    out = Image.new("RGBA", sh.size, (0, 0, 0, 0))
    out.alpha_composite(blur, (10, 16))
    out.alpha_composite(sh)
    return out


CAL = calendar()
ROWS = [(RED, 0.62, True), ((40, 110, 220), 0.48, False), (Y, 0.70, True), ((120, 60, 190), 0.55, False),
        ((240, 130, 40), 0.40, True), ((20, 160, 160), 0.66, False)]


def tag(word, col):
    f = m.font(m.BLACK_F, 34)
    w = int(f.getlength(word)) + 44
    im = Image.new("RGBA", (w, 58), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, 57), 12, fill=col + (255,))
    d.text((w / 2, 30), word, font=f, fill=INK if col != RED else WHITE, anchor="mm")
    return im


TAG_IN, TAG_OUT = tag("RETAINED", GREEN), tag("RELEASED", RED)


def list_panel(t):
    """Retention list: rows tick in, names redacted (we don't know the lists yet)."""
    pw, ph = 980, 640
    im = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, pw - 1, ph - 1), 28, fill=(18, 20, 28, 236), outline=Y + (255,), width=3)
    d.text((44, 52), "RETENTION LISTS", font=m.font(m.ANTON, 64), fill=Y, anchor="lm")
    d.text((pw - 44, 54), "17 NOV", font=m.font(m.ANTON, 44), fill=GREY, anchor="rm")
    d.line((40, 100, pw - 40, 100), fill=(60, 62, 72), width=2)
    for k, (col, frac, kept) in enumerate(ROWS):
        t0 = B + 0.05 + k * 0.26
        a = ein(t, t0, 0.18)
        if a <= 0:
            continue
        y = 130 + k * 82
        x = 44 + int((1 - a) * 60)
        row = Image.new("RGBA", (pw, 70), (0, 0, 0, 0))
        r = ImageDraw.Draw(row)
        r.ellipse((x, 14, x + 40, 54), fill=col + (255,))
        r.rounded_rectangle((x + 66, 20, x + 66 + int(520 * frac), 50), 10, fill=(92, 96, 110, 255))
        r.rounded_rectangle((x + 66, 20, x + 66 + int(520 * frac * 0.35), 50), 10, fill=(130, 134, 150, 255))
        row.alpha_composite(TAG_IN if kept else TAG_OUT, (pw - 44 - (TAG_IN if kept else TAG_OUT).width, 6))
        im.alpha_composite(m.fade(row, a), (0, y))
    return im


def counter(t):
    """Spinning crore counter (never lands: the money keeps moving)."""
    im = Image.new("RGBA", (1300, 420), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((650, 60), "CRORES ON THE TABLE", font=m.font(m.ANTON, 64), fill=GREY, anchor="mm")
    f = m.font(m.ANTON, 230)
    k = int((t - C1) * 40)
    digits = [(k * 7 + 3) % 10, (k * 3 + 1) % 10, (k * 11 + 5) % 10]
    s = "".join(str(v) for v in digits)
    d.text((300, 262), "₹", font=m.font(m.BLACK_F, 190), fill=Y, anchor="mm")  # Anton has no rupee sign
    d.text((600, 250), s, font=f, fill=Y, anchor="mm", stroke_width=4, stroke_fill=INK)
    d.text((960, 262), "CR", font=m.font(m.ANTON, 150), fill=WHITE, anchor="mm")
    return im


def silhouette():
    im = Image.new("RGBA", (440, 560), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, 439, 559), 30, fill=(24, 26, 36, 255), outline=Y + (255,), width=4)
    d.ellipse((150, 90, 290, 250), fill=(70, 74, 88, 255))                    # head
    d.rounded_rectangle((70, 260, 370, 560), 120, fill=(70, 74, 88, 255))     # shoulders
    d.rectangle((70, 480, 370, 556), fill=(70, 74, 88, 255))
    d.text((220, 170), "?", font=m.font(m.ANTON, 120), fill=Y, anchor="mm")
    d.text((220, 400), "BIG NAME", font=m.font(m.ANTON, 54), fill=(150, 154, 168), anchor="mm")
    return im


SIL = silhouette()


def stamp_img(word="RELEASED", size=120):
    f = m.font(m.BLACK_F, size)
    l, tt, r, b = f.getbbox(word)
    im = Image.new("RGBA", (r - l + 70, b - tt + 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((5, 5, im.width - 6, im.height - 6), outline=RED + (255,), width=10)
    d.text((35 - l, 30 - tt), word, font=f, fill=RED + (255,))
    a = np.asarray(im.getchannel("A"), np.float32)
    a = a * np.where(np.random.default_rng(7).random(a.shape) > 0.88, 0.3, 1.0)
    im.putalpha(Image.fromarray(a.astype(np.uint8)))
    return im.rotate(-10, expand=True, resample=Image.BICUBIC)


STAMP = stamp_img()


def ticker_strip(base, t, a):
    if a <= 0:
        return
    strip = Image.new("RGBA", (W, 74), (0, 0, 0, 0))
    d = ImageDraw.Draw(strip)
    d.rectangle((0, 0, W, 74), fill=(14, 15, 20, 240))
    msg = "IPL RETENTION LISTS  ·  17 NOVEMBER  ·  CRORES ON THE TABLE  ·  BIG NAMES RELEASED  ·  "
    f = m.font(m.ANTON, 42)
    lw = f.getlength(msg)
    x = -((t * 180) % lw)
    while x < W:
        d.text((x + 300, 38), msg, font=f, fill=WHITE, anchor="lm")
        x += lw
    d.rectangle((0, 0, 270, 74), fill=RED)
    d.text((135, 38), "BREAKING", font=m.font(m.ANTON, 46), fill=WHITE, anchor="mm")
    d.line((0, 0, W, 0), fill=Y, width=3)
    base.alpha_composite(m.fade(strip, a), (0, H - 74 - 40))


def ecg(base, t):
    """Heart monitor: sweep left to right, beats getting slower and weaker, then flat."""
    if t < E - 0.4:
        return
    a_in = ein(t, E - 0.4, 0.4)
    x0, x1, base_y = 120, W - 120, 700
    span = FLAT - (E - 0.3)
    pos = lambda tt: x0 + (x1 - x0) * min(max((tt - (E - 0.3)) / span, 0), 1)  # noqa: E731
    cur = pos(t)
    pts = []
    xs = np.arange(x0, int(cur) + 1, 3)
    amps = [1.0, 0.75, 0.5, 0.28]
    for x in xs:
        y = 0.0
        for tb, amp in zip(BEATS, amps):
            xb = pos(tb)
            u = (x - xb) / 14.0
            y += amp * (-0.15 * math.exp(-((u + 3.5) ** 2)) - 1.0 * math.exp(-((u) ** 2) * 3)
                        + 0.45 * math.exp(-((u - 1.0) ** 2) * 3) - 0.12 * math.exp(-((u - 5) ** 2) / 4))
        pts.append((x, base_y + y * 230))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for gx in range(x0, x1 + 1, 60):
        d.line((gx, 470, gx, 930), fill=(40, 90, 60, 60), width=1)
    for gy in range(470, 931, 60):
        d.line((x0, gy, x1, gy), fill=(40, 90, 60, 60), width=1)
    col = (110, 255, 150) if t < FLAT else RED
    if len(pts) > 1:
        d.line(pts, fill=col + (255,), width=6, joint="curve")
    if t >= FLAT - 0.05:
        d.line((pts[-1][0] if pts else x0, base_y, x1, base_y), fill=RED + (255,), width=6)
    glow = lay.filter(ImageFilter.GaussianBlur(10))
    base.alpha_composite(m.fade(glow, a_in))
    base.alpha_composite(m.fade(lay, a_in))
    if t < FLAT:
        d2 = ImageDraw.Draw(base)
        d2.ellipse((cur - 10, pts[-1][1] - 10, cur + 10, pts[-1][1] + 10), fill=(220, 255, 230))
    # BPM readout
    bpm = 0 if t >= FLAT else int(np.interp(t, [E, BEATS[1], BEATS[2], BEATS[3]], [74, 62, 47, 31]))
    blink = t < FLAT or int(t * 4) % 2 == 0
    if blink:
        dd = ImageDraw.Draw(base)
        dd.text((W - 150, 410), "BPM", font=m.font(m.ANTON, 40), fill=GREY, anchor="rm")
        dd.text((W - 130, 412), str(bpm), font=m.font(m.ANTON, 76), fill=(110, 255, 150) if bpm else RED,
                anchor="lm")


def headline(base, t):
    """IS IPL DYING? above the monitor."""
    if t < E + 0.35:
        return
    im = m.text_img([("IS IPL", WHITE), ("DYING?", RED)], 150)
    a = ein(t, E + 0.35, 0.3)
    s = 1 + 0.25 * (1 - ein(t, E + 0.35, 0.25))
    im2 = m.text_img([("IS IPL ", WHITE)], 160)
    im3 = m.text_img([("DYING?", RED)], 160)
    w = im2.width + im3.width - 60
    cx = W / 2
    m.paste_center(base, im2, cx - w / 2 + im2.width / 2, 300, s, a)
    a3 = ein(t, E + 1.2, 0.2)
    m.paste_center(base, im3, cx + w / 2 - im3.width / 2, 300, 1 + 0.4 * (1 - ein(t, E + 1.2, 0.18)), a3)
    del im


def frame(t):
    # background: the main video's moving plate, darker during the silence
    bg = m.plate(t)
    dark = 1.0
    if t > D - 0.2:
        dark = 1 - 0.45 * ein(t, D - 0.2, 0.6)
    base = Image.fromarray(np.clip(bg * dark, 0, 255).astype(np.uint8)).convert("RGBA")

    # 1) calendar slams in, then parks top-left while the list ticks in
    if t < C1 + 0.2:
        k_in = ein(t, A - 0.1, 0.28)
        park = ein(t, B - 0.1, 0.45)
        s = (1.6 - 0.6 * k_in) * (1 - 0.48 * park)
        cx = W / 2 + (330 - W / 2) * park
        cy = H / 2 - 30 + (330 - (H / 2 - 30)) * park
        m.paste_center(base, CAL, cx, cy, s, k_in * eout(t, C1 + 0.2, 0.3))
        if t < B:
            chip = m.text_img([("RETENTION DAY", Y)], 70)
            m.paste_center(base, chip, W / 2, 900, 1, ein(t, A + 0.6, 0.25) * eout(t, B, 0.2))
    if B - 0.1 < t < C1 + 0.25:
        p = list_panel(t)
        m.paste_center(base, p, 1170, 500, 1, ein(t, B - 0.1, 0.3) * eout(t, C1 + 0.25, 0.3))
    ticker_strip(base, t, ein(t, A + 0.2, 0.3) * eout(t, D, 0.35))

    # 2) crore counter
    if C1 - 0.1 < t < C2 + 0.15:
        a = ein(t, C1 - 0.1, 0.2) * eout(t, C2 + 0.15, 0.2)
        m.paste_center(base, counter(t), W / 2, 470, 1 + 0.05 * (t - C1), a)

    # 3) big name -> RELEASED
    if C2 - 0.1 < t < D + 0.1:
        a = ein(t, C2 - 0.1, 0.25) * eout(t, D + 0.1, 0.35)
        sh = 6 * math.exp(-max(0, t - STAMP_AT) * 14) * math.sin(t * 90) if t > STAMP_AT else 0
        m.paste_center(base, SIL, W / 2 + sh, 470, 0.98 + 0.04 * (t - C2), a)
        if t > STAMP_AT:
            k = t - STAMP_AT
            m.paste_center(base, STAMP, W / 2 + sh, 520, 1 + 1.0 * (1 - ease(k / 0.12)), ease(k / 0.05) * a)

    # 4) the question nobody asks (typewriter, quiet)
    if D + 0.15 < t < E + 0.1:
        line = "THE QUESTION NOBODY IS ASKING..."
        n = int(len(line) * min(1, (t - D - 0.15) / 1.3))
        im = m.text_img([(line[:max(1, n)], (200, 202, 210))], 76)
        m.paste_center(base, im, W / 2, H / 2, 1 + 0.03 * (t - D), eout(t, E + 0.1, 0.3))

    # 5) heart monitor + IS IPL DYING?
    ecg(base, t)
    headline(base, t)

    out = base.convert("RGB")
    if t > DUR - 0.45:  # dip to black into the main video
        out = Image.fromarray((np.asarray(out, np.float32) * max(0, (DUR - t) / 0.45)).astype(np.uint8))
    return out


# ----------------------------------------------------------------------------- sound

def at(buf, x, t, g):
    i = int(t * SR)
    if i >= len(buf):
        return
    n = min(len(x), len(buf) - i)
    buf[i:i + n] += x[:n] * g


def rs(x, sr=44100):
    """kohli_countdown sfx kit runs at 44.1 kHz."""
    n = int(len(x) * SR / sr)
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x)


def beep(dur=0.11, f=1000.0):
    t = np.arange(int(SR * dur)) / SR
    return np.sin(2 * np.pi * f * t) * np.minimum(1, (dur - t) / 0.02) * np.minimum(1, t / 0.004)


def load_vo():
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(HERE, "vo", "hook_raw.mp3"), "-ac", "1",
                          "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def soundtrack(path):
    import sfx
    from virat_hook import braam, drone
    n = int(DUR * SR)
    bed = np.zeros(n)
    dr = rs(drone(DUR + 0.5))[:n]
    lvl = np.interp(np.arange(n) / SR, [0, D - 0.2, D + 0.3, E, FLAT, DUR], [0.30, 0.34, 0.07, 0.10, 0.12, 0.0])
    bed[: len(dr)] += dr * lvl[: len(dr)]
    fx = np.zeros(n)
    at(fx, rs(sfx.whoosh()), A - 0.3, 0.35)
    at(fx, rs(sfx.impact()), A - 0.05, 0.55)
    for k in range(len(ROWS)):
        at(fx, rs(sfx.pop()), B + 0.05 + k * 0.26, 0.28)
    t = C1
    while t < C2 - 0.05:  # counter rattle
        at(fx, rs(sfx.tick()), t, 0.30)
        t += 0.055
    at(fx, rs(sfx.whoosh()), C2 - 0.25, 0.3)
    at(fx, rs(braam(2.6, 0.8)), STAMP_AT - 0.02, 0.55)
    for tb, g in zip(BEATS, [0.32, 0.28, 0.22, 0.16]):
        at(fx, beep(), tb, g)
        at(fx, rs(sfx.heartbeat()), tb - 0.05, g * 1.3)
    flat = beep(DUR - FLAT, 1000.0) * np.interp(np.linspace(0, 1, int((DUR - FLAT) * SR)), [0, 0.7, 1], [1, 1, 0])
    at(fx, flat, FLAT, 0.22)
    vo = load_vo()
    voice = np.zeros(n)
    at(voice, vo, OFF, 1.0)
    mix = voice / (np.abs(vo).max() + 1e-9) * 0.9 + bed * 0.6 + fx * 0.7
    st = np.stack([mix, mix], 1)
    st = (np.clip(st, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(st.tobytes())


# ----------------------------------------------------------------------------- render + join

def sheet():
    ts = [0.6, 1.4, 2.6, 3.8, 4.6, 5.8, 6.5, 8.2, 10.3, 11.6, 12.6, 13.4]
    ims = [frame(t).resize((480, 270)) for t in ts]
    sh = Image.new("RGB", (480 * 4, 270 * 3))
    for k, im in enumerate(ims):
        sh.paste(im, ((k % 4) * 480, (k // 4) * 270))
    os.makedirs(os.path.join(m.OUT, "chk"), exist_ok=True)
    sh.save(os.path.join(m.OUT, "chk", "hook_sheet.jpg"))


def main():
    if "--sheet" in _args:
        return sheet()
    out = m.OUT
    wav = os.path.join(out, "hook.wav")
    soundtrack(wav)
    silent = os.path.join(out, "hook_video.mp4")
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                            "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        enc.stdin.write(frame(i / FPS).tobytes())
    enc.stdin.close()
    enc.wait()
    hook = os.path.join(out, "hook.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", silent, "-i", wav, "-c:v", "copy",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
                    "-shortest", hook], check=True)
    main_v = os.path.join(out, "IPL_Ko_Kisne_Maara.mp4")
    full = os.path.join(out, "IPL_Ko_Kisne_Maara_hook.mp4")
    fc = "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", hook, "-i", main_v, "-filter_complex", fc,
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", full], check=True)
    up = os.path.join(out, "IPL_Ko_Kisne_Maara_hook_upload.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", full, "-c:v", "libx264", "-preset", "medium",
                    "-b:v", "5M", "-maxrate", "6M", "-bufsize", "10M", "-pix_fmt", "yuv420p", "-c:a", "copy",
                    up], check=True)
    print("HOOK_DONE", full, up)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Cold-open the documentary on Virat Kohli's answer, and call back to it before the CTA.

    python3 virat_hook.py   ->  final/Centurion2003_The98_ViratHook.mp4

Running order:
  1. Virat clip (footage/virat_interview.mp4, whole 14.7 s) - the very first frame of the video,
     with a VIRAT KOHLI name strap once he is on screen
  2. suspense: trailer-style text on heavy braam hits over blurred, pushing-in real footage -
     "Why would Virat Kohli..." (over Virat) / "...want to bat with Sachin at Centurion, 2003?" (the upper-cut) /
     ICC CRICKET WORLD CUP 2003 SOUTH AFRICA title (Centurion crowd) / "It was not just a match." (flags) /
     "It changed the belief of Indian cricket." (crowd erupting), dissolving into the film's first frame
  3. the film from 0 s up to the quiet beat after "Centurion was won in both." (FILM_CUT)
  4. ending card   "This is why even / Virat Kohli / wishes he was out there."
  5. Virat callback - on camera: "I would have loved to be batting with Sachin Paaji, when he hit that...",
     then on "...shot off Shoaib" the upper-cut itself (m_six_sideon) and the crowd, quote on screen
  6. the film from FILM_CUT to the end (CTA + logo sting)

Cards are drawn on the film's own background plate (assets/plate_dark.png, watermark included) in its
type and colour (Inter Display, #FEDE5C), with sfx from kohli_countdown/sfx.py.
"""
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "kohli_countdown"))
from sfx import SR, impact, whoosh  # noqa: E402

FILM = os.path.join(HERE, "final", "Centurion2003_The98_web.mp4")
VIRAT = os.path.join(HERE, "footage", "virat_interview.mp4")
OUT = os.path.join(HERE, "out", "virat")
FINAL = os.path.join(HERE, "final", "Centurion2003_The98_ViratHook.mp4")
PLATE = os.path.join(HERE, "assets", "plate_dark.png")
W, H, FPS = 1920, 1080, 30
Y = (254, 222, 92)
BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
XB = "/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf"
SEMI = "/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf"

FILM_CUT = 390.0        # dark, quiet beat between "Centurion was won in both." and the CTA card
VIRAT_ON = 4.6          # first shot of Virat (before that it's the interviewer asking)
CALLBACK_IN = 10.9      # "I would have loved to be batting..."
VIRAT_OFF = 13.567      # source cuts from Virat to the interviewer ("...shot off Shoaib")
ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "22", "-pix_fmt", "yuv420p", "-r", str(FPS),
       "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2"]


def run(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def ease(t):
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3


# ---------- cards ----------

def text_layer(lines):
    """lines: [(text, font, size, colour, tracking)] centred as a block. Returns per-line RGBA layers + y."""
    out, heights = [], []
    for txt, path, size, col, track in lines:
        f = ImageFont.truetype(path, size)
        w = sum(f.getlength(c) for c in txt) + track * (len(txt) - 1)
        l, t, r, b = f.getbbox(txt)
        im = Image.new("RGBA", (int(w) + 40, b - t + 40), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        x = 20
        for c in txt:
            d.text((x, 20 - t), c, font=f, fill=col)
            x += f.getlength(c) + track
        out.append(im)
        heights.append(b - t)
    gap = 26
    total = sum(heights) + gap * (len(lines) - 1)
    y, ys = (H - total) // 2 - 20, []
    for h in heights:
        ys.append(y - 20)
        y += h + gap
    return out, ys


def render_card(name, lines, starts, dur, fade_out=0.35):
    plate = Image.open(PLATE).convert("RGBA")
    layers, ys = text_layer(lines)
    path = os.path.join(OUT, name + "_v.mp4")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                          "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for i in range(int(round(dur * FPS))):
        t = i / FPS
        fr = plate.copy()
        for im, y, s in zip(layers, ys, starts):
            k = ease((t - s) / 0.55)
            if k <= 0:
                continue
            lay = im.copy()
            lay.putalpha(lay.getchannel("A").point(lambda v, k=k: int(v * k)))
            fr.alpha_composite(lay, ((W - im.width) // 2, int(y + 28 * (1 - k))))
        out = np.asarray(fr.convert("RGB"), np.float32)
        out *= min(1.0, (dur - t) / fade_out) if dur - t < fade_out else 1.0
        p.stdin.write(out.clip(0, 255).astype(np.uint8).tobytes())
    p.stdin.close()
    p.wait()
    return path


def sfx_track(name, dur, hits):
    """hits: [(time, kind, gain)] -> stereo wav."""
    n = int(dur * SR)
    mix = np.zeros(n, np.float32)
    for t, kind, g in hits:
        s = (impact() if kind == "impact" else whoosh()) * g
        i = int(t * SR)
        seg = s[: max(0, n - i)]
        mix[i:i + len(seg)] += seg
    path = os.path.join(OUT, name + "_a.wav")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
        w.writeframes(np.repeat(pcm[:, None], 2, axis=1).tobytes())
    return path


# ---------- suspense sequence: trailer-style text slams on heavy "braam" hits ----------

def braam(dur=3.2, weight=1.0):
    """Cinematic low brass hit: detuned saws at A1/E2 through a closing lowpass, plus sub-drop and a noise crack."""
    from sfx import _lowpass  # same one-pole filter the sfx kit uses
    t = np.arange(int(SR * dur)) / SR
    env = np.minimum(t / 0.015, 1) * np.exp(-t * 1.25)
    x = np.zeros_like(t)
    for f in (55.0, 55.4, 54.6, 82.4, 82.0, 110.0):
        x += 2 * ((t * f + rng_sfx.uniform()) % 1.0) - 1
    cutoff = 140 + 1600 * np.exp(-t * 3.0)
    x = _lowpass(x / 6, cutoff)
    sub = np.sin(2 * np.pi * np.cumsum(70 * np.exp(-t * 1.6) + 28) / SR) * np.exp(-t * 0.9)
    crack = _lowpass(rng_sfx.standard_normal(len(t)), 2500) * np.exp(-t * 28)
    y = np.tanh(2.2 * (x * env + 0.9 * sub * weight)) + 0.35 * crack
    # cheap room: a few decaying echoes so the tail breathes
    out = y.copy()
    for d, g in ((0.043, 0.35), (0.071, 0.28), (0.113, 0.2), (0.167, 0.14)):
        k = int(d * SR)
        out[k:] += y[:-k] * g
    return out / np.max(np.abs(out))


def drone(dur):
    """Low tension bed that swells across the sequence."""
    from sfx import _lowpass
    t = np.arange(int(SR * dur)) / SR
    hum = np.sin(2 * np.pi * 41.2 * t) + 0.5 * np.sin(2 * np.pi * 61.7 * t + 1.0)
    air = _lowpass(rng_sfx.standard_normal(len(t)), 300 + 900 * t / dur)
    swell = (t / dur) ** 1.5
    return (0.6 * hum + 0.5 * air) * (0.25 + 0.75 * swell) * np.minimum(t / 0.6, 1)


rng_sfx = np.random.default_rng(2003)

CLIPS = os.path.join(HERE, "footage", "clips")
# Each segment: duration, background, text. Backgrounds are real footage, blurred + graded, slowly pushing in.
#   ("still", path, t)  -> a frame from a video;  ("clip", name, speed) -> footage/clips/<name>.mp4
SEGMENTS = [
    dict(dur=2.6, bg=("still", VIRAT, 12.6), blur_in=True,
         lines=[[("Why", 0), ("would", 0), ("Virat", 1), ("Kohli…", 1)]], size=118),
    dict(dur=2.9, bg=("clip", "m_six_sideon", 0.5),
         lines=[[("…want", 0), ("to", 0), ("bat", 0), ("with", 0), ("Sachin", 0)],
                [("at", 1), ("Centurion,", 1), ("2003?", 1)]], size=104),
    dict(dur=4.3, bg=("clip", "crowd_flags", 1.0), title=True),
    dict(dur=2.6, bg=("clip", "m_flags_wave", 0.8),
         lines=[[("It", 0), ("was", 0), ("not", 0), ("just", 0), ("a", 0), ("match.", 0)]], size=124),
    dict(dur=3.7, bg=("clip", "m_six_crowd_jump", 0.8),
         lines=[[("It", 0), ("changed", 0), ("the", 0), ("belief", 0)],
                [("of", 1), ("Indian", 1), ("cricket.", 1)]], size=124, final=True),
]
STAGGER, RISE = 0.07, 0.38   # per-word delay, per-word rise time
LINE_GAP = 0.3               # second line starts this long after the first line has landed


def bg_frames(spec, dur):
    """Yield 960x540 RGB frames for one segment (crop off score bar / channel bug, slow, fill 16:9)."""
    n = int(round(dur * FPS))
    kind = spec[0]
    if kind == "still":
        cmd = ["ffmpeg", "-v", "error", "-ss", str(spec[2]), "-i", spec[1], "-frames:v", "1",
               "-vf", "crop=2880:1620:400:0,scale=960:540", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]  # drop subtitle line
        fr = np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.uint8).reshape(540, 960, 3)
        for _ in range(n):
            yield fr
        return
    _, name, speed = spec
    vf = (f"crop=716:600:0:50,setpts={1 / speed}*PTS,fps={FPS},"
          "scale=960:-2,crop=960:540:0:(ih-540)/2")
    cmd = ["ffmpeg", "-v", "error", "-stream_loop", "-1", "-i", os.path.join(CLIPS, name + ".mp4"),
           "-vf", vf, "-frames:v", str(n), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    last = None
    for _ in range(n):
        buf = p.stdout.read(960 * 540 * 3)
        if len(buf) == 960 * 540 * 3:
            last = np.frombuffer(buf, np.uint8).reshape(540, 960, 3)
        yield last
    p.stdout.close()
    p.wait()


VIGNETTE = None


def grade_bg(small, t, dur, blur_in=False):
    """Push-in, blur, darken, desaturate toward the film's warm-dark look; returns float 1080p frame."""
    global VIGNETTE
    from PIL import ImageFilter
    im = Image.fromarray(small)
    z = 1.04 + 0.06 * (t / dur)
    cw, ch = 960 / z, 540 / z
    im = im.crop(((960 - cw) / 2, (540 - ch) / 2, (960 + cw) / 2, (540 + ch) / 2)).resize((960, 540), Image.BILINEAR)
    r = 7 if not blur_in else 0.5 + 6.5 * ease(t / 0.5)
    im = im.filter(ImageFilter.GaussianBlur(r)).resize((W, H), Image.BILINEAR)
    a = np.asarray(im, np.float32)
    lum = a.mean(-1, keepdims=True)
    a = lum + (a - lum) * 0.55
    a = a * np.array([1.02, 0.97, 0.9], np.float32)
    dark = 0.42 if not blur_in else 1.0 - 0.58 * ease(t / 0.5)
    if VIGNETTE is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        VIGNETTE = (1 - 0.65 * np.clip(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.68)) ** 2, 0, 1))[..., None]
    return a * dark * VIGNETTE


def word_images(lines, size):
    f = ImageFont.truetype(BLACK, size)
    space = f.getlength(" ")
    rows = []
    for line in lines:
        ims = []
        for txt, accent in line:
            l, t, r, b = f.getbbox(txt)
            im = Image.new("RGBA", (r - l + 40, size + 60), (0, 0, 0, 0))
            d = ImageDraw.Draw(im)
            col = Y if accent else (255, 255, 255)
            d.text((20 - l, 20), txt, font=f, fill=col)
            ims.append(im)
        width = sum(i.width - 40 for i in ims) + space * (len(ims) - 1)
        rows.append((ims, width))
    lh = int(size * 1.12)
    top = (H - lh * len(rows)) // 2 - 30
    placed = []  # (img, x, y, line index, word index)
    for li, (ims, width) in enumerate(rows):
        x = (W - width) / 2
        for wi, im in enumerate(ims):
            placed.append((im, int(x) - 20, top + li * lh - 20, li, wi))
            x += im.width - 40 + space
    return placed, [len(r[0]) for r in rows]


def word_start(li, wi, counts, t_text):
    s = t_text
    for k in range(li):
        s += (counts[k] - 1) * STAGGER + RISE + LINE_GAP
    return s + wi * STAGGER


def landing(counts, t_text):
    li = len(counts) - 1
    return word_start(li, counts[-1] - 1, counts, t_text) + RISE * 0.7


def draw_words(frame, placed, counts, t, t_text, exit_k):
    from PIL import ImageFilter
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for im, x, y, li, wi in placed:
        p = (t - word_start(li, wi, counts, t_text)) / RISE
        if p <= 0:
            continue
        e = ease(p)
        w = im
        blur = 9 * (1 - e) + 10 * exit_k
        if blur > 0.4:
            w = im.filter(ImageFilter.GaussianBlur(blur))
        a = e * (1 - exit_k)
        if a < 1:
            w = w.copy()
            w.putalpha(w.getchannel("A").point(lambda v, a=a: int(v * a)))
        layer.alpha_composite(w, (x, int(y + 46 * (1 - e))))
    return layer


def title_layer(t):
    """ICC CRICKET WORLD CUP / 2003 (digits rise) / yellow rule / SOUTH AFRICA (wipe) / date line."""
    from PIL import ImageFilter
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # kicker with tracking that tightens as it fades in
    k = ease((t - 0.1) / 0.6)
    if k > 0:
        f = ImageFont.truetype(XB, 40)
        txt = "ICC CRICKET WORLD CUP"
        track = 34 - 22 * k
        w = sum(f.getlength(c) for c in txt) + track * (len(txt) - 1)
        x = (W - w) / 2
        for c in txt:
            d.text((x, 250), c, font=f, fill=(235, 235, 235, int(255 * k)))
            x += f.getlength(c) + track
    # 2003: each digit rises out of a mask line
    f = ImageFont.truetype(BLACK, 270)
    digits = "2003"
    widths = [f.getlength(c) for c in digits]
    x0 = (W - sum(widths) - 10 * 3) / 2
    base_y, mask_bottom = 310, 310 + 300
    for i, c in enumerate(digits):
        p = ease((t - 0.45 - i * 0.09) / 0.42)
        if p > 0:
            dig = Image.new("RGBA", (int(widths[i]) + 40, 340), (0, 0, 0, 0))
            ImageDraw.Draw(dig).text((20, 0), c, font=f, fill=Y)
            off = int(320 * (1 - p))
            visible = dig.crop((0, 0, dig.width, max(0, min(340, mask_bottom - (base_y + off)))))
            if visible.height:
                layer.alpha_composite(visible, (int(x0) - 20, base_y + off))
        x0 += widths[i] + 10
    # rule draws out from the centre
    r = ease((t - 1.25) / 0.45)
    if r > 0:
        half = 470 * r
        d.rectangle((W / 2 - half, 640, W / 2 + half, 647), fill=Y + (255,))
    # SOUTH AFRICA wipes in left to right
    wpe = ease((t - 1.45) / 0.55)
    if wpe > 0:
        f2 = ImageFont.truetype(BLACK, 92)
        txt = "SOUTH AFRICA"
        track = 14
        w = int(sum(f2.getlength(c) for c in txt) + track * (len(txt) - 1))
        sa = Image.new("RGBA", (w + 20, 120), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sa)
        x = 10
        for c in txt:
            sd.text((x, 0), c, font=f2, fill=(255, 255, 255))
            x += f2.getlength(c) + track
        sa = sa.crop((0, 0, max(1, int(sa.width * wpe)), sa.height))
        layer.alpha_composite(sa, ((W - w - 20) // 2, 672))
    # date line
    q = ease((t - 2.3) / 0.5)
    if q > 0:
        f3 = ImageFont.truetype(XB, 36)
        txt = "1 MARCH  ·  CENTURION  ·  INDIA vs PAKISTAN"
        tw = f3.getlength(txt)
        d.text(((W - tw) / 2, 812 + 20 * (1 - q)), txt, font=f3, fill=(215, 215, 215, int(255 * q)))
    return layer


TITLE_HIT = 0.45 + 3 * 0.09 + 0.3   # "2003" fully landed


def suspense():
    film0 = np.asarray(Image.open(os.path.join(OUT, "film_first.png")).convert("RGB"), np.float32)
    path_v = os.path.join(OUT, "suspense_v.mp4")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                          "-pix_fmt", "yuv420p", path_v], stdin=subprocess.PIPE)
    rng_shake = np.random.default_rng(7)
    hits, whooshes = [], []
    t_global = 0.0
    prev_last = None
    for si, seg in enumerate(SEGMENTS):
        dur = seg["dur"]
        title = seg.get("title")
        t_text = 0.12
        if title:
            hit = TITLE_HIT
        else:
            placed, counts = word_images(seg["lines"], seg["size"])
            hit = landing(counts, t_text)
        hits.append((t_global + hit, 1.0 if seg.get("final") else (0.8 if title else 0.6 + 0.05 * si),
                     1.3 if seg.get("final") else 1.0))
        if si:
            whooshes.append(t_global - 0.22)
        frames = bg_frames(seg["bg"], dur)
        for i in range(int(round(dur * FPS))):
            t = i / FPS
            frame = grade_bg(next(frames), t, dur, seg.get("blur_in"))
            if prev_last is not None and t < 0.16:            # quick dissolve from the previous card
                a = t / 0.16
                frame = prev_last * (1 - a) + frame * a
            exit_k = ease((t - (dur - 0.24)) / 0.24) if not seg.get("final") else 0.0
            layer = title_layer(t) if title else draw_words(frame, placed, counts, t, t_text, exit_k)
            if title and exit_k > 0:
                layer.putalpha(layer.getchannel("A").point(lambda v, k=exit_k: int(v * (1 - k))))
            # punch + shake on the hit
            k = t - hit
            sc = 1.0
            jx = jy = 0
            if 0 <= k < 0.3:
                sc = 1.0 + 0.05 * np.exp(-k * 18)
                amp = 12 * (1 - k / 0.3)
                jx, jy = rng_shake.uniform(-amp, amp, 2)
            if exit_k > 0:
                sc *= 1 + 0.07 * exit_k
            if sc != 1.0 or jx or jy:
                bw, bh = int(W * sc), int(H * sc)
                big = layer.resize((bw, bh), Image.BILINEAR)
                ox, oy = int((bw - W) / 2 - jx), int((bh - H) / 2 - jy)
                layer = big.crop((ox, oy, ox + W, oy + H))
            la = np.asarray(layer, np.float32)
            al = la[..., 3:4] / 255
            frame = frame * (1 - al) + la[..., :3] * al
            if 0 <= k:
                frame = frame + 255 * 0.2 * np.exp(-k * 14)    # flash on the hit
            if t < 0.12 and si:
                frame = frame + 255 * 0.25 * (1 - t / 0.12)   # flash on the cut
            if seg.get("final"):                               # flash, then dissolve into the film's first frame
                f_out = ease((t - (dur - 0.45)) / 0.45)
                if f_out > 0:
                    flash = np.sin(np.pi * f_out) * 0.5
                    frame = frame * (1 - f_out) + film0 * f_out + 255 * flash
            frame = np.clip(frame, 0, 255)
            p.stdin.write(frame.astype(np.uint8).tobytes())
            prev_frame = frame
        prev_last = prev_frame
        t_global += dur
    p.stdin.close()
    p.wait()

    total = t_global
    n = int(total * SR)
    mix = drone(total) * 0.16
    for t, g, wgt in hits:
        h = braam(weight=wgt) * g
        i = int(t * SR)
        seg = h[: n - i]
        mix[i:i + len(seg)] += seg
    for t in whooshes:
        h = whoosh(0.4) * 0.22
        i = max(0, int(t * SR))
        seg = h[: n - i]
        mix[i:i + len(seg)] += seg
    tail = int(0.5 * SR)
    mix[-tail:] *= np.linspace(1, 0, tail) ** 2
    mix = np.tanh(mix * 1.1) * 0.89
    path_a = os.path.join(OUT, "suspense_a.wav")
    with wave.open(path_a, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
        w.writeframes(np.repeat(pcm[:, None], 2, axis=1).tobytes())
    path = os.path.join(OUT, "suspense.mp4")
    run("-i", path_v, "-i", path_a, "-map", "0:v", "-map", "1:a", *ENC, "-shortest", path)
    return path


def card(name, lines, starts, dur, hits):
    v = render_card(name, lines, starts, dur)
    a = sfx_track(name, dur, hits)
    path = os.path.join(OUT, name + ".mp4")
    run("-i", v, "-i", a, "-map", "0:v", "-map", "1:a", *ENC, "-shortest", path)
    return path


# ---------- Virat segments ----------

def name_strap():
    im = Image.new("RGBA", (900, 170), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 18, 9, 150), fill=Y + (255,))
    d.text((34, 6), "VIRAT KOHLI", font=ImageFont.truetype(BLACK, 62), fill=(255, 255, 255))
    d.text((36, 98), "on the moment he wishes he'd been part of", font=ImageFont.truetype(SEMI, 30),
           fill=(225, 225, 225))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.putalpha(im.getchannel("A").point(lambda v: int(v * 0.75)))
    from PIL import ImageFilter
    out = Image.new("RGBA", (im.width + 40, im.height + 40), (0, 0, 0, 0))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)), (24, 24))
    out.alpha_composite(im, (20, 20))
    path = os.path.join(OUT, "strap.png")
    out.save(path)
    return path


def virat_hook():
    strap = name_strap()
    path = os.path.join(OUT, "hook.mp4")
    a, b = VIRAT_ON + 0.3, 9.6  # strap on screen while Virat answers
    run("-i", VIRAT, "-loop", "1", "-t", "15", "-i", strap,
        "-filter_complex",
        f"[0:v]scale={W}:{H}:flags=lanczos,setsar=1[v];"
        f"[1:v]format=rgba,fade=in:st={a}:d=0.35:alpha=1,fade=out:st={b - 0.35}:d=0.35:alpha=1[s];"
        f"[v][s]overlay=70:600:enable='between(t,{a},{b})':shortest=1,format=yuv420p[vo];"
        "[0:a]afade=out:st=14.58:d=0.15[ao]",
        "-map", "[vo]", "-map", "[ao]", *ENC, "-shortest", path)
    return path


def quote_layer():
    """Virat's line, left column, film headline style (yellow bar, white + yellow accent line)."""
    f = ImageFont.truetype(BLACK, 66)
    lines = [("“I would have loved", (255, 255, 255)), ("to be batting with", (255, 255, 255)),
             ("Sachin Paaji when he hit", (255, 255, 255)), ("that shot off Shoaib.”", Y)]
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x, y0, lh = 150, 330, 84
    for i, (txt, col) in enumerate(lines):
        d.text((x, y0 + i * lh), txt, font=f, fill=col)
    d.rectangle((x - 40, y0 + 8, x - 32, y0 + 4 * lh - 14), fill=Y + (255,))
    d.text((x + 2, y0 + 4 * lh + 34), "VIRAT KOHLI", font=ImageFont.truetype(XB, 34), fill=Y)
    path = os.path.join(OUT, "quote.png")
    im.save(path)
    return path


def card_mask(w, h, r=30):
    from PIL import ImageFilter
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), radius=r, fill=255)
    m.save(os.path.join(OUT, "card_mask.png"))
    sh = Image.new("RGBA", (w + 120, h + 120), (0, 0, 0, 0))
    a = Image.new("L", sh.size, 0)
    ImageDraw.Draw(a).rounded_rectangle((60, 70, 60 + w, 70 + h), radius=r, fill=200)
    sh.putalpha(a.filter(ImageFilter.GaussianBlur(24)))
    sh.save(os.path.join(OUT, "card_shadow.png"))
    return os.path.join(OUT, "card_mask.png"), os.path.join(OUT, "card_shadow.png")


def virat_on_camera():
    """Virat himself: "I would have loved to be batting with Sachin Paaji, when he hit that..." (wide, then close-up)."""
    path = os.path.join(OUT, "callback_virat.mp4")
    dur = VIRAT_OFF - CALLBACK_IN
    run("-ss", str(CALLBACK_IN), "-t", str(dur), "-i", VIRAT,
        "-vf", f"scale={W}:{H}:flags=lanczos,setsar=1,fade=in:st=0:d=0.25",
        "-af", "afade=in:st=0:d=0.08", *ENC, path)
    return path


def virat_callback():
    """...then the shot he is talking about, on "shot off Shoaib": the upper-cut, then the crowd, quote on screen."""
    dur = 3.2
    word = 14.733 - VIRAT_OFF  # rest of Virat's line
    shot = 1.5  # upper-cut until the camera pans off to empty grass
    cw, ch = 640, 698  # clips are 716x780
    cx, cy = 1160, (H - ch) // 2 - 10
    mask, shadow = card_mask(cw, ch)
    quote = quote_layer()
    hit = sfx_track("callback_hit", dur, [(0.45, "impact", 0.35)])
    clips = os.path.join(HERE, "footage", "clips")
    path = os.path.join(OUT, "callback.mp4")
    run("-loop", "1", "-t", str(dur), "-i", PLATE,
        "-ss", "0.6", "-i", os.path.join(clips, "m_six_sideon.mp4"),
        "-ss", "1.0", "-i", os.path.join(clips, "m_six_crowd_jump.mp4"),
        "-loop", "1", "-t", str(dur), "-i", mask,
        "-loop", "1", "-t", str(dur), "-i", shadow,
        "-loop", "1", "-t", str(dur), "-i", quote,
        "-ss", str(VIRAT_OFF), "-i", VIRAT,
        "-i", hit,
        "-filter_complex",
        f"[1:v]fps={FPS},setsar=1,trim=duration={shot}[a];[2:v]fps={FPS},setsar=1,trim=duration={dur - shot + 0.05}[b];"
        f"[a][b]concat=n=2:v=1:a=0,scale={cw}:{ch},format=rgba[clip];"
        "[3:v]format=gray[m];[clip][m]alphamerge[card];"
        "[4:v]format=rgba[sh];"
        "[5:v]format=rgba,fade=in:st=0:d=0.35:alpha=1[q];"
        f"[0:v]scale={W}:{H},format=rgba[bg];"
        f"[bg][sh]overlay={cx - 60}:{cy - 60}[b1];[b1][card]overlay={cx}:{cy}[b2];"
        f"[b2][q]overlay=0:0,format=yuv420p,trim=duration={dur}[vo];"
        f"[6:a]atrim=duration={word},afade=out:st={word - 0.15}:d=0.15,apad[v];"
        "[7:a]aresample=48000[h];[v][h]amix=inputs=2:duration=longest:normalize=0,"
        f"atrim=duration={dur},afade=out:st={dur - 0.4}:d=0.4[ao]",
        "-map", "[vo]", "-map", "[ao]", *ENC, "-t", str(dur), path)
    return path


def film_part(name, start, end=None):
    path = os.path.join(OUT, name + ".mp4")
    args = ["-ss", str(start), "-i", FILM]
    if end is not None:
        args = ["-ss", str(start), "-to", str(end), "-i", FILM]
    fades = "afade=in:st=0:d=0.05"
    run(*args, "-af", fades, *ENC, path)
    return path


def main():
    os.makedirs(OUT, exist_ok=True)
    run("-i", FILM, "-frames:v", "1", os.path.join(OUT, "film_first.png"))
    parts = [
        virat_hook(),
        suspense(),
        film_part("film_a", 0, FILM_CUT),
        card("ending",
             [("This is why even", BLACK, 92, (255, 255, 255), 0),
              ("Virat Kohli", BLACK, 150, Y, 0),
              ("wishes he was out there.", BLACK, 92, (255, 255, 255), 0)],
             [0.3, 1.05, 1.9], 4.6,
             [(1.0, "impact", 0.4)]),
        virat_on_camera(),
        virat_callback(),
        film_part("film_b", FILM_CUT),
    ]
    lst = os.path.join(OUT, "concat.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{p}'\n" for p in parts)
    run("-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", FINAL)
    print(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration,size", "-of", "csv=p=0",
                          FINAL], capture_output=True, text=True).stdout.strip())
    print("VIRAT_HOOK_DONE", FINAL)


if __name__ == "__main__":
    main()

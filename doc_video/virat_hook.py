#!/usr/bin/env python3
"""Cold-open the documentary on Virat Kohli's answer, and call back to it before the CTA.

    python3 virat_hook.py   ->  final/Centurion2003_The98_ViratHook.mp4

Running order:
  1. Virat clip (footage/virat_interview.mp4, whole 14.7 s) - the very first frame of the video,
     with a VIRAT KOHLI name strap once he is on screen
  2. suspense: trailer-style slams on heavy braam hits - "Why would Virat Kohli... / ...want to bat with
     Sachin at Centurion, 2003? / It was not just a match. / It changed the belief of Indian cricket."
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
ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p", "-r", str(FPS),
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

SUSPENSE = [  # (start, end, slam time, [(text, font, size, colour)], small kicker above)
    (0.0, 2.5, 0.15, [("Why would Virat Kohli…", BLACK, 112, (255, 255, 255))], None),
    (2.5, 5.3, 2.65, [("…want to bat with Sachin", BLACK, 104, (255, 255, 255)),
                      ("at Centurion, 2003?", BLACK, 104, Y)], None),
    (5.3, 8.1, 5.5, [("It was not just a match.", BLACK, 118, (255, 255, 255))],
     "1 MARCH 2003  ·  INDIA vs PAKISTAN"),
    (8.1, 11.6, 8.25, [("It changed the belief", BLACK, 116, (255, 255, 255)),
                       ("of Indian cricket.", BLACK, 132, Y)], None),
]
SUSPENSE_HITS = [(0.15, 0.55, 0.8), (2.65, 0.62, 0.9), (5.5, 0.75, 1.0), (8.25, 1.0, 1.25)]  # (t, gain, sub weight)


def suspense():
    dur = SUSPENSE[-1][1]
    plate = np.asarray(Image.open(PLATE).convert("RGB"), np.float32) * 0.55
    beats = []
    for t0, t1, slam, lines, kicker in SUSPENSE:
        layers, ys = text_layer([(txt, f, s, c, 0) for txt, f, s, c in lines])
        block = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for im, y in zip(layers, ys):
            block.alpha_composite(im, ((W - im.width) // 2, y))
        if kicker:
            ImageDraw.Draw(block).text((W // 2, ys[0] - 30), kicker, font=ImageFont.truetype(XB, 34),
                                       fill=(200, 200, 200), anchor="ms")
        beats.append((t0, t1, slam, block))

    path_v = os.path.join(OUT, "suspense_v.mp4")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                          "-pix_fmt", "yuv420p", path_v], stdin=subprocess.PIPE)
    shake_rng = np.random.default_rng(7)
    for i in range(int(round(dur * FPS))):
        t = i / FPS
        beat = next(b for b in beats if b[0] <= t < b[1])
        t0, t1, slam, block = beat
        frame = plate.copy()
        if t >= slam:
            k = t - slam
            s = 1.0 + 0.14 * np.exp(-k * 22)            # slams in from slightly too big
            drift = 1.0 + 0.012 * k                      # then a slow push while it holds
            sc = s * drift
            bw, bh = int(W * sc), int(H * sc)
            lay = block.resize((bw, bh), Image.BICUBIC)
            jx = jy = 0
            if k < 0.25:                                 # impact shake
                amp = 14 * (1 - k / 0.25)
                jx, jy = shake_rng.uniform(-amp, amp, 2)
            ox, oy = int((W - bw) / 2 + jx), int((H - bh) / 2 + jy)
            canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            canvas.alpha_composite(lay.crop((max(0, -ox), max(0, -oy), max(0, -ox) + W, max(0, -oy) + H)),
                                   (max(0, ox), max(0, oy)))
            a = np.asarray(canvas, np.float32)
            alpha = a[..., 3:4] / 255 * min(1.0, k / 0.06)
            frame = frame * (1 - alpha) + a[..., :3] * alpha
            frame += 255 * 0.22 * np.exp(-k * 16)        # flash on the hit
        frame *= min(1.0, (t1 - t) / 0.22)               # dip to black between beats
        frame *= min(1.0, (t - t0 + 0.04) / 0.12) if t0 > 0 else 1.0
        p.stdin.write(np.clip(frame, 0, 255).astype(np.uint8).tobytes())
    p.stdin.close()
    p.wait()

    n = int(dur * SR)
    mix = drone(dur) * 0.16
    for t, g, wgt in SUSPENSE_HITS:
        h = braam(weight=wgt) * g
        i = int(t * SR)
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

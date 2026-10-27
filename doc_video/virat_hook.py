#!/usr/bin/env python3
"""Cold-open the documentary on Virat Kohli's answer, and call back to it before the CTA.

    python3 virat_hook.py   ->  final/Centurion2003_The98_ViratHook.mp4

Running order:
  1. Virat clip (footage/virat_interview.mp4, whole 14.7 s) - the very first frame of the video,
     with a VIRAT KOHLI name strap once he is on screen
  2. bridge card   "1 March 2003 · Centurion / India vs Pakistan. / More than a cricket match."
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
        card("bridge",
             [("1 MARCH 2003  ·  CENTURION", XB, 34, (190, 190, 190), 6),
              ("India vs Pakistan.", BLACK, 104, (255, 255, 255), 0),
              ("More than a cricket match.", BLACK, 104, Y, 0)],
             [0.2, 0.75, 1.75], 5.2,
             [(0.55, "whoosh", 0.25), (0.75, "impact", 0.35), (1.75, "impact", 0.45)]),
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

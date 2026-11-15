#!/usr/bin/env python3
"""Cinematic cold open for "IPL Ko Kisne Maara?" (~14 s), joined in front of the finished video.

Same treatment as the Centurion documentary's Virat hook (doc_video/virat_hook.py): real footage behind every line,
blurred, graded warm-dark and slowly pushing in; big Inter Black words rising in one by one; a braam hit with a
white flash and a short shake when a line lands; whooshes on the cuts; the last shot flashes and dissolves into the
video's first frame.

VO (vo/hook_raw.mp3): "17 November, retention lists out. Crores ki deals, bade naam release... par ek sawal koi
nahi pooch raha: kya IPL dheere dheere mar raha hai?"

Footage is only from stretches of the clean IPL clips the main video doesn't use (nothing repeats).

    python3 hook.py          ->  out/hook.mp4, out/IPL_Ko_Kisne_Maara_hook.mp4 (+ _hook_upload.mp4, 5 Mbit/s)
    python3 hook.py --sheet  ->  out/chk/hook_sheet.jpg
"""
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "kohli_countdown"))
sys.path.insert(0, os.path.join(ROOT, "doc_video"))
import sfx  # noqa: E402
import virat_hook as vh  # noqa: E402  (grade_bg, braam, drone)

W, H, FPS = 1920, 1080, 30
Y = (255, 222, 89)
BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
SR = sfx.SR
OUT = os.path.join(HERE, "out")
A = lambda n: os.path.join(HERE, "assets", n + ".mp4")  # noqa: E731
OFF = 0.35                                    # VO starts here; phrase times below are hook time
STAGGER, RISE = 0.07, 0.38

# (start, dur, (clip, src_start, speed), [(line start, size, [(word, accent)])], hit weight, blur_in, final)
SEGS = [
    (0.00, 3.75, ("kkr_clean", 6.6, 0.6),
     [(0.35, 150, [("17", 1), ("NOVEMBER.", 1)]), (1.86, 104, [("RETENTION", 0), ("LISTS", 0), ("OUT.", 0)])],
     0.75, True, False),
    (3.75, 1.60, ("jadeja_six_clean", 8.4, 0.7),
     [(4.14, 150, [("CRORES", 1), ("IN", 0), ("DEALS.", 0)])], 0.8, False, False),
    (5.35, 1.70, ("reel_shot", 0.0, 0.95),
     [(5.44, 140, [("BIG", 0), ("NAMES", 0)]), (5.95, 160, [("RELEASED.", 1)])], 1.0, False, False),
    (7.05, 2.70, ("kkr_clean", 5.0, 0.6),
     [(7.40, 96, [("BUT", 0), ("NOBODY", 0), ("IS", 0), ("ASKING...", 0)])], 0.0, False, False),
    (9.75, 4.25, ("jadeja_spin_clean", 6.55, 0.48),
     [(9.97, 150, [("IS", 0), ("IPL", 0)]), (11.35, 170, [("SLOWLY", 1), ("DYING?", 1)])], 1.3, False, True),
]
DUR = SEGS[-1][0] + SEGS[-1][1]
FLAT = 12.95  # flat-line beep under the last hit


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


# ----------------------------------------------------------------------------- text

def place_words(lines):
    """Word images laid out centred, one row per line; returns [(img, x, y, start time)] and each line's landing."""
    rows = []
    for t0, size, words in lines:
        f = ImageFont.truetype(BLACK, size)
        sp = f.getlength(" ")
        ims = []
        for txt, acc in words:
            l, tt, r, b = f.getbbox(txt)
            im = Image.new("RGBA", (r - l + 40, size + 60), (0, 0, 0, 0))
            ImageDraw.Draw(im).text((20 - l, 20), txt, font=f, fill=Y if acc else (255, 255, 255))
            ims.append(im)
        rows.append((t0, size, ims, sum(i.width - 40 for i in ims) + sp * (len(ims) - 1), sp))
    total_h = sum(int(r[1] * 1.12) for r in rows)
    y = (H - total_h) // 2 - 40
    placed, lands = [], []
    for t0, size, ims, width, sp in rows:
        x = (W - width) / 2
        for wi, im in enumerate(ims):
            placed.append((im, int(x) - 20, y - 20, t0 + wi * STAGGER))
            x += im.width - 40 + sp
        lands.append(t0 + (len(ims) - 1) * STAGGER + RISE * 0.7)
        y += int(size * 1.12)
    return placed, lands


def words_layer(placed, t, exit_k):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for im, x, y, s in placed:
        p = (t - s) / RISE
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
        sh = Image.new("RGBA", w.size, (0, 0, 0, 0))
        sh.putalpha(w.getchannel("A").filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.6)))
        layer.alpha_composite(sh, (x + 4, int(y + 46 * (1 - e)) + 8))
        layer.alpha_composite(w, (x, int(y + 46 * (1 - e))))
    return layer


# ----------------------------------------------------------------------------- footage

def bg_frames(clip, src, speed, dur):
    n = int(round(dur * FPS)) + 2
    vf = f"setpts={1 / speed}*PTS,fps={FPS},scale=960:540"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(src), "-i", A(clip), "-vf", vf, "-frames:v", str(n),
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    last = None
    for _ in range(n):
        buf = p.stdout.read(960 * 540 * 3)
        if len(buf) == 960 * 540 * 3:
            last = np.frombuffer(buf, np.uint8).reshape(540, 960, 3)
        yield last
    p.stdout.close()
    p.wait()


def first_frame():
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(OUT, "IPL_Ko_Kisne_Maara.mp4"), "-frames:v", "1",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(H, W, 3).astype(np.float32)


def frames(only=None):
    """Yield (hook time, RGB uint8 frame). `only`: set of frame indices to actually draw (contact sheet)."""
    film0 = first_frame()
    rng = np.random.default_rng(7)
    prev_last = None
    for si, (t0, dur, (clip, src, speed), lines, weight, blur_in, final) in enumerate(SEGS):
        placed, lands = place_words(lines)
        hit = lands[-1] if weight else None
        src_frames = bg_frames(clip, src, speed, dur)
        n = int(round(dur * FPS))
        for i in range(n):
            small = next(src_frames)
            gi = int(round(t0 * FPS)) + i
            if only is not None and gi not in only:
                continue
            t = t0 + i / FPS
            lt = i / FPS
            frame = vh.grade_bg(small, lt, dur, blur_in)
            if si == 3:                                        # the quiet line: darker
                frame = frame * 0.62
            if prev_last is not None and lt < 0.16:
                a = lt / 0.16
                frame = prev_last * (1 - a) + frame * a
            exit_k = ease((lt - (dur - 0.24)) / 0.24) if not final else 0.0
            layer = words_layer(placed, t, exit_k)
            sc, jx, jy = 1.0, 0, 0
            if hit is not None and 0 <= t - hit < 0.3:
                k = t - hit
                sc = 1.0 + 0.05 * np.exp(-k * 18)
                amp = 12 * (1 - k / 0.3) * weight
                jx, jy = rng.uniform(-amp, amp, 2)
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
            if hit is not None and t >= hit:
                frame = frame + 255 * 0.2 * weight * np.exp(-(t - hit) * 14)
            if lt < 0.12 and si:
                frame = frame + 255 * 0.22 * (1 - lt / 0.12)
            if final:
                f_out = ease((lt - (dur - 0.5)) / 0.5)
                if f_out > 0:
                    frame = frame * (1 - f_out) + film0 * f_out + 255 * np.sin(np.pi * f_out) * 0.45
            frame = np.clip(frame, 0, 255)
            prev_last = frame
            yield t, frame.astype(np.uint8)


def hits():
    out = []
    for t0, dur, _, lines, weight, _, final in SEGS:
        if weight:
            out.append((place_words(lines)[1][-1], weight))
    return out


# ----------------------------------------------------------------------------- sound

def at(buf, x, t, g):
    i = int(t * SR)
    if 0 <= i < len(buf):
        n = min(len(x), len(buf) - i)
        buf[i:i + n] += x[:n] * g


def beep(dur, f=1000.0):
    t = np.arange(int(SR * dur)) / SR
    return np.sin(2 * np.pi * f * t) * np.minimum(1, (dur - t) / 0.03) * np.minimum(1, t / 0.004)


def soundtrack(path):
    n = int(DUR * SR)
    tt = np.arange(n) / SR
    bed = vh.drone(DUR) * np.interp(tt, [0, 7.0, 7.5, 9.7, 10.2, DUR], [0.16, 0.18, 0.05, 0.06, 0.15, 0.1])
    fx = np.zeros(n)
    for t, w in hits():
        at(fx, vh.braam(weight=min(w, 1.3)), t, 0.55 + 0.35 * w / 1.3)
    for t0, *_ in SEGS[1:]:
        at(fx, sfx.whoosh(0.4), t0 - 0.22, 0.22)
    for tb, g in [(10.1, 0.5), (10.95, 0.4), (11.95, 0.3)]:      # slowing heartbeat under "dheere dheere"
        at(fx, sfx.heartbeat(), tb, g)
    flat = beep(DUR - FLAT) * np.interp(np.linspace(0, 1, int((DUR - FLAT) * SR)), [0, 0.6, 1], [1, 1, 0])
    at(fx, flat, FLAT, 0.07)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(HERE, "vo", "hook_raw.mp3"), "-ac", "1",
                          "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    vo = np.frombuffer(raw, np.float32).astype(np.float64)
    voice = np.zeros(n)
    at(voice, vo / (np.abs(vo).max() + 1e-9) * 0.9, OFF, 1.0)
    duck = 1 - 0.45 * np.convolve(np.abs(voice) > 0.02, np.ones(int(0.15 * SR)) / int(0.15 * SR), "same")
    mix = voice + (bed + fx * 0.8) * duck
    tail = int(0.3 * SR)
    mix[-tail:] *= np.linspace(1, 0, tail)
    mix = np.tanh(mix * 1.05) * 0.95
    pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(np.repeat(pcm[:, None], 2, axis=1).tobytes())


# ----------------------------------------------------------------------------- render + join

def sheet():
    ts = [0.9, 2.6, 3.4, 4.7, 5.8, 6.6, 8.2, 9.3, 10.6, 11.9, 12.8, 13.8]
    idx = {int(round(t * FPS)) for t in ts}
    got = {int(round(t * FPS)): Image.fromarray(f).resize((480, 270)) for t, f in frames(idx)}
    sh = Image.new("RGB", (1920, 810))
    for k, i in enumerate(sorted(got)):
        sh.paste(got[i], ((k % 4) * 480, (k // 4) * 270))
    os.makedirs(os.path.join(OUT, "chk"), exist_ok=True)
    sh.save(os.path.join(OUT, "chk", "hook_sheet.jpg"))


def main():
    if "--sheet" in sys.argv:
        return sheet()
    wav = os.path.join(OUT, "hook.wav")
    soundtrack(wav)
    silent = os.path.join(OUT, "hook_video.mp4")
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                            "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    for _, f in frames():
        enc.stdin.write(f.tobytes())
    enc.stdin.close()
    enc.wait()
    hook = os.path.join(OUT, "hook.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", silent, "-i", wav, "-c:v", "copy",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
                    "-shortest", hook], check=True)
    full = os.path.join(OUT, "IPL_Ko_Kisne_Maara_hook.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", hook, "-i", os.path.join(OUT, "IPL_Ko_Kisne_Maara.mp4"),
                    "-filter_complex", "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]", "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "256k", "-ar", "48000", full], check=True)
    up = os.path.join(OUT, "IPL_Ko_Kisne_Maara_hook_upload.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", full, "-c:v", "libx264", "-preset", "medium",
                    "-b:v", "5M", "-maxrate", "6M", "-bufsize", "10M", "-pix_fmt", "yuv420p", "-c:a", "copy", up],
                   check=True)
    print("HOOK_DONE", full, up)


if __name__ == "__main__":
    main()

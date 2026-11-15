#!/usr/bin/env python3
"""Cinematic cold open for "IPL Ko Kisne Maara?" (~14 s), joined in front of the finished video.

Style taken from the channel's Virat 82* (MCG 2022) hook: sharp real footage in smooth slow motion (motion-
interpolated, not frame-blended), hard cuts every 1.5-2 s, thin letterbox bars, a dark moody grade with a heavy
vignette, and a small two-line caption bottom-left behind a thin yellow bar (line 1 white, line 2 yellow,
sentence case).

VO (vo/hook_raw.mp3): "17 November, retention lists out. Crores ki deals, bade naam release... par ek sawal koi
nahi pooch raha: kya IPL dheere dheere mar raha hai?"
Bridge (vo/bridge_raw.mp3), over the IPL KO KISNE MAARA? title card: "Chalo, case kholte hain."

Footage: only stretches of the clean IPL clips (logos and score bars cropped) the main video doesn't use.

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
import virat_hook as vh  # noqa: E402  (braam, drone)

W, H, FPS = 1920, 1080, 30
Y = (255, 222, 89)
BOLD = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
SR = sfx.SR
OUT = os.path.join(HERE, "out")
CACHE = os.path.join(OUT, "hookcache")
OFF = 0.35                       # VO starts here; all times below are hook time
BAR = 42                         # letterbox bar height

# (start, dur, clip, src start, speed, push-in direction)
SHOTS = [
    (0.00, 1.80, "kkr_clean", 5.45, 0.45, 1),            # Eden pavilion stands
    (1.80, 1.95, "kkr_clean", 8.00, 0.45, -1),           # floodlight tower (camera cuts at 9.0)
    (3.75, 1.60, "jadeja_six_clean", 10.95, 0.40, 1),    # CSK crowd erupting
    (5.35, 1.70, "jadeja_spin_clean", 12.75, 0.45, -1),  # helmet close-ups, batter and Dhoni
    (7.05, 1.35, "livingstone_clean", 3.62, 0.45, 1),    # stadium lights at night
    (8.40, 1.35, "reel_six", 0.05, 0.45, -1),            # bowler running in
    (9.75, 1.65, "jadeja_spin_clean", 5.85, 0.40, 1),    # Dhoni keeping, batter waiting
    (11.40, 2.60, "jadeja_spin_clean", 7.70, 0.30, 1),   # ball into the stumps, very slow
]
SHOTS_END = SHOTS[-1][0] + SHOTS[-1][1]
# bridge: "Chalo, case kholte hain." (vo/bridge_raw.mp3) over the title card, then into the video
TITLE_DUR = 3.4
BRIDGE_AT = SHOTS_END + 0.2           # bridge VO start
TITLE_HIT = SHOTS_END + 1.0           # title slams on "case"
DUR = SHOTS_END + TITLE_DUR
# (line 1 in, line 2 in, out, line 1, line 2)
CAPS = [
    (0.40, 1.90, 3.70, "17 November.", "Retention lists out."),
    (4.15, 5.45, 7.00, "Crores in deals.", "Big names released."),
    (7.35, 8.30, 9.70, "But one question", "nobody is asking."),
    (10.00, 11.40, 13.55, "Is IPL", "slowly dying?"),
]
HITS = [(1.90, 0.55), (5.45, 0.9), (11.40, 1.2)]   # soft braam under the key lines
FLAT = 12.95


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


# ----------------------------------------------------------------------------- footage

def shot_file(k):
    """Pre-render one shot: cut, slow down with motion interpolation (smooth slow-mo), 1080p, cached."""
    t0, dur, clip, src, speed, _ = SHOTS[k]
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f"shot{k}_{clip}_{src}_{speed}.mp4")
    if not os.path.exists(path):
        need = dur * speed + 0.2
        vf = (f"setpts={1 / speed:.4f}*PTS,minterpolate=fps={FPS}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,"
              f"scale={W}:{H}:flags=lanczos")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(src), "-t", f"{need:.3f}",
                        "-i", os.path.join(HERE, "assets", clip + ".mp4"), "-vf", vf, "-an",
                        "-c:v", "libx264", "-preset", "fast", "-crf", "14", path], check=True)
    return path


def read_frames(path, n):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-frames:v", str(n), "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    last = None
    for _ in range(n):
        buf = p.stdout.read(W * H * 3)
        if len(buf) == W * H * 3:
            last = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        yield last
    p.stdout.close()
    p.wait()


_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = (1 - 0.5 * np.clip(((_xx - W / 2) / (W * 0.6)) ** 2 + ((_yy - H / 2) / (H * 0.62)) ** 2, 0, 1) ** 1.2)[..., None]
LOW = np.clip((_yy - H * 0.45) / (H * 0.55), 0, 1)[..., None] * np.clip(1 - _xx / (W * 0.55), 0, 1)[..., None]


def grade(fr, lt, dur, direction):
    """Slow push-in, then dark cinematic grade: lifted contrast, less colour, teal shadows, heavy vignette."""
    z = 1.02 + 0.05 * (lt / dur)
    im = Image.fromarray(fr)
    cw, ch = W / z, H / z
    cx = W / 2 + direction * 20 * (lt / dur)
    im = im.crop((cx - cw / 2, (H - ch) / 2, cx + cw / 2, (H + ch) / 2)).resize((W, H), Image.BILINEAR)
    a = np.asarray(im, np.float32) / 255
    lum = a.mean(-1, keepdims=True)
    a = lum + (a - lum) * 0.78
    a = np.clip((a - 0.5) * 1.15 + 0.52, 0, 1) ** 0.98
    a = a * (1 - 0.08 * (1 - lum)) + np.array([0.0, 0.025, 0.04]) * (1 - lum)    # teal in the shadows
    a = a * 1.0 * VIG
    a = a * (1 - 0.3 * LOW)                                                   # room for the caption
    return a * 255


# ----------------------------------------------------------------------------- caption

FONT = ImageFont.truetype(BOLD, 74)


def caption(base, t):
    for l1_in, l2_in, out_t, l1, l2 in CAPS:
        if not (l1_in - 0.05 <= t < out_t):
            continue
        x, y = 92, 700
        fade_out = 1 - ease((t - (out_t - 0.25)) / 0.25)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        bar_h = 0
        for k, (txt, col, t_in) in enumerate([(l1, (255, 255, 255), l1_in), (l2, Y, l2_in)]):
            p = ease((t - t_in) / 0.35)
            if p <= 0:
                continue
            a = int(255 * p * fade_out)
            yy = y + k * 88 + int(18 * (1 - p))
            d.text((x + 34, yy), txt, font=FONT, fill=col + (a,))
            bar_h = max(bar_h, (k + 1) * 88 * p)
        if bar_h > 14:
            d.rectangle((x, y + 8, x + 6, y + 8 + bar_h - 12), fill=Y + (int(255 * fade_out),))
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sh.putalpha(lay.getchannel("A").filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.55)))
        base.alpha_composite(sh, (3, 5))
        base.alpha_composite(lay)


# ----------------------------------------------------------------------------- frames

def first_frame():
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(OUT, "IPL_Ko_Kisne_Maara.mp4"), "-frames:v", "1",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(H, W, 3).astype(np.float32)


def frames(only=None):
    film0 = first_frame()
    for k, (t0, dur, clip, src, speed, direction) in enumerate(SHOTS):
        n = int(round(dur * FPS))
        g0 = int(round(t0 * FPS))
        if only is not None and not any(g0 <= i < g0 + n for i in only):
            continue
        src_frames = read_frames(shot_file(k), n)
        for i in range(n):
            fr = next(src_frames)
            if only is not None and g0 + i not in only:
                continue
            t, lt = t0 + i / FPS, i / FPS
            a = grade(fr, lt, dur, direction)
            if k == len(SHOTS) - 1:                       # white flash out into the title card
                f_out = ease((lt - (dur - 0.3)) / 0.3)
                if f_out > 0:
                    a = a + 255 * 0.55 * f_out
            base = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
            caption(base, t)
            out = np.asarray(base.convert("RGB")).copy()
            out[:BAR] = 0
            out[H - BAR:] = 0
            yield t, out
    yield from title_frames(film0, only)


TITLE_FONT = ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Black.otf", 150)
KICK_FONT = ImageFont.truetype(BOLD, 40)


def title_layer(lt):
    """CASE FILE kicker, then IPL KO KISNE MAARA? slamming in (KISNE yellow)."""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    k = ease((lt - 0.25) / 0.5)
    if k > 0:
        txt = "CASE FILE  ·  #IPL2026"
        tr = 22 - 12 * k
        w = sum(KICK_FONT.getlength(c) for c in txt) + tr * (len(txt) - 1)
        x = (W - w) / 2
        for c in txt:
            d.text((x, 372), c, font=KICK_FONT, fill=(225, 225, 225, int(255 * k)))
            x += KICK_FONT.getlength(c) + tr
        d.rectangle((W / 2 - 60 * k, 440, W / 2 + 60 * k, 445), fill=Y + (int(255 * k),))
    p = ease((lt - (TITLE_HIT - SHOTS_END - 0.12)) / 0.12)
    if p > 0:
        words = [("IPL KO ", (255, 255, 255)), ("KISNE ", Y), ("MAARA?", (255, 255, 255))]
        tw = sum(TITLE_FONT.getlength(w) for w, _ in words)
        t_im = Image.new("RGBA", (int(tw) + 40, 220), (0, 0, 0, 0))
        td = ImageDraw.Draw(t_im)
        x = 20
        for w, col in words:
            td.text((x, 20), w, font=TITLE_FONT, fill=col)
            x += TITLE_FONT.getlength(w)
        s = 1.35 - 0.35 * p
        t_im = t_im.resize((int(t_im.width * s), int(t_im.height * s)), Image.BILINEAR)
        t_im.putalpha(t_im.getchannel("A").point(lambda v: int(v * p)))
        sh = Image.new("RGBA", t_im.size, (0, 0, 0, 0))
        sh.putalpha(t_im.getchannel("A").filter(ImageFilter.GaussianBlur(16)).point(lambda v: int(v * 0.6)))
        cx, cy = (W - t_im.width) // 2, 560 - t_im.height // 2
        lay.alpha_composite(sh, (cx + 5, cy + 8))
        lay.alpha_composite(t_im, (cx, cy))
    return lay


def title_frames(film0, only):
    """Blurred dark freeze of the stumps shot, slowly pushing in, with the title; flash-dissolve into the video."""
    k = len(SHOTS) - 1
    raw = subprocess.run(["ffmpeg", "-v", "error", "-sseof", "-0.1", "-i", shot_file(k), "-frames:v", "1",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    freeze = np.frombuffer(raw, np.uint8).reshape(H, W, 3)
    freeze = np.asarray(Image.fromarray(freeze).filter(ImageFilter.GaussianBlur(14)), np.uint8)
    rng = np.random.default_rng(11)
    g0 = int(round(SHOTS_END * FPS))
    for i in range(int(round(TITLE_DUR * FPS))):
        if only is not None and g0 + i not in only:
            continue
        lt = i / FPS
        t = SHOTS_END + lt
        a = grade(freeze, lt, TITLE_DUR, 1) * 0.5
        a = a + 255 * 0.55 * np.exp(-lt * 9)                      # flash carried over from the cut
        hit = TITLE_HIT - SHOTS_END
        if lt >= hit:
            a = a + 255 * 0.22 * np.exp(-(lt - hit) * 14)
        lay = title_layer(lt)
        if 0 <= lt - hit < 0.3:                                   # punch + shake on the hit
            kk = lt - hit
            sc = 1 + 0.05 * np.exp(-kk * 18)
            amp = 12 * (1 - kk / 0.3)
            jx, jy = rng.uniform(-amp, amp, 2)
            big = lay.resize((int(W * sc), int(H * sc)), Image.BILINEAR)
            ox, oy = int((big.width - W) / 2 - jx), int((big.height - H) / 2 - jy)
            lay = big.crop((ox, oy, ox + W, oy + H))
        la = np.asarray(lay, np.float32)
        al = la[..., 3:4] / 255
        a = a * (1 - al) + la[..., :3] * al
        f_out = ease((lt - (TITLE_DUR - 0.45)) / 0.45)
        if f_out > 0:
            a = a * (1 - f_out) + film0 * f_out + 255 * np.sin(np.pi * f_out) * 0.35
        out = np.clip(a, 0, 255).astype(np.uint8)
        bar = int(BAR * (1 - f_out))
        if bar:
            out[:bar] = 0
            out[H - bar:] = 0
        yield t, out


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
    bed = vh.drone(DUR) * np.interp(tt, [0, 7.0, 7.5, 9.7, 10.2, DUR], [0.17, 0.19, 0.06, 0.07, 0.16, 0.1])
    fx = np.zeros(n)
    for t, w in HITS:
        at(fx, vh.braam(weight=w), t - 0.03, 0.35 + 0.3 * w)
    for tb, g in [(10.1, 0.5), (10.95, 0.4), (11.95, 0.3)]:      # slowing heartbeat under "dheere dheere"
        at(fx, sfx.heartbeat(), tb, g)
    at(fx, vh.braam(weight=1.3), TITLE_HIT - 0.03, 0.75)
    at(fx, sfx.whoosh(0.4), SHOTS_END - 0.3, 0.25)
    flat = beep(SHOTS_END - FLAT) * np.interp(np.linspace(0, 1, int((SHOTS_END - FLAT) * SR)), [0, 0.6, 1], [1, 1, 0])
    at(fx, flat, FLAT, 0.06)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(HERE, "vo", "hook_raw.mp3"), "-ac", "1",
                          "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    vo = np.frombuffer(raw, np.float32).astype(np.float64)
    voice = np.zeros(n)
    at(voice, vo / (np.abs(vo).max() + 1e-9) * 0.9, OFF, 1.0)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(HERE, "vo", "bridge_raw.mp3"), "-ac", "1",
                          "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    br = np.frombuffer(raw, np.float32).astype(np.float64)
    at(voice, br / (np.abs(vo).max() + 1e-9) * 0.9, BRIDGE_AT, 1.0)   # same gain as the hook VO
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
    ts = [0.9, 4.6, 6.2, 9.0, 11.8, 13.9, 14.3, 14.9, 15.1, 15.8, 16.8, 17.3]
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
    if "--hook-only" in sys.argv:
        return print("HOOK_ONLY", hook)
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

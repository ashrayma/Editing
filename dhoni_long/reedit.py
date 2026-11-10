#!/usr/bin/env python3
"""Re-edit of Dhoni2011_Masterstroke_v3 to the retention plan (Kohli Cried analysis).

    python3 reedit.py  ->  out/Dhoni2011_Masterstroke_v4.mp4

Works on the finished v3 (src/v3.mp4): every cut sits inside a voice pause found in the speech band
(src/pauses.json), so no word is clipped. Changes:
  - first frame = the "2007 = 2011?" thumbnail, crossfading into the original opening (voice untouched)
  - chapter 1 ("The hero", Yuvraj's stats, both tosses) cut; the final now starts at Mahela's 103*
  - cuts only at section boundaries, so every sentence stays whole
  - re-hook card before the Murali chapter, re-hook card before the finish
  - Murali's quote card held 2 s in silence; light comic beat after "not even a toilet break"
  - Yuvraj-tumour aside cut
  - the six: 0.5 s silence, the ball, then an impact + 2x slow-motion replay (no voice removed)
  - Kulasekara, Gavaskar / seat 210 and the close kept whole, in the original order
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
from virat_hook import braam, drone  # noqa: E402

SRC = os.path.join(HERE, "src", "v3.mp4")
TMP = os.path.join(HERE, "out", "parts")
OUT = os.path.join(HERE, "out", "Dhoni2011_Masterstroke_v4.mp4")
THUMB = os.path.join(ROOT, "dhoni_2007_2011", "thumb_dhoni.png")
ANTON = os.path.join(ROOT, "doc_video", "thumb", "fonts", "Anton-Regular.woff")
XB = "/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf"
W, H, FPS, SR = 1920, 1080, 30, 48000
Y, WHITE = (255, 222, 89), (255, 255, 255)
ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS),
       "-c:a", "aac", "-b:a", "256k", "-ar", str(SR), "-ac", "2"]

# the new running order: (kind, args)
EDL = [
    ("clip", 0.00, 78.50, "thumb_open"),          # hook + "4 years earlier" tease + title
    ("clip", 141.20, 149.30, None),                 # 274/6 -> 275 to win
    ("clip", 199.05, 265.70, None),                 # 114/3 -> out walked Dhoni -> GUWAHATI 2007 -> same result
    ("card", ("PAR ASLI TWIST ABHI BAAKI HAI…", "MURALI NE KHUD KYA BOLA?"), 3.0, None),
    ("clip", 265.70, 290.05, None),                 # THE MURALI SECRET ... the quote
    ("hold", 290.00, 2.0, None),                    # quote breathes: 2 s, music only
    ("clip", 290.05, 370.85, None),                 # the chase ... "not even a toilet break"
    ("beat", 370.85, 0.7, None),                    # comic pause + pop
    ("clip", 370.85, 394.10, None),                 # superstition, the man Dhoni held back
    ("card", ("AUR PHIR WOH OVER AAYA…", "JISKA PLAN 4 SAAL PEHLE BANA THA"), 3.0, None),
    ("clip", 411.75, 429.70, None),                 # THE FINISH, over 49, the 4
    ("clip", 459.75, 463.00, None),                 # time stood still
    ("hush", 463.00, 0.5, None),                    # 0.5 s silence before the ball
    ("clip", 463.00, 465.25, None),                 # the six, real time
    ("slomo", 464.35, 465.25, None),                # impact + 2x slow-motion replay of the contact
    ("clip", 465.25, 486.15, None),                 # ball in the stands, MS DHONI, Shastri's call
    ("clip", 429.70, 459.75, None),                 # Kulasekara in full (later at CSK under Dhoni, his line),
                                                    # Gavaskar and the ball near seat 210, L block
    ("clip", 500.55, 529.00, None),                 # 28 years. they say a six won it. it was a plan. end screen
]


def run(*a):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)


def write_wav(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(np.repeat((x * 32767).astype(np.int16)[:, None], 2, axis=1).tobytes())


def resample(x, sr_from=sfx.SR):
    n = int(len(x) * SR / sr_from)
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x).astype(np.float32)


def clip(i, a, b, extra):
    out = os.path.join(TMP, f"{i:02d}.mp4")
    d = b - a
    af = f"afade=t=in:d=0.04,afade=t=out:st={d - 0.06:.3f}:d=0.06"
    if extra == "thumb_open":  # thumbnail as the first frame, dissolving into the original opening by 1.4 s
        run("-ss", str(a), "-t", str(d), "-i", SRC, "-loop", "1", "-t", "1.6", "-i", THUMB,
            "-filter_complex",
            "[1:v]scale=1920:1080,zoompan=z='1.0+0.0012*on':d=1:s=1920x1080:fps=30,format=rgba,"
            "fade=t=out:st=0.9:d=0.6:alpha=1[t];[0:v][t]overlay=0:0:eof_action=pass,format=yuv420p[v]",
            "-map", "[v]", "-map", "0:a", "-af", af, *ENC, out)
    else:
        run("-ss", str(a), "-t", str(d), "-i", SRC, "-af", af, *ENC, out)
    return out


def still_of(t):
    p = os.path.join(TMP, f"still_{t:.2f}.png")
    run("-ss", str(t), "-i", SRC, "-frames:v", "1", p)
    return p


def audio_only(i, x):
    p = os.path.join(TMP, f"{i:02d}.wav")
    write_wav(p, x)
    return p


def hold(i, t, dur):
    """Freeze the quote card; voice gone, a soft drone keeps it alive."""
    s = still_of(t)
    a = resample(drone(dur)) * 0.05
    a *= np.minimum(1, np.linspace(0, dur / 0.3, len(a))) * np.minimum(1, np.linspace(dur / 0.3, 0, len(a)))
    out = os.path.join(TMP, f"{i:02d}.mp4")
    run("-loop", "1", "-t", str(dur), "-i", s, "-i", audio_only(i, a),
        "-vf", f"zoompan=z='1.0+0.0007*on':d=1:s=1920x1080:fps=30", "-shortest", *ENC, out)
    return out


def beat(i, t, dur):
    s = still_of(t)
    a = np.zeros(int(dur * SR), np.float32)
    p = resample(sfx.pop()) * 0.35
    a[int(0.15 * SR):int(0.15 * SR) + len(p)] += p
    out = os.path.join(TMP, f"{i:02d}.mp4")
    run("-loop", "1", "-t", str(dur), "-i", s, "-i", audio_only(i, a), "-shortest", *ENC, out)
    return out


def hush(i, t, dur):
    s = still_of(t)
    out = os.path.join(TMP, f"{i:02d}.mp4")
    run("-loop", "1", "-t", str(dur), "-i", s, "-i", audio_only(i, np.zeros(int(dur * SR), np.float32)),
        "-shortest", *ENC, out)
    return out


def slomo(i, a, b):
    """1 s of the shot stretched to 2 s, with the impact hit."""
    d = (b - a) * 2
    x = np.zeros(int(d * SR), np.float32)
    for h, g in ((resample(sfx.impact()), 0.55), (resample(braam(1.8, 1.0)), 0.35)):
        h = h[: len(x)]
        x[: len(h)] += h * g
    out = os.path.join(TMP, f"{i:02d}.mp4")
    run("-ss", str(a), "-t", str(b - a), "-i", SRC, "-i", audio_only(i, x),
        "-filter_complex", "[0:v]setpts=2.0*PTS,minterpolate=fps=30:mi_mode=blend[v]",
        "-map", "[v]", "-map", "1:a", "-t", str(d), *ENC, out)
    return out


def card(i, lines, dur):
    """Re-hook card in the film's style: dark plate, Anton, yellow bar."""
    base = Image.open(still_of(394.0)).convert("RGB").filter(ImageFilter.GaussianBlur(24))
    a = np.asarray(base, np.float32) * 0.28
    img = Image.fromarray(a.astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    f1, f2 = ImageFont.truetype(ANTON, 110), ImageFont.truetype(ANTON, 84)
    y = 380
    for txt, f, col in ((lines[0], f1, WHITE), (lines[1], f2, Y)):
        w = d.textlength(txt, font=f)
        d.text(((W - w) / 2, y), txt, font=f, fill=col)
        y += 150
    d.rectangle((W / 2 - 220, y + 10, W / 2 + 220, y + 18), fill=Y)
    p = os.path.join(TMP, f"card_{i}.png")
    img.convert("RGB").save(p)
    x = resample(drone(dur)) * 0.10
    hb = resample(braam(min(dur, 3.0), 0.9))[: len(x)] * 0.45
    x[: len(hb)] += hb
    wh = resample(sfx.whoosh()) * 0.15
    x[: len(wh)] += wh
    x *= np.minimum(1, np.linspace(dur / 0.25, 0, len(x)))
    out = os.path.join(TMP, f"{i:02d}.mp4")
    run("-loop", "1", "-t", str(dur), "-i", p, "-i", audio_only(i, x),
        "-vf", "zoompan=z='1.0+0.0006*on':d=1:s=1920x1080:fps=30,fade=t=in:d=0.2", "-shortest", *ENC, out)
    return out


def main():
    os.makedirs(TMP, exist_ok=True)
    parts = []
    i = 0
    for kind, a, b, extra in EDL:
        if kind == "clip":
            parts.append(clip(i, a, b, extra))
        elif kind == "hold":
            parts.append(hold(i, a, b))
        elif kind == "beat":
            parts.append(beat(i, a, b))
        elif kind == "hush":
            parts.append(hush(i, a, b))
        elif kind == "slomo":
            parts.append(slomo(i, a, b))
        elif kind == "card":
            parts.append(card(i, a, b))
        i += 1
        print("part", i, kind, flush=True)
    lst = os.path.join(TMP, "list.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{p}'\n" for p in parts)
    joined = os.path.join(TMP, "joined.mp4")
    run("-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined)
    run("-i", joined, "-c:v", "libx264", "-preset", "slow", "-b:v", "10M", "-maxrate", "14M", "-bufsize", "20M",
        "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", str(SR), "-c:a", "aac",
        "-b:a", "256k", "-movflags", "+faststart", OUT)
    print("V4_DONE", OUT)


if __name__ == "__main__":
    main()

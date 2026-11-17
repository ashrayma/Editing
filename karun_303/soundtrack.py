#!/usr/bin/env python3
"""Score + sound design for "303" (all synthesised here, royalty-free) -> out/soundtrack.wav

    python3 soundtrack.py

Music follows the chapters: suspense under the cold open, a dark drone at the river, a driving groove through the
303 innings, a ticking pulse for "the benchmark", a heavy pad when he is dropped, tension through Australia, an
almost-empty bed for the silent years, a build from the county hundred into Vidarbha and the IPL, a hopeful lift
for the comeback that deflates, and a warm, slow close. SFX land on every on-screen event logged by gen.py; the
highlight clips keep their own crowd sound underneath (loudest on the 300). Music and nat sound duck under the voice.
"""
import json
import os
import subprocess
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "kohli_countdown"))
sys.path.insert(0, os.path.join(HERE, "..", "doc_video"))
import music  # noqa: E402
import sfx  # noqa: E402
from music import add  # noqa: E402
from soundtrack import A_MINOR, D_MINOR, WARM, arps, norm, pad, pulse, reverb, section, ticker  # noqa: E402

SR = sfx.SR


def load_wav(path):
    with wave.open(path) as w:
        sr, ch = w.getframerate(), w.getnchannels()
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    if ch == 2:
        x = x.reshape(-1, 2).mean(1)
    if sr != SR:
        n = int(len(x) * SR / sr)
        x = np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x).astype(np.float32)
    return x


def clip_audio(src, start, dur):
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(start), "-i", os.path.join(HERE, src), "-t", str(dur),
                          "-vn", "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
    return np.frombuffer(pcm, np.int16).astype(np.float32) / 32768


def main():
    ev = json.load(open(os.path.join(HERE, "out", "events.json")))
    total, B = ev["total"], ev["beats"]
    s = lambda beat, off=0.0: B[beat][0] + off  # noqa: E731
    N = int(SR * total)

    # ------------------------------------------------------------------ music, chapter by chapter
    m = np.zeros(N)

    def bed(x, t0, t1, fi=1.5, fo=1.5, g=1.0):
        m[:] += section(norm(x[: int((t1 - t0 + 2) * SR)]) * g, t0, total, fi, fo)

    t0, t1 = 0.0, s("river")
    bed(reverb(pad(A_MINOR, t1 - t0 + 2, 4.0, 1100), 2.0, 0.35) * 0.6 + norm(pulse(t1 - t0 + 2, 84, lambda t: min(1, t / 40))) * 0.5,
        t0, t1, 0.3, 1.2, 0.55)
    t0, t1 = s("river"), s("debut")
    bed(reverb(pad(D_MINOR, t1 - t0 + 2, 6.0, 700), 3.0, 0.45), t0, t1, 2.0, 1.5, 0.5)
    t0, t1 = s("debut"), s("pressure_q")
    bed(music.track(t1 - t0 + 2), t0, t1, 1.0, 2.0, 0.6)
    t0, t1 = s("pressure_q"), s("judged")
    bed(reverb(pad(WARM, t1 - t0 + 2, 4.0, 1300), 2.5, 0.4), t0, t1, 1.5, 1.0, 0.42)
    t0, t1 = s("judged"), s("hyderabad")
    bed(pulse(t1 - t0 + 2, 96, lambda t: 0.5) * 0.6 + norm(ticker(t1 - t0 + 2, 120)) * 0.35 +
        norm(reverb(pad(A_MINOR, t1 - t0 + 2, 4.0, 900), 2.0, 0.3)) * 0.4, t0, t1, 1.0, 1.0, 0.5)
    t0, t1 = s("hyderabad"), s("australia")
    bed(reverb(pad(D_MINOR, t1 - t0 + 2, 5.0, 850), 2.5, 0.4), t0, t1, 1.5, 1.5, 0.45)
    t0, t1 = s("australia"), s("eng2018")
    bed(pulse(t1 - t0 + 2, 88, lambda t: min(1, t / 30)) * 0.6 + norm(reverb(pad(A_MINOR, t1 - t0 + 2, 4.0, 900), 2.0, 0.3)) * 0.5,
        t0, t1, 1.0, 1.5, 0.5)
    t0, t1 = s("eng2018"), s("crack")
    bed(reverb(pad(D_MINOR, t1 - t0 + 2, 8.0, 600), 3.5, 0.5), t0, t1, 2.0, 2.0, 0.38)
    t0, t1 = s("crack"), s("headingley")
    bed(norm(music.track(t1 - t0 + 2)) * 0.7 + norm(reverb(arps(WARM, t1 - t0 + 2), 1.5, 0.3)) * 0.3, t0, t1, 3.0, 1.5, 0.58)
    t0, t1 = s("headingley"), s("wi_2025")
    bed(reverb(pad(WARM, t1 - t0 + 2, 4.0, 1500), 2.5, 0.4) + norm(pulse(t1 - t0 + 2, 90, lambda t: 0.4)) * 0.3, t0, t1, 1.5, 1.5, 0.5)
    t0, t1 = s("wi_2025"), s("villains")
    bed(reverb(pad(D_MINOR, t1 - t0 + 2, 5.0, 800), 2.5, 0.45), t0, t1, 1.0, 1.0, 0.45)
    t0, t1 = s("villains"), total
    bed(reverb(pad(WARM, t1 - t0 + 2, 4.0, 1600), 2.5, 0.4) * 0.6 + norm(reverb(arps(WARM, t1 - t0 + 2), 1.5, 0.3)) * 0.4,
        t0, t1, 2.0, 3.5, 0.5)

    # ------------------------------------------------------------------ voice
    vo = np.zeros(N)
    v = load_wav(os.path.join(HERE, "out", "vo_clean.wav"))
    i = int(ev["lead"] * SR)
    vo[i:i + len(v)] = v[: N - i]

    # ------------------------------------------------------------------ natural sound from the highlight clips
    nat = np.zeros(N)
    loud = {"three_hundred_four.mp4": 0.9, "hundred_roar.mp4": 0.6, "crowd_200.mp4": 0.55, "two_hundred_helmet.mp4": 0.5,
            "cook_drop.mp4": 0.45, "root_drop.mp4": 0.45}
    for start, src, ms, dur in ev["nat"]:
        x = clip_audio(src, ms, dur)
        if len(x) == 0:
            continue
        f = int(0.15 * SR)
        x[:f] *= np.linspace(0, 1, min(f, len(x)))[: len(x[:f])]
        x[-f:] *= np.linspace(1, 0, min(f, len(x)))[-len(x[-f:]):]
        add(nat, x, start, loud.get(os.path.basename(src), 0.3))

    # ------------------------------------------------------------------ duck music + nat under the voice
    hop = SR // 100
    env = np.abs(vo[: N // hop * hop]).reshape(-1, hop).max(1)
    env = np.convolve(env > 0.03, np.ones(25), "same") > 0
    duck = np.repeat(np.where(env, 0.38, 1.0), hop)
    duck = np.convolve(duck, np.ones(SR // 8) / (SR // 8), "same")
    m[: len(duck)] *= duck
    nat[: len(duck)] *= np.clip(duck * 0.9, 0, 1)

    # ------------------------------------------------------------------ SFX on events
    fx = np.zeros(N)
    cache = {}

    def put(name, t, g):
        if name not in cache:
            cache[name] = getattr(sfx, name)()
        add(fx, cache[name], max(0, t), g)

    last = {}
    for e in ev["events"]:
        t, kind = e[0], e[1]
        if t - last.get(kind, -9) < 0.12:   # never stack the same sound
            continue
        last[kind] = t
        if kind == "whoosh":
            put("whoosh", t - 0.12, 0.16)
        elif kind == "cut":
            put("whoosh", t - 0.10, 0.10)
        elif kind == "paper":
            put("camera_shutter", t, 0.10)
            put("whoosh", t - 0.08, 0.07)
        elif kind == "tick":
            put("tick", t, 0.12)
        elif kind == "slam":
            put("impact", t, 0.22)
        elif kind == "roll":
            for k in range(8):
                put("tick", t + 0.05 * k, 0.08)
        elif kind == "pop":
            put("pop", t, 0.14)
        elif kind == "stamp":
            put("impact", t, 0.26)
        elif kind == "soft":
            put("pop", t, 0.08)
        elif kind == "boom":
            put("riser", t - 1.8, 0.16)
            put("impact", t, 0.36)
        elif kind == "flip":
            put("camera_shutter", t + 0.1, 0.12)
            put("camera_shutter", t + 0.28, 0.10)
        elif kind == "swell":
            put("riser", t - 1.5, 0.14)
            put("impact", t + 0.05, 0.2)
        elif kind == "msg":
            put("pop", t, 0.18)
        elif kind == "click":
            put("tick", t, 0.3)
        elif kind == "ding":
            put("ding", t, 0.22)
        elif kind == "scratch":
            put("whoosh", t, 0.1)
    put("heartbeat", s("open_last", 5.0), 0.3)
    put("heartbeat", s("open_last", 6.0), 0.3)
    put("crowd", s("humara", 0.0), 0.2)

    mix = vo * 0.95 + m * 0.24 + nat * 0.30 + fx * 0.55
    mix = np.tanh(mix * 1.05) / np.tanh(1.05)
    mix = mix / max(1e-6, np.abs(mix).max()) * 0.9
    st = np.stack([mix, mix], 1)
    with wave.open(os.path.join(HERE, "out", "soundtrack.wav"), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())
    print(f"soundtrack {total:.1f}s written")


if __name__ == "__main__":
    main()

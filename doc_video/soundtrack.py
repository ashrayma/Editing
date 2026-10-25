#!/usr/bin/env python3
"""Score + sound design for the Centurion 2003 documentary (all synthesised here: royalty-free).

    python3 soundtrack.py   ->  out/soundtrack.wav (voice + music + SFX, mixed, ~-14 LUFS after mux)

Music follows the story: dark suspense under the history and Pakistan's innings, the energetic groove for
Sachin's assault, a ticking pulse into the bouncer (dropping to near-silence at the catch), a hopeful lift
for the finish and a soft, emotional bed under the closing lines. SFX land on the on-screen events that
gen.py logged (card slide-ins, headline slams, rolling numbers, chips).
"""
import json
import os
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "kohli_countdown"))
import music  # noqa: E402
import sfx  # noqa: E402
from music import add, bp, hp, hz, lp, pluck, reverb, saw  # noqa: E402

SR = sfx.SR
rng = np.random.default_rng(2003)


def _t(d):
    return np.arange(int(SR * d)) / SR


# ----------------------------------------------------------------------------- music beds

A_MINOR = [[45, 57, 60, 64], [41, 57, 60, 65], [48, 55, 60, 64], [43, 55, 59, 62]]   # Am F C G
D_MINOR = [[38, 50, 53, 57], [46, 50, 53, 58], [41, 53, 57, 60], [45, 52, 57, 61]]   # Dm Bb F A
WARM = [[48, 55, 60, 64, 67], [45, 57, 60, 64, 69], [41, 57, 60, 65, 69], [43, 55, 59, 62, 67]]  # C Am F G


def pad(chords, dur, bar=4.0, cutoff=1400, detune=(-0.1, 0.0, 0.1)):
    out = np.zeros(int(SR * (dur + bar)))
    t0 = 0.0
    k = 0
    while t0 < dur:
        notes = chords[k % len(chords)]
        t = _t(bar + 1.0)
        x = np.zeros_like(t)
        for m in notes:
            for d in detune:
                x += saw(hz(m) * 2 ** (d / 12), t, rng.random())
        x = lp(x / (len(notes) * len(detune)), cutoff)
        env = np.minimum(1, t / 1.2) * np.clip((bar + 1.0 - t) / 1.4, 0, 1)
        add(out, x * env, t0)
        t0 += bar
        k += 1
    return out[: int(SR * dur)]


def thump():
    t = _t(0.5)
    f = 42 + 50 * np.exp(-t * 25)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6)


def pulse(dur, bpm, intensity, hats=True):
    """Low heartbeat-like pulse; `intensity(t)` 0..1 scales hats and accents."""
    out = np.zeros(int(SR * (dur + 1)))
    beat = 60 / bpm
    th = thump()
    ht = _t(0.05)
    hat = hp(rng.standard_normal(len(ht)), 8000) * np.exp(-ht * 80)
    t = 0.0
    while t < dur:
        g = intensity(t)
        add(out, th, t, 0.55 + 0.35 * g)
        if hats and g > 0.25:
            for q in (0.5, 0.75) if g > 0.6 else (0.5,):
                add(out, hat, t + q * beat, 0.05 + 0.08 * g)
        t += beat
    return out[: int(SR * dur)]


def ticker(dur, bpm=120, rise=True):
    """Clock-like tension ticks that get denser."""
    out = np.zeros(int(SR * (dur + 1)))
    tk = sfx.tick() * 0.6
    t, step = 0.0, 60 / bpm
    while t < dur:
        add(out, tk, t, 0.25 + (0.25 * t / dur if rise else 0))
        t += step * (0.5 if (rise and t > dur * 0.6) else 1.0)
    return out[: int(SR * dur)]


def arps(chords, dur, bar=4.0, step=0.5, gain=0.18):
    out = np.zeros(int(SR * (dur + 2)))
    t0, k = 0.0, 0
    while t0 < dur:
        notes = chords[k % len(chords)]
        seq = [notes[1] + 12, notes[2] + 12, notes[3] + 12, notes[2] + 12]
        for j in range(int(bar / step)):
            add(out, pluck(seq[j % len(seq)], 1.2) * np.exp(-_t(1.2) * 2.5), t0 + j * step, gain)
        t0 += bar
        k += 1
    return out[: int(SR * dur)]


def norm(x, peak=1.0):
    m = np.abs(x).max()
    return x / m * peak if m > 0 else x


def section(x, start, total, fade_in=1.5, fade_out=1.5):
    buf = np.zeros(int(SR * total))
    i = int(start * SR)
    x = x[: len(buf) - i].copy()
    n = len(x)
    fi, fo = int(fade_in * SR), int(fade_out * SR)
    if fi:
        x[:fi] *= np.linspace(0, 1, min(fi, n))[: len(x[:fi])]
    if fo:
        x[-fo:] *= np.linspace(1, 0, min(fo, n))[-len(x[-fo:]):]
    buf[i:i + n] += x
    return buf


# ----------------------------------------------------------------------------- build

def main():
    ev = json.load(open(os.path.join(HERE, "out", "events.json")))
    total, B = ev["total"], ev["beats"]
    s = lambda beat, off=0.0: B[beat][0] + off  # noqa: E731
    e = lambda beat: B[beat][1]  # noqa: E731

    # --- music sections
    m = np.zeros(int(SR * total))
    # 1. suspense: hook + history + Pakistan's innings (darkens, pulse builds toward the chase)
    d1 = s("wasim_over") - 0.0
    bed = norm(reverb(pad(A_MINOR, d1 + 2, bar=4.0, cutoff=1100), 2.0, 0.35)) * 0.55
    pl = norm(pulse(d1 + 2, 72, lambda t: min(1, max(0, (t - 90) / (d1 - 90))))) * 0.5
    m += section(bed + pl, 0.0, total, 2.0, 1.2)
    # 2. the assault: the energetic groove (starts on Wasim's first ball)
    d2 = s("kaif") - s("wasim_over") + 1.5
    m += section(norm(music.track(d2)) * 0.62, s("wasim_over", -0.4), total, 0.4, 1.8)
    # 3. tension: Kaif, cramps, the nineties, the bouncer - drops out at the catch
    t3a, t3b = s("kaif", -0.5), s("bouncer", 10.0)
    d3 = t3b - t3a
    tens = (norm(reverb(pad(D_MINOR, d3 + 2, bar=4.0, cutoff=900), 2.0, 0.35)) * 0.45
            + norm(pulse(d3 + 2, 96, lambda t: min(1, t / d3))) * 0.5
            + norm(ticker(d3 + 2, 120)) * 0.25)
    m += section(tens, t3a, total, 1.5, 0.25)
    # 4. after the 98: a slow, heavy pad, then a hopeful lift into the finish
    t4 = s("out_98", 3.0)
    d4 = s("won") - t4 + 1.0
    m += section(norm(reverb(pad(A_MINOR, d4 + 2, bar=5.0, cutoff=900), 2.5, 0.4)) * 0.4, t4, total, 2.0, 1.5)
    t5 = s("dravid_yuvraj", -0.5)
    d5 = e("won") - t5 + 1.0
    lift = norm(music.track(d5)) * 0.5
    m += section(lift, t5, total, 3.0, 2.5)
    # 5. emotional close: warm chords + soft plucked arps under the reflections and CTA, out with the logo
    t6 = s("aftermath", 0.0)
    d6 = total - t6
    close = norm(reverb(pad(WARM, d6 + 2, bar=4.0, cutoff=1600), 2.5, 0.4)) * 0.45 + norm(reverb(arps(WARM, d6 + 2), 1.5, 0.3)) * 0.35
    m += section(close, t6, total, 3.0, 3.5)

    # --- voice
    vo = np.zeros(int(SR * total))
    with wave.open(os.path.join(HERE, "out", "vo_final.wav")) as w:
        v = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    i = int(ev["vo_offset"] * SR)
    vo[i:i + len(v)] = v[: len(vo) - i]

    # duck music under the voice (fast attack, slow release), ~-18 dB below the voice overall
    hop = 441
    env = np.abs(vo[: len(vo) // hop * hop]).reshape(-1, hop).max(1)
    env = np.convolve(env > 0.03, np.ones(30), "same") > 0
    duck = np.repeat(np.where(env, 0.42, 1.0), hop)
    duck = np.convolve(duck, np.ones(4410) / 4410, "same")
    m[: len(duck)] *= duck

    # --- SFX on the logged events + story moments
    fx = np.zeros(int(SR * total))
    cache = {}

    def put(name, t, g):
        if name not in cache:
            cache[name] = getattr(sfx, name)()
        add(fx, cache[name], max(0, t), g)

    for t, kind in ev["events"]:
        if kind == "whoosh":
            put("whoosh", t - 0.12, 0.18)
        elif kind == "impact":
            put("impact", t, 0.28)
        elif kind == "soft":
            put("pop", t, 0.12)
        elif kind == "roll":
            for k in range(9):
                put("tick", t + 0.05 * k, 0.10)
        elif kind == "pop":
            put("pop", t, 0.16)
        elif kind == "hit":
            put("impact", t, 0.34)
            put("whoosh", t - 0.15, 0.14)
        elif kind == "swell":
            put("riser", t - 1.6, 0.18)
    put("crowd", s("the_six", 4.2), 0.42)          # the six
    put("crowd", s("three_balls", 0.0), 0.30)
    put("riser", s("bouncer", 3.6), 0.35)          # into the bouncer
    for k in range(6):                             # heartbeat as he reaches the nineties
        put("heartbeat", s("nineties", 4.0) + 0.95 * k, 0.32)
    put("heartbeat", s("bouncer", 10.4), 0.45)
    put("crowd", s("won", 0.2), 0.40)              # the win
    put("ding", s("cta", 0.6), 0.25)

    mix = vo * 0.95 + m * 0.22 + fx * 0.55
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

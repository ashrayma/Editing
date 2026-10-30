#!/usr/bin/env python3
"""Original soundtrack for the Rohit reel: half-time beat + sound design, mixed under the narration.

    python3 soundtrack.py   ->  out/soundtrack.wav (stereo 44.1 kHz) and out/music_sfx_only.wav (no voice)

Music: 140 BPM half-time. Warm major chords under the childhood hook, the beat drops in D minor on the
legends, thins out through "So I grew up", goes fully silent for the pause, slams back on "I didn't grow out
of it", and the outro opens up into warm major chords again. SFX come from out/events.json (written by reel.py). Music ducks under the voice.
"""
import json
import os
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "kohli_countdown"))
sys.path.insert(0, os.path.join(HERE, "..", "doc_video"))
import sfx  # noqa: E402
from music import add, bp, clap, hat, hp, hz, lp, pluck, reverb, saw  # noqa: E402
from sfx import SR  # noqa: E402

rng = np.random.default_rng(11)
BPM = 140
BEAT = 60 / BPM
BAR = 4 * BEAT
DM = [(38, [50, 53, 57, 62]), (34, [50, 53, 58, 62]), (41, [53, 57, 60, 65]), (33, [49, 52, 57, 61])]  # Dm Bb F A
WARM = [(36, [55, 60, 64, 67]), (33, [57, 60, 64, 69]), (29, [57, 60, 65, 69]), (31, [55, 59, 62, 67])]  # C Am F G


def _t(d):
    return np.arange(int(SR * d)) / SR


def norm(x, peak=1.0):
    m = np.abs(x).max()
    return x / m * peak if m > 0 else x


# ----------------------------------------------------------------------------- instruments

def k808(m, d):
    """808: pitched sine kick with a long saturated tail."""
    t = _t(d)
    f = hz(m) + 90 * np.exp(-t * 30)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR)
    env = np.minimum(1, t / 0.003) * np.exp(-t * 1.6) * np.clip((d - t) / 0.05, 0, 1)
    return np.tanh(2.2 * x * env) * 0.9


def kick():
    t = _t(0.3)
    f = 50 + 140 * np.exp(-t * 45)
    return np.tanh(2 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 11))


def snare():
    t = _t(0.3)
    n = bp(rng.standard_normal(len(t)), 1200, 7000) * np.exp(-t * 16)
    body = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 28) * 0.6
    return n + body + 0.6 * clap()[: len(t)]


def dark_pad(notes, d, cutoff=1200):
    t = _t(d)
    x = np.zeros_like(t)
    for m in notes:
        for det in (-0.1, 0.0, 0.1):
            x += saw(hz(m) * 2 ** (det / 12), t, rng.random())
    x = lp(x / (len(notes) * 3), cutoff)
    env = np.minimum(1, t / 0.4) * np.clip((d - t) / 0.4, 0, 1)
    return x * env


def bell(m, d=1.2):
    t = _t(d)
    x = sum(a * np.sin(2 * np.pi * hz(m) * r * t) for r, a in ((1, 1), (2.76, 0.35), (5.4, 0.12)))
    return x * np.exp(-t * 3.2) * np.minimum(1, t / 0.002)


# ----------------------------------------------------------------------------- arrangement

def music(total, drop, breaks, outro, thin=(), mute=(), intro_warm=False):
    """drop: time drums come in. breaks: chapter-number times (drums stop one beat before, return after).
    outro: time the beat gives way to the warm ending."""
    n = int(SR * (total + 3))
    drums, bass, pads, keys = (np.zeros(n) for _ in range(4))
    K, S, HC, HO = kick(), snare(), hat(), hat(True)
    # bars are laid on a grid anchored at the drop so the downbeat lands on "Number one"
    t0 = drop - BAR * np.ceil(drop / BAR)
    b = 0
    while t0 < total + BAR:
        warm = t0 >= outro - 0.01 or (intro_warm and t0 < drop - 0.01)
        root, notes = (WARM if warm else DM)[b % 4]
        if t0 + BAR > 0:
            add(pads, dark_pad(notes, BAR + 0.4, 1800 if warm else 1100), max(0, t0), 0.8 if not warm else 0.65)
            for k in range(8):
                ts = t0 + k * BEAT / 2
                if ts < 0:
                    continue
                if (k in (0, 3, 6) and not warm) or (warm and k % 2 == 0):
                    add(keys, bell(notes[(k * 2) % 4] + (12 if warm else 0)), ts, 0.28 if not warm else 0.22)
        for q in range(16):  # 16th grid
            ts = t0 + q * BEAT / 4
            if ts >= outro or ts < 0:
                continue
            if ts < drop or any(a <= ts < b2 for a, b2 in thin):  # hook: just a muffled pulse on the downbeats under the filtered pad
                if q in (0, 8):
                    add(drums, lp(K, 400), ts, 0.55)
                if q == 0:
                    add(bass, k808(root, BEAT * 3), ts, 0.35)
                continue
            if any(bt - BEAT * 1.2 <= ts < bt + 0.05 for bt in breaks if bt > drop + 0.5):
                continue  # the drop-out before each chapter number
            if q in (0, 10):
                add(drums, K, ts, 0.75)
                add(bass, k808(root, BEAT * (2.5 if q == 0 else 1.5)), ts, 0.7)
            if q == 8:
                add(drums, S, ts, 0.5)
            if q % 2 == 0:
                add(drums, HC, ts, 0.09 if q % 4 else 0.12)
            if b % 4 == 3 and q >= 12:  # hat roll into the next phrase
                for r in range(3):
                    add(drums, HC, ts + r * BEAT / 12, 0.07)
            if q == 14 and b % 2:
                add(drums, HO, ts, 0.08)
        t0 += BAR
        b += 1
    tt = np.arange(n) / SR
    melodic = reverb(pads + keys, 1.8, 0.35)
    # hook: low-passed, opening up toward the drop
    i_drop = int(drop * SR)
    melodic[:i_drop] = lp(melodic[:i_drop], 900) * 1.3
    mix = melodic * 0.55 + bass * 0.6 + reverb(drums, 0.4, 0.08)
    mix = hp(mix, 28)[: int(SR * total)]
    for a, b2 in mute:  # dead silence (with 60 ms edges)
        i0, i1 = int(a * SR), int(b2 * SR)
        g = np.ones(len(mix))
        g[i0:i1] = 0
        g = np.convolve(g, np.ones(2646) / 2646, "same")
        mix *= g
    fade = np.clip(np.minimum(tt[: len(mix)] / 0.3, (total - tt[: len(mix)]) / 1.8), 0, 1)
    return norm(np.tanh(1.2 * norm(mix) * fade)) * 0.85


# ----------------------------------------------------------------------------- sound design

def glitch_sfx(d=0.35):
    t = _t(d)
    x = rng.standard_normal(len(t))
    x = np.round(x * 3) / 3  # bit-crush
    hold = np.repeat(x[::12], 12)[: len(t)]  # sample-rate crush
    gate = (np.sin(2 * np.pi * 28 * t) > 0).astype(float)
    chirp = np.sin(2 * np.pi * np.cumsum(np.geomspace(2400, 300, len(t))) / SR) * 0.5
    return norm((hp(hold, 400) * 0.6 + chirp) * gate * np.exp(-t * 4), 0.8)


def boom(d=1.6):
    t = _t(d)
    f = 34 + 70 * np.exp(-t * 8)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2)
    return norm(np.tanh(2.5 * sub) + 0.5 * sfx.impact(d)[: len(t)], 1.0)


def rise(d=0.6):
    t = _t(d)
    x = sfx._lowpass(rng.standard_normal(len(t)), np.geomspace(400, 7000, len(t)))
    return norm(x * (t / d) ** 2 * np.clip((d - t) / 0.05, 0, 1), 0.7)


def swish(d=0.7):
    t = _t(d)
    x = bp(rng.standard_normal(len(t)), 800, 5000)
    return norm(x * np.sin(np.pi * t / d) ** 3, 0.6)


def key_click():
    t = _t(0.03)
    return norm(hp(rng.standard_normal(len(t)), 2500) * np.exp(-t * 260), 0.5)


def big_whoosh(d=0.8):
    a = sfx.whoosh(d)
    return norm(a + 0.6 * np.sin(2 * np.pi * np.cumsum(np.geomspace(90, 40, len(a))) / SR) * np.sin(np.pi * _t(d) / d), 1)


def soft():
    t = _t(0.25)
    return norm(lp(rng.standard_normal(len(t)), 2500) * np.exp(-t * 18) + 0.4 * np.sin(2 * np.pi * 110 * t) * np.exp(-t * 20), 0.6)


SFX = {
    "whoosh": (lambda: sfx.whoosh(0.4), 0.15, -0.05), "whoosh_big": (big_whoosh, 0.35, -0.2),
    "impact": (sfx.impact, 0.32, 0.0), "boom": (boom, 0.55, 0.0), "riser": (lambda: sfx.riser(1.05), 0.3, 0.0),
    "soft": (soft, 0.14, 0.0), "pop": (sfx.pop, 0.13, 0.0), "tick": (sfx.tick, 0.12, 0.0),
    "key": (key_click, 0.07, 0.0), "glitch": (glitch_sfx, 0.26, 0.0), "swish": (swish, 0.2, 0.0),
    "shutter": (sfx.camera_shutter, 0.3, 0.0), "rise": (rise, 0.16, 0.0), "crowd": (lambda: sfx.crowd(3.0), 0.3, 0.0),
    "roll": (None, 0.09, 0.0),
}


def build_sfx(total, events):
    out = np.zeros(int(SR * (total + 3)))
    cache = {}
    for t, kind, g in events:
        gen, gain, off = SFX[kind]
        if kind == "roll":
            for k in range(9):
                cache.setdefault("tick", sfx.tick())
                add(out, cache["tick"], max(0, t + 0.045 * k), gain * g * (1 - k / 12))
            continue
        if kind not in cache:
            cache[kind] = gen()
        add(out, cache[kind], max(0, t + off), gain * g)
    return out[: int(SR * total)]


def read_wav(path):
    with wave.open(path) as w:
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768


def write_wav(path, x):
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.stack([x, x], 1) * 32767).astype(np.int16).tobytes())


def main():
    ev = json.load(open(os.path.join(HERE, "out", "events.json")))
    tl = json.load(open(os.path.join(HERE, "out", "timeline.json")))
    L = {ln["id"]: ln for ln in tl["lines"]}
    total = ev["total"]
    n = int(SR * total)
    m = music(total, drop=L["n5"]["start"], breaks=[L[k]["start"] for k in ("n4", "n3", "n2", "n1")],
              outro=L["q1"]["start"] - 0.1, thin=[(L["n1"]["start"], L["r4"]["start"])],
              mute=[(L["r3"]["end"] + 0.05, L["r4"]["start"] - 0.02)], intro_warm=False)
    fx = build_sfx(total, ev["events"])
    vo = np.zeros(n, np.float32)
    v = read_wav(os.path.join(HERE, "out", "vo.wav"))
    vo[: min(n, len(v))] = v[:n]
    # duck the music under the voice (fast attack, slow release)
    hop = 441
    env = np.abs(vo[: n // hop * hop]).reshape(-1, hop).max(1)
    on = np.convolve(env > 0.04, np.ones(25), "same") > 0
    duck = np.repeat(np.where(on, 0.42, 1.0), hop)
    duck = np.convolve(duck, np.ones(2205) / 2205, "same")
    m[: len(duck)] *= duck
    bed = m * 0.32 + fx * 0.62
    write_wav(os.path.join(HERE, "out", "music_sfx_only.wav"), norm(np.tanh(bed * 1.1), 0.9))
    mix = vo * 1.0 + bed
    mix = np.tanh(mix * 1.05) / np.tanh(1.05)
    write_wav(os.path.join(HERE, "out", "soundtrack.wav"), norm(mix, 0.92))
    print(f"soundtrack {total:.1f}s, {len(ev['events'])} sfx")


if __name__ == "__main__":
    main()

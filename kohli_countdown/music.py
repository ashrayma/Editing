"""Original, royalty-free background music: an upbeat, feel-good house/pop loop, synthesised here.

    track(duration)  ->  mono float32 at sfx.SR, peak ~0.8

118 BPM, G major, I-V-vi-IV (G D Em C). Four-on-the-floor kick, claps on 2 and 4, offbeat hats,
pumping offbeat bass, side-chained supersaw pads and a plucked arpeggio. Two bars of filtered intro,
then the full groove, a small fill every 8 bars, and a fade at the end.
"""
import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

from sfx import SR

rng = np.random.default_rng(18)
BPM = 118
BEAT = 60 / BPM
BAR = 4 * BEAT
# chord roots (MIDI) and their triads, one per bar: G D Em C
CHORDS = [(43, [55, 59, 62, 67]), (38, [54, 57, 62, 66]), (40, [55, 59, 64, 67]), (36, [55, 60, 64, 67])]


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def _t(d):
    return np.arange(int(SR * d)) / SR


def lp(x, f, order=2):
    return sosfilt(butter(order, f, "low", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, "high", fs=SR, output="sos"), x)


def bp(x, lo, hi):
    return sosfilt(butter(2, [lo, hi], "band", fs=SR, output="sos"), x)


def saw(f, t, phase=0.0):
    return 2 * ((f * t + phase) % 1.0) - 1


def add(buf, sig, t0, gain=1.0):
    i = int(t0 * SR)
    if i >= len(buf):
        return
    sig = sig[: len(buf) - i]
    buf[i:i + len(sig)] += sig * gain


# ----------------------------------------------------------------------------- instruments

def kick():
    t = _t(0.38)
    f = 52 + 110 * np.exp(-t * 38)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.5)
    click = hp(rng.standard_normal(len(t)), 3000) * np.exp(-t * 300) * 0.25
    return np.tanh(1.8 * body) + click


def clap():
    t = _t(0.35)
    n = rng.standard_normal(len(t))
    env = sum(np.exp(-np.clip(t - d, 0, None) * 160) * (t >= d) for d in (0, 0.011, 0.022))
    env += 0.5 * np.exp(-np.clip(t - 0.03, 0, None) * 18) * (t >= 0.03)
    return bp(n, 900, 3200) * env


def hat(open_=False):
    t = _t(0.25 if open_ else 0.06)
    n = bp(rng.standard_normal(len(t)), 6000, 11000)
    return n * np.exp(-t * (14 if open_ else 90))


def bass_note(m, d):
    t = _t(d)
    x = saw(hz(m), t) + 0.5 * saw(hz(m) * 1.005, t)
    env = np.minimum(1, t / 0.005) * np.exp(-t * 5)
    return lp(x, 700) * env + 0.6 * np.sin(2 * np.pi * hz(m) * t) * env


def pad_chord(notes, d):
    t = _t(d)
    x = np.zeros_like(t)
    for m in notes:
        for det in (-0.12, -0.05, 0.0, 0.06, 0.13):
            x += saw(hz(m) * 2 ** (det / 12), t, rng.random())
    x = lp(x / (len(notes) * 5), 3400)
    env = np.minimum(1, t / 0.06) * np.minimum(1, (d - t) / 0.08)
    return x * np.clip(env, 0, 1)


def pluck(m, d=0.32):
    t = _t(d)
    x = sum(np.sin(2 * np.pi * hz(m) * k * t) / k ** 1.1 * np.exp(-t * 4 * k) for k in range(1, 9))
    return x * np.exp(-t * 8) * np.minimum(1, t / 0.002)


def reverb(x, secs=1.1, wet=0.22):
    t = _t(secs)
    ir = rng.standard_normal(len(t)) * np.exp(-t * 5.5)
    ir = lp(ir, 5000)
    tail = fftconvolve(x, ir)[: len(x)]
    return x + wet * tail / (np.abs(tail).max() + 1e-9) * np.abs(x).max()


# ----------------------------------------------------------------------------- arrangement

ARP = [0, 1, 2, 3, 2, 1, 0, 2, 3, 2, 1, 2, 0, 3, 2, 1]  # 16th-note pattern over the chord tones


def track(duration):
    n = int(SR * (duration + 2))
    drums = np.zeros(n)
    bass = np.zeros(n)
    pads = np.zeros(n)
    arp = np.zeros(n)
    K, C, HC, HO = kick(), clap(), hat(), hat(True)
    bars = int(np.ceil(duration / BAR)) + 1
    intro = 2
    for b in range(bars):
        t0 = b * BAR
        root, notes = CHORDS[b % 4]
        add(pads, pad_chord(notes, BAR), t0, 0.75)
        for s in range(16):
            ts = t0 + s * BEAT / 4
            add(arp, pluck(notes[ARP[s]] + 12), ts, 0.62 if s % 4 == 0 else 0.46)
        if b < intro:
            continue
        fill = b % 8 == 7
        for beat in range(4):
            tb = t0 + beat * BEAT
            add(drums, K, tb, 0.7)
            if beat in (1, 3):
                add(drums, C, tb, 0.42)
            add(drums, HO, tb + BEAT / 2, 0.11)
            for q in (1, 3):
                add(drums, HC, tb + q * BEAT / 4, 0.06)
            add(bass, bass_note(root + 12 if beat == 3 else root, BEAT / 2 * 0.9), tb + BEAT / 2, 0.38)
        if fill:  # clap roll into the next 8
            for q in range(4):
                add(drums, C, t0 + 3 * BEAT + q * BEAT / 4, 0.18 + 0.06 * q)

    tt = np.arange(n) / SR
    # side-chain pump: everything melodic ducks on each kick once the drums are in
    beat_pos = (tt % BEAT) / BEAT
    pump = 1 - 0.55 * np.exp(-beat_pos * BEAT / 0.11)
    pump[tt < intro * BAR] = 1.0
    # intro: low-passed music opening up into the drop
    melodic = reverb(pads * pump + arp * (0.6 + 0.4 * pump), 1.3, 0.3) + bass * pump
    i_end = int(intro * BAR * SR)
    melodic[:i_end] = lp(melodic[:i_end], 900)
    mix = melodic + reverb(drums, 0.5, 0.08)
    mix = hp(mix, 30)
    mix = mix[: int(SR * duration)]
    fade = np.minimum(1, np.minimum(tt[: len(mix)] / 0.4, (duration - tt[: len(mix)]) / 2.5))
    mix *= np.clip(fade, 0, 1)
    mix = np.tanh(1.3 * mix / (np.abs(mix).max() + 1e-9)) / np.tanh(1.3)
    return (mix * 0.8).astype(np.float32)


if __name__ == "__main__":
    import sys
    import wave
    d = float(sys.argv[1]) if len(sys.argv) > 1 else 30
    x = track(d)
    with wave.open(sys.argv[2] if len(sys.argv) > 2 else "music_preview.wav", "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())
    print(f"{d:.0f}s written")

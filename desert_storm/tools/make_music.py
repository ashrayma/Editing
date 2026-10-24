#!/usr/bin/env python3
"""Original background music for the reel, synthesised from scratch (no samples, no
third-party material, so there is nothing to clear). 128 BPM, A minor, Am-F-C-G.

The arrangement follows the story, read from timing.json + edit.json:
  hook          soft pad only, so the hook clip's dialogue stays clear
  story         four-on-the-floor kick, hats, bass, pluck arpeggio
  turn/storm    drums drop out: drone + ticking pulse (tension)
  "real"        the drop lands on a bar line exactly on "asli toofan": full kit, clap, open hats
  warne -> end  breakdown, half-time kick, fade out
and it ducks about 7 dB under the voice wherever you are speaking.

usage: python3 tools/make_music.py   -> film/assets/audio/music.wav
"""
import json, os
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 44100
BPM = 128
BEAT = 60 / BPM
BAR = 4 * BEAT
rng = np.random.default_rng(1998)

A = 440.0


def hz(midi):
    return A * 2 ** ((midi - 69) / 12)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, "low", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, "high", fs=SR, output="sos"), x)


def bp(x, lo, hi):
    return sosfilt(butter(2, [lo, hi], "band", fs=SR, output="sos"), x)


def env(n, a, r):
    e = np.exp(-np.arange(n) / (SR * r))
    k = max(1, int(SR * a))
    e[:k] *= np.linspace(0, 1, k)
    return e


def saw(f, n, phase=0.0):
    t = np.arange(n) / SR
    return 2 * ((t * f + phase) % 1.0) - 1


# ---------------------------------------------------------------- instruments
def kick(n=int(SR * 0.45)):
    t = np.arange(n) / SR
    f = 45 + 95 * np.exp(-t * 28)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 0.16) + 0.25 * np.sin(2 * np.pi * 50 * t) * env(n, 0.002, 0.3)


def clap(n=int(SR * 0.3)):
    x = bp(rng.standard_normal(n), 900, 4500)
    e = env(n, 0.001, 0.07)
    for d in (0.008, 0.017):  # the three-hand smear of a clap
        k = int(SR * d)
        e[k:] += 0.6 * env(n - k, 0.001, 0.05)
    return x * e * 0.6


def hat(open_=False):
    n = int(SR * (0.22 if open_ else 0.05))
    return hp(rng.standard_normal(n), 7000) * env(n, 0.001, 0.08 if open_ else 0.012) * 0.35


def pluck(f, n=int(SR * 0.35)):
    x = saw(f, n) + 0.5 * saw(f * 2.003, n)
    return lp(x, 2600) * env(n, 0.003, 0.09) * 0.28


def bass_note(f, n):
    x = saw(f, n) + 0.6 * np.sin(2 * np.pi * f / 2 * np.arange(n) / SR)
    return lp(x, 420, 4) * env(n, 0.004, 0.25) * 0.55


def pad_chord(freqs, n, bright):
    t = np.arange(n) / SR
    x = sum(saw(f * d, n, rng.random()) for f in freqs for d in (0.996, 1.004))
    x = lp(x, bright, 2) / (2 * len(freqs))
    swell = np.minimum(1, t / 0.35) * np.minimum(1, (n / SR - t) / 0.3)
    return x * swell * 0.5


# ---------------------------------------------------------------- arrangement
def build(total, sections, speech):
    n = int(SR * total) + SR
    mix = {k: np.zeros(n) for k in ("drums", "bass", "pad", "pluck", "fx")}

    def put(track, x, t):
        i = int(t * SR)
        if i < 0 or i >= n:
            return
        j = min(n, i + len(x))
        mix[track][i:j] += x[:j - i]

    prog = [(57, [57, 60, 64]), (53, [53, 57, 60]), (48, [48, 52, 55]), (55, [55, 59, 62])]  # Am F C G
    arp_steps = [0, 2, 1, 2, 0, 2, 1, 2]
    t_real = sections["real"]
    origin = t_real - BAR * int(t_real / BAR)  # bar grid that puts a downbeat on the drop
    bar_i = 0
    t = origin - BAR
    while t < total:
        sec = section_at(t, sections)
        root, chord = prog[bar_i % 4]
        bright = {"hook": 700, "story": 1500, "tension": 900, "drop": 3200, "outro": 1200}[sec]
        if t >= 0 or sec == "hook":
            put("pad", pad_chord([hz(m) for m in chord], int(SR * BAR), bright), max(0, t))
        for b in range(4):
            tb = t + b * BEAT
            if tb < 0 or tb >= total:
                continue
            if sec in ("story", "drop"):
                put("drums", kick(), tb)
            if sec == "outro" and b in (0, 2):
                put("drums", kick() * 0.8, tb)
            if sec == "drop" and b in (1, 3):
                put("drums", clap(), tb)
            for h in range(2 if sec != "tension" else 4):
                th = tb + h * BEAT / (2 if sec != "tension" else 4)
                if sec == "story" and h == 1 or sec == "drop" or sec == "tension":
                    put("drums", hat(open_=(sec == "drop" and h == 1)) * (0.7 if sec == "tension" else 1), th)
            if sec in ("story", "drop"):
                for h in range(2):
                    put("bass", bass_note(hz(root - 12), int(SR * BEAT / 2)), tb + h * BEAT / 2)
            if sec == "tension":
                put("bass", bass_note(hz(45), int(SR * BEAT)) * 0.6, tb)
            if sec in ("story", "drop", "hook", "outro"):
                for s in range(2):
                    note = chord[arp_steps[(b * 2 + s) % 8]] + 12
                    v = {"hook": 0.35, "story": 0.8, "drop": 1.0, "outro": 0.5}[sec]
                    put("pluck", pluck(hz(note)) * v, tb + s * BEAT / 2)
        t += BAR
        bar_i += 1

    # riser into the drop: filtered noise sweeping up over 4 bars
    rn = int(SR * BAR * 4)
    noise = rng.standard_normal(rn)
    sweep = np.concatenate([lp(noise[i:i + 2048], 300 + 9000 * (i / rn) ** 2) for i in range(0, rn, 2048)])[:rn]
    put("fx", sweep * np.linspace(0, 0.35, rn) ** 1.5, t_real - BAR * 4)
    put("fx", kick() * 1.4, t_real)  # downbeat hit

    levels = {"drums": 0.9, "bass": 0.8, "pad": 0.55, "pluck": 0.45, "fx": 0.7}
    out = sum(mix[k] * v for k, v in levels.items())[: int(SR * total)]

    # duck under the voice: -7 dB while speaking, 60 ms attack / 250 ms release
    g = np.ones(len(out))
    for s, e in speech:
        g[int(s * SR):int(e * SR)] = 10 ** (-7 / 20)
    k = int(SR * 0.25)
    g = np.convolve(g, np.ones(k) / k, mode="same")
    out *= g
    fade = int(SR * 2.0)
    out[-fade:] *= np.linspace(1, 0, fade)
    return out / np.abs(out).max() * 0.89


def section_at(t, s):
    if t < s["story"]:
        return "hook"
    if t < s["turn"]:
        return "story"
    if t < s["real"]:
        return "tension"
    if t < s["outro"]:
        return "drop"
    return "outro"


if __name__ == "__main__":
    tim = json.load(open(os.path.join(ROOT, "timing.json")))
    edit = json.load(open(os.path.join(ROOT, "edit.json")))
    off = edit["hook"]["duration"] - edit["hook"].get("overlap", 0) if edit.get("hook") else 0
    L = {l["id"]: (l["start"] + off, l["end"] + off) for l in tim["lines"]}
    total = off + tim["duration"]
    sections = {"story": off, "turn": L["turn"][0], "real": L["real"][0], "outro": L["warne"][0]}
    speech = [(0.2, edit["hook"]["duration"])] if edit.get("hook") else []
    speech += list(L.values())
    audio = build(total, sections, speech)
    out = os.path.join(ROOT, "film/assets/audio/music.wav")
    sf.write(out, np.stack([audio, audio], 1).astype(np.float32), SR)
    print(f"music {total:.1f}s, drop at {sections['real']:.2f}s -> {out}")

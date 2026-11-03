#!/usr/bin/env python3
"""Score + sound design for "31 for 4". Every note is synthesised here, so it's original and copyright-free.

    python3 soundtrack.py   ->  out/soundtrack.wav (voice + music + SFX, mixed; -14 LUFS after the mux)

Music map (follows the story, like the reference film's score):
  cold open      suspense: low pad + heartbeat pulse + ticking clock, a braam hit on the title
  01 Silence     sparse minor piano-pluck arps and a cold pad (the drought), lifting on the 71st hundred
  02 Stage       the energetic DRIVE (128 BPM minor, side-chained) builds under the MCG and the target
  03 31 for 4    the drive cuts dead on "31 for 4": heartbeat and near-silence, a riser on the re-hook
  04 Plan        pulse + ticks get denser as the asking rate climbs
  05 28 off 8    tension peaks, drops to almost nothing on the TV beat, then the DRIVE slams back on six one
  06 Last over   full-energy drive under the ball-by-ball madness, riser into the winning run, crowd roar
  07 Answer      warm major chords and soft arps, out with the logo
"""
import importlib.util
import json
import os
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "kohli_countdown"))
import music  # noqa: E402
import sfx  # noqa: E402
from music import add, hp, hz, lp, reverb, saw  # noqa: E402

_spec = importlib.util.spec_from_file_location("st03", os.path.join(HERE, "..", "doc_video", "soundtrack.py"))
st03 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(st03)
pad, pulse, ticker, arps, norm, section = st03.pad, st03.pulse, st03.ticker, st03.arps, st03.norm, st03.section
A_MINOR, D_MINOR, WARM = st03.A_MINOR, st03.D_MINOR, st03.WARM

SR = sfx.SR
rng = np.random.default_rng(2022)


def _t(d):
    return np.arange(int(SR * d)) / SR


# ----------------------------------------------------------------------------- new instruments

def braam(dur=3.0):
    """Cinematic low brass hit: detuned saws an octave apart, low-passed, slow decay."""
    t = _t(dur)
    x = sum(saw(hz(m) * 2 ** (d / 1200), t, rng.random()) for m in (26, 38, 45) for d in (-12, 0, 12))
    x = lp(x, 700) * np.exp(-t * 1.3) * np.minimum(1, t / 0.03)
    return norm(np.tanh(1.8 * x), 0.9)


def drive(dur, bpm=128, chords=((45, [57, 60, 64]), (41, [57, 60, 65]), (48, [55, 60, 64]), (43, [55, 59, 62]))):
    """Energetic sports-doc groove: four-on-the-floor, claps, 16th hats, rolling 16th saw bass, stabs.
    Am F C G, side-chained. Original, synthesised."""
    beat = 60 / bpm
    bar = 4 * beat
    n = int(SR * (dur + 2))
    drums, bass, stabs = np.zeros(n), np.zeros(n), np.zeros(n)
    K, C, HC = music.kick(), music.clap(), music.hat()
    bars = int(np.ceil(dur / bar)) + 1
    bt = _t(beat / 4 * 0.9)
    for b in range(bars):
        t0 = b * bar
        root, notes = chords[b % 4]
        for k in range(4):
            tb = t0 + k * beat
            add(drums, K, tb, 0.75)
            if k in (1, 3):
                add(drums, C, tb, 0.45)
            for q in range(4):
                add(drums, HC, tb + q * beat / 4, 0.05 if q % 2 == 0 else 0.09)
            for q in range(4):  # rolling bass, root/octave
                m = root - 12 + (12 if q == 2 else 0)
                tone = lp(saw(hz(m), bt) + 0.5 * saw(hz(m) * 1.005, bt), 900) * np.exp(-bt * 9)
                add(bass, tone, tb + q * beat / 4, 0.32)
        # off-beat chord stabs on beats 2& and 4&
        st = _t(0.22)
        stab = sum(saw(hz(m + 12), st, rng.random()) for m in notes)
        stab = lp(stab / len(notes), 2400) * np.exp(-st * 14)
        for k in (1, 3):
            add(stabs, stab, t0 + k * beat + beat / 2, 0.35)
        if b % 8 == 7:  # snare-roll fill
            for q in range(8):
                add(drums, C, t0 + 2 * beat + q * beat / 4, 0.12 + 0.04 * q)
    tt = np.arange(n) / SR
    pump = 1 - 0.6 * np.exp(-((tt % beat) / beat) * beat / 0.1)
    mel = reverb(stabs * pump, 0.9, 0.25) + bass * pump
    mix = hp(mel + reverb(drums, 0.4, 0.06), 30)[: int(SR * dur)]
    mix = np.tanh(1.4 * mix / (np.abs(mix).max() + 1e-9)) / np.tanh(1.4)
    return mix * 0.85


def flatline(dur=2.2):
    t = _t(dur)
    return norm(np.sin(2 * np.pi * 1000 * t) * np.minimum(1, t / 0.01) * np.minimum(1, (dur - t) / 0.3), 0.35)


def rewind_fx(dur=1.4):
    """Tape-rewind squeal: a fast falling chirp with noise."""
    n = int(SR * dur)
    f = np.geomspace(2400, 300, n)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.6 + 0.4 * np.sin(2 * np.pi * 23 * _t(dur)))
    x += 0.3 * hp(rng.standard_normal(n), 3000)
    return norm(x * np.minimum(1, _t(dur) / 0.05) * np.minimum(1, (dur - _t(dur)) / 0.3), 0.6)


# ----------------------------------------------------------------------------- build

def main():
    ev = json.load(open(os.path.join(HERE, "out", "events.json")))
    total, B = ev["total"], ev["beats"]
    s = lambda beat, off=0.0: B[beat][0] + off  # noqa: E731
    e = lambda beat: B[beat][1]  # noqa: E731
    m = np.zeros(int(SR * total))

    # cold open: suspense (pad + pulse + ticks), cut at the rewind
    d = s("open_tease", 4.9)
    m += section(norm(reverb(pad(D_MINOR, d + 2, cutoff=900), 2.0, 0.35)) * 0.5 + norm(pulse(d + 2, 84, lambda t: 0.5 + t / d / 2)) * 0.5
                 + norm(ticker(d + 2, 120)) * 0.2, 0.0, total, 0.3, 0.4)
    # 01 silence: sparse sad arps on a cold pad; 02 lifts into the drive at the MCG
    t1, t2 = e("open_tease") + 0.3, s("mcg", 0.0)
    m += section(norm(reverb(pad(A_MINOR, t2 - t1 + 2, bar=5.0, cutoff=800), 2.5, 0.4)) * 0.4
                 + norm(reverb(arps(A_MINOR, t2 - t1 + 2, bar=5.0, step=0.625, gain=0.12), 2.0, 0.45)) * 0.35, t1, total, 2.0, 2.0)
    # 02 stage: the drive (filtered for the first bars), until "31 for 4" cuts it dead
    t3 = s("31_4", -0.05)
    dr = drive(t3 - t2 + 1)
    k = int(SR * 4)
    dr[:k] = lp(dr[:k], 700)
    m += section(dr * 0.75, t2, total, 1.5, 0.05)
    # 03 the silence after 31/4: low drone, heartbeat SFX carries it; 04 pulse + ticks build
    t4 = s("hardik", 0.0)
    m += section(norm(lp(pad(D_MINOR, t4 - t3 + 2, bar=6.0, cutoff=500), 400)) * 0.35, t3 + 0.6, total, 1.5, 1.0)
    t5 = s("rauf_over", 0.0)
    m += section(norm(pulse(t5 - t4 + 1, 96, lambda t: min(1, t / (t5 - t4)))) * 0.5
                 + norm(ticker(t5 - t4 + 1, 120)) * 0.25 + norm(pad(D_MINOR, t5 - t4 + 1, cutoff=900)) * 0.3, t4, total, 1.0, 0.5)
    # 05 tension peak over Rauf, almost nothing on the TV beat, then the drive slams in on six one
    t6 = s("tv_off", 0.0)
    m += section(norm(pulse(t6 - t5 + 1, 120, lambda t: 1.0)) * 0.55 + norm(ticker(t6 - t5 + 1, 160, rise=True)) * 0.3, t5, total, 0.3, 0.6)
    t7 = s("six_one", 0.0)
    m += section(norm(lp(pad(A_MINOR, t7 - t6 + 1, cutoff=500), 350)) * 0.25, t6, total, 0.6, 0.2)
    t8 = e("ashwin") + 0.6
    m += section(drive(t8 - t7 + 1, bpm=132) * 0.85, t7 + 0.15, total, 0.05, 0.4)
    # 07 the answer: warm chords + soft arps
    t9 = s("punch", -0.4)
    close = norm(reverb(pad(WARM, total - t9 + 2, cutoff=1600), 2.5, 0.4)) * 0.45 + norm(reverb(arps(WARM, total - t9 + 2), 1.5, 0.3)) * 0.35
    m += section(close, t9, total, 2.0, 3.5)

    # voice
    vo = np.zeros(int(SR * total))
    with wave.open(os.path.join(HERE, "out", "vo_final.wav")) as w:
        v = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    i = int(ev["vo_offset"] * SR)
    vo[i:i + len(v)] = v[: len(vo) - i]
    hop = 441
    env = np.abs(vo[: len(vo) // hop * hop]).reshape(-1, hop).max(1)
    env = np.convolve(env > 0.03, np.ones(30), "same") > 0
    duck = np.convolve(np.repeat(np.where(env, 0.45, 1.0), hop), np.ones(4410) / 4410, "same")
    m[: len(duck)] *= duck

    # SFX on the logged events + the story moments
    fx = np.zeros(int(SR * total))
    cache = {"braam": braam(), "flatline": flatline(), "rewind": rewind_fx()}

    def put(name, t, g):
        if name not in cache:
            cache[name] = getattr(sfx, name)()
        add(fx, cache[name], max(0, t), g)

    for t, kind in ev["events"]:
        if kind == "whoosh":
            put("whoosh", t - 0.12, 0.16)
        elif kind == "impact":
            put("impact", t, 0.26)
        elif kind == "soft":
            put("pop", t, 0.10)
        elif kind == "roll":
            for k in range(9):
                put("tick", t + 0.05 * k, 0.09)
        elif kind == "pop":
            put("pop", t, 0.14)
        elif kind == "hit":
            put("impact", t, 0.30)
            put("whoosh", t - 0.15, 0.12)
        elif kind == "cut":
            put("whoosh", t - 0.1, 0.07)
        elif kind == "swell":
            put("riser", t - 1.6, 0.15)
        elif kind == "heartbeat":
            put("heartbeat", t, 0.30)
        elif kind == "flatline":
            put("flatline", t, 0.22)
        elif kind == "rewind":
            put("rewind", t, 0.32)
        elif kind.startswith("chip_"):
            put("impact" if kind in ("chip_w", "chip_six", "chip_win") else "pop", t, 0.22 if kind != "chip_n" else 0.14)
    put("braam", e("open_tease") + 0.4, 0.55)             # title hit
    put("braam", s("31_4", 0.05), 0.5)                    # 31/4
    put("riser", s("rehook_2", -1.4), 0.3)
    put("riser", s("six_one", -1.9), 0.35)
    put("impact", s("six_one", 3.6), 0.45)                # bat on ball, the straight six
    put("crowd", s("six_one", 3.8), 0.5)
    put("crowd", s("six_two", 2.0), 0.5)
    put("crowd", s("no_ball", 2.8), 0.45)
    put("riser", s("ashwin", -0.2), 0.3)
    put("crowd", s("ashwin", D_ash := (e("ashwin") - s("ashwin")) * 0.8), 0.6)
    put("crowd", s("ashwin", D_ash + 3.0), 0.4)
    put("ding", s("cta", 0.5), 0.22)

    mix = vo * 0.95 + m * 0.24 + fx * 0.55
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

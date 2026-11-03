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
    s = lambda n, off=0.0: B[f"l{n:03d}"][0] + off  # noqa: E731
    e = lambda n: B[f"l{n:03d}"][1]  # noqa: E731
    m = np.zeros(int(SR * total))

    def bed(x, t0, t1, fi=1.5, fo=1.5):
        nonlocal m
        m += section(x[: int(SR * (t1 - t0 + 1))], t0, total, fi, fo)

    def suspense(d, bpm=84):
        return (norm(reverb(pad(D_MINOR, d + 2, cutoff=900), 2.0, 0.35)) * 0.5
                + norm(pulse(d + 2, bpm, lambda t: 0.5 + min(t / d, 1) / 2)) * 0.5 + norm(ticker(d + 2, 120)) * 0.2)

    def sad(d):
        return (norm(reverb(pad(A_MINOR, d + 2, bar=5.0, cutoff=800), 2.5, 0.4)) * 0.4
                + norm(reverb(arps(A_MINOR, d + 2, bar=5.0, step=0.625, gain=0.12), 2.0, 0.45)) * 0.35)

    def warm(d):
        return (norm(reverb(pad(WARM, d + 2, cutoff=1600), 2.5, 0.4)) * 0.45
                + norm(reverb(arps(WARM, d + 2), 1.5, 0.3)) * 0.35)

    # cold open: suspense, cut at the rewind; title braam
    bed(suspense(s(5, 1.0)), 0.0, s(5, 1.0), 0.3, 0.3)
    # 01 the king: bright, confident groove (the peak years)
    t0, t1 = s(6, 0.0), s(15, 0.0)
    bed(norm(music.track(t1 - t0 + 1)) * 0.6, t0 + 3.0, t1, 1.0, 2.5)
    # 15-32 the silence: sad arps on a cold pad; suspense under Dubai 2021
    bed(sad(s(23) - s(15) + 1), s(15), s(23), 2.0, 1.5)
    bed(suspense(s(26) - s(23) + 1, 92), s(23), s(26), 1.0, 1.5)
    bed(sad(s(33) - s(26) + 1), s(26), s(33, -0.5), 1.5, 1.5)
    # 03 the return: warm and hopeful, lifting into the 122*
    bed(warm(s(38) - s(33) + 1), s(33), s(38), 2.0, 1.0)
    bed(norm(music.track(s(42) - s(38) + 1)) * 0.6, s(38, -0.3), s(42), 0.5, 2.0)
    bed(suspense(s(44) - s(42) + 1, 72), s(42), s(44), 1.5, 1.0)
    # 04 the stage: the energetic drive, filtered intro, through Pakistan's innings
    dr = drive(s(54) - s(44) + 1)
    k = int(SR * 6)
    dr[:k] = lp(dr[:k], 700)
    bed(dr * 0.72, s(44), s(54), 1.5, 0.6)
    # 05 31 for 4: tension, cut dead on 31/4, a low drone in the silence
    bed(norm(pulse(s(59) - s(54) + 1, 110, lambda t: 1.0)) * 0.55 + norm(ticker(s(59) - s(54) + 1, 150)) * 0.3, s(54), s(59, -0.05), 0.5, 0.05)
    bed(norm(lp(pad(D_MINOR, s(64) - s(59) + 2, bar=6.0, cutoff=500), 400)) * 0.35, s(59, 0.6), s(64), 1.5, 1.0)
    # 06 the plan: pulse + ticks get denser
    d6 = s(70) - s(64)
    bed(norm(pulse(d6 + 1, 96, lambda t: min(1, t / d6))) * 0.5 + norm(ticker(d6 + 1, 120)) * 0.25
        + norm(pad(D_MINOR, d6 + 1, cutoff=900)) * 0.3, s(64), s(70), 1.0, 0.5)
    # 07: peak tension over Rauf, near-silence on the TV beat, then the drive slams in on the six
    bed(norm(pulse(s(72) - s(70) + 1, 120, lambda t: 1.0)) * 0.55 + norm(ticker(s(72) - s(70) + 1, 160)) * 0.3, s(70), s(72), 0.3, 0.6)
    bed(norm(lp(pad(A_MINOR, s(74) - s(72) + 1, cutoff=500), 350)) * 0.25, s(72), s(74), 0.6, 0.2)
    six = s(74) + (s(75) - s(74)) * 0.55
    bed(drive(e(92) + 4.0 - six + 1, bpm=132) * 0.85, six - 0.05, e(92) + 4.0, 0.05, 1.5)
    # 09 the answer: warm close, out with the logo
    t9 = s(93, -0.4)
    bed(warm(total - t9 + 2), t9, total, 2.0, 3.5)

    # voice, ducked music
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

    # SFX on the logged events + story moments
    fx = np.zeros(int(SR * total))
    cache = {"braam": braam(), "flatline": flatline(), "rewind": rewind_fx()}

    def put(name, t, g):
        if name not in cache:
            cache[name] = getattr(sfx, name)()
        add(fx, cache[name], max(0, t), g)

    for t, kind in ev["events"]:
        if kind == "whoosh":
            put("whoosh", t - 0.12, 0.15)
        elif kind == "impact":
            put("impact", t, 0.25)
        elif kind == "soft":
            put("pop", t, 0.10)
        elif kind == "roll":
            for k in range(9):
                put("tick", t + 0.05 * k, 0.09)
        elif kind == "pop":
            put("pop", t, 0.13)
        elif kind == "hit":
            put("impact", t, 0.28)
            put("whoosh", t - 0.15, 0.12)
        elif kind == "cut":
            put("whoosh", t - 0.1, 0.06)
        elif kind == "swell":
            put("riser", t - 1.6, 0.15)
        elif kind == "heartbeat":
            put("heartbeat", t, 0.30)
        elif kind == "flatline":
            put("flatline", t, 0.22)
        elif kind == "rewind":
            put("rewind", t, 0.32)
        elif kind == "freeze":
            put("camera_shutter", t, 0.3)
            put("impact", t, 0.2)
        elif kind.startswith("chip_"):
            put("impact" if kind in ("chip_w", "chip_six", "chip_win") else "pop", t, 0.22 if kind != "chip_n" else 0.14)
    put("braam", e(6) + 0.9, 0.55)                       # title
    put("braam", s(59, -0.05), 0.5)                      # 31/4
    put("riser", s(63, -1.4), 0.3)
    put("riser", six - 1.9, 0.35)
    put("impact", six, 0.5)                              # bat on ball
    put("crowd", six + 0.2, 0.55)
    put("crowd", s(77) + (s(78) - s(77)) * 0.45, 0.55)   # second six
    put("crowd", s(83, 1.5), 0.45)                       # no-ball six
    put("riser", s(91, -0.3), 0.3)
    put("crowd", e(91) - 0.3, 0.6)                       # the win
    put("crowd", e(92) + 1.5, 0.45)
    put("ding", s(99, 0.4), 0.22)

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

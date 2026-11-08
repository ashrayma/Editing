#!/usr/bin/env python3
"""Score + sound design for the Adelaide 2003 Short. Original, synthesised (shared instruments with kohli_mcg).

    python3 soundtrack.py   ->  out/soundtrack.wav
Hook: suspense pulse. "LOST": braam. Dravid & Laxman -> chase: the energetic drive (filtered in, full from the twist).
"The real twist": near silence + riser. "India won": hit + crowd. "Think about it" -> CTA: warm close.
"""
import importlib.util
import json
import os
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "kohli_countdown"))
import sfx  # noqa: E402
from music import add, lp  # noqa: E402

_spec = importlib.util.spec_from_file_location("km", os.path.join(HERE, "..", "kohli_mcg", "soundtrack.py"))
km = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(km)
SR = sfx.SR


def main():
    ev = json.load(open(os.path.join(HERE, "out", "events.json")))
    total, B = ev["total"], ev["beats"]
    s = lambda b, f=0.0: B[b][0] + f * (B[b][1] - B[b][0])  # noqa: E731
    e = lambda b: B[b][1]  # noqa: E731
    m = np.zeros(int(SR * total))

    def bed(x, t0, t1, fi=1.0, fo=1.0):
        nonlocal m
        m += km.section(x[: int(SR * (t1 - t0 + 1))], t0, total, fi, fo)

    d = s("l02", 0.3)
    bed(km.norm(km.reverb(km.pad(km.D_MINOR, d + 2, cutoff=900), 2.0, 0.35)) * 0.5
        + km.norm(km.pulse(d + 2, 92, lambda t: 0.5 + min(t / d, 1) / 2)) * 0.5 + km.norm(km.ticker(d + 2, 120)) * 0.2,
        0.0, d, 0.3, 0.2)
    t1 = s("l06")
    bed(km.norm(km.reverb(km.pad(km.A_MINOR, t1 - d + 2, bar=4.0, cutoff=800), 2.0, 0.4)) * 0.4, d + 0.8, t1, 1.0, 0.8)
    t2 = s("l10")
    dr = km.drive(t2 - t1 + 1, bpm=128)
    k = int(SR * 3)
    dr[:k] = lp(dr[:k], 700)
    bed(dr * 0.7, t1, t2, 0.8, 0.1)
    t3 = s("l11")
    bed(km.norm(lp(km.pad(km.D_MINOR, t3 - t2 + 2, cutoff=500), 400)) * 0.3, t2, t3, 0.3, 0.1)
    t4 = s("l18")
    bed(km.drive(t4 - t3 + 1, bpm=138) * 0.85, t3 - 0.05, t4, 0.05, 0.8)
    bed(km.norm(km.reverb(km.pad(km.WARM, total - t4 + 2, cutoff=1600), 2.5, 0.4)) * 0.45
        + km.norm(km.reverb(km.arps(km.WARM, total - t4 + 2), 1.5, 0.3)) * 0.35, t4 - 0.3, total, 1.5, 2.5)

    vo = np.zeros(int(SR * total))
    with wave.open(os.path.join(HERE, "out", "vo_final.wav")) as w:
        v = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    vo[: min(len(v), len(vo))] = v[: len(vo)]
    hop = 441
    env = np.abs(vo[: len(vo) // hop * hop]).reshape(-1, hop).max(1)
    env = np.convolve(env > 0.03, np.ones(30), "same") > 0
    duck = np.convolve(np.repeat(np.where(env, 0.42, 1.0), hop), np.ones(4410) / 4410, "same")
    m[: len(duck)] *= duck

    fx = np.zeros(int(SR * total))
    cache = {"braam": km.braam()}

    def put(name, t, g):
        if name not in cache:
            cache[name] = getattr(sfx, name)()
        add(fx, cache[name], max(0.0, t), g)

    for t, kind in ev["events"]:
        if kind == "whoosh":
            put("whoosh", t - 0.12, 0.16)
        elif kind == "impact":
            put("impact", t, 0.26)
        elif kind == "soft":
            put("pop", t, 0.10)
        elif kind == "roll":
            for q in range(9):
                put("tick", t + 0.05 * q, 0.09)
        elif kind == "pop":
            put("pop", t, 0.13)
        elif kind == "hit":
            put("impact", t, 0.3)
        elif kind == "tick_run":
            for q in range(28):
                put("tick", t + 0.12 * q, 0.07)
    put("braam", s("l01", 0.0), 0.5)                 # 556
    put("braam", s("l02", 0.4), 0.55)                # LOST
    put("riser", s("l11", 0.0) - 1.6, 0.3)           # the twist
    put("braam", s("l13", 0.4), 0.5)                 # 196 all out
    put("riser", s("l17", 0.0) - 1.4, 0.3)
    put("crowd", s("l17", 0.1), 0.55)                # India won
    put("ding", s("l25", 0.6), 0.22)

    mix = vo * 0.95 + m * 0.24 + fx * 0.55
    mix = np.tanh(mix * 1.05) / np.tanh(1.05)
    mix = mix / max(1e-6, np.abs(mix).max()) * 0.9
    with wave.open(os.path.join(HERE, "out", "soundtrack.wav"), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.stack([mix, mix], 1) * 32767).astype(np.int16).tobytes())
    print(f"soundtrack {total:.1f}s")


if __name__ == "__main__":
    main()

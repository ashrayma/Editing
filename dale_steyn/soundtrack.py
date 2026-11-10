#!/usr/bin/env python3
"""Score + sound design for the Dale Steyn Short. Original, synthesised (shared instruments with kohli_mcg).

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
    LAST = max(B, key=lambda k: B[k][0])
    m = np.zeros(int(SR * total))

    def bed(x, t0, t1, fi=1.0, fo=1.0):
        nonlocal m
        m += km.section(x[: int(SR * (t1 - t0 + 1))], t0, total, fi, fo)

    d = s("l03", 0.6)                                     # cold open: suspense pulse up to "FEAR."
    bed(km.norm(km.reverb(km.pad(km.D_MINOR, d + 2, cutoff=900), 2.0, 0.35)) * 0.5
        + km.norm(km.pulse(d + 2, 100, lambda t: 0.5 + min(t / d, 1) / 2)) * 0.5 + km.norm(km.ticker(d + 2, 132)) * 0.25,
        0.0, d, 0.2, 0.15)
    t1 = s("l08", 0.55)                                   # build to the reveal
    bed(km.norm(km.reverb(km.pad(km.A_MINOR, t1 - d + 2, bar=4.0, cutoff=800), 2.0, 0.4)) * 0.4
        + km.norm(km.pulse(t1 - d + 2, 120, lambda t: 0.4 + 0.6 * min(t / (t1 - d), 1))) * 0.4, d + 0.4, t1, 0.6, 0.1)
    t2 = s("l20")                                         # STEYN: the drive, full from the reveal
    bed(km.drive(t2 - t1 + 1, bpm=140) * 0.85, t1 - 0.05, t2, 0.05, 0.5)
    t3 = s("l22")                                         # "terrifying... only number 2": dark pad, then the question
    bed(km.norm(km.reverb(km.pad(km.D_MINOR, t3 - t2 + 2, cutoff=600), 2.0, 0.4)) * 0.4, t2, t3, 0.3, 0.2)
    bed(km.norm(km.pulse(total - t3 + 2, 100, lambda t: 0.6)) * 0.4 + km.norm(km.ticker(total - t3 + 2, 132)) * 0.25
        + km.norm(km.reverb(km.pad(km.WARM, total - t3 + 2, cutoff=1400), 2.5, 0.4)) * 0.4, t3, total, 0.2, 2.0)

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

    # light touch: soft whooshes on cuts (not every one), a hit only on the big stamps/3D, no pops or tick rolls
    last_w = -9.0
    for t, kind in ev["events"]:
        if kind == "whoosh" and t - last_w > 1.5:
            put("whoosh", t - 0.12, 0.07)
            last_w = t
        elif kind == "hit":
            put("impact", t, 0.16)
    put("braam", s("l03", 0.6), 0.35)                # FEAR.
    put("riser", s("l08", 0.55) - 1.5, 0.18)
    put("braam", s("l08", 0.55), 0.4)                # Dale Steyn
    put("riser", s("l22", 0.0) - 1.3, 0.15)
    put("ding", s(LAST, 0.2), 0.15)

    mix = vo * 0.95 + m * 0.24 + fx * 0.4
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

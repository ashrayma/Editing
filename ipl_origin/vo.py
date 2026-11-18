#!/usr/bin/env python3
"""Clean the creator's take (vo/vo_raw.m4a) into out/vo_reel.wav, using the Karun cleaner's silence rules:
every cut sits in real room silence (checked on the loudness curve and by transcribing each side), and pauses are
shortened only inside silence, keeping TAIL after the last word.
"""
import json
import os
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "karun_303"))
import clean_vo as C  # noqa: E402

START, END = 3.70, 116.90
CUTS = [(45.00, 58.90)]   # first "2007 tak kahani badal chuki thi…" take; the full retake starts at 58.95
C.PAUSE, C.TAIL = 0.34, 0.17


def main():
    a = C.load(os.path.join(HERE, "vo", "vo_raw.m4a"))
    env = C.Env(a)
    for t in [START, END] + [x for c in CUTS for x in c]:
        assert env.silent(t), f"edit point {t} is not in silence"
    keep, t = [], START
    for c0, c1 in CUTS:
        keep.append((t, c0))
        t = c1
    keep.append((t, END))
    out, vmap, pos = [], [], 0.0
    for k0, k1 in keep:
        for s0, s1 in C.shorten(env, k0, k1):
            seg = C.fade(a[int(s0 * C.SR):int(s1 * C.SR)])
            out.append(seg)
            vmap.append({"raw": [round(s0, 3), round(s1, 3)], "clean": round(pos, 3)})
            pos += len(seg) / C.SR
    y = np.concatenate(out)
    y = y / (np.abs(y).max() + 1e-9) * 0.9
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    import scipy.signal as ss
    y44 = ss.resample_poly(y, 147, 160)                    # 48 kHz -> 44.1 kHz, the reel's soundtrack rate
    with wave.open(os.path.join(HERE, "out", "vo_reel.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(44100)
        w.writeframes((np.clip(y44, -1, 1) * 32767).astype(np.int16).tobytes())
    json.dump(vmap, open(os.path.join(HERE, "vo", "vo_map.json"), "w"), indent=0)
    print(f"clean VO {pos:.1f}s, {len(vmap)} pieces")


if __name__ == "__main__":
    main()

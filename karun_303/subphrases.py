#!/usr/bin/env python3
"""Finer split of a window of a take at short pauses, to find exactly where a fumble/retake starts.

    python3 subphrases.py <take> <start> <end> [min_sil=0.14]
"""
import os
import sys

import numpy as np

import transcribe as T

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = open(os.path.join(HERE, "script.txt")).read()


def split(a, s, e, min_sil):
    T.MIN_SIL = min_sil
    T.MIN_PHRASE = 0.12
    seg = a[int(s * T.SR): int(e * T.SR)]
    ph, _ = T.phrases(seg)
    return [(round(s + p[0], 2), round(s + p[1], 2)) for p in ph]


if __name__ == "__main__":
    from faster_whisper import WhisperModel
    take, s, e = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
    ms = float(sys.argv[4]) if len(sys.argv) > 4 else 0.14
    a = T.load(os.path.join(HERE, "vo_raw", take + ".m4a"))
    m = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=4)
    for ps, pe in split(a, s, e, ms):
        segs, _ = m.transcribe(a[int(ps * T.SR): int(pe * T.SR)], language="en", beam_size=2,
                               initial_prompt="Hinglish, Roman script: " + T.PROMPT[:140], without_timestamps=True,
                               condition_on_previous_text=False)
        print(f"  [{ps:7.2f}-{pe:7.2f}] {' '.join(x.text.strip() for x in segs)}", flush=True)

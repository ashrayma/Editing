#!/usr/bin/env python3
"""Scratch English narration so the Short can be timed before the real voiceover arrives.

    python3 scratch_vo.py   ->  out/vo_final.wav + out/vo_timeline.json
Replace with the real recording via build_vo.py (same output files); the edit re-times itself.
"""
import json
import os
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from beats import BEATS, BREATH  # noqa: E402

SR, GAP, LEAD = 44100, 0.35, 0.4
MODELS = os.path.join(HERE, "..", "kohli_countdown", "models")


def main():
    from kokoro_onnx import Kokoro
    tts = Kokoro(os.path.join(MODELS, "kokoro-v1.0.onnx"), os.path.join(MODELS, "voices-v1.0.bin"))
    out, beats, t = [np.zeros(int(SR * LEAD))], [], LEAD
    for bid, text in BEATS:
        x, sr = tts.create(text.replace("…", ","), voice="am_michael", speed=1.08, lang="en-us")
        x = np.interp(np.linspace(0, len(x) - 1, int(len(x) * SR / sr)), np.arange(len(x)), x)
        x = x / (np.abs(x).max() + 1e-9) * 0.8
        beats.append({"id": bid, "start": round(t, 3), "end": round(t + len(x) / SR, 3), "text": text})
        gap = GAP + BREATH.get(bid, 0.0)
        out += [x, np.zeros(int(SR * gap))]
        t += len(x) / SR + gap
    a = np.concatenate(out)
    with wave.open(os.path.join(HERE, "out", "vo_final.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((a * 32767).astype(np.int16).tobytes())
    json.dump({"duration": round(len(a) / SR, 3), "scratch": True, "beats": beats},
              open(os.path.join(HERE, "out", "vo_timeline.json"), "w"), indent=1)
    print(f"total {len(a) / SR:.1f}s")


if __name__ == "__main__":
    main()

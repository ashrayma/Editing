#!/usr/bin/env python3
"""Scratch narration so the edit can be timed before the real voiceover arrives.

    python3 scratch_vo.py   ->  out/vo_final.wav + out/vo_timeline.json   (same format build_vo.py writes)

Offline Kokoro TTS reads each beat of beats.py. It's only a timing guide: replace it with your recording
(build_vo.py) and every cut, caption and B-roll entry re-times itself.
"""
import json
import os
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from beats import BEATS  # noqa: E402

SR = 44100
GAP = 0.45          # pause between beats
MODELS = os.path.join(HERE, "..", "kohli_countdown", "models")


def resample(x, sr_in, sr_out):
    n = int(len(x) * sr_out / sr_in)
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x)


def main():
    from kokoro_onnx import Kokoro
    tts = Kokoro(os.path.join(MODELS, "kokoro-v1.0.onnx"), os.path.join(MODELS, "voices-v1.0.bin"))
    out, beats, t = [], [], 0.6
    out.append(np.zeros(int(SR * t)))
    for bid, text in BEATS:
        samples, sr = tts.create(text, voice="hm_omega", speed=1.08, lang="en-us")
        x = resample(np.asarray(samples, dtype=np.float64), sr, SR)
        x = x / (np.abs(x).max() + 1e-9) * 0.8
        beats.append({"id": bid, "start": round(t, 3), "end": round(t + len(x) / SR, 3), "text": text})
        out.append(x)
        out.append(np.zeros(int(SR * GAP)))
        t += len(x) / SR + GAP
        print(f"{bid:16s} {beats[-1]['start']:7.2f} -> {beats[-1]['end']:7.2f}", flush=True)
    a = np.concatenate(out)
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    with wave.open(os.path.join(HERE, "out", "vo_final.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((a * 32767).astype(np.int16).tobytes())
    json.dump({"duration": round(len(a) / SR, 3), "scratch": True, "beats": beats},
              open(os.path.join(HERE, "out", "vo_timeline.json"), "w"), indent=1, ensure_ascii=False)
    print(f"total {len(a) / SR:.1f}s")


if __name__ == "__main__":
    main()

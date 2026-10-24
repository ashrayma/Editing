#!/usr/bin/env python3
"""Scratch voiceover from script.json with the offline Kokoro TTS, so the edit can be
timed before the real recording exists. Writes film/assets/audio/scratch_vo.wav and
timing.json (start/end of every script line, in seconds).

Replace it with your own recording via tools/timing_from_recording.py.

usage: python3 tools/scratch_vo.py [--voice hm_omega] [--speed 1.25] [--lang hi]

Times are relative to the start of the voice; build.py places the voice after the hook clip.
"""
import argparse, json, os
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.environ.get("KOKORO_MODELS", os.path.join(ROOT, "..", "kohli_countdown", "models"))
GAP = 0.14  # tight, Warikoo-style: barely a breath between lines


def trim(a, thr=0.01):
    idx = np.where(np.abs(a) > thr)[0]
    return a[max(0, idx[0] - 400):idx[-1] + 1200] if len(idx) else a


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default="hm_omega")
    ap.add_argument("--speed", type=float, default=1.25)
    ap.add_argument("--lang", default="hi")
    args = ap.parse_args()
    script = json.load(open(os.path.join(ROOT, "script.json")))
    tts = Kokoro(os.path.join(MODELS, "kokoro-v1.0.onnx"), os.path.join(MODELS, "voices-v1.0.bin"))
    out, timing, t, sr = [], [], 0.05, 24000
    out.append(np.zeros(int(sr * t), dtype=np.float32))
    for line in script["lines"]:
        a, sr = tts.create(line.get("tts", line["text"]), voice=args.voice, speed=args.speed, lang=args.lang)
        a = trim(a.astype(np.float32))
        d = len(a) / sr
        timing.append({"id": line["id"], "start": round(t, 3), "end": round(t + d, 3)})
        out += [a, np.zeros(int(sr * GAP), dtype=np.float32)]
        t += d + GAP
    out.append(np.zeros(int(sr * 0.8), dtype=np.float32))
    audio = np.concatenate(out)
    audio *= 0.89 / max(1e-6, np.abs(audio).max())  # peak about -1 dBFS
    os.makedirs(os.path.join(ROOT, "film/assets/audio"), exist_ok=True)
    sf.write(os.path.join(ROOT, "film/assets/audio/scratch_vo.wav"), audio, sr)
    doc = {"source": "scratch", "audio": "assets/audio/scratch_vo.wav", "duration": round(len(audio) / sr, 3), "lines": timing}
    json.dump(doc, open(os.path.join(ROOT, "timing.json"), "w"), indent=1)
    # reference rhythm for tools/timing_from_recording.py
    json.dump(doc, open(os.path.join(ROOT, "timing_scratch.json"), "w"), indent=1)
    print(f"scratch VO {len(audio) / sr:.1f}s, {len(timing)} lines")

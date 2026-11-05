#!/usr/bin/env python3
"""Transcribe raw voice takes phrase by phrase (offline Whisper small.en via sherpa-onnx).

    python3 transcribe.py vo_raw/*.m4a   ->  out/transcript_<take>.json + printout: [start-end] text

Splits each take at its pauses first, so every phrase gets its own timestamps; that's what the
edit list in build_vo.py (TAKES / PIECES) is picked from.
"""
import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "kohli_countdown"))
from voiceover import SR, voiced_regions  # noqa: E402

M = os.path.join(HERE, "models", "sherpa-onnx-whisper-small.en")


def decode(path, sr):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def main():
    import sherpa_onnx
    rec = sherpa_onnx.OfflineRecognizer.from_whisper(
        encoder=f"{M}/small.en-encoder.int8.onnx", decoder=f"{M}/small.en-decoder.int8.onnx",
        tokens=f"{M}/small.en-tokens.txt", language="en", task="transcribe", num_threads=4)
    for path in sys.argv[1:]:
        a = decode(path, SR)
        a16 = decode(path, 16000)
        out = []
        for s0, s1 in voiced_regions(a / max(1e-6, np.abs(a).max())):
            seg = a16[int(max(0, s0 - 0.1) * 16000): int((s1 + 0.1) * 16000)]
            st = rec.create_stream()
            st.accept_waveform(16000, seg)
            rec.decode_stream(st)
            out.append({"start": round(s0, 2), "end": round(s1, 2), "text": st.result.text.strip()})
            print(f"[{s0:6.2f}-{s1:6.2f}] {out[-1]['text']}", flush=True)
        name = os.path.splitext(os.path.basename(path))[0]
        json.dump(out, open(os.path.join(HERE, "out", f"transcript_{name}.json"), "w"), indent=1)
        print("----", name)


if __name__ == "__main__":
    main()

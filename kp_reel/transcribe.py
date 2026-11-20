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
MH = os.path.join(HERE, "models", "sherpa-onnx-whisper-small")  # multilingual, for Hinglish reads (--hi)


def split(a, sr, min_gap=0.22):
    """Phrases separated by pauses of at least min_gap s (finer than voiced_regions, so retakes split apart)."""
    hop = int(0.01 * sr)
    e = 20 * np.log10(np.sqrt((a[: len(a) // hop * hop].reshape(-1, hop) ** 2).mean(1)) + 1e-9)
    loud = e > max(np.percentile(e, 95) - 32, np.percentile(e, 10) + 7)
    segs, i, n = [], 0, len(loud)
    while i < n:
        if loud[i]:
            j = i
            gap = 0
            while j < n and gap < int(min_gap / 0.01):
                gap = 0 if loud[j] else gap + 1
                j += 1
            segs.append((i * 0.01, (j - gap) * 0.01))
            i = j
        else:
            i += 1
    out = []
    for a0, b0 in segs:  # Whisper reads at most 30 s: cut long runs at their quietest points, max ~8 s each
        while b0 - a0 > 6.0:
            lo, hi_ = int((a0 + 2.5) / 0.01), int((a0 + 6.0) / 0.01)
            cut = (lo + int(np.argmin(e[lo:hi_]))) * 0.01
            out.append((a0, cut))
            a0 = cut
        out.append((a0, b0))
    return [(a0, b0) for a0, b0 in out if b0 - a0 > 0.25]


def decode(path, sr):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def main():
    import sherpa_onnx
    hi = "--hi" in sys.argv
    if hi:
        rec = sherpa_onnx.OfflineRecognizer.from_whisper(
            encoder=f"{MH}/small-encoder.onnx", decoder=f"{MH}/small-decoder.onnx",
            tokens=f"{MH}/small-tokens.txt", language="hi", task="transcribe", num_threads=4)
    else:
        rec = sherpa_onnx.OfflineRecognizer.from_whisper(
            encoder=f"{M}/small.en-encoder.int8.onnx", decoder=f"{M}/small.en-decoder.int8.onnx",
            tokens=f"{M}/small.en-tokens.txt", language="en", task="transcribe", num_threads=4)
    for path in [p for p in sys.argv[1:] if not p.startswith("--")]:
        a = decode(path, SR)
        a16 = decode(path, 16000)
        out = []
        regions = split(a16, 16000) if hi else voiced_regions(a / max(1e-6, np.abs(a).max()))
        for s0, s1 in regions:
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

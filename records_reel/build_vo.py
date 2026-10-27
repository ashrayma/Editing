#!/usr/bin/env python3
"""Narration track + timeline.

    python3 build_vo.py              ->  temporary AI voice (offline Kokoro), one clip per line
    python3 build_vo.py my_take.m4a  ->  your recording: cleaned, split at the pauses, matched to the lines

Writes out/vo.wav (44.1 kHz mono) and out/timeline.json: start/end of every line, plus
per-word caption timings (spread across the line by syllable weight).
"""
import json
import os
import re
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "kohli_countdown"))
from voiceover import SR, clean_recording, load_any, voiced_regions  # noqa: E402
from script import LINES  # noqa: E402

OUT = os.path.join(HERE, "out")
LEAD = 0.25
os.makedirs(OUT, exist_ok=True)


def tts_lines():
    from kokoro_onnx import Kokoro
    import soundfile as sf
    tts = Kokoro(os.path.join(HERE, "models", "kokoro-v1.0.onnx"), os.path.join(HERE, "models", "voices-v1.0.bin"))
    clips = []
    for lid, text, _, _ in LINES:
        samples, sr = tts.create(text, voice="am_michael", speed=1.12, lang="en-us")
        tmp = os.path.join(OUT, "_tts.wav")
        sf.write(tmp, samples, sr)
        clips.append(load_any(tmp))
        os.remove(tmp)
        print(f"  {lid:>4}: {len(clips[-1]) / SR:.2f}s")
    return clips


def recording_lines(path):
    """Split one long take at its pauses and map the pieces onto the script lines in order.

    Each speech region is assigned to the line whose expected length (from the text) it best fills; regions
    that belong to the same line (a breath mid-sentence) are merged. Check the printout: if a line got the
    wrong audio, re-record with a clear ~1 s pause between lines.
    """
    a = clean_recording(path)  # also shortens long pauses to 0.28 s, so use raw regions
    regions = voiced_regions(a)
    weights = np.array([len(t) for _, t, _, _ in LINES], float)
    total = sum(r[1] - r[0] for r in regions)
    expect = weights / weights.sum() * total
    clips, k, cur = [], 0, []
    for li in range(len(LINES)):
        acc = 0.0
        while k < len(regions) and (not cur or abs(acc + (regions[k][1] - regions[k][0]) - expect[li]) < abs(acc - expect[li])):
            cur.append(regions[k])
            acc += regions[k][1] - regions[k][0]
            k += 1
        if li == len(LINES) - 1:
            cur += regions[k:]
        s, e = cur[0][0], cur[-1][1]
        clips.append(a[int(max(0, s - 0.04) * SR): int((e + 0.06) * SR)])
        print(f"  {LINES[li][0]:>4}: {e - s:.2f}s (expected {expect[li]:.2f}s)")
        cur = []
    return clips


def syllables(w):
    w = re.sub(r"[^a-z0-9]", "", w.lower())
    if w.isdigit():
        return 1.5 * len(w)
    return max(1, len(re.findall(r"[aeiouy]+", w)))


def main():
    clips = recording_lines(sys.argv[1]) if len(sys.argv) > 1 else tts_lines()
    parts, t, lines = [np.zeros(int(LEAD * SR), np.float32)], LEAD, []
    for (lid, text, cap, gap), c in zip(LINES, clips):
        c = c / max(1e-6, np.abs(c).max()) * 0.9
        fade = int(0.01 * SR)
        c[:fade] *= np.linspace(0, 1, fade)
        c[-fade:] *= np.linspace(1, 0, fade)
        dur = len(c) / SR
        # word timings: spread over the voiced part of the clip
        vr = voiced_regions(c) or [(0, dur)]
        v0, v1 = vr[0][0], vr[-1][1]
        words = (cap or text).split()
        wt = np.array([syllables(w) for w in words], float)
        edges = v0 + np.concatenate([[0], np.cumsum(wt)]) / wt.sum() * (v1 - v0)
        lines.append({"id": lid, "text": text, "caption": cap or text, "start": round(t, 3), "end": round(t + dur, 3),
                      "words": [[w, round(t + edges[i], 3), round(t + edges[i + 1], 3)] for i, w in enumerate(words)]})
        parts += [c.astype(np.float32), np.zeros(int(gap * SR), np.float32)]
        t += dur + gap
    vo = np.concatenate(parts)
    with wave.open(os.path.join(OUT, "vo.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((vo * 32767).astype(np.int16).tobytes())
    json.dump({"duration": round(t, 3), "source": sys.argv[1] if len(sys.argv) > 1 else "tts", "lines": lines},
              open(os.path.join(OUT, "timeline.json"), "w"), indent=1)
    print(f"VO {t:.1f}s")


if __name__ == "__main__":
    main()

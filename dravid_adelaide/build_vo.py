#!/usr/bin/env python3
"""The user's voiceover -> out/vo_final.wav + out/vo_timeline.json (replaces the scratch voice).

    python3 build_vo.py vo_raw/vo_125124.mp3@h1-h3 vo_raw/vo_124640.mp3@l01-l25

Each file is given the script lines it holds. The lines are found by forced alignment of the script text
(PocketSphinx, ../kohli_mcg/tools/align.py; the narration is English, so it aligns closely); each cut goes in the
pause between one line's last word and the next line's first, then lines are laid out with short gaps.
"""
import json
import os
import subprocess
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "kohli_countdown"))
sys.path.insert(0, os.path.join(HERE, "..", "kohli_mcg", "tools"))
from align import align_chunked  # noqa: E402
from beats import BEATS, BREATH  # noqa: E402
from voiceover import SR, voiced_regions  # noqa: E402

GAP, LEAD = 0.3, 0.3


def load(path):
    """Light cleanup for a studio/TTS voice: high-pass, gentle compression; no pause tightening."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(SR), "-af",
                          "highpass=f=70,acompressor=threshold=-20dB:ratio=2.5:attack=5:release=120:makeup=2",
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def main():
    ids = [b for b, _ in BEATS]
    pieces = {}
    for arg in sys.argv[1:]:
        path, rng = arg.split("@")
        lo, hi = rng.split("-")
        sub = BEATS[ids.index(lo): ids.index(hi) + 1]
        audio = load(os.path.join(HERE, path))
        raw16 = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(HERE, path), "-ac", "1", "-ar", "16000",
                                "-f", "s16le", "-"], capture_output=True, check=True).stdout
        total = len(audio) / SR
        chars = sum(len(t) for _, t in sub)
        tm = align_chunked(raw16, sub, {b: total * len(t) / chars for b, t in sub})
        regions = voiced_regions(audio)
        pauses = [(regions[k][1] + regions[k + 1][0]) / 2 for k in range(len(regions) - 1)]
        cuts, lo_t = [0.0], 0.0
        for (b0, _), (b1, _) in zip(sub, sub[1:]):
            if b0 in tm and b1 in tm:
                e, s = tm[b0][1], tm[b1][0]
                gap = [p for p in pauses if e - 0.25 <= p <= s + 0.25 and p > lo_t + 0.3]
                c = min(gap, key=lambda p: abs(p - (e + s) / 2)) if gap else (e + s) / 2
            else:
                c = lo_t + total * len(dict(sub)[b0]) / chars
                print("  estimated (not aligned):", b0)
            cuts.append(c)
            lo_t = c
        cuts.append(total)
        for k, (b, _) in enumerate(sub):
            seg = audio[int(cuts[k] * SR): int(cuts[k + 1] * SR)]
            r = voiced_regions(seg)
            if r:
                seg = seg[max(0, int((r[0][0] - 0.04) * SR)): int((r[-1][1] + 0.08) * SR)]
            pieces[b] = seg
    missing = [b for b in ids if b not in pieces]
    if missing:
        sys.exit(f"no audio for: {missing}")
    out, beats, t = [np.zeros(int(SR * LEAD), np.float32)], [], LEAD
    for b, text in BEATS:
        seg = pieces[b]
        beats.append({"id": b, "start": round(t, 3), "end": round(t + len(seg) / SR, 3), "text": text})
        gap = GAP + BREATH.get(b, 0.0)
        out += [seg, np.zeros(int(SR * gap), np.float32)]
        t += len(seg) / SR + gap
        print(f"{b:4s} {beats[-1]['start']:6.2f} -> {beats[-1]['end']:6.2f}  {text[:55]}")
    a = np.concatenate(out)
    a = a / (np.abs(a).max() + 1e-9) * 0.89
    with wave.open(os.path.join(HERE, "out", "vo_final.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((a * 32767).astype(np.int16).tobytes())
    json.dump({"duration": round(len(a) / SR, 3), "scratch": False, "beats": beats},
              open(os.path.join(HERE, "out", "vo_timeline.json"), "w"), indent=1)
    print(f"total {len(a) / SR:.1f}s")


if __name__ == "__main__":
    main()

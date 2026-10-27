#!/usr/bin/env python3
"""Narration track + timeline.

    python3 build_vo.py              ->  your recording, cut from the takes in script.TAKES by script.PIECES
    python3 build_vo.py --tts        ->  temporary AI voice (offline Kokoro), one clip per line
    python3 build_vo.py my_take.m4a  ->  one clean single take: split at the pauses, matched to the lines

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
from script import LINES, PIECES, TAKES  # noqa: E402

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


CLEAN = ("highpass=f=85,afftdn=nf=-28:nr=14,equalizer=f=250:t=q:w=1.2:g=-2,equalizer=f=3500:t=q:w=1.0:g=3,"
         "acompressor=threshold=-22dB:ratio=3.5:attack=4:release=90:makeup=4")  # voiceover.clean_recording's chain


def load_take(take):
    import subprocess
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(HERE, TAKES[take]), "-ac", "1", "-ar", str(SR),
                          "-af", CLEAN, "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def pauses(a, min_len=0.07):
    """(start, end) of every real pause in a take: >= 70 ms below the speech-relative silence threshold."""
    hop = int(0.01 * SR)
    e = 20 * np.log10(np.sqrt((a[: len(a) // hop * hop].reshape(-1, hop) ** 2).mean(1)) + 1e-9)
    quiet = e < max(np.percentile(e, 95) - 30, np.percentile(e, 10) + 6)
    out, i = [], 0
    while i < len(quiet):
        if quiet[i]:
            j = i
            while j < len(quiet) and quiet[j]:
                j += 1
            if (j - i) * 0.01 >= min_len:
                out.append((i * 0.01, j * 0.01))
            i = j
        else:
            i += 1
    return out


def near_pause(ps, t, win=0.22):
    best = None
    for p in ps:
        if p[0] - win <= t <= p[1] + win:
            d = 0 if p[0] <= t <= p[1] else min(abs(t - p[0]), abs(t - p[1]))
            if best is None or d < best[0]:
                best = (d, p)
    return best[1] if best else None


FORCE_CUT = {"n1a", "n2a", "n3a"}  # always cut after these (the 3D chapter cards need the breath)


def quiet_point(a, t, win=0.08):
    hop = int(0.005 * SR)
    i0, i1 = int((t - win) * SR), int((t + win) * SR)
    e = [float(np.sqrt((a[i:i + 4 * hop] ** 2).mean())) for i in range(i0, i1, hop)]
    return (i0 + int(np.argmin(e)) * hop + 2 * hop) / SR


def edit_groups():
    """Cut the lines out of the raw takes. A boundary between two lines that run on in the same take is only cut
    where there is a real pause; otherwise the lines stay joined (no gap inserted) and only the captions split.
    Returns [(audio, [(line id, start, end) within the audio])]."""
    takes = {k: load_take(k) for k in TAKES}
    ps = {k: pauses(v) for k, v in takes.items()}
    flat = [(lid, take, a, b, k == len(PIECES[lid]) - 1) for lid, *_ in LINES for k, (take, a, b) in enumerate(PIECES[lid])]
    # decide each boundary: cut (with snapped edges) or join
    groups, cur, lines_in, line_start = [], [], [], {}
    for n, (lid, take, a, b, last) in enumerate(flat):
        prev = flat[n - 1] if n else None
        contiguous = prev and prev[1] == take and abs(prev[3] - a) < 0.02
        p_in = near_pause(ps[take], a)
        if prev and prev[0] == lid:
            start, joined = a, True  # second piece of a spliced line
        elif contiguous and prev[0] in FORCE_CUT and p_in is None:
            start, joined = quiet_point(takes[take], a), False
        elif contiguous and prev[4] and p_in is None:
            start = a  # join: the previous line runs straight into this one
            joined = True
        else:
            start = p_in[1] - 0.04 if p_in else a
            joined = contiguous and not prev[4]  # splice inside a line: butt-join
        nxt = flat[n + 1] if n + 1 < len(flat) else None
        p_out = near_pause(ps[take], b)
        if nxt and nxt[1] == take and abs(nxt[2] - b) < 0.02 and last and p_out is None and lid in FORCE_CUT:
            end = quiet_point(takes[take], b)
        elif nxt and nxt[1] == take and abs(nxt[2] - b) < 0.02 and last and p_out is None:
            end = b
        elif nxt and nxt[0] == lid:
            end = b
        else:
            end = p_out[0] + 0.05 if p_out else b
        seg = takes[take][int(start * SR): int(end * SR)].copy()
        if not joined and cur:
            groups.append((np.concatenate(cur), lines_in))
            cur, lines_in = [], []
        f = min(int(0.012 * SR), len(seg) // 2)
        if not joined:
            seg[:f] *= np.linspace(0, 1, f)
        if not (end == b and nxt and (last or nxt[0] == lid)):
            seg[len(seg) - f:] *= np.linspace(1, 0, f)
        t0 = sum(len(c) for c in cur) / SR
        cur.append(seg)
        if lid not in line_start:
            line_start[lid] = (len(groups), t0)
        if last:
            g, ls = line_start[lid]
            lines_in.append((lid, ls if g == len(groups) else 0.0, t0 + len(seg) / SR))
    groups.append((np.concatenate(cur), lines_in))
    for audio, ls in groups:
        print(f"  [{len(audio) / SR:5.2f}s] " + " | ".join(f"{l} {s:.2f}-{e:.2f}" for l, s, e in ls))
    return groups


def syllables(w):
    w = re.sub(r"[^a-z0-9]", "", w.lower())
    if w.isdigit():
        return 1.5 * len(w)
    return max(1, len(re.findall(r"[aeiouy]+", w)))


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    if arg:
        clips = tts_lines() if arg == "--tts" else recording_lines(arg)
        groups = [(c, [(lid, 0.0, len(c) / SR)]) for (lid, *_), c in zip(LINES, clips)]
    else:
        groups = edit_groups()
    meta = {lid: (text, cap, gap) for lid, text, cap, gap in LINES}
    parts, t, lines = [np.zeros(int(LEAD * SR), np.float32)], LEAD, []
    for c, ls in groups:
        c = c / max(1e-6, np.abs(c).max()) * 0.9
        for lid, s0, s1 in ls:
            text, cap, _ = meta[lid]
            # word timings: spread over the voiced part of the line, by syllable weight
            seg = c[int(s0 * SR): int(s1 * SR)]
            vr = voiced_regions(seg) or [(0, s1 - s0)]
            v0, v1 = s0 + vr[0][0], s0 + vr[-1][1]
            words = (cap or text).split()
            wt = np.array([syllables(w) for w in words], float)
            edges = v0 + np.concatenate([[0], np.cumsum(wt)]) / wt.sum() * (v1 - v0)
            lines.append({"id": lid, "text": text, "caption": cap or text, "start": round(t + s0, 3), "end": round(t + s1, 3),
                          "words": [[w, round(t + edges[i], 3), round(t + edges[i + 1], 3)] for i, w in enumerate(words)]})
        gap = meta[ls[-1][0]][2]
        parts += [c.astype(np.float32), np.zeros(int(gap * SR), np.float32)]
        t += len(c) / SR + gap
    vo = np.concatenate(parts)
    with wave.open(os.path.join(OUT, "vo.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((vo * 32767).astype(np.int16).tobytes())
    json.dump({"duration": round(t, 3), "source": arg or "takes", "lines": lines},
              open(os.path.join(OUT, "timeline.json"), "w"), indent=1)
    print(f"VO {t:.1f}s")


if __name__ == "__main__":
    main()

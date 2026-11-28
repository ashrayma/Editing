#!/usr/bin/env python3
"""Split each voice take into phrases at real silences, then transcribe each phrase (Roman Hinglish).

    python3 transcribe.py vo_raw/take_*.m4a   ->  out/tx/<take>.json  [{start, end, text}], out/tx/<take>.txt

Phrase edges sit in the middle of silences, so any phrase can be cut out or kept without clipping a word.
Whisper runs in English mode with a Hinglish prompt: it then writes the Hindi in Roman script, the same way
the script is written, which makes matching phrases to script lines easy.
"""
import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", os.environ.get("TXDIR", "tx"))
SR = 16000
HOP = 160            # 10 ms frames
MIN_SIL = 0.28       # a pause at least this long splits phrases
MIN_PHRASE = 0.25
HINT = ("James Anderson, deliveries, wickets, Test cricket, England, Lancashire, Sachin Tendulkar.")
PROMPT = ("Sachin Tendulkar, Karun Nair, Ajit Agarkar, Lord's, 248, 493, 37, 34,357, Bangladesh, Australia. "
          "Vijay Hazare, Northamptonshire, BCCI, terbutaline, IPL auction, Maharashtra. Hinglish in Roman script.")


def load(path):
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(pcm, np.int16).astype(np.float32) / 32768


def phrases(a):
    n = len(a) // HOP
    rms = np.sqrt(np.mean(a[: n * HOP].reshape(n, HOP) ** 2, axis=1) + 1e-10)
    db = 20 * np.log10(rms)
    floor = np.percentile(db, 10)
    speech = db > max(floor + 15, np.percentile(db, 60) - 18)
    # close tiny gaps inside words, drop tiny blips
    k = int(MIN_SIL * 100)
    out, i = [], 0
    runs = []
    while i < n:
        j = i
        while j < n and speech[j] == speech[i]:
            j += 1
        runs.append([bool(speech[i]), i, j])
        i = j
    for r in runs:  # short silences count as speech
        if not r[0] and r[2] - r[1] < k:
            r[0] = True
    merged = []
    for r in runs:
        if merged and merged[-1][0] == r[0]:
            merged[-1][2] = r[2]
        else:
            merged.append(r)
    for idx, (sp, s, e) in enumerate(merged):
        if not sp or (e - s) / 100 < MIN_PHRASE:
            continue
        # extend edges into the neighbouring silences (keep breaths natural, ~120 ms pad max)
        s2 = max(0, s - 12)
        e2 = min(n, e + 15)
        out.append((s2 / 100, e2 / 100, s / 100, e / 100))
    return out, db


def main():
    from faster_whisper import WhisperModel
    os.makedirs(OUT, exist_ok=True)
    model = WhisperModel(os.environ.get("WHISPER", "small"), device="cpu", compute_type="int8", cpu_threads=4)
    for path in sys.argv[1:]:
        name = os.path.splitext(os.path.basename(path))[0]
        a = load(path)
        ph, _ = phrases(a)
        rows, prev = [], PROMPT
        for k, (s, e, vs, ve) in enumerate(ph):
            chunk = a[int(s * SR): int(e * SR)]
            segs, _ = model.transcribe(chunk, language="en", beam_size=2, initial_prompt=(HINT + " " + prev)[-220:],
                                       without_timestamps=True, vad_filter=False, condition_on_previous_text=False)
            text = " ".join(x.text.strip() for x in segs).strip()
            rows.append({"i": k, "start": round(s, 2), "end": round(e, 2), "voice": [vs, ve], "text": text})
            print(f"{name} #{k:03d} [{s:7.2f}-{e:7.2f}] {text}", flush=True)
            if text:
                prev = text
        json.dump(rows, open(os.path.join(OUT, name + ".json"), "w"), ensure_ascii=False, indent=1)
        open(os.path.join(OUT, name + ".txt"), "w").write(
            "\n".join(f"#{r['i']:03d} [{r['start']:7.2f}-{r['end']:7.2f}] {r['text']}" for r in rows) + "\n")


if __name__ == "__main__":
    main()

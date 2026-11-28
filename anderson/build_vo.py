#!/usr/bin/env python3
"""Assemble the clean voiceover from the raw takes: best take per line, fumbles and retakes cut out.

    python3 build_vo.py           ->  out/vo_clean.wav (48 kHz mono) + out/vo_timeline.json
    python3 build_vo.py --check   ->  also re-transcribe every piece cut mid-phrase (sanity check)

EDL entries: (beat_id, take, start, end, pause_after). `start`/`end` may be ("gap", t0, t1): the cut lands
on the quietest 30 ms inside that window, i.e. the breath between two words. Every join gets 12 ms fades.
Takes: A = first session (opening -> "say no"), B = second session (rest). Last clean take wins.
"""
import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000
TAKES = {"A": "take_en"}
S, M, PARA, CH = 0.03, 0.08, 0.22, 0.35   # reel pace   # pause after: same sentence, next sentence, new paragraph (fast pace)
G = "gap"

EDL = [   # one AI-voice read of the English script; the spoken stage note about Surrey is cut out
    ("hook_a", "A", 0.0, 7.45, M),
    ("hook_b", "A", 7.58, 13.43, PARA),
    ("tests_188", "A", 13.56, 18.53, M),
    ("tests_40k", "A", 18.73, 24.25, M),
    ("tests_704", "A", 24.48, 28.38, PARA),
    ("ctr_tests", "A", 28.54, 30.12, S),
    ("ctr_odi", "A", 30.15, (G, 33.60, 34.40), S),
    ("ctr_fc", "A", (G, 33.60, 34.40), 38.37, S),
    ("ctr_dom", "A", 38.67, 42.32, PARA),
    ("total", "A", 42.43, 47.82, M),
    ("action", "A", 48.08, 56.12, PARA),
    ("follow", "A", 56.22, 60.70, PARA),
    ("twist_2024", "A", 60.76, 68.17, M),
    ("lancs", "A", 68.21, 76.07, M),
    ("nocontract", "A", 76.24, 82.27, PARA),
    ("stop", "A", 82.31, 84.31, S),          # "Did Jimmy stop? Absolutely not."
    ("surrey", "A", 88.90, 91.49, M),        # "Now he's in talks with Surrey for 2027." (swap: 84.39-86.12 "In 2027, it's Surrey.")
    ("age", "A", 91.76, 94.08, S),
    ("wkts", "A", 94.26, 100.76, PARA),
    ("end_a", "A", 100.84, 106.46, M),
    ("end_b", "A", 106.66, 109.84, 0.0),
]

def load(take):
    path = os.path.join(HERE, "vo_raw", TAKES[take] + ".m4a")
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(pcm, np.int16).astype(np.float32) / 32768


def quietest(a, t0, t1, win=0.03):
    s, e = int(t0 * SR), int(t1 * SR)
    w = int(win * SR)
    seg = a[s:e]
    n = (len(seg) - w) // (w // 3)
    best, bt = 1e9, t0
    for k in range(n):
        i = k * (w // 3)
        r = float(np.mean(seg[i:i + w] ** 2))
        if r < best:
            best, bt = r, t0 + (i + w / 2) / SR
    return bt


def squeeze(seg, max_gap=0.40, keep=0.26):
    """Shorten any pause inside a piece longer than max_gap to `keep` seconds (crossfaded), so lines flow."""
    hop = SR // 100
    n = len(seg) // hop
    if n < 10:
        return seg
    db = 20 * np.log10(np.sqrt(np.mean(seg[: n * hop].reshape(n, hop) ** 2, axis=1)) + 1e-9)
    quiet = db < max(np.percentile(db, 10) + 12, np.percentile(db, 70) - 26)
    out, i, last = [], 0, 0
    while i < n:
        if quiet[i]:
            j = i
            while j < n and quiet[j]:
                j += 1
            if (j - i) / 100 > max_gap and i > 0 and j < n:      # interior pause only
                cut0 = (i * hop) + int(keep / 2 * SR)
                cut1 = (j * hop) - int(keep / 2 * SR)
                out.append(seg[last:cut0])
                last = cut1
            i = j
        else:
            i += 1
    out.append(seg[last:])
    if len(out) == 1:
        return seg
    f = int(0.01 * SR)
    res = out[0]
    for p in out[1:]:
        if len(res) > f and len(p) > f:
            x = np.linspace(0, 1, f, dtype=np.float32)
            res = np.concatenate([res[:-f], res[-f:] * (1 - x) + p[:f] * x, p[f:]])
        else:
            res = np.concatenate([res, p])
    return res


def resolve(a, t):
    return quietest(a, t[1], t[2]) if isinstance(t, tuple) else t


def main():
    audio = {k: load(k) for k in TAKES}
    fade = int(0.012 * SR)
    out, timeline, t = [], [], 0.0
    pieces = []
    for bid, take, s, e, pause in EDL:
        a = audio[take]
        s2, e2 = resolve(a, s), resolve(a, e)
        seg = squeeze(a[int(s2 * SR): int(e2 * SR)].copy())
        ramp = np.linspace(0, 1, fade, dtype=np.float32)
        seg[:fade] *= ramp
        seg[-fade:] *= ramp[::-1]
        out.append(seg)
        dur = len(seg) / SR
        timeline.append({"id": bid, "start": round(t, 3), "end": round(t + dur, 3), "take": take,
                         "src": [round(s2, 3), round(e2, 3)]})
        pieces.append((bid, seg, isinstance(s, tuple) or isinstance(e, tuple)))
        t += dur
        if pause:
            out.append(np.zeros(int(pause * SR), np.float32))
            t += pause
    vo = np.concatenate(out)
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    raw = os.path.join(HERE, "out", "vo_raw_concat.wav")
    import wave
    with wave.open(raw, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(vo, -1, 1) * 32767).astype(np.int16).tobytes())
    # voice chain: rumble cut, gentle presence, steady compression, broadcast loudness
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af",
                    "highpass=f=75,lowpass=f=15000,equalizer=f=3200:t=q:w=1.2:g=2.5,equalizer=f=250:t=q:w=1:g=-2,"
                    "acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=3,"
                    "loudnorm=I=-16:TP=-1.5:LRA=7", "-ar", str(SR), "-ac", "1",
                    os.path.join(HERE, "out", "vo_clean.wav")], check=True)
    json.dump({"duration": round(t, 3), "beats": timeline}, open(os.path.join(HERE, "out", "vo_timeline.json"), "w"),
              indent=1)
    print(f"VO {t:.1f}s, {len(EDL)} pieces")
    # the reel engine reads out/beats.json + out/vo_reel.wav (picture starts LEAD seconds before the voice)
    lead, tempo = 0.25, 1.15            # 15% faster read for reel pace (pitch kept)
    beats = {"lines": {b["id"]: [round(b["start"] / tempo + lead, 3), round(b["end"] / tempo + lead, 3)] for b in timeline},
             "vo_end": round(t / tempo + lead, 3), "no_vo": []}
    json.dump(beats, open(os.path.join(HERE, "out", "beats.json"), "w"), indent=1)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(HERE, "out", "vo_clean.wav"), "-af", f"atempo={tempo},adelay={int(lead * 1000)}",
                    "-ar", "44100", "-ac", "1", os.path.join(HERE, "out", "vo_reel.wav")], check=True)

    if "--check" in sys.argv:
        from faster_whisper import WhisperModel
        m = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=4)
        for bid, seg, cut in pieces:
            if not cut:
                continue
            x = seg[::3]  # 48k -> 16k
            r, _ = m.transcribe(x, language="en", beam_size=2, without_timestamps=True,
                                initial_prompt="Hinglish, Roman script: Karun Nair, 303, Vidarbha.")
            print(bid, "->", " ".join(z.text.strip() for z in r))


if __name__ == "__main__":
    main()

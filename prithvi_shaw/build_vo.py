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
TAKES = {"A": "take_261124_171317", "B": "take_261124_173038"}
S, M, PARA, CH = 0.04, 0.10, 0.30, 1.2   # CH: cinematic pause before a chapter title   # pause after: same sentence, next sentence, new paragraph (fast pace)
G = "gap"

EDL = [
    # --- OPENING
    ("o_546", "A", 1.94, 8.15, M),
    ("o_superstar", "A", 8.41, 16.00, M),
    ("o_fewyears", "A", 16.27, 18.56, S),
    ("o_door", "A", 18.70, 23.35, M),
    ("o_status", "A", 23.63, 27.94, M),
    ("o_what", "A", 28.40, 30.71, 2.0),
    # --- CH1 THE PRODIGY
    ("c1_nov2013", "A", 31.42, 34.83, M),
    ("c1_boy", "A", 35.15, 41.17, M),
    ("c1_546", "A", 41.42, 46.07, M),
    ("c1_confidence", "A", 46.43, 48.85, S),
    ("c1_frontfoot", "A", 50.05, 55.73, M),
    ("c1_talent", "A", 60.27, 64.13, M),           # 3rd and complete take
    ("c1_u19", "A", 64.16, 69.15, M),
    ("c1_gill", "A", 70.48, 73.03, M),
    ("c1_expect", "A", 76.12, 79.15, M),            # retake of "Dono young stars the…"
    ("c1_before_gill", "A", 79.42, 85.81, M),
    ("c1_makes", "A", 86.12, 88.57, S),
    ("c1_134", "A", 88.87, 92.30, M),
    ("c1_youngest", "A", 92.63, 97.06, M),
    ("c1_dominate", "A", 97.24, 102.65, M),
    ("c1_nextsachin", "A", 102.87, 106.45, M),
    ("c1_staying", "A", 106.85, 113.04, M),
    ("c1_setback", "A", 113.67, 117.82, CH),
    # --- CH2 THE INJURY
    ("c2_nov2018", "A", 119.80, 126.68, M),
    ("c2_ankle", "A", 127.03, 133.92, M),
    ("c2_history", "A", 134.23, 140.39, M),
    ("c2_timing", "A", 142.95, 155.65, M),
    ("c2_momentum", "A", 156.03, 160.57, CH),
    # --- CH3 THE SUSPENSION
    ("c3_july", "A", 163.84, (G, 164.6, 165.7), S),
    ("c3_bcci", "A", 185.54, 189.32, S),            # cleanest "BCCI ne announce kiya…" take
    ("c3_terbutaline", "A", 175.30, 179.60, M),     # the one complete "terbutaline" line
    ("c3_cough", "A", 196.66, 202.69, M),
    ("c3_backdated", "A", 208.95, 219.86, M),
    ("c3_stage", "A", 219.97, 227.11, M),
    ("c3_u19mates", "A", 232.40, 236.56, S),        # retake
    ("c3_gill", "A", 236.74, 237.95, M),
    ("c3_journeys", "A", 240.26, 249.66, M),
    ("c3_dec2020", "A", 249.81, 251.96, S),
    ("c3_direction", "A", 256.41, 259.70, CH),    # retake of "Woh match jisne…"
    # --- CH4 ADELAIDE
    ("c4_adelaide", "A", 260.78, 265.05, M),
    ("c4_xi", "A", 265.59, (G, 267.30, 267.47), S),
    ("c4_confidence", "A", 275.45, 280.75, M),      # retake of the confidence line (mumble before it cut)
    ("c4_scores", "A", 280.95, 283.46, M),
    ("c4_36", "A", (G, 285.49, 285.69), 293.55, M),   # second "Dono innings…" only
    ("c4_lowest", "A", 294.44, 297.07, M),
    ("c4_changes", "A", 297.13, 299.90, S),
    ("c4_never", "A", 304.80, 308.60, M),
    ("c4_socho", "A", 317.52, 318.27, S),           # last take of the "Socho…" block
    ("c4_134", "A", 318.52, 324.06, S),
    ("c4_career", "A", 324.18, 325.64, S),
    ("c4_stopped", "A", 326.27, 328.50, M),
    ("c4_notover", "A", 329.00, 336.44, PARA),
    ("mid_sub", "B", 242.80, (G, 247.5, 247.8), CH),  # CTA moved here from the end (cliffhanger)
    # --- CH5 THE COMEBACKS
    ("c5_vht", "A", 337.23, 342.76, M),
    ("c5_827", "A", 343.00, 344.86, M),
    ("c5_227", "A", 345.13, 348.88, M),
    ("c5_title", "A", 354.32, (G, 358.5, 359.3), S),  # retake, minus the stray "Prithvi"
    ("c5_notfinished", "A", 360.28, 361.84, M),
    ("c5_northants", "A", 377.14, 385.73, M),
    ("c5_remember", "A", 385.99, 388.38, M),
    ("c5_unstoppable", "A", 399.21, 405.485, S),    # 4th clean take, minus the false start "Lekin wo ek…"
    ("c5_convert", "A", 407.15, 412.07, M),
    ("c5_controversy", "A", 412.91, 416.62, CH),
    # --- CH6 THE CONTROVERSY
    ("c6_feb2023", "A", 416.88, 421.105, S),        # stop before "Wahaan kuch log" (retaken next)
    ("c6_selfies", "A", 423.45, 426.52, M),
    ("c6_refused", "A", 426.65, 432.99, M),
    ("c6_argument", "A", 433.13, 436.87, M),
    ("c6_notover", "A", 437.10, 438.95, M),
    ("c6_attack", "A", 448.76, 459.60, M),          # the clean retake of the police-complaint line
    ("c6_arrest", "A", 463.58, 470.32, M),
    ("c6_june", "A", 470.67, 476.50, M),
    ("c6_cctv", "A", (G, 479.6, 479.85), 488.99, M),   # retake of the CCTV line only
    ("c6_sayno", "B", 2.40, 7.50, M),               # session 2 restarts on "He had every right to say no"
    ("c6_struggle", "B", 14.93, 19.12, S),
    ("c6_distraction", "B", 19.39, 27.65, CH),
    # --- CH7 THE FALL
    ("c7_oct2024", "B", 28.85, 33.66, M),
    ("c7_break", "B", 33.73, 39.27, M),
    ("c7_auction", "B", 39.53, 47.28, M),
    ("c7_nobody", "B", 48.54, 50.17, M),
    ("c7_mca", "B", 50.56, 58.89, M),
    ("c7_10fielders", "B", 61.06, 65.78, M),
    ("c7_harsh", "B", 67.69, 69.54, M),
    ("c7_enough", "B", 69.69, 74.15, M),
    ("c7_modern", "B", 76.94, 85.23, M),
    ("c7_halffacts", "B", 85.60, 87.76, M),
    ("c7_performance", "B", 87.94, 96.62, M),
    ("c7_over", "B", 97.50, 99.64, CH),
    # --- CH8 THE ROAD BACK
    ("c8_maharashtra", "B", 100.27, 109.42, M),
    ("c8_simple", "B", 110.24, 116.55, M),
    ("c8_national", "B", 116.77, 118.80, S),
    ("c8_runs", "B", 126.24, 129.95, M),           # "…kaafi nahi hoti" (the correct take)
    ("c8_fitness", "B", 129.98, 137.27, M),
    ("c8_dream", "B", 142.22, 148.81, CH),
    # --- FINAL
    ("f_what", "B", 149.86, 151.95, M),
    ("f_questions", "B", 151.97, 159.11, M),
    ("f_fitness", "B", 162.41, 167.67, M),
    ("f_failure", "B", 167.72, 174.99, M),
    ("f_control", "B", 175.23, 177.39, S),
    ("f_missed", "B", 180.74, 183.20, S),
    ("f_expect", "B", 186.92, 190.46, M),
    ("f_at18", "B", 193.70, 202.04, M),
    ("f_talent", "B", 202.98, 210.09, M),
    ("f_door", "B", 210.66, 214.48, M),
    ("f_young", "B", 214.56, 217.49, M),
    ("f_sawaal", "B", 217.70, 223.26, S),
    ("f_history", "B", (G, 226.9, 227.3), 231.47, S),
    ("f_superstar", "B", 231.53, 235.68, PARA),
    ("f_think", "B", (G, 237.52, 237.62), 240.86, M),  # second take only
    ("f_comment", "B", 241.12, 242.555, M),
    ("f_story", "B", (G, 247.5, 247.8), 251.13, 0.0),
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

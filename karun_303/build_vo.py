#!/usr/bin/env python3
"""Assemble the clean voiceover from the raw takes: best take per line, fumbles and retakes cut out.

    python3 build_vo.py           ->  out/vo_clean.wav (48 kHz mono) + out/vo_timeline.json
    python3 build_vo.py --check   ->  also re-transcribe every piece cut mid-phrase (sanity check)

EDL entries: (beat_id, take, start, end, pause_after). `start`/`end` may be ("gap", t0, t1): the cut lands
on the quietest 30 ms inside that window, i.e. the breath between two words. Every join gets 12 ms fades.
Takes: L = the long session take, P1..P4 = the later pickups (they replace the fluffed lines in L).
"""
import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000
TAKES = {
    "L": "take_261116_120557", "P1": "take_261116_142215", "P2": "take_261116_145200",
    "P3": "take_261116_145224", "P4": "take_261116_145313",
}
S, M, PARA = 0.06, 0.16, 0.42   # pause after: same sentence, next sentence, new paragraph (fast pace)
G = "gap"

EDL = [
    # --- cold open
    ("open_300", "L", 10.30, 18.70, M),
    ("open_3tests", "L", 19.30, 23.50, M),
    ("open_381", "L", 23.90, 31.10, M),
    ("open_channel", "L", 31.40, 37.80, M),
    ("open_last", "L", 38.50, 46.00, PARA),
    ("num_303", "L", 46.50, 50.50, M),
    ("anyaay", "L", 50.90, 55.70, M),
    ("not_whole", "L", 56.20, 60.10, M),
    ("saza", "L", 60.30, 63.80, M),
    ("came_back", "L", 64.40, 68.50, PARA),
    # --- the river
    ("river", "L", 69.00, 75.20, M),
    ("boat", "L", 87.30, 94.20, M),
    ("on_boat", "L", 94.60, 99.90, M),
    ("saved", "L", 100.40, 104.10, S),
    ("chennai_fate", "L", 113.70, 117.50, PARA),
    # --- debut + 303
    ("debut", "L", 117.70, 120.80, S),
    ("mohali", "L", 121.60, 124.00, M),
    ("slow", "L", 124.10, 126.50, M),
    ("december", "L", 126.60, 128.40, S),
    ("fifth_test", "L", 128.50, 132.70, M),
    ("cook_drop", "L", 132.80, 136.50, M),
    ("changed", "L", 136.60, 141.10, M),
    ("rahul", "L", 141.80, 147.60, M),
    ("root_drop", "L", 147.70, 152.10, M),
    ("rashid_four", "L", 158.70, 162.10, M),
    ("stats_303", "L", 162.80, 167.40, M),
    ("declare", "P1", 1.30, 7.10, M),
    ("won", "L", 179.10, 183.60, M),
    ("sehwag", "L", 184.50, 190.30, M),
    ("second", "L", 190.60, 193.90, M),
    ("sobers", "L", 194.70, 202.90, M),
    ("avg160", "L", 204.00, 207.50, M),
    ("pressure_q", "P2", 2.40, 6.51, S),
    ("maut", "P2", 6.63, 11.34, M),
    ("nadi_free", "P2", 11.78, 17.83, PARA),
    # --- the benchmark
    ("judged", "L", 208.20, 220.20, M),
    ("before_after", "L", 220.40, 227.30, M),
    ("young_expect", "L", 227.60, 230.10, S),
    ("prove_expect", "L", 230.40, 235.40, M),
    ("two_q", "L", 235.50, 241.30, M),
    ("benchmark", "L", 242.70, 246.80, S),
    ("touch", "L", 250.20, 253.10, PARA),
    ("rukiye", "L", 253.40, 255.00, S),
    ("boss_a", "L", 255.10, 258.67, S),
    ("boss_b", "L", 261.60, 266.70, PARA),
    # --- dropped
    ("hyderabad", "L", 266.90, 271.40, M),
    ("not_in_xi", "L", 272.40, 277.20, M),
    ("rahane_back", "L", 277.60, 284.30, M),
    ("hutton", "L", 284.60, 288.80, S),
    ("inzamam", "L", 291.60, 294.80, M),
    ("fit_out", "L", 295.30, 298.02, M),
    ("rahane_ok", "L", 302.50, 306.50, M),
    ("senior", "L", 306.60, 310.80, M),
    ("father", "L", 314.80, 319.50, M),
    ("karun_said", "L", 320.40, 326.00, M),
    ("no_villain", "L", 326.30, 330.38, S),
    ("no_worse", "L", 335.87, 341.30, S),
    ("time", "L", 341.80, 346.50, PARA),
    # --- Australia
    ("australia", "L", 347.30, 356.10, M),
    ("winning", "L", 356.60, 362.90, M),
    ("first_q", "L", 363.80, 370.00, M),
    ("attention", "L", 370.60, 374.00, M),
    ("measured", "L", 374.50, 379.20, M),
    ("four_inn", "L", 379.90, 384.78, S),
    ("form", "L", 384.65, 387.92, S),
    ("saboot", "L", 390.04, 391.30, M),
    ("dharamsala", "L", 391.30, 397.20, PARA),
    ("not_end", "L", 397.30, 402.40, S),
    ("stranger", "L", 406.20, 410.90, PARA),
    # --- 2018 England tour
    ("eng2018", "L", 413.50, 417.90, M),
    ("whole_tour", "L", 418.70, 422.80, M),
    ("vihari", "L", 423.00, 429.60, M),
    ("wi_squad", "L", 430.10, 438.90, M),
    ("no_talk", "L", 439.00, 441.80, S),
    ("no_answer", "L", 441.90, (G, 444.0, 446.6), M),
    ("msk", "L", 455.11, 459.60, M),
    ("truth_who", "L", 459.81, 462.80, M),
    ("avg62", "L", 477.42, (G, 484.0, 486.2), S),
    ("squad_name", "L", 487.37, 491.58, PARA),
    # --- the wall
    ("consistency", "L", 493.00, 499.80, M),
    ("wall", "L", 499.90, 507.90, M),
    ("no_runs", "L", 521.30, 524.60, M),
    ("dec2022", "L", 525.10, 530.00, S),
    ("dear_cricket", "L", 530.10, 533.10, M),
    ("sochiye_ask", "L", 533.40, 535.83, S),
    ("ask_chance", "L", 536.31, 538.16, M),
    ("county", "L", 541.90, 544.60, M),
    ("surrey", "L", 545.20, 552.70, M),
    ("crack", "L", 553.00, 559.66, M),
    ("vidarbha", "L", 561.10, 564.00, M),
    ("year1", "L", 564.70, 572.50, M),
    ("vht", "L", 580.80, 585.10, M),
    ("record", "L", 585.54, 588.45, M),
    ("ranji_final", "L", 593.33, (G, 599.0, 600.8), PARA),
    # --- IPL pickup
    ("ipl_door", "P3", 1.00, 3.10, S),
    ("ipl_1077", "P3", 3.26, 9.18, M),
    ("bumrah", "P3", 9.43, 13.22, M),
    ("ipl_89", "P3", 19.07, 24.14, M),
    ("bumrah_record", "P3", 24.36, 28.87, M),
    ("dc_lost", "P3", 29.58, 36.65, M),
    ("ind_score", "P3", 37.18, 41.29, S),
    ("no_value", "P3", 41.58, 44.86, M),
    ("lions_204", "L", (G, 599.0, 600.8), 605.07, PARA),
    # --- 2025 England
    ("headingley", "L", 608.20, 610.40, S),
    ("cap_3006", "L", 610.50, 614.20, M),
    ("country_said", "L", 620.30, 622.80, M),
    ("duck", "L", 623.00, 628.80, M),
    ("edgbaston", "L", 632.00, 635.90, M),
    ("same_q", "L", 636.00, 640.00, M),
    ("oval57", "L", 640.10, 645.60, M),
    ("nine_years", "L", 646.20, 648.80, M),
    ("dk", "L", 649.30, 653.30, M),
    ("lbw", "L", 653.40, 659.40, M),
    ("avg25", "L", 659.80, 669.20, M),
    ("prove", "L", 669.60, 676.70, S),
    ("one_day", "L", 677.40, 680.00, PARA),
    ("wi_2025", "L", 680.60, 685.40, M),
    ("agarkar", "L", 685.80, 689.70, M),
    ("zyada", "L", 690.10, 692.10, M),
    ("haqdaar", "L", 692.30, 696.60, M),
    ("back_karnataka", "L", 696.90, 701.39, M),
    ("same_cycle", "L", 702.12, 704.97, S),
    ("measured_303", "L", 715.59, 720.93, PARA),
    # --- the truth
    ("villains", "L", 721.60, 726.50, M),
    ("subscribe", "L", 726.70, 732.70, PARA),
    ("truth", "L", 758.15, 763.55, M),
    ("own_innings", "L", 763.70, 767.40, M),
    ("number", "L", 768.10, 774.60, M),
    ("bojh", "P4", 2.05, 8.54, S),
    ("never_far", "P4", 13.72, 17.16, M),
    ("sahi", "P4", 24.59, 27.22, S),
    ("humara", "P4", 27.40, 30.30, PARA),
    ("kadvi", "L", 774.90, 776.40, S),
    ("trapped", "L", 776.80, 783.60, S),
    ("character", "L", 783.80, 789.70, S),
    ("one_thing", "L", 789.80, 796.10, M),
    ("no_score", "L", 797.00, 805.41, PARA),
    ("aap_bataiye", "L", 806.19, 813.42, M),
    ("comment", "L", 813.49, 818.30, 0.0),
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
        seg = a[int(s2 * SR): int(e2 * SR)].copy()
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

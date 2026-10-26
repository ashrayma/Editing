#!/usr/bin/env python3
"""Cut the three raw takes into one clean narration: best takes only, fumbles and retakes removed.

    python3 build_vo.py      ->  out/vo_final.wav  +  out/vo_timeline.json  (start/end of every beat)

Each beat is a list of (take, start, end) pieces cut from the raw recordings (seconds). Pieces inside a
beat are joined with a short breath; beats are separated by a slightly longer pause.
"""
import json
import os
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "kohli_countdown"))
from voiceover import SR, clean_recording, voiced_regions  # noqa: E402  (same cleanup chain as the reels)

TAKES = {"A": "vo_raw/a_174854.m4a", "B": "vo_raw/b_175945.m4a", "C": "vo_raw/c_180625.m4a"}

# (beat id, [(take, start, end), ...])  -- in story order
BEATS = [
    ("hook_fastest",   [("A", 1.40, 9.45)]),
    ("hook_first_ball", [("A", 9.80, 15.95)]),
    ("hook_six",       [("A", 16.85, 23.65)]),
    ("not_one_shot",   [("A", 24.10, 32.55)]),
    ("cramps_98",      [("A", 33.80, 43.90)]),
    ("kargil",         [("A", 45.10, 54.55)]),
    ("parliament",     [("A", 55.05, 64.60)]),
    ("no_cricket",     [("A", 65.20, 68.70), ("A", 75.25, 79.80)]),
    ("not_just_match", [("A", 79.95, 81.90)]),
    ("months_talk",    [("A", 86.75, 93.65)]),
    ("phone_calls",    [("A", 93.95, 104.60)]),
    ("toss_ties",      [("A", 105.65, 117.80)]),
    ("match_starts",   [("A", 118.65, 124.00)]),
    ("saeed_anwar",    [("A", 137.05, 145.15)]),
    ("saeed_101",      [("A", 145.60, 150.45)]),
    ("target_274",     [("A", 156.30, 163.35)]),
    ("bowling_attack", [("A", 164.15, 176.65)]),
    ("sachin_plan",    [("A", 177.50, 179.60), ("A", 189.45, 194.90)]),
    ("wasim_over",     [("B", 3.65, 10.40)]),
    ("shoaib_runup",   [("B", 10.80, 18.98)]),
    ("the_six",        [("B", 30.55, 39.55)]),
    ("two_fours",      [("B", 40.75, 48.10)]),
    ("three_balls",    [("B", 55.55, 61.85)]),
    ("eighteen",       [("B", 62.95, 64.55)]),
    ("that_feeling",   [("B", 65.85, 71.30)]),
    ("sehwag_53",      [("B", 72.10, 81.10)]),
    ("two_wickets",    [("B", 82.10, 90.25)]),
    ("53_for_2",       [("B", 90.55, 95.00)]),
    ("if_sachin_out",  [("B", 95.35, 99.60)]),
    ("kaif",           [("B", 100.40, 107.25)]),
    ("partnership",    [("B", 107.80, 113.40)]),
    ("kaif_out",       [("B", 114.20, 119.45)]),
    ("cramps",         [("B", 119.95, 127.25)]),
    ("runner",         [("B", 134.25, 138.45)]),
    ("nineties",       [("B", 139.05, 148.95)]),
    ("bouncer",        [("B", 152.35, 169.45)]),
    ("out_98",         [("B", 174.10, 179.40), ("B", 182.90, 184.90)]),
    ("97_needed",      [("B", 185.65, 197.05)]),
    ("dravid_yuvraj",  [("B", 197.25, 201.35)]),
    ("finish",         [("B", 202.10, 206.60), ("B", 213.85, 218.10)]),
    ("won",            [("C", 8.95, 15.25)]),
    ("aftermath",      [("B", 248.45, 276.10)]),
    ("two_points",     [("C", 15.15, 18.15)]),
    ("belief",         [("C", 18.38, 28.60)]),
    ("pride",          [("C", 28.80, 35.78)]),
    ("crores",         [("C", 37.95, 45.45)]),
    ("hearts",         [("C", 47.30, 50.70), ("C", 51.78, 53.95), ("C", 55.30, 58.30)]),
    ("cta",            [("B", 276.15, 281.05), ("B", 287.05, 297.05)]),
]

PIECE_GAP, BEAT_GAP = 0.22, 0.42
SECTION_GAPS = {"kargil": 0.9, "saeed_anwar": 0.8, "wasim_over": 0.8, "bouncer": 0.9, "won": 0.8,
                "two_points": 1.0, "cta": 0.9}  # longer breaths where the story turns


def main():
    out_dir = os.path.join(HERE, "out")
    os.makedirs(out_dir, exist_ok=True)
    track, timeline, t = [], [], 0.0
    for bid, pieces in BEATS:
        gap = SECTION_GAPS.get(bid, BEAT_GAP) if track else 0.0
        if gap:
            track.append(np.zeros(int(gap * SR), np.float32))
            t += gap
        start = t
        for k, (take, a, b) in enumerate(pieces):
            clip = clean_recording(os.path.join(HERE, TAKES[take]), (a, b)).copy()
            f = min(int(0.015 * SR), len(clip) // 2)
            clip[:f] *= np.linspace(0, 1, f)
            clip[len(clip) - f:] *= np.linspace(1, 0, f)
            if k:
                track.append(np.zeros(int(PIECE_GAP * SR), np.float32))
                t += PIECE_GAP
            track.append(clip)
            t += len(clip) / SR
        timeline.append({"id": bid, "start": round(start, 3), "end": round(t, 3)})
    audio = np.concatenate(track)
    audio = audio / max(1e-6, np.abs(audio).max()) * 0.9
    with wave.open(os.path.join(out_dir, "vo_final.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((audio * 32767).astype(np.int16).tobytes())
    with open(os.path.join(out_dir, "vo_timeline.json"), "w") as f:
        json.dump({"duration": round(t, 3), "beats": timeline,
                   "voiced": [(round(a, 2), round(b, 2)) for a, b in voiced_regions(audio)]}, f, indent=1)
    print(f"{len(timeline)} beats, {t:.1f}s ({t / 60:.1f} min)")


if __name__ == "__main__":
    main()

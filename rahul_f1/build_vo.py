#!/usr/bin/env python3
"""out/vo_full.wav = cleaned voice with Rahul's own press-conference words inserted after the Red Bull line,
and out/beats.json = line times on that timeline (from the word-level transcript of the cleaned voice)."""
import json
import os
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 44100
INS_AT, PAD = 35.62, 0.3          # in the cleaned voice: after "...train karte hain." (35.45), before "Ek F1 car" (35.9)
# line times in the cleaned voice (vo/words.json)
CLEAN = {"hook": (0.0, 6.9), "well": (7.9, 11.9), "leave": (12.0, 17.4), "tired": (18.0, 19.5), "score": (19.6, 21.2),
         "first": (21.3, 23.3), "sena": (23.4, 26.6), "twist": (26.8, 29.1), "redbull": (29.7, 35.45),
         "f1car": (35.9, 39.0), "r100": (39.1, 41.9), "because": (42.0, 48.95), "follow": (49.0, 52.2),
         "lesson": (52.7, 57.5), "ask": (57.8, 62.2)}


def read(p):
    with wave.open(p) as w:
        assert w.getframerate() == SR
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768


vo = read(os.path.join(HERE, "out", "vo_reel.wav"))
clip = read(os.path.join(HERE, "assets", "interview_audio.wav"))
clip = clip / (np.abs(clip).max() + 1e-9) * np.abs(vo).max() * 0.92
f = int(0.02 * SR)
clip[:f] *= np.linspace(0, 1, f)
clip[-f:] *= np.linspace(1, 0, f)
k = int(INS_AT * SR)
pad = np.zeros(int(PAD * SR), np.float32)
full = np.concatenate([vo[:k], pad, clip, pad, vo[k:]])
shift = len(clip) / SR + 2 * PAD
with wave.open(os.path.join(HERE, "out", "vo_full.wav"), "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((np.clip(full, -1, 1) * 32767).astype(np.int16).tobytes())
lines = {}
for kk, (a, b) in CLEAN.items():
    if a > INS_AT:
        a, b = a + shift, b + shift
    lines[kk] = [round(a, 2), round(b, 2)]
    if kk == "redbull":
        lines["clip"] = [round(INS_AT + PAD, 2), round(INS_AT + PAD + len(clip) / SR, 2)]
json.dump({"lines": lines, "vo_end": round(len(full) / SR, 2), "no_vo": ["clip"]}, open(os.path.join(HERE, "out", "beats.json"), "w"), indent=1)
print("vo_full", round(len(full) / SR, 2), "s; clip", lines["clip"])

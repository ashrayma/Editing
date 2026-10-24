#!/usr/bin/env python3
"""Your raw voice take -> a clean, tight voiceover: keeps the ranges listed in vo_edit.json
(dropping false starts and dead air), joins them with a short breath and 12 ms fades so
the cuts don't click, then cleans the voice: rumble filter, gentle noise reduction,
presence EQ, compression, loudness to -16 LUFS.

usage: python3 tools/clean_vo.py <raw_take> [vo_edit.json] -> film/assets/audio/voice_clean.wav
then:  python3 tools/timing_from_recording.py film/assets/audio/voice_clean.wav
"""
import json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
raw = sys.argv[1]
edit = json.load(open(sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "vo_edit.json")))
out = os.path.join(ROOT, "film/assets/audio/voice_clean.wav")
breath = edit.get("join_gap", 0.22)

parts, labels = [], []
for i, (a, b) in enumerate(edit["keep"]):
    d = b - a
    parts.append(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={d - 0.012:.3f}:d=0.012[k{i}]")
    labels.append(f"[k{i}]")
    if i + 1 < len(edit["keep"]):
        parts.append(f"anullsrc=r=48000:cl=mono,atrim=0:{breath}[g{i}]")
        labels.append(f"[g{i}]")
chain = ("highpass=f=85,afftdn=nr=10:nf=-50,"
         "equalizer=f=200:t=q:w=1.0:g=-2,equalizer=f=3500:t=q:w=1.2:g=2.5,"
         "acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=2,"
         "loudnorm=I=-16:TP=-1.5:LRA=7")
fc = ";".join(parts) + f";{''.join(labels)}concat=n={len(labels)}:v=0:a=1,{chain}[out]"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-filter_complex", fc, "-map", "[out]",
                "-ac", "1", "-ar", "48000", out], check=True)
print("wrote", out)

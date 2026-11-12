#!/usr/bin/env python3
"""Wicket clips from the user's extra footage, cropped to the 716x780 card shape.

footage/new/shoaib_destroys.mp4 (360x640 phone export, picture at y184) - Sachin c Younis b Shoaib, replay, walk-off.
footage/new/rec1-3.mp4 (2340x1080 YouTube screen recordings, picture x418-1922) - Sehwag, Ganguly, Kaif wickets.
The recordings' crop starts below the cricketWEB logo (top-right) and inside the player chrome.
"""
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
NEW = os.path.join(HERE, "footage", "new")
OUT = os.path.join(HERE, "footage", "clips")
ENC = ["-an", "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-pix_fmt", "yuv420p"]
PHONE = "crop=250:272:55:184,scale=716:780:flags=lanczos,unsharp=5:5:0.6,fps=30"
REC = "crop=935:1016:703:64,scale=716:780:flags=lanczos,fps=30"

CLIPS = [  # name, source, start, duration, crop, slow factor
    ("sachin_out_live",   "shoaib_destroys", 4.8, 5.2, PHONE, 1.0),   # the bouncer, gloved, Younis catches at point
    ("sachin_out_replay", "shoaib_destroys", 26.0, 3.3, PHONE, 1.0),  # replay: bouncer, fended off the gloves
    ("sachin_walk",       "shoaib_destroys", 16.8, 4.5, PHONE, 1.0),  # Sachin walks, Pakistan celebrate
    ("shoaib_celebrates", "shoaib_destroys", 33.0, 5.0, PHONE, 1.0),
    ("sachin_walk97",     "shoaib_destroys", 39.0, 5.4, PHONE, 1.0),  # walk-off, "need 97 more" strap
    ("sehwag_out",        "rec1", 30.3, 3.7, REC, 1.0),               # Waqar to Sehwag, caught
    ("waqar_celebrates",  "rec1", 23.0, 3.0, REC, 1.0),
    ("ganguly_out",       "rec2", 10.4, 6.2, REC, 1.0),               # first ball, lbw, umpire's finger
    ("kaif_out_afridi",   "rec3", 13.2, 5.4, REC, 1.0),               # Afridi bowls Kaif, 155/3
]

for name, src, start, dur, crop, slow in CLIPS:
    vf = crop + (f",setpts={slow}*PTS,minterpolate=fps=30:mi_mode=mci" if slow != 1.0 else "")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-t", str(dur), "-i", os.path.join(NEW, src + ".mp4"),
                    "-vf", vf] + ENC + [os.path.join(OUT, f"m_{name}.mp4")], check=True)
    print(name)

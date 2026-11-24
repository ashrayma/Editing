#!/usr/bin/env python3
"""Cut the source clips (footage/src/*.mp4) into one-use clips -> footage/clips/<name>.mp4 (1280x720).

Each clip is used once in the edit (no repeats). Times are seconds in the highlights video; an optional third
value slows the clip down (e.g. 1.9 = 1.9x longer) for moments that hold the screen longer.
    python3 cut_clips.py
"""
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "footage", "clips")
os.makedirs(OUT, exist_ok=True)

CLIPS = {   # name: (source, start, dur[, slow])  -- times read off half-second contact sheets
    # Adelaide 2020, 1st innings: Starc, second ball
    "starc_bowled":   ("adelaide_starc_0", 8.8, 3.0),
    "starc_roar":     ("adelaide_starc_0", 12.0, 2.4, 2.4),
    "starc_highfive": ("adelaide_starc_0", 14.5, 3.4),
    "starc_huddle":   ("adelaide_starc_0", 18.5, 3.0),
    "shaw_walks":     ("adelaide_starc_0", 27.4, 2.6, 1.85),
    "stumps_slowmo":  ("adelaide_starc_0", 30.6, 3.0, 1.3),
    # Adelaide 2020, 2nd innings: Cummins
    "cummins_bowled": ("adelaide_cummins_4", 0.6, 3.6),
    "cummins_cele":   ("adelaide_cummins_4", 4.2, 3.4),
    "cummins_wide":   ("adelaide_cummins_4", 14.2, 2.8),
    "cummins_roar":   ("adelaide_cummins_4", 17.0, 4.4),
    "ball_replay":    ("adelaide_cummins_4", 21.6, 2.0),
    "bat_stumps":     ("adelaide_cummins_4", 23.8, 2.0, 1.3),
    # Sydney warm-up, Nov 2018: the ankle
    "inj_chase":      ("injury_2018", 3.0, 3.0),
    "inj_fall":       ("injury_2018", 6.0, 3.0),
    "inj_lying":      ("injury_2018", 9.0, 3.0),
    "inj_physio":     ("injury_2018", 21.5, 3.6),
    "inj_replay":     ("injury_2018", 112.0, 4.0),
    "inj_helped":     ("injury_2018", 117.0, 4.5),
    "inj_carried":    ("injury_2018", 127.0, 5.0, 1.3),
    "inj_carried2":   ("injury_2018", 132.5, 4.0),
    "inj_stairs":     ("injury_2018", 148.0, 6.0),
}
# Shaw batting in Test whites (NZ 2020): generic "Shaw bats" pieces, never labelled as a specific match
for k, (a, d) in enumerate([(0.2, 7.0), (8.0, 6.0), (14.2, 5.6), (20.0, 6.0), (28.2, 3.8), (32.2, 3.8), (36.2, 5.6),
                            (44.2, 3.8), (48.2, 4.6), (52.2, 3.8), (56.2, 5.6), (62.2, 5.6), (68.2, 5.6), (74.2, 5.6),
                            (80.2, 7.0)]):
    CLIPS[f"nz_bat_{k:02d}"] = ("insta_clip", a, d)

for name, spec in CLIPS.items():
    src, ss, dur = spec[:3]
    SRC = os.path.join(HERE, "footage", "src", src + ".mp4")
    slow = spec[3] if len(spec) > 3 else 1.0   # >1 = slow motion (frame-blended), audio stretched to match
    dst = os.path.join(OUT, name + ".mp4")
    if os.path.exists(dst):
        continue
    vf = "scale=1280:720:flags=lanczos"
    af = "anull"
    if slow != 1.0:
        vf += f",setpts={slow}*PTS,minterpolate=fps=30:mi_mode=blend"
        r, chain = 1 / slow, []
        while r < 0.5:
            chain.append("atempo=0.5")
            r /= 0.5
        af = ",".join(chain + [f"atempo={r:.4f}"])
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(ss), "-t", str(dur), "-i", SRC,
                    "-vf", vf + ",fps=30", "-af", af,
                    "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", dst], check=True)
    print("cut", name)

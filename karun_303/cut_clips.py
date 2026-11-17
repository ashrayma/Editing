#!/usr/bin/env python3
"""Cut the 303 highlights (footage/hl_303.mp4, 640x360) into one-use clips -> footage/clips/<name>.mp4 (1280x720).

Each clip is used once in the edit (no repeats). Times are seconds in the highlights video; an optional third
value slows the clip down (e.g. 1.9 = 1.9x longer) for moments that hold the screen longer.
    python3 cut_clips.py
"""
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "footage", "hl_303.mp4")
OUT = os.path.join(HERE, "footage", "clips")
os.makedirs(OUT, exist_ok=True)

CLIPS = {
    "chepauk_aerial":   (0.3, 3.4),     # stadium flyover
    "profile_card":     (6.0, 5.0),     # broadcast card: Karun Nair, age 25, Test career
    "drive_early":      (13.6, 4.5),
    "cook_drop":        (27.3, 6.5),    # edge, Cook drops it at slip, lies on the turf (Karun 34)
    "cook_face":        (37.6, 2.4),
    "fifty":            (56.8, 5.0),
    "shot_a":           (48.5, 4.5),
    "shot_b":           (66.0, 5.0),
    "shot_c":           (110.0, 6.0),
    "hundred_shot":     (141.0, 8.0),
    "hundred_roar":     (151.0, 5.0),
    "hundred_wide":     (158.0, 4.6),
    "hundred_crowd":    (163.0, 3.2),
    "card_103":         (167.0, 2.4),
    "stokes_tired":     (175.5, 1.6, 1.35),
    "shot_d":           (200.0, 6.0),
    "card_150":         (240.0, 9.0),   # bat raised for 150 then the 150* off 240 card
    "two_hundred_shot": (283.0, 10.0),
    "two_hundred_helmet": (295.0, 3.6),
    "dressing_200":     (299.0, 1.6, 2.1),
    "crowd_200":        (303.0, 3.4),
    "ashwin_hug":       (307.0, 2.2),
    "root_drop":        (327.0, 10.0),  # Root drops him on 217
    "pull_close":       (357.0, 5.0),
    "shot_e":           (380.0, 6.0),
    "shot_f":           (420.0, 7.5),
    "three_hundred_four": (445.5, 7.0), # the Rashid four for 300
    "three_hundred_run":  (452.6, 6.4),
    "kohli_claps":      (459.9, 1.4, 1.9),
    "arms_up":          (461.0, 4.6, 1.1),
    "umesh_hug":        (467.0, 2.0, 1.2),
    "close_breath":     (469.0, 2.4, 1.15),
    "walk_off":         (472.0, 3.8),
}

for name, spec in CLIPS.items():
    ss, dur = spec[:2]
    slow = spec[2] if len(spec) > 2 else 1.0   # >1 = slow motion (frame-blended), audio stretched to match
    dst = os.path.join(OUT, name + ".mp4")
    if os.path.exists(dst):
        continue
    vf = "scale=1280:720:flags=lanczos,unsharp=5:5:0.6"
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

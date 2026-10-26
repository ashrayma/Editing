#!/usr/bin/env python3
"""The short-ball six off Shoaib (match_chase.mp4 0-13.5 s) as edit-ready clips.

m_six_ramp: live angle with a speed ramp on the upper-cut (0.33x around contact at ~0.95 s), so the short
ball and the bat-on-ball read clearly before the camera picks up the ball sailing over third man.
"""
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "footage", "match_chase.mp4")
OUT = os.path.join(HERE, "footage", "clips")
ENC = ["-an", "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-pix_fmt", "yuv420p"]


def run(args):
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + args, check=True)


def ramp(name="six_ramp", a=0.75, b=1.3, end=3.6, slow=3.0):
    fc = (f"[0:v]fps=30,split=3[x][y][z];"
          f"[x]trim=0:{a},setpts=PTS-STARTPTS[p1];"
          f"[y]trim={a}:{b},setpts={slow}*(PTS-STARTPTS),minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:vsbmc=1[p2];"
          f"[z]trim={b}:{end},setpts=PTS-STARTPTS[p3];"
          f"[p1][p2][p3]concat=n=3:v=1:a=0[v]")
    run(["-i", SRC, "-filter_complex", fc, "-map", "[v]"] + ENC + [os.path.join(OUT, f"m_{name}.mp4")])


def slow(name, start, dur, factor=2.0):
    vf = f"fps=30,setpts={factor}*PTS,minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:vsbmc=1"
    run(["-ss", str(start), "-t", str(dur), "-i", SRC, "-vf", vf] + ENC + [os.path.join(OUT, f"m_{name}.mp4")])


if __name__ == "__main__":
    ramp()
    slow("six_crowd_live", 3.7, 1.5)     # ball lands in the stands, flags go up
    slow("six_sideon", 5.45, 1.3)        # side-on replay of the upper-cut
    slow("six_crowd_jump", 8.95, 1.45)     # fans jumping
    run(["-ss", "11.0", "-i", SRC, "-t", "2.5", "-vf", "fps=30"] + ENC + [os.path.join(OUT, "m_six_pitch.mp4")])  # super-slow-mo: pitched short
    for f in ("six_ramp", "six_crowd_live", "six_sideon", "six_crowd_jump", "six_pitch"):
        d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                            os.path.join(OUT, f"m_{f}.mp4")], capture_output=True, text=True).stdout.strip()
        print(f, d)

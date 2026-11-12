#!/usr/bin/env python3
"""Edit-ready full-screen clips (1080x1920, 30 fps) from the user's Sehwag tribute download (incoming/viru.mp4).

The source is a 1076x1920 frame with the picture letterboxed in the middle. Every crop here keeps clear of
what the user asked to remove: the channel's "Cricket Buddy" / "@ict2000s" watermarks and broadcaster
scoreboards (all below y~1235), the SETANTA / channel bugs (top edge, above y~380) and the "BWC" logo on the
Ganguly interview (top right). Landscape match clips become full-screen with a blurred copy of the same
footage behind a large, softly feathered front picture. Ganguly's voice comes from a vocal-only stem
(incoming/talk_vocals.wav, background music removed with UVR-MDX-NET-Voc_FT).
"""
import os
import shutil
import subprocess

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "incoming", "viru.mp4")
OUT = os.path.join(HERE, "assets")
FRONT_TOP, FRONT_H = 270, 1200
HOLD = 7  # seconds of held last frame, so a scene never outlasts its clip
ENC = ["-an", "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p"]

# name, start, duration, speed (1 = real time)
MATCH = [
    ("c_cut_aus", 19.4, 0.9, 0.5),      # opening: square cut vs Australia, slowed
    ("c_big_hit", 26.7, 0.6, 0.6, 520),  # lofted hit (scoreboard cropped off)
    ("c_drive_nz", 27.8, 0.9, 0.6),     # drive vs New Zealand
    ("c_cut_aus2", 30.3, 0.7, 0.6, 520),
    ("c_shot_167", 31.4, 0.7, 0.6, 580),
    ("c_test_block", 32.6, 0.6, 0.5),   # compact defence (shown in grey as "survive")
    ("c_test_sweep", 35.0, 0.7, 0.4),   # Test whites
    ("c_celebrate", 40.1, 0.8, 0.5),    # helmet-off celebration with partner
]


def feather_mask(path):
    a = np.ones((FRONT_H, 1080), np.float32)
    ramp = int(FRONT_H * 0.12)
    a[:ramp] *= np.linspace(0, 1, ramp)[:, None]
    a[-ramp * 2:] *= np.linspace(1, 0, ramp * 2)[:, None]
    Image.fromarray((a * 255).astype(np.uint8), "L").save(path)


def match_clip(name, start, dur, speed, top=380):
    mask = os.path.join(HERE, "incoming", "feather.png")
    if not os.path.exists(mask):
        feather_mask(mask)
    pts = 1 / speed
    fc = (f"[0:v]crop=1076:{1220 - top}:0:{top},fps=30,setpts={pts}*PTS"
          + (",minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:vsbmc=1" if speed < 1 else "") + ",split[a][b];"
          f"[a]scale=-2:1920,crop=1080:1920,boxblur=30:3,eq=brightness=-0.18:saturation=1.2[bg];"
          f"[b]scale=-2:{FRONT_H},crop=1080:{FRONT_H}[fg0];[1:v]format=gray,scale=1080:{FRONT_H}[m];"
          f"[fg0][m]alphamerge[fg];[bg][fg]overlay=0:{FRONT_TOP}:format=auto,format=yuv420p,tpad=stop_mode=clone:stop_duration={HOLD}[v]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-t", str(dur), "-i", SRC, "-loop", "1", "-i", mask,
                    "-filter_complex", fc, "-map", "[v]", "-t", str(round(dur / speed + HOLD, 2))] + ENC
                   + [os.path.join(OUT, name + ".mp4")], check=True)


def raw(name, start, dur, speed):
    """Plain landscape crop (no blur frame), for footage shown inside the TV."""
    vf = f"crop=1076:840:0:380,fps=30,setpts={1 / speed}*PTS,minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:vsbmc=1,scale=1080:-2,tpad=stop_mode=clone:stop_duration={HOLD}"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-t", str(dur), "-i", SRC, "-vf", vf] + ENC
                   + [os.path.join(OUT, name + ".mp4")], check=True)


def ganguly():
    # 676x1200 portrait window on the interview, left of the BWC logo, scaled to fill 9:16
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "0", "-t", "5.35", "-i", SRC,
                    "-vf", "delogo=x=480:y=1280:w=130:h=40,crop=676:1200:100:360,scale=1080:1920:flags=lanczos,unsharp=5:5:0.4,fps=30"] + ENC
                   + [os.path.join(OUT, "ganguly.mp4")], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "0.6", "-i", os.path.join(OUT, "ganguly.mp4"), "-frames:v", "1",
                    os.path.join(OUT, "ganguly_still.jpg")], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-t", "5.35", "-i", os.path.join(HERE, "incoming", "talk_vocals.wav"),
                    "-af", "highpass=f=90,afade=t=out:st=5.15:d=0.2", "-ac", "1", "-ar", "44100",
                    os.path.join(HERE, "incoming", "ganguly_vo.wav")], check=True)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for spec in MATCH:
        match_clip(*spec)
        print(spec[0])
    raw("tv_drive_nz", 27.8, 0.9, 0.4)
    # a video file can only appear once on the timeline, so reused footage gets its own copy
    shutil.copy(os.path.join(OUT, "c_big_hit.mp4"), os.path.join(OUT, "c_big_hit_2.mp4"))
    ganguly()
    print("ganguly")

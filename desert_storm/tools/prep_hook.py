#!/usr/bin/env python3
"""Hook clip -> film/assets/video/hook.mp4: 1080x1920, 30 fps, keyframe every second,
with its burned-in caption band blurred out (our own captions replace it).

usage: python3 tools/prep_hook.py <clip.mp4> [band_top band_height]   (band in source pixels)
"""
import os, subprocess, sys

src = sys.argv[1]
top, h = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (626, 88)
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "film/assets/video/hook.mp4")
vf = (f"[0:v]split[base][b];[b]crop=iw:{h}:0:{top},boxblur=22:3,eq=brightness=-0.06[bl];"
      f"[base][bl]overlay=0:{top},scale=1080:1920:flags=lanczos,fps=30,format=yuv420p[v]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", vf, "-map", "[v]", "-map", "0:a",
                "-af", "loudnorm=I=-14:TP=-1.5:LRA=9", "-c:v", "libx264", "-crf", "17", "-g", "30",
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000", out], check=True)
print("wrote", out)

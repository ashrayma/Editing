#!/usr/bin/env python3
"""Cut the shared Steyn clips into 9:16 shots with no channel logos or scorebars.

Each moment is cropped to a square window that avoids the 'CRICKET NETWORK' bugs (top-left, bottom strip) and the score
bar, scaled to 1080x1080 and laid over a blurred, darkened copy of itself filling 1080x1920.
    python3 clips.py  ->  footage/clips/<name>.mp4
"""
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
UP = "/root/.claude/uploads/f2eff30b-6270-5fa6-842d-750db1fc6e1c/"
SRC = {"A": UP + "e8506022-plrz5w.mp4", "B": UP + "5b6cfb85-snapgram.io_x5gtn41x2z14.mp4"}
# clean area per source (x0, y0, x1, y1): below the top-left bug, above the score bar / bottom logo strip
FULL = set()                                 # nothing is cropped to fill 9:16 (too zoomed)
SAFE = {"A": (0, 120, 960, 840), "B": (0, 0, 480, 402)}
# name: (source, start, end, horizontal centre 0..1)
MOMENTS = {
    "a_wicket_wide": ("A", 0.0, 3.6, 0.5), "a_hug": ("A", 9.6, 12.0, 0.45), "a_flags": ("A", 14.0, 17.5, 0.5),
    "a_steyn_bowl": ("A", 21.6, 22.55, 0.58), "a_stumps": ("A", 24.4, 28.0, 0.45), "a_celeb": ("A", 32.6, 35.6, 0.45),
    "a_batsman": ("A", 38.0, 41.5, 0.5),
    "b_runup": ("B", 1.0, 3.0, 0.5), "b_bowled": ("B", 3.0, 4.0, 0.5), "b_smile": ("B", 4.0, 6.6, 0.5),
    "b_hug": ("B", 9.0, 13.0, 0.5), "b_batsman": ("B", 22.5, 26.6, 0.5), "b_ball": ("B", 28.0, 32.0, 0.5),
    "b_stumps": ("B", 31.4, 35.5, 0.5), "b_walk": ("B", 35.5, 37.6, 0.5),
}


def cut(name, src, a, b, cx):
    x0, y0, x1, y1 = SAFE[src]
    h = y1 - y0
    full = src in FULL                       # enough resolution to fill 9:16 outright
    w = min(x1 - x0, int(h * (9 / 16 if full else 1.0))) // 2 * 2
    x = int(min(max(x0, cx * (x1 - x0) - w / 2), x1 - w))
    if full:
        fc = (f"[0:v]crop={w}:{h // 2 * 2}:{x}:{y0},setsar=1,scale=1080:1920:flags=lanczos,unsharp=5:5:0.5,"
              f"fps=30,format=yuv420p")
    else:
        fc = (f"[0:v]crop={w}:{h // 2 * 2}:{x}:{y0},setsar=1,split[a][b];"
          f"[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:2,eq=brightness=-0.18[bg];"
              f"[b]scale=1080:1080:flags=lanczos,unsharp=5:5:0.6[fg];[bg][fg]overlay=0:420,fps=30,format=yuv420p")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(a), "-t", str(b - a), "-i", SRC[src], "-filter_complex", fc,
                    "-an", "-c:v", "libx264", "-crf", "16", "-preset", "fast",
                    os.path.join(HERE, "footage", "clips", name + ".mp4")], check=True)


if __name__ == "__main__":
    for n, m in MOMENTS.items():
        cut(n, *m)
        print("clip", n)

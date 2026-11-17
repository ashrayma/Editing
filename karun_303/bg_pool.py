#!/usr/bin/env python3
"""Background shots: every part of the 303 highlights NOT already cut into a clip, split at camera cuts, keeping only
wide field shots (mostly grass, players small) so headlines can sit on them without covering a face.

    python3 bg_pool.py   ->  footage/bg/bg_###.mp4 + out/bg_pool.json [{file, dur, src}]

Each background shot is a separate file and is used at most once, like every other clip.
"""
import json
import os
import subprocess

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "footage", "hl_303.mp4")
OUT = os.path.join(HERE, "footage", "bg")
os.makedirs(OUT, exist_ok=True)

src = open(os.path.join(HERE, "cut_clips.py")).read()
CLIPS = eval(src.split("CLIPS = ")[1].split("\n}\n")[0] + "}")
used = sorted((v[0] - 0.4, v[0] + v[1] + 0.4) for v in CLIPS.values())
cuts = [float(x) for x in open(os.path.join(HERE, "out", "cuts.txt")) if x.strip()]
bounds = [12.0] + [c for c in cuts if 12.0 < c < 475.5] + [475.5]   # skip the title card and the end slate


def frame(t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", SRC, "-frames:v", "1", "-vf", "scale=160:90",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(90, 160, 3).astype(int) if len(raw) == 160 * 90 * 3 else None


def wide(t):
    """Wide field shot: lots of grass green in the middle band, no big skin-toned blob (close-up face)."""
    f = frame(t)
    if f is None:
        return False
    mid = f[15:75]
    r, g, b_ = mid[..., 0], mid[..., 1], mid[..., 2]
    green = np.mean((g > r + 12) & (g > b_ + 8))
    skin = np.mean((r > 120) & (r > g + 20) & (g > b_) & (r - b_ > 40))
    return green > 0.30 and skin < 0.06


pool = []
for a, e in zip(bounds[:-1], bounds[1:]):
    a, e = a + 0.15, e - 0.15          # stay clear of the cut itself
    pieces = [(a, e)]
    for u0, u1 in used:                # remove anything already used as a clip
        nxt = []
        for p0, p1 in pieces:
            if u1 <= p0 or u0 >= p1:
                nxt.append((p0, p1))
                continue
            if u0 > p0:
                nxt.append((p0, u0))
            if u1 < p1:
                nxt.append((u1, p1))
        pieces = nxt
    for p0, p1 in pieces:
        d = p1 - p0
        if d < 1.6:
            continue
        # long shots are split into ~3 s pieces so each one is a fresh moment
        n = max(1, int(d // 3.2))
        step = d / n
        for k in range(n):
            s0 = p0 + k * step
            if all(wide(s0 + step * f) for f in (0.2, 0.5, 0.8)):
                pool.append((round(s0, 2), round(step, 2)))

meta = []
for k, (s0, d) in enumerate(pool):
    dst = os.path.join(OUT, f"bg_{k:03d}.mp4")
    if not os.path.exists(dst):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(s0), "-t", str(d), "-i", SRC, "-an",
                        "-vf", "scale=1280:720:flags=lanczos,fps=30", "-c:v", "libx264", "-crf", "20", "-preset", "fast",
                        "-pix_fmt", "yuv420p", "-movflags", "+faststart", dst], check=True)
    meta.append({"file": f"footage/bg/bg_{k:03d}.mp4", "dur": d, "src": s0})
json.dump(meta, open(os.path.join(HERE, "out", "bg_pool.json"), "w"), indent=1)
print(f"{len(meta)} wide background shots, {sum(m['dur'] for m in meta):.0f}s total")

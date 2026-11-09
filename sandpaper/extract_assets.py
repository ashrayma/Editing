#!/usr/bin/env python3
"""Pull the raw footage, stills and Khawaja's own voice out of the reference reel (footage/source.mp4).

    python3 extract_assets.py  ->  footage/clips/*.mp4, footage/stills/*.png, footage/khawaja/*.wav

Each clip sits inside a card in the reel's layout; crops are inset a few pixels so no border or label of that
layout survives. Clips are upscaled 2x (Lanczos + light sharpen) for our 1920x1080 cards.
"""
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "footage", "source.mp4")

# name: (start, end, x, y, w, h) in the reel's 1280x720 frame
CLIPS = {
    "hands":      (77.0, 86.4, 100, 184, 740, 408),   # Bancroft rubbing the ball (Fox Sports)
    "walkie":     (86.6, 98.4, 58, 187, 504, 279),    # Lehmann on the walkie-talkie
    "handscomb":  (86.6, 98.4, 711, 186, 511, 282),   # Handscomb on the boundary with Bancroft
    "yellow":     (99.0, 101.8, 61, 181, 805, 412),   # sandpaper into the trousers
    "pouch":      (104.0, 110.2, 93, 177, 746, 414),  # umpires, the sunglasses pouch
    "smith":      (8.5, 11.9, 59, 179, 370, 327),     # press conferences
    "warner":     (8.5, 11.9, 455, 178, 371, 329),
    "bancroft":   (8.5, 11.9, 852, 176, 370, 330),
    "warner2":    (173.6, 177.4, 59, 182, 462, 412),
    "reel1":      (30.6, 76.4, 852, 98, 281, 500),    # Khawaja's Instagram reel
    "reel2":      (157.4, 173.6, 852, 98, 281, 500),
}
STILLS = {
    "khawaja":    (115.0, 58, 179, 420, 415),
    "lehmann":    (15.0, 58, 178, 484, 412),
    "sabr":       (6.0, 136, 169, 274, 425),
    "huddle":     (138.0, 58, 198, 664, 372),
    "bowlers":    (150.0, 82, 171, 548, 351),
}
# Khawaja's own voice (from his reel), cut on pauses
KHAWAJA = {"k1": (31.34, 38.28), "k2": (64.43, 76.12), "k3": (158.13, 170.57)}


def run(*a):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)


def main():
    for d in ("clips", "stills", "khawaja"):
        os.makedirs(os.path.join(HERE, "footage", d), exist_ok=True)
    for n, (a, b, x, y, w, h) in CLIPS.items():
        run("-ss", str(a), "-to", str(b), "-i", SRC, "-an",
            "-vf", f"crop={w}:{h}:{x}:{y},scale={w * 2}:{h * 2}:flags=lanczos,unsharp=5:5:0.6,fps=30",
            "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p",
            os.path.join(HERE, "footage", "clips", n + ".mp4"))
        print("clip", n)
    for n, (t, x, y, w, h) in STILLS.items():
        run("-ss", str(t), "-i", SRC, "-frames:v", "1",
            "-vf", f"crop={w}:{h}:{x}:{y},scale={w * 2}:{h * 2}:flags=lanczos,unsharp=5:5:0.5",
            os.path.join(HERE, "footage", "stills", n + ".png"))
        print("still", n)
    for n, (a, b) in KHAWAJA.items():
        run("-ss", str(a - 0.05), "-to", str(b + 0.1), "-i", SRC, "-vn", "-ac", "1", "-ar", "44100",
            "-af", "afade=in:d=0.04,areverse,afade=in:d=0.12,areverse",
            os.path.join(HERE, "footage", "khawaja", n + ".wav"))
        print("voice", n)


if __name__ == "__main__":
    main()

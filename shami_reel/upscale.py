#!/usr/bin/env python3
"""Upscale the low-res source photos 4x with EDSR (OpenCV dnn_superres) so they hold up full-screen at 1080x1920.

    python3 upscale.py   ->  assets/hi/<name>.png   (skips photos already at least 1600 px tall)
"""
import glob
import os

import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "assets", "hi")
os.makedirs(OUT, exist_ok=True)
sr = cv2.dnn_superres.DnnSuperResImpl_create()
sr.readModel(os.path.join(HERE, "models", "EDSR_x4.pb"))
sr.setModel("edsr", 4)

for f in sorted(glob.glob(os.path.join(HERE, "assets", "photos", "*.jpg"))):
    dst = os.path.join(OUT, os.path.basename(f)[:-4] + ".png")
    if os.path.exists(dst):
        continue
    im = cv2.imread(f)
    h, w = im.shape[:2]
    if h >= 1600:
        cv2.imwrite(dst, im)
    elif max(h, w) >= 1100:  # already big: a sharp Lanczos x2 is enough (and far faster than EDSR)
        cv2.imwrite(dst, cv2.resize(im, (w * 2, h * 2), interpolation=cv2.INTER_LANCZOS4))
    else:
        if max(h, w) > 540:  # EDSR is slow on big inputs: bring them to ~540 px first, then x4
            s = 540 / max(h, w)
            im = cv2.resize(im, (round(w * s), round(h * s)), interpolation=cv2.INTER_AREA)
        cv2.imwrite(dst, sr.upsample(im))
    print(os.path.basename(dst), cv2.imread(dst).shape[:2])

#!/usr/bin/env python3
"""Find the players' faces in every photo and cut-out, so the edit can keep type and the logo off them.

    python3 faces.py   ->  assets/faces.json  {"hi/<name>": [[x, y, w, h], ...], "cut/<name>": [...]}
Boxes are fractions of the image size. Detector: YuNet (OpenCV), models/yunet.onnx.
"""
import glob
import json
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def detect(img, det):
    h, w = img.shape[:2]
    s = 1280 / max(h, w)
    small = cv2.resize(img, (round(w * s), round(h * s)))
    det.setInputSize((small.shape[1], small.shape[0]))
    _, faces = det.detect(small)
    out = []
    for f in faces if faces is not None else []:
        if f[14] < 0.75:
            continue
        x, y, fw, fh = (float(v) / s for v in f[:4])
        out.append([round(x / w, 4), round(y / h, 4), round(fw / w, 4), round(fh / h, 4)])
    # keep the players, not the crowd: drop faces much smaller than the biggest one
    big = max((b[2] * b[3] for b in out), default=0)
    return [b for b in out if b[2] * b[3] >= 0.2 * big]


def main():
    det = cv2.FaceDetectorYN.create(os.path.join(HERE, "models", "yunet.onnx"), "", (320, 320), 0.6, 0.3, 50)
    res = {}
    for f in sorted(glob.glob(os.path.join(HERE, "assets", "hi", "*.png"))):
        res["hi/" + os.path.basename(f)[:-4]] = detect(cv2.imread(f), det)
    for f in sorted(glob.glob(os.path.join(HERE, "assets", "cut", "*.png"))):
        rgba = cv2.imread(f, cv2.IMREAD_UNCHANGED)
        a = rgba[:, :, 3:4].astype(np.float32) / 255
        img = (rgba[:, :, :3] * a + 128 * (1 - a)).astype(np.uint8)
        res["cut/" + os.path.basename(f)[:-4]] = detect(img, det)
    # hand-placed boxes where the detector locked onto a face in the crowd instead of the player
    mp = os.path.join(HERE, "assets", "faces_manual.json")
    if os.path.exists(mp):
        res.update(json.load(open(mp)))
    json.dump(res, open(os.path.join(HERE, "assets", "faces.json"), "w"), indent=1)
    for k, v in res.items():
        print(f"{k:34s} {len(v)} {v[:2]}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Face boxes for every photo -> assets/faces.json, so crops and zooms keep faces in frame."""
import json
import os
import sys

from facenet_pytorch import MTCNN
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = ["x"]
import make_ipl as m  # noqa: E402

det = MTCNN(keep_all=True, device="cpu", min_face_size=20)
out = {}
for name in m.PHOTO_PATHS:
    if name in m.INTL:
        continue
    im = m.photo(name)
    s = min(1.0, 1600 / max(im.size))
    sm = im.resize((int(im.width * s), int(im.height * s)))
    boxes, probs = det.detect(sm)
    faces = []
    if boxes is not None:
        for b, p in zip(boxes, probs):
            if p > 0.9:
                x0, y0, x1, y1 = (b / s).tolist()
                faces.append([x0 / im.width, y0 / im.height, x1 / im.width, y1 / im.height, float(p)])
    out[name] = faces
    print(name, len(faces))
json.dump(out, open(os.path.join(HERE, "assets", "faces.json"), "w"), indent=1)

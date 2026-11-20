#!/usr/bin/env python3
"""Remove logos and sponsor text from the source photos before anything else touches them.

    python3 clean_logos.py   ->  assets/photos/<name>.jpg  (from assets/photos_raw/)

1. Crop away watermarks / graphic banners (CROP).
2. Find every bit of text (sponsors, wordmarks, banners, boards) with a text detector and blur it out.
3. Blur the extra regions listed in BOXES (crests and badges without text).
Faces are never blurred: any region that overlaps a detected face is shrunk away from it.
"""
import glob
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RAW, OUT = os.path.join(HERE, "assets", "photos_raw"), os.path.join(HERE, "assets", "photos")
os.makedirs(OUT, exist_ok=True)

# (x0, y0, x1, y1) as fractions of the raw image
CROP = {}
# crests / badges with no readable text, as fractions of the image
BOXES = {
    "kp_walk_tall": [(0.60, 0.33, 0.73, 0.43), (0.34, 0.83, 0.47, 0.93), (0.27, 0.32, 0.47, 0.38)],
    "kp_skunk": [(0.52, 0.80, 0.61, 0.95), (0.76, 0.68, 0.86, 0.80), (0.24, 0.42, 0.30, 0.52)],
    "kp_skunk_wave": [(0.50, 0.55, 0.58, 0.68), (0.37, 0.52, 0.47, 0.66)],
    "strauss_2005": [(0.32, 0.72, 0.42, 0.85), (0.53, 0.76, 0.62, 0.89), (0.82, 0.72, 0.92, 0.80)],
    "kp_mumbai": [(0.38, 0.56, 0.48, 0.62), (0.31, 0.71, 0.48, 0.80), (0.48, 0.71, 0.58, 0.80)],
    "kp_headingley": [(0.18, 0.50, 0.38, 0.62)],
    "kp_raise": [(0.53, 0.30, 0.66, 0.38), (0.63, 0.31, 0.72, 0.45)],
    "kp_flower": [(0.56, 0.45, 0.83, 0.72)],
    "kp_bell": [(0.18, 0.40, 0.42, 0.75), (0.60, 0.28, 0.92, 0.65)],
    "strauss_captain": [(0.30, 0.42, 0.56, 0.65)],
}
FACES = {}


def faces(img):
    det = cv2.FaceDetectorYN.create(os.path.join(HERE, "models", "yunet.onnx"), "", (img.shape[1], img.shape[0]), 0.7)
    _, f = det.detect(img)
    return [] if f is None else [tuple(int(v) for v in r[:4]) for r in f]


def blur_box(img, x0, y0, x1, y1):
    h, w = img.shape[:2]
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(w, x1), min(h, y1)
    if x1 - x0 < 4 or y1 - y0 < 4:
        return
    roi = img[y0:y1, x0:x1]
    k = max(15, (max(x1 - x0, y1 - y0) // 3) | 1)
    soft = cv2.GaussianBlur(cv2.resize(roi, (max(1, (x1 - x0) // 8), max(1, (y1 - y0) // 8))), (3, 3), 0)
    soft = cv2.resize(soft, (x1 - x0, y1 - y0), interpolation=cv2.INTER_LINEAR)
    soft = cv2.GaussianBlur(soft, (k, k), 0)
    # feathered edge so the patch melts into the fabric
    m = np.zeros((y1 - y0, x1 - x0), np.float32)
    pad = max(2, min(x1 - x0, y1 - y0) // 6)
    m[pad:-pad or None, pad:-pad or None] = 1
    # no feather on a side that touches the photo's edge (otherwise the last rows stay readable)
    if y0 == 0: m[:pad, pad:-pad or None] = 1
    if y1 == h: m[-pad:, pad:-pad or None] = 1
    if x0 == 0: m[:, :pad] = m[:, pad:pad + 1]
    if x1 == w: m[:, -pad:] = m[:, -pad - 1:-pad]
    m = cv2.GaussianBlur(m, (0, 0), pad)
    if y1 == h: m[-pad:] = np.maximum(m[-pad:], m[-pad - 1:-pad].max())
    if x0 == 0: m[:, :pad] = np.maximum(m[:, :pad], m[:, pad:pad + 1])
    if x1 == w: m[:, -pad:] = np.maximum(m[:, -pad:], m[:, -pad - 1:-pad])
    m = m[..., None]
    img[y0:y1, x0:x1] = (soft * m + roi * (1 - m)).astype(np.uint8)


def clear_of_faces(box, fs):
    x0, y0, x1, y1 = box
    for fx, fy, fw, fh in fs:
        if x0 < fx + fw and fx < x1 and y0 < fy + fh and fy < y1:
            # keep the part of the box below the face (sponsors sit on the chest)
            y0 = max(y0, fy + fh + 4)
    return (x0, y0, x1, y1)


def main():
    from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR()
    for f in sorted(glob.glob(os.path.join(RAW, "*.jpg"))):
        name = os.path.basename(f)[:-4]
        img = cv2.imread(f)
        if name in CROP:
            h, w = img.shape[:2]
            x0, y0, x1, y1 = CROP[name]
            img = img[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)].copy()
        h, w = img.shape[:2]
        fs = faces(img) + [(int(a * w), int(b * h), int((c - a) * w), int((d - b) * h)) for a, b, c, d in FACES.get(name, [])]
        boxes = []
        for sc in (1.0, 2.0, 3.0):  # small sponsors only show up when the photo is enlarged
            big = cv2.resize(img, None, fx=sc, fy=sc, interpolation=cv2.INTER_CUBIC) if sc != 1 else img
            res, _ = ocr(big, use_det=True, use_cls=False, use_rec=True, box_thresh=0.3, text_score=0.2)
            boxes += [[(px / sc, py / sc) for px, py in b] for b, _, _ in (res or [])]
        n = 0
        for box in boxes:
            xs, ys = [p[0] for p in box], [p[1] for p in box]
            bw, bh = max(xs) - min(xs), max(ys) - min(ys)
            ex, ey = int(bw * 0.12) + 4, int(bh * 0.35) + 4
            b = clear_of_faces((int(min(xs)) - ex, int(min(ys)) - ey, int(max(xs)) + ex, int(max(ys)) + ey), fs)
            blur_box(img, *b)
            n += 1
        for x0, y0, x1, y1 in BOXES.get(name, []):
            blur_box(img, *clear_of_faces((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)), fs))
        cv2.imwrite(os.path.join(OUT, name + ".jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        print(f"{name:18s} {w}x{h}  text regions blurred: {n}")


if __name__ == "__main__":
    main()

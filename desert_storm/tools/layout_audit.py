#!/usr/bin/env python3
"""Check that no card, B-roll or caption box overlaps the protected area: the photo
frame in the faceless format, or a face if you ever switch to a talking head.

Reads out_layout.json (written by build.py). --max-scale grows the protected box for
punch-ins; --video measures a real face-cam first (OpenCV Haar).

usage: python3 tools/layout_audit.py [--video facecam.mp4 --max-scale 1.2]
"""
import argparse, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOP_UI = 168  # Instagram/YouTube status + search bar


def measure(video):
    import cv2
    cap = cv2.VideoCapture(video)
    casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    W, H = cap.get(3), cap.get(4)
    sx, sy = 1080 / W, 1920 / H
    boxes, i = [], 0
    while True:
        ok, f = cap.read()
        if not ok:
            break
        if i % 15 == 0:
            for (x, y, w, h) in casc.detectMultiScale(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), 1.1, 6, minSize=(80, 80)):
                if w * sx > 250:
                    boxes.append((x * sx, y * sy, (x + w) * sx, (y + h) * sy))
        i += 1
    if not boxes:
        raise SystemExit("no face found in " + video)
    # the face's full travel over the take, with a little headroom for hair and chin
    x0, y0 = min(b[0] for b in boxes), min(b[1] for b in boxes)
    x1, y1 = max(b[2] for b in boxes), max(b[3] for b in boxes)
    return (x0 - 20, y0 - 40, x1 + 20, y1 + 40)


def overlap(a, b):
    return max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--video")
    ap.add_argument("--max-scale", type=float, default=1.0)
    args = ap.parse_args()
    lay = json.load(open(os.path.join(ROOT, "out_layout.json")))
    face = measure(args.video) if args.video else tuple(lay["face"])
    ox, oy = (float(v.replace("px", "")) for v in lay["origin"].split())
    s = args.max_scale
    zoomed = (ox + (face[0] - ox) * s, oy + (face[1] - oy) * s, ox + (face[2] - ox) * s, oy + (face[3] - oy) * s)
    print(f"protected box {tuple(round(v) for v in face)}  ->  at {s}x {tuple(round(v) for v in zoomed)}")
    bad = 0
    for b in lay["boxes"]:
        x, y, w, h = b["box"]
        r = (x, y, x + w, y + h)
        hit = overlap(r, zoomed)
        flags = []
        if hit:
            flags.append(f"OVERLAPS PROTECTED AREA by {hit:.0f} px²")
        if y < TOP_UI:
            flags.append("inside top UI band")
        bad += bool(flags)
        print(f"  {'FAIL' if flags else 'ok  '} {b['id']:<11} {b['t0']:6.2f}-{b['t1']:6.2f}s  box y {y}-{y + h}  {'; '.join(flags)}")
    print("PASS: nothing covers the protected area" if not bad else f"{bad} problem(s)")
    raise SystemExit(1 if bad else 0)

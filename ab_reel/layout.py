#!/usr/bin/env python3
"""Keep type and the logo off the players' faces.

    node measure.js && python3 layout.py [--report]   ->  out/layout.json (read by reel.py)

For every movable type element that touches a visible face at any moment it is on screen, find the nearest
position (vertical first, then the other side for left-aligned blocks) where it clears every face it shares the
screen with, stays out of the caption band and doesn't land on other type. Captions choose between a few fixed
rows. The logo fades out while a face (or a headline) is under it. Run it again after a rebuild to confirm.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1920
TOP_SAFE, BOTTOM_SAFE = 250, 1500
CAP_BAND = (1400, 1500)
CAP_ROWS = [1420, 1290, 1560, 1180]


def grow(r, m):
    x, y, w, h = r
    return (x - m, y - m, w + 2 * m, h + 2 * m)


def hit(a, b):
    return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]


def face_box(f):
    # pad faces: a bit at the sides and chin, more above (hair / helmet peak)
    x, y, w, h = f
    return (x - 0.15 * w, y - 0.3 * h, 1.3 * w, 1.45 * h)


def main():
    m = json.load(open(os.path.join(HERE, "out", "measure.json")))
    lp = os.path.join(HERE, "out", "layout.json")
    old = json.load(open(lp)) if os.path.exists(lp) else {"move": {}, "brand_hide": []}
    S = m["samples"]
    ids = {}
    for s in S:
        for i, e in s["els"].items():
            ids.setdefault(i, []).append((s, e))
    report = "--report" in sys.argv
    moves, bad = dict(old["move"]), []
    placed = {}  # id -> (dx, dy) decided this run, to keep later choices off earlier ones
    for i, occ in sorted(ids.items(), key=lambda kv: kv[1][0][0]["t"]):
        faces = [[face_box(f) for f in s["faces"]] for s, _ in occ]
        clash = [s["t"] for (s, e), fs in zip(occ, faces) if any(hit(grow(e["r"], 10), f) for f in fs)]
        if not clash:
            continue
        bad.append((i, clash[0], clash[-1]))
        if report:
            continue
        cap = i.startswith("cap")
        e0 = occ[-1][1]
        top0, left0, (rx, ry, rw, rh) = e0["top"], e0["left"], e0["r"]
        cands = []
        if cap:
            cands = [(0, r - top0) for r in CAP_ROWS]
        else:
            lefts = [0]
            if left0 and rw < W * 0.6:  # left-aligned block: may also swap to the right-hand side
                lefts.append(W - 70 - rw - rx)
            for dx in lefts:
                for ty in range(TOP_SAFE, BOTTOM_SAFE, 10):
                    cands.append((dx, ty - ry))
            cands.sort(key=lambda d: abs(d[1]) + 2.5 * abs(d[0]))

        def ok(dx, dy):
            for (s, e), fs in zip(occ, faces):
                r = (e["r"][0] + dx, e["r"][1] + dy, e["r"][2], e["r"][3])
                if r[1] < (1100 if cap else TOP_SAFE) or r[1] + r[3] > (1650 if cap else BOTTOM_SAFE):
                    return False
                if not cap and hit(r, (0, CAP_BAND[0], W, CAP_BAND[1] - CAP_BAND[0])) and not hit(e["r"], (0, CAP_BAND[0], W, 100)):
                    return False
                if any(hit(grow(r, 10), f) for f in fs):
                    return False
                for j, o in s["els"].items():  # other type on screen at the same moment
                    if j == i:
                        continue
                    ox, oy = placed.get(j, (0, 0))
                    if hit(grow(r, 8), (o["r"][0] + ox, o["r"][1] + oy, o["r"][2], o["r"][3])):
                        return False
            return True

        for dx, dy in cands:
            if ok(dx, dy):
                mv = {"top": round(top0 + dy)}
                if dx:
                    mv["left"] = round(left0 + dx)
                moves[i] = mv
                placed[i] = (dx, dy)
                print(f"  move {i:8s} {clash[0]:5.1f}s  top {top0:.0f} -> {mv['top']}" + (f", left {left0:.0f} -> {mv['left']}" if dx else ""))
                break
        else:
            print(f"  !! {i}: no clear spot ({clash[0]:.1f}-{clash[-1]:.1f}s)")
    # logo: hide while a face or headline is under it
    hide, cur = [], None
    for s in S:
        b = s["brand"]
        blocked = bool(b) and (any(hit(grow(b, 14), face_box(f)) for f in s["faces"]) or
                               any(hit(grow(b, 14), e["r"]) for e in s["els"].values()))
        if blocked and cur is None:
            cur = [s["t"], s["t"]]
        elif blocked:
            cur[1] = s["t"]
        elif cur:
            hide.append(cur)
            cur = None
    if cur:
        hide.append(cur)
    merged = []
    for a, b in hide:
        a, b = a - 0.15, b + 0.25
        if merged and a - merged[-1][1] < 0.6:
            merged[-1][1] = b
        else:
            merged.append([a, b])
    # windows found on an earlier pass stay (the logo is already hidden there, so it no longer reports them)
    for a, b in old.get("brand_hide", []):
        if not any(x <= a <= y or x <= b <= y for x, y in merged):
            merged.append([a, b])
    merged = sorted([round(max(0, a), 2), round(b, 2)] for a, b in merged)
    longer = []  # no blinks: every hide lasts at least 0.8 s
    for a, b in merged:
        if b - a < 0.8:
            c = (a + b) / 2
            a, b = max(0, c - 0.4), c + 0.4
        if longer and a - longer[-1][1] < 0.6:
            longer[-1][1] = max(longer[-1][1], round(b, 2))
        else:
            longer.append([round(a, 2), round(b, 2)])
    merged = longer
    print(f"conflicts: {len(bad)} type elements; logo hidden in {len(merged)} windows")
    if report:
        for i, a, b in bad:
            print(f"  {i:8s} {a:5.1f}-{b:5.1f}s")
        return len(bad)
    json.dump({"move": moves, "brand_hide": merged}, open(lp, "w"), indent=1)


if __name__ == "__main__":
    sys.exit(main() if "--report" in sys.argv else main() or 0)

#!/usr/bin/env python3
"""Clean the creator's take (vo/vo_raw.m4a, 13:40) into vo/vo_clean.wav.

1. Drop the false starts / retakes (CUTS, raw seconds; the better take that follows is kept).
2. Shorten every pause: anything over MAXP becomes MAXP (BREAKS keep a longer, deliberate beat).
3. Light polish (high-pass, de-noise, presence EQ, gentle compression), then peak-normalise.
Writes vo/vo_map.json: kept raw ranges and where each starts in the clean file, so the edit can be timed to raw
transcript times.
"""
import json
import os
import re
import subprocess

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000
RAW = os.path.join(HERE, "vo", "vo_raw.m4a")

START, END = 10.45, 817.9
CUTS = [                                   # (from, to) raw seconds removed, with what they were
    (104.00, 113.85),   # "aur paanch mahine baad Chennai mein kismat…" stopped half-way; retake follows
    (298.05, 302.40),   # "Lekin ek baat saaf samajh lijiye" said twice
    (463.00, 477.80),   # "jis ladke ka Test average 62 tha…" first take trailed off
    (508.70, 521.38),   # "Aur sach ye bhi hai" x2 + a take with the wrong word
    (572.85, 579.90),   # Vijay Hazare line with wrong numbers (789 / 399); retake has 779 / 389
    (703.60, 715.60),   # "aath saal baad bhi England ki us har pari ko" stopped; retake follows
    (733.20, 750.35),   # "Toh asli sach kya hai" — three false starts; the clean take is at 750.4
]
# re-recorded lines spliced in place of the original (raw from, raw to, file, file from, file to)
REPLACE = [(167.55, 178.85, "vo/fix_759.m4a", 1.45, 6.55)]   # creator said "569" (and a false start of the next line); the re-record says 759
# new lines recorded separately, inserted at a raw time (best takes only; false starts left out)
INSERTS = [
    (207.60, "vo/ins_a.m4a", [(2.15, 17.85)]),                                   # "Match ke baad… wahi 303"
    (599.60, "vo/ins_b.m4a", [(0.85, 13.40), (18.55, 44.75)]),                  # IPL 2025 (2nd "40 balls" take)
    (774.60, "vo/ins_c.m4a", [(2.0, 8.5), (13.75, 17.10), (24.45, 27.15), (27.45, 30.30)]),  # "…wo humara ho gaya"
]
MAXP = 0.55                                # longest ordinary pause after cleaning
BREAKS = {                                 # raw time of a section start -> pause kept before it
    68.9: 1.0, 118.0: 1.0, 208.0: 1.0, 253.5: 0.9, 267.0: 1.0, 346.6: 1.0, 405.0: 1.0, 414.0: 0.9,
    493.0: 1.0, 557.3: 0.9, 608.2: 1.0, 680.5: 0.9, 721.0: 1.0, 727.7: 0.8, 750.35: 0.8, 806.2: 1.0,
}


def silences(path):
    out = subprocess.run(["ffmpeg", "-i", path, "-af", "silencedetect=n=-36dB:d=0.25", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", out)]
    en = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", out)]
    return list(zip(st, en))


CHAIN = ("highpass=f=80,afftdn=nf=-30:nr=10,equalizer=f=220:t=q:w=1.2:g=-2,"
         "equalizer=f=3200:t=q:w=1.0:g=2.5,acompressor=threshold=-22dB:ratio=3:attack=5:release=120:makeup=3")


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-af", CHAIN, "-ac", "1", "-ar", str(SR), "-f", "f32le",
                          "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def rms_voiced(x):
    e = np.sqrt(np.convolve(x ** 2, np.ones(2400) / 2400, "same"))
    return np.sqrt(np.mean(x[e > np.percentile(e, 60)] ** 2))


TIGHT = 0.40      # second pass: every pause, measured against the voice itself, becomes this
TIGHT_BREAK = 0.75


def BREAK_CLEAN(vmap):
    """Clean-file times of the section BREAKS (raw times mapped through the first-pass map)."""
    out = []
    for bt in BREAKS:
        for p in vmap:
            if not p.get("fix") and p["raw"][0] - 0.05 <= bt <= p["raw"][1] + 3.0:
                out.append(p["clean"] + max(0.0, bt - p["raw"][0]))
                break
    return out


def tighten(y, keep_near):
    """Energy-relative pause finder (breaths and room tone count as pause); returns new audio + retime map."""
    hop = int(0.01 * SR)
    e = np.sqrt((y[:len(y) // hop * hop].reshape(-1, hop) ** 2).mean(1))
    db = 20 * np.log10(e + 1e-9)
    thr = np.percentile(db[db > -60], 90) - 24
    quiet = db < thr
    runs, i = [], 0
    while i < len(quiet):
        if quiet[i]:
            j = i
            while j < len(quiet) and quiet[j]:
                j += 1
            runs.append((i * 0.01, j * 0.01))
            i = j
        else:
            i += 1
    segs, cur, out = [], 0.0, []
    for r0, r1 in runs:
        want = TIGHT_BREAK if any(abs(k - r1) < 1.2 for k in keep_near) else TIGHT
        if r1 - r0 > want + 0.05:
            cut0 = r0 + 0.08                       # keep the word's tail
            cut1 = r1 - (want - 0.08)
            segs.append((cur, cut0))
            cur = cut1
    segs.append((cur, len(y) / SR))
    fade = int(0.008 * SR)
    pos, retime = 0.0, []
    for a0, a1 in segs:
        x = y[int(a0 * SR):int(a1 * SR)].copy()
        if len(x) > 2 * fade:
            x[:fade] *= np.linspace(0, 1, fade)
            x[-fade:] *= np.linspace(1, 0, fade)
        out.append(x)
        retime.append([round(a0, 3), round(a1, 3), round(pos, 3)])
        pos += len(x) / SR
    return np.concatenate(out), retime


def main():
    a = load(RAW)

    # keep-ranges: START..END minus CUTS
    keep, t = [], START
    for c0, c1 in sorted(CUTS + [(r[0], r[1]) for r in REPLACE] + [(i[0], i[0]) for i in INSERTS]):
        keep.append((t, c0))
        t = c1
    keep.append((t, END))

    # inside each keep-range, shorten long silences
    sil = silences(RAW)
    pieces = []                            # (raw_from, raw_to)
    for k0, k1 in keep:
        cur = k0
        for s0, s1 in sil:
            if s1 <= k0 or s0 >= k1:
                continue
            s0, s1 = max(s0, k0), min(s1, k1)
            nxt = s1
            want = MAXP
            for bt, bp in BREAKS.items():
                if abs(bt - s1) < 2.5:
                    want = bp
            if s1 - s0 > want:
                mid = s0 + 0.12           # keep the breath tail of the word
                pieces.append((cur, mid))
                cur = s1 - (want - 0.12)
        pieces.append((cur, k1))

    ref = rms_voiced(a[int(150 * SR):int(200 * SR)])
    fixes = {}
    for r0, r1, f, f0, f1 in REPLACE:
        b = load(os.path.join(HERE, f))[int(f0 * SR):int(f1 * SR)]
        fixes[r1] = (r0, b * ref / rms_voiced(b))
    gap = np.zeros(int(0.32 * SR))
    for at, f, parts in INSERTS:
        full = load(os.path.join(HERE, f))
        segs = []
        for p0, p1 in parts:
            x = full[int(p0 * SR):int(p1 * SR)].copy()
            fd = int(0.015 * SR)
            x[:fd] *= np.linspace(0, 1, fd)
            x[-fd:] *= np.linspace(1, 0, fd)
            segs += [x, gap]
        b = np.concatenate(segs[:-1])
        fixes[at] = (at, b * ref / rms_voiced(b))
    pieces = sorted(pieces + [(k, None) for k in fixes], key=lambda p: (p[0], p[1] is not None))
    fade = int(0.012 * SR)
    out, vmap, pos = [], [], 0.0
    for r0, r1 in pieces:
        if r1 is None:                      # spliced re-record; it sits where the original line was
            fr0, seg = fixes[r0]
            seg = seg.copy()
            seg[:fade] *= np.linspace(0, 1, fade)
            seg[-fade:] *= np.linspace(1, 0, fade)
            out += [np.zeros(int(0.25 * SR)), seg, np.zeros(int(0.25 * SR))]
            vmap.append({"raw": [fr0, r0], "clean": round(pos + 0.25, 3), "fix": True})
            pos += len(seg) / SR + 0.5
            continue
        seg = a[int(r0 * SR):int(r1 * SR)].copy()
        if len(seg) < 2 * fade:
            continue
        seg[:fade] *= np.linspace(0, 1, fade)
        seg[-fade:] *= np.linspace(1, 0, fade)
        out.append(seg)
        vmap.append({"raw": [round(r0, 3), round(r1, 3)], "clean": round(pos, 3)})
        pos += len(seg) / SR
    y = np.concatenate(out)
    y, retime = tighten(y, [p["clean"] for p in vmap if p.get("fix")] + [bt for bt in BREAK_CLEAN(vmap)])
    json.dump(retime, open(os.path.join(HERE, "vo", "retime.json"), "w"))
    pos = len(y) / SR
    y = y / (np.abs(y).max() + 1e-9) * 0.92
    pcm = (y * 32767).astype(np.int16)
    import wave
    with wave.open(os.path.join(HERE, "vo", "vo_clean.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    json.dump(vmap, open(os.path.join(HERE, "vo", "vo_map.json"), "w"), indent=0)
    print(f"clean VO: {int(pos // 60)}:{pos % 60:04.1f}  ({len(pieces)} pieces)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Your voiceover -> out/vo_final.wav + out/vo_timeline.json (replaces the scratch voice; the whole edit re-times).

    python3 build_vo.py vo_raw/take1.m4a [vo_raw/take2.m4a ...]     # one long take or several, in script order
    python3 build_vo.py --manual                                     # use the hand-checked cut list in MANUAL

Cleanup: the same chain as the reels (high-pass, de-noise, presence EQ, compression), long pauses tightened.
Auto mode splits the cleaned narration at its pauses and assigns each beat of beats.py its share of the speech
by script length, snapping every boundary to the nearest real pause. Check the result with --report; any beat
that lands wrong (a fumble or a retake) goes into MANUAL as (file, start, end) pieces and wins over auto mode.
"""
import json
import os
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "kohli_countdown"))
from beats import BEATS, BREATH, NEW  # noqa: E402
from voiceover import SR, clean_recording, tighten_pauses, voiced_regions  # noqa: E402

BEAT_GAP = 0.42      # silence between beats
LEAD = 0.6           # silence before the first word
MANUAL = {
    # "six_one": [("vo_raw/take1.m4a", 212.4, 219.9)],
}


def clean(path, trim=None):
    """The reels' cleanup chain WITHOUT pause tightening (the split needs the real pause lengths)."""
    import voiceover
    keep = voiceover.tighten_pauses
    voiceover.tighten_pauses = lambda a: a
    try:
        return clean_recording(path, trim)
    finally:
        voiceover.tighten_pauses = keep


def auto_split(audio, beats=None):
    """Boundaries (seconds) between beats: the set of pauses whose split best matches each beat's share of the
    script (by length), favouring longer pauses. Dynamic programming over all candidate pauses."""
    regions = voiced_regions(audio)
    cands = [((regions[k][1] + regions[k + 1][0]) / 2, regions[k + 1][0] - regions[k][1]) for k in range(len(regions) - 1)]
    starts = np.array([r[0] for r in regions])
    durs = np.array([r[1] - r[0] for r in regions])
    cum = np.concatenate([[0], np.cumsum(durs)])

    def speech_before(t):
        k = np.searchsorted(starts, t)
        return cum[k]

    total = cum[-1]
    beats = beats or BEATS
    lens = np.array([len(t) for _, t in beats], float)
    exp = lens / lens.sum() * total
    n, P = len(beats), len(cands)
    sp = np.array([speech_before(c[0]) for c in cands])
    bonus = np.array([np.log(max(c[1], 0.05) / 0.3) for c in cands])
    INF = 1e18
    # cost[k][j]: best cost with cut k (0-based) at candidate j
    cost = np.full((n - 1, P), INF)
    back = np.zeros((n - 1, P), int)
    for j in range(P):
        cost[0][j] = ((sp[j] - exp[0]) / exp[0]) ** 2 - 0.35 * bonus[j]
    for k in range(1, n - 1):
        for j in range(k, P):
            seg = sp[j] - sp[:j]
            c = cost[k - 1][:j] + ((seg - exp[k]) / exp[k]) ** 2
            i = int(np.argmin(c))
            cost[k][j] = c[i] - 0.35 * bonus[j]
            back[k][j] = i
    last = cost[n - 2] + (((total - sp) - exp[n - 1]) / exp[n - 1]) ** 2
    j = int(np.argmin(last))
    cuts = []
    for k in range(n - 2, -1, -1):
        cuts.append(cands[j][0])
        j = back[k][j]
    return sorted(cuts)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    pieces = []
    if args:
        # each argument is a file, optionally with the lines it covers: vo_raw/part1.mp3@l001-l048
        jobs, ids = [], [b for b, _ in BEATS]
        for k, a in enumerate(args):
            path, _, rng = a.partition("@")
            if rng == "new":   # one file holding only the lines added for the 15-minute cut, in script order
                sub = [b for b in BEATS if b[0] in NEW]
            elif rng:
                lo, hi = rng.split("-")
                sub = [b for b in BEATS[ids.index(lo): ids.index(hi) + 1] if b[0] not in NEW]
            else:
                sub = BEATS if len(args) == 1 else sys.exit("with several files, give each its lines: file@l001-l048")
            jobs.append((os.path.join(HERE, path) if not os.path.isabs(path) else path, sub))
        for path, sub in jobs:
            audio = clean(path)
            cuts = [0.0] + auto_split(audio, sub) + [len(audio) / SR]
            for k, (bid, _) in enumerate(sub):
                seg = audio[int(cuts[k] * SR): int(cuts[k + 1] * SR)]
                if bid in MANUAL:
                    seg = np.concatenate([clean_recording(os.path.join(HERE, f), trim=(s, e)) for f, s, e in MANUAL[bid]])
                pieces.append((bid, tighten_pauses(seg)))
    else:
        for bid, _ in BEATS:
            if bid not in MANUAL:
                sys.exit(f"--manual needs a cut list for every beat; {bid} is missing")
            pieces.append((bid, np.concatenate([clean_recording(os.path.join(HERE, f), trim=(s, e)) for f, s, e in MANUAL[bid]])))

    order = {b: k for k, (b, _) in enumerate(BEATS)}
    pieces.sort(key=lambda p: order[p[0]])          # files may arrive in any order; the film follows the script
    got = {p[0] for p in pieces}
    missing = [b for b, _ in BEATS if b not in got]
    if missing:
        print("note: no audio yet for", len(missing), "lines:", ", ".join(missing))
    out, beats, t = [np.zeros(int(SR * LEAD), np.float32)], [], LEAD
    for bid, seg in pieces:
        r = voiced_regions(seg)
        if r:  # trim each beat to its own speech
            seg = seg[max(0, int((r[0][0] - 0.05) * SR)): int((r[-1][1] + 0.08) * SR)]
        beats.append({"id": bid, "start": round(t, 3), "end": round(t + len(seg) / SR, 3), "text": dict(BEATS)[bid]})
        gap = BEAT_GAP + BREATH.get(bid, 0.0)
        out += [seg, np.zeros(int(SR * gap), np.float32)]
        t += len(seg) / SR + gap
    a = np.concatenate(out)
    a = a / (np.abs(a).max() + 1e-9) * 0.89
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    with wave.open(os.path.join(HERE, "out", "vo_final.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((a * 32767).astype(np.int16).tobytes())
    json.dump({"duration": round(len(a) / SR, 3), "scratch": False, "beats": beats},
              open(os.path.join(HERE, "out", "vo_timeline.json"), "w"), indent=1, ensure_ascii=False)
    for bb in beats:
        print(f"{bb['id']:16s} {bb['start']:7.2f} -> {bb['end']:7.2f}  {bb['text'][:60]}")
    print(f"total {len(a) / SR:.1f}s")


if __name__ == "__main__":
    main()

"""Pin script lines to a recording using the English words an offline recogniser (PocketSphinx) hears.

The narration is Hinglish, so most words are unrecognisable to an English model, but names, places, months and
cricket terms come through. Matching the script's English words in order (LCS) against the recognised words gives
time anchors for many lines; build_vo.py uses them to keep the line split from drifting.
"""
import re

import numpy as np

ANCHOR_WORDS = set("""australia england melbourne cricket ground stadium pakistan world cup covid december september
november october march august january captain captaincy century golden duck partnership final free hit wide short ball
catch fifty sixty seventy twenty thirty forty hundred rule technique intensity fake family social media nets gym selfies
kolkata adelaide dubai afghanistan hong kong asia mohali england swing diet body game record ponting sachin anderson
dhoni shaheen babar rizwan arshdeep hardik pandya rohit sharma naseem iftikhar masood suryakumar axar patel nawaz
karthik ashwin edge stumps lbw toss anthem diwali forecast boundaries pace attack nightmare drama plan spinner over
overs back foot length delivery speed slog bowler sightscreen six square leg umpire no free stumping mid off india
shot comment subscribe story hobart malinga team selfie test pink""".split())


def recognise(raw16k):
    """[(word, seconds)] from 16 kHz mono int16 bytes."""
    from pocketsphinx import Decoder
    d = Decoder(samprate=16000)
    d.start_utt()
    d.process_raw(raw16k, full_utt=True)
    d.end_utt()
    return [(s.word.lower().split("(")[0], s.start_frame / 100) for s in d.seg()
            if not s.word.startswith(("<", "["))]


def line_anchors(beats, heard):
    """{line id: first matched time} via LCS between the script's anchor words and the recognised words."""
    script = []
    for bid, text in beats:
        low = text.lower()
        for m in re.finditer(r"[a-z]+", low):
            if m.group(0) in ANCHOR_WORDS:
                script.append((m.group(0), (bid, m.start() / max(len(low), 1))))
    rec = [(w, t) for w, t in heard if w in ANCHOR_WORDS]
    n, m = len(script), len(rec)
    L = np.zeros((n + 1, m + 1), np.int32)
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            L[i, j] = L[i + 1, j + 1] + 1 if script[i][0] == rec[j][0] else max(L[i + 1, j], L[i, j + 1])
    i = j = 0
    out = {}
    while i < n and j < m:
        if script[i][0] == rec[j][0]:
            out.setdefault(script[i][1], []).append(rec[j][1])
            i += 1
            j += 1
        elif L[i + 1, j] >= L[i, j + 1]:
            i += 1
        else:
            j += 1
    return out


def line_starts(beats, heard, total):
    """{line index: estimated start time} for lines pinned by a recognised keyword, keeping only anchors whose
    implied pace (seconds per character since the previous anchor) is plausible. A keyword heard at time T,
    a fraction f into its line's text, puts the line's start at about T - f * (line length in seconds)."""
    ids = [b for b, _ in beats]
    text = dict(beats)
    chars = sum(len(t) for t in text.values())
    pace = total / chars
    raw = {}
    for (bid, f), times in line_anchors(beats, heard).items():
        est = min(times) - f * len(text[bid]) * pace
        raw.setdefault(bid, []).append(est)
    est = {ids.index(b): float(np.median(v)) for b, v in raw.items()}
    kept, last_k, last_t = {}, 0, 0.0
    for k in sorted(est):
        if k == 0:
            continue
        span_chars = sum(len(text[b]) for b in ids[last_k:k])
        r = (est[k] - last_t) / (span_chars * pace)
        if 0.72 < r < 1.4:
            kept[k] = est[k]
            last_k, last_t = k, est[k]
    return kept

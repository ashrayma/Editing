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
    script = [(w, bid) for bid, text in beats for w in re.findall(r"[a-z]+", text.lower()) if w in ANCHOR_WORDS]
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
    return {k: min(v) for k, v in out.items() if len(v) >= 1}

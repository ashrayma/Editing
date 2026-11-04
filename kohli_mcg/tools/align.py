"""Forced alignment of the Hinglish script to a recording with PocketSphinx (offline, bundled English model).

Words outside the English dictionary get an approximate pronunciation from a small romanised-Hindi
letter-to-phone mapping; numbers are spelled out in English. The alignment is constrained to the script order,
so approximate pronunciations only blur timings locally. Returns the start/end time of every line.
"""
import re

import numpy as np

DIG = "zero one two three four five six seven eight nine".split()
TEENS = "ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def num_words(n):
    n = int(n)
    if n < 10:
        return [DIG[n]]
    if n < 20:
        return [TEENS[n - 10]]
    if n < 100:
        return [TENS[n // 10]] + ([DIG[n % 10]] if n % 10 else [])
    if 1900 <= n <= 2099:                       # years: twenty twenty two
        return num_words(n // 100) + (num_words(n % 100) if n % 100 else ["hundred"])
    if n < 1000:
        return [DIG[n // 100], "hundred"] + (num_words(n % 100) if n % 100 else [])
    return num_words(n // 1000) + ["thousand"] + (num_words(n % 1000) if n % 1000 else [])


G2P = [("chh", "CH"), ("kh", "K"), ("gh", "G"), ("ch", "CH"), ("jh", "JH"), ("th", "T"), ("dh", "D"), ("ph", "F"),
       ("bh", "B"), ("sh", "SH"), ("aa", "AA"), ("ee", "IY"), ("oo", "UW"), ("ai", "AY"), ("au", "AW"), ("ei", "EY"),
       ("a", "AH"), ("e", "EY"), ("i", "IH"), ("o", "OW"), ("u", "UH"), ("k", "K"), ("g", "G"), ("j", "JH"),
       ("t", "T"), ("d", "D"), ("n", "N"), ("p", "P"), ("b", "B"), ("m", "M"), ("y", "Y"), ("r", "R"), ("l", "L"),
       ("v", "V"), ("w", "W"), ("s", "S"), ("h", "HH"), ("z", "Z"), ("f", "F"), ("q", "K"), ("x", "K S"), ("c", "K")]


def g2p(w):
    out, i = [], 0
    while i < len(w):
        for k, ph in G2P:
            if w.startswith(k, i):
                out.append(ph)
                i += len(k)
                break
        else:
            i += 1
    return " ".join(out) or "AH"


def tokens(text):
    out = []
    for t in re.findall(r"[A-Za-z]+|\d[\d,]*", text):
        if t[0].isdigit():
            out += num_words(t.replace(",", "")) if len(t.replace(",", "")) <= 4 else \
                [w for part in t.split(",") for w in num_words(part)]
        else:
            out.append(t.lower())
    return out


def align(raw16k, beats):
    """{line id: (start, end)} by forced alignment of the lines' text (in order) to 16 kHz mono int16 audio."""
    from pocketsphinx import Decoder
    d = Decoder(samprate=16000, bestpath=False, beam=1e-80, wbeam=1e-60, pbeam=1e-80)
    words, owner = [], []
    for bid, text in beats:
        for w in tokens(text):
            key = "x" + w if d.lookup_word(w) is None else w
            if key != w and d.lookup_word(key) is None:
                d.add_word(key, g2p(w), False)
            words.append(key)
            owner.append(bid)
    d.set_align_text(" ".join(words))
    d.start_utt()
    d.process_raw(raw16k, full_utt=True)
    d.end_utt()
    if d.hyp() is None:
        return {}
    segs = [s for s in d.seg() if not s.word.startswith(("<", "["))]
    times = {}
    k = 0
    for s in segs:
        w = s.word.split("(")[0]
        while k < len(words) and words[k] != w:
            k += 1
        if k == len(words):
            break
        a, b = s.start_frame / 100, s.end_frame / 100
        bid = owner[k]
        times[bid] = (min(times.get(bid, (a, b))[0], a), max(times.get(bid, (a, b))[1], b))
        k += 1
    return times


def align_chunked(raw16k, beats, expect, chunk=4):
    """Align `chunk` lines at a time. Each window runs from the current position to the expected end of the chunk
    plus slack; the window is grown until the alignment succeeds. The last line of each chunk is re-aligned as the
    first line of the next, so a chunk never has to end exactly at a line boundary."""
    sr2 = 32000                       # bytes per second (16 kHz int16)
    total = len(raw16k) / sr2
    ids = [b for b, _ in beats]
    out, pos, k = {}, 0.0, 0
    while k < len(ids):
        grp = beats[k:k + chunk]
        exp = sum(expect[b] for b, _ in grp)
        res = {}
        for slack in (1.25, 1.5, 1.9, 2.5):
            end = min(total, pos + exp * slack + 2.0)
            res = align(raw16k[int(pos * sr2) & ~1: int(end * sr2) & ~1], grp)
            if len(res) == len(grp):
                break
        if len(res) < len(grp) and len(grp) > 1:
            for n in (2, 1):                 # retry with fewer lines and a generous window
                g2 = beats[k:k + n]
                e2 = sum(expect[b] for b, _ in g2)
                for slack in (1.6, 2.2, 3.0):
                    r2 = align(raw16k[int(pos * sr2) & ~1: int(min(total, pos + e2 * slack + 3.0) * sr2) & ~1], g2)
                    if len(r2) == len(g2):
                        break
                if len(r2) == len(g2):
                    grp, res = g2, r2
                    break
        if len(res) < len(grp):
            pos += expect[ids[k]]            # give up on this line: move on by its expected length
            k += 1
            continue
        last = k + len(grp) - 1 if k + len(grp) >= len(ids) else k + len(grp) - 2
        for b, _ in grp[: last - k + 1]:
            if b in res:
                out[b] = (pos + res[b][0], pos + res[b][1])
        nxt = ids[last]
        pos = out[nxt][1] if nxt in out else pos + sum(expect[b] for b in ids[k:last + 1])
        k = last + 1
    return out

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
    if len(raw16k) < 32000 // 2:                 # less than half a second of audio: nothing to align
        return {}
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
    """Align `chunk` lines at a time with the tightest window that works (windows grow only on failure), using a
    pace that keeps updating from the lines already aligned. The last line of each window is re-aligned as the first
    of the next, since the aligner stretches a window's final word to fill whatever audio is left."""
    sr2 = 32000
    total = len(raw16k) / sr2
    ids = [b for b, _ in beats]
    text = dict(beats)
    pace = sum(expect.values()) / sum(len(t) for t in text.values())      # seconds per character, updated as we go
    done_chars, done_secs = 0, 0.0
    out, pos, k = {}, 0.0, 0
    while k < len(ids):
        res, grp = {}, []
        for n in (chunk, 2, 1):
            grp = beats[k:k + n]
            exp = sum(len(t) for _, t in grp) * pace
            for slack in (1.08, 1.2, 1.35, 1.55, 1.8):
                end = min(total, pos + exp * slack + 0.8)
                res = align(raw16k[int(pos * sr2) & ~1: int(end * sr2) & ~1], grp)
                if len(res) == len(grp):
                    break
            if len(res) == len(grp):
                break
        if len(res) < len(grp):
            pos += len(text[ids[k]]) * pace
            k += 1
            continue
        last = k + len(grp) - 1 if (k + len(grp) >= len(ids) or len(grp) == 1) else k + len(grp) - 2
        for b, _ in grp[: last - k + 1]:
            out[b] = (pos + res[b][0], pos + res[b][1])
            done_chars += len(text[b])
        done_secs = out[ids[last]][1]
        pace = 0.5 * pace + 0.5 * done_secs / max(done_chars, 1)
        pos = out[ids[last]][1]
        k = last + 1
    return out


def align_anchored(raw16k, beats, starts):
    """Align lines between consecutive anchored line starts ({line index: time}); each window holds exactly its
    lines, so errors cannot carry past an anchor. Windows that won't align fall back to align_chunked inside."""
    sr2 = 32000
    total = len(raw16k) / sr2
    ids = [b for b, _ in beats]
    marks = [(0, 0.0)] + sorted(starts.items()) + [(len(ids), total)]
    out = {}
    for (k0, t0), (k1, t1) in zip(marks, marks[1:]):
        if k1 <= k0:
            continue
        a, b = max(0.0, t0 - 0.3), min(total, t1 + 0.3)
        grp = beats[k0:k1]
        res = align(raw16k[int(a * sr2) & ~1: int(b * sr2) & ~1], grp) if len(grp) <= 8 else {}
        if len(res) < len(grp):
            seg = raw16k[int(a * sr2) & ~1: int(b * sr2) & ~1]
            chars = sum(len(t) for _, t in grp)
            res = align_chunked(seg, grp, {x: (b - a) * len(t) / chars for x, t in grp})
        for x, (s0, s1) in res.items():
            out[x] = (a + s0, a + s1)
    return out

#!/usr/bin/env python3
"""Phrase timings for the Dada 51* voiceover (vo/vo_raw.m4a, the creator's own recording) -> vo/timings.json.

Same method as sandpaper/align_vo.py: speech chunks from silence detection; anchors where the English recogniser
(pocketsphinx) caught a word ("fifty one", "statement", "World Cup", "subscribes"); between anchors the phrases are
fitted to the chunks by dynamic programming so each phrase's length matches its character count.
"""
import json
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
VO = os.path.join(HERE, "vo", "vo_raw.m4a")

LINES = [
    "Koi mujhse pooche, meri favourite Test innings kaunsi hai?",           # 0
    "Main bolunga: Sourav Ganguly, 51 not out.",                            # 1
    "Log hasenge.",                                                          # 2
    "Bhai, yahan log 200, 300 maar dete hain... aur tum 51 pe atke ho?",     # 3
    "Toh suno. Ye 51 runs nahi the.",                                        # 4
    "Ye ek statement tha.",                                                  # 5
    "2003 World Cup final tak team ko le gaye.",                             # 6
    "Poora desh pyaar se Dada bulata tha.",                                  # 7
    "Phir naya coach aata hai, Greg Chappell.",                              # 8
    "Ek email leak hota hai.",                                               # 9
    "Captaincy jaati hai... aur phir team se bhi bahar.",                    # 10
    "Sab bolte hain: Dada khatam.",                                          # 11
    "Ab wapas nahi aayega.",                                                 # 12
    "Lagbhag ek saal baad, South Africa mein India buri tarah haar rahi thi.",  # 13
    "Aur selectors ne phir se Dada ko bulaya.",                              # 14
    "Johannesburg, December 2006.",                                          # 15
    "Hari pitch.",                                                           # 16
    "Saamne Pollock, Steyn, Ntini, Nel aur Kallis.",                         # 17
    "Sirf pace.",                                                            # 18
    "Sehwag out. Sachin out. Dravid out.",                                   # 19
    "110 pe 4.",                                                             # 20
    "Aur andar aaye... Sourav Ganguly.",                                     # 21
    "Aage kya hua, jaanne se pehle...",                                      # 22
    "agar aap sachche cricket fan ho, toh channel ko subscribe zaroor karna.",  # 23
    "101 balls. Har ball pe khatra.",                                        # 24
    "Aur Dada? 51 not out.",                                                 # 25
    "Team ke top scorer.",                                                   # 26
    "India 249 pe all out.",                                                 # 27
    "Phir Sreesanth ke 5 wicket...",                                         # 28
    "aur South Africa sirf 84 pe all out.",                                  # 29
    "India ne jeeta South Africa mein apna pehla Test. Ever.",               # 30
    "Ye 51 runs nahi the.",                                                  # 31
    "Ye Dada ka jawab tha, har us insaan ko jisne bola tha: Dada khatam.",   # 32
    "Dada ka 51 ya Laxman ka 281?",                                          # 33
    "Comment karo.",                                                         # 34
]
# line index -> time the line starts (s), from words the recogniser caught
ANCHORS = {1: 4.83, 5: 16.4, 6: 18.21, 22: 59.86, 23: 61.1, 24: 65.24, 34: 90.64}  # a line start inside a chunk splits it


def chunks():
    out = subprocess.run(["ffmpeg", "-i", VO, "-af", "silencedetect=n=-30dB:d=0.12", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", out)]
    en = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", out)]
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", VO],
                               capture_output=True, text=True).stdout)
    starts = [0.0] + en
    ends = st + [dur]
    return [(a, b) for a, b in zip(starts, ends) if b - a > 0.12], dur


def fit(lines, cks):
    """Split chunk list into len(lines) consecutive groups; group duration ~ chars."""
    n, m = len(lines), len(cks)
    if m < n:
        raise SystemExit(f"only {m} chunks for {n} lines")
    total_c = sum(len(l) for l in lines)
    total_d = cks[-1][1] - cks[0][0]
    want = [len(l) / total_c * total_d for l in lines]
    INF = float("inf")
    best = [[INF] * (m + 1) for _ in range(n + 1)]
    prev = [[0] * (m + 1) for _ in range(n + 1)]
    best[0][0] = 0
    for i in range(1, n + 1):
        for j in range(i, m - (n - i) + 1):
            for k in range(i - 1, j):
                if best[i - 1][k] == INF:
                    continue
                d = cks[j - 1][1] - cks[k][0]
                c = best[i - 1][k] + (d - want[i - 1]) ** 2
                if c < best[i][j]:
                    best[i][j], prev[i][j] = c, k
    j, cuts = m, []
    for i in range(n, 0, -1):
        k = prev[i][j]
        cuts.append((k, j))
        j = k
    return [(cks[a][0], cks[b - 1][1]) for a, b in reversed(cuts)]


def main():
    cks, dur = chunks()
    cks = [c for c in cks if not (c[0] == 0.0 and c[1] - c[0] < 0.3)]
    for t in ANCHORS.values():                      # anchors split the chunk they fall in
        for k, (a, b) in enumerate(cks):
            if a + 0.1 < t < b - 0.1:
                cks[k:k + 1] = [(a, t - 0.02), (t, b)]
                break

    def chunk_at(t):
        return min(range(len(cks)), key=lambda i: abs(cks[i][0] - t))

    bounds = [0] + sorted(ANCHORS) + [len(LINES)]
    cpos = [0] + [chunk_at(ANCHORS[k]) for k in sorted(ANCHORS)] + [len(cks)]
    times = []
    for (l0, l1), (c0, c1) in zip(zip(bounds, bounds[1:]), zip(cpos, cpos[1:])):
        if l1 > l0:
            times += fit(LINES[l0:l1], cks[c0:c1])
    res = [{"i": i, "start": round(a, 2), "end": round(b, 2), "text": t} for i, ((a, b), t) in enumerate(zip(times, LINES))]
    json.dump({"duration": dur, "lines": res}, open(os.path.join(HERE, "vo", "timings.json"), "w"), indent=1)
    for r in res:
        print(f"{r['i']:2d} {r['start']:6.2f}-{r['end']:6.2f}  {r['text'][:70]}")
    print(len(cks), "chunks")


if __name__ == "__main__":
    main()

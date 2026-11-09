#!/usr/bin/env python3
"""Line-level timings for the Hinglish voiceover (vo/vo_raw.mp3) -> vo/timings.json.

English speech recognition can't read Hinglish, but it does catch names (Bancroft, Warner, Sabr, "press
conference", walkie-talkie, notes). Those give anchor points; between anchors, script lines are fitted to the
silence-separated speech chunks by dynamic programming, so each line's length matches its character count.
"""
import json
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
VO = os.path.join(HERE, "vo", "vo_raw.mp3")

LINES = [
    "Ek chhota sa peela tukda.", "Hatheli se bhi chhota.",
    "Par usi tukde ne Australian cricket ka poora ghamand chheel ke rakh diya.", "Cape Town, 2018.",
    "Bancroft ball ragad raha hai,", "camera sab dekh raha hai,", "aur replay seedha stadium ki badi screen par!",
    "Camera ghoomta hai coach Lehmann ki taraf.", "Walkie-talkie uthta hai.",
    "Sandesh pahunchta hai 12th man Handscomb tak.", "Bancroft ghabra ke sandpaper daal leta hai patloon ke andar!",
    "Umpire aate hain toh jeb se nikalta hai kaala chashme wala kapda.",
    "Bhai, itni tez acting toh Bollywood mein bhi nahi hoti.", "Ban lage sirf teen par: Smith, Warner aur Bancroft.",
    "Lehmann ko jaanch ne clean chit di, phir bhi unhone coach ki kursi chhod di.",
    "Dressing room mein sannata chha gaya.", "Aur us sannate ke beech ek banda chup-chaap likh raha tha.",
    "Usman Khawaja.", "Cape Town ke kuch hi din baad usne sab kuch kaagaz par utaar liya.",
    "Phir aath saal tak woh kaagaz dabaye baitha raha.", "Aur kitaab ka naam kya rakha? Sabr.",
    "Ab shuru hota hai asli tamasha.",
    "Lehmann radio par aate hain aur taana maarte hain ki kitaabein toh bikne ke liye hi hoti hain.",
    "Matlab, paison ke liye muh khola hai.", "Kuch hi ghanton mein Khawaja phone uthata hai.",
    "Na press conference, na PR team.", "Peeche ped, saamne seedhi baat:",
    "sabko pata tha, is baat se woh inkaar nahi karega.", "Phir aata hai asli chhakka.",
    "Meri kahani par shak karna hai, shauk se karo.", "Par meri yaaddasht par? Na bhai na, sab likha hua hai.",
    "Khawaja ka daawa hai ki match ke baad usne poori team se kaha tha, galti sabki hai, saath mein jhelenge.",
    "Uske mutabik do senior khiladiyon ne yeh hone hi nahi diya.",
    "Naam? Abhi tak do khaali chehre aur do bade question mark.",
    "Aur 2021 mein jab chaar star bowlers ne kaha ki unhe kuch pata hi nahi tha, tab Khawaja chup kyun raha?",
    "Jawab sabse zyada chubhta hai.", "Khud bolta hai, chicken bol lo mujhe.",
    "Team mein tha, jung ladne ka dum nahi tha.", "Par ruko, picture abhi baaki hai.",
    "Lehmann aaj bhi kehte hain ki unhe plan ka kuch nahi pata tha, aur chaaron bowlers bhi yahi kehte hain.",
    "Cricket Australia ki jaanch ka record aaj bhi yahi hai ki baaki kisi khiladi ko plan ki bhanak nahi thi.",
    "Aur CA ke hisaab se walkie-talkie par koi warning nahi gayi thi, Lehmann ne bas gaali ke saath poocha tha ki yeh ho kya raha hai.",
    "Toh ek taraf official file.", "Doosri taraf ek aadmi ke aath saal purane notes.",
    "Asli sach shayad sirf us dressing room ki deewaron ko pata hai.", "Khawaja ya Lehmann? Aapka verdict kya hai?",
]
# line index -> chunk start (s), from words the recogniser caught
ANCHORS = {4: 11.11, 13: 39.12, 20: 62.69, 25: 78.85, 41: 143.84, 43: 157.10, 45: 165.62}


def chunks():
    out = subprocess.run(["ffmpeg", "-i", VO, "-af", "silencedetect=n=-38dB:d=0.22", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", out)]
    en = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", out)]
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", VO],
                               capture_output=True, text=True).stdout)
    starts = [0.0] + en
    ends = st + [dur]
    return [(a, b) for a, b in zip(starts, ends) if b - a > 0.15], dur


def fit(lines, cks):
    """Split chunk list into len(lines) consecutive groups; group duration ~ chars."""
    n, m = len(lines), len(cks)
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
    idx = {round(a, 2): i for i, (a, _) in enumerate(cks)}

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
        print(f"{r['i']:2d} {r['start']:7.2f}-{r['end']:7.2f}  {r['text'][:70]}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Merge the 16 recorded inserts (vo/inserts_raw.mp3) into the original voiceover (vo/vo_raw.mp3).

    python3 merge_vo.py  ->  vo/vo_full.wav + vo/timings_full.json

ElevenLabs ignored the 2-second gaps between inserts, so each insert's boundaries come from the same method as the
line alignment: speech chunks + recognised anchor words (T20, bowling machine, fantasy apps, strategic timeout…)
+ fitting the remaining inserts by text length. Inserts go in at sentence boundaries of the original (timings.json).
"""
import json
import os
import subprocess
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "sandpaper"))
import align_vo as base  # noqa: E402

INSERTS = [
    "Ek waqt tha jab IPL ka last over dekhne ke liye log khaana chhod dete the. Ghar mein sab ek TV ke saamne, aur har ball pe saans rukti thi. Aaj? Aadhe log second screen pe hain. Match chal raha hai, lekin dhyaan kahin aur hai.",
    "Aur yeh sirf ek feeling nahi hai. Jab har dusre match mein 200 ban raha ho, toh 200 special nahi rehta. Jo cheez roz hoti hai, woh yaad nahi rehti.",
    "Toh chalo, case kholte hain. Ek-ek suspect ko bulayenge, sawaal poochenge, aur dekhenge ki asli gunehgaar kaun hai. Aur haan, end tak rukna, kyunki jawab wahi milega.",
    "Rule 2023 mein aaya. Idea achha tha: zyada players ko mauka, match mein zyada strategy. Toss ke baad ek player badal sakte ho, situation ke hisaab se. Kaagaz pe yeh smart lagta hai.",
    "Socho, pehle ek team ke liye 6 wicket gire matlab match khatam. Number 7, 8 pe bowlers aate the, jo bas bat ghuma ke bhaag jaate the. Aaj number 8 pe ek proper batter khada hai. Toh top order ko rukne ki zaroorat hi nahi. Pehli ball se attack. Aur bowler? Usko pata hai, wicket lene ke baad bhi raahat nahi milegi.",
    "Aur yeh sirf mera opinion nahi hai. Rohit Sharma ne khud kaha tha ki woh is rule ke fan nahi hain, kyunki isse all-rounders ka development rukta hai. Socho, jo player kal India ke liye bat aur ball dono kar sakta tha, usko aaj IPL mein bowling hi nahi mil rahi.",
    "Toh haan, Impact Player guilty hai. Runs badhaaye, risk badhaaya, balance bigaada. Lekin agar yahi akela culprit hota, toh kahani yahin khatam ho jaati.",
    "T20 ek bowler ke liye pehle hi mushkil format hai. Chaar over, field restrictions, chhoti boundaries. Bowler ke paas bas ek cheez bachti thi: pitch se thodi madad. Thoda swing, thoda turn, thoda uneven bounce. Wahi uska hathiyaar tha.",
    "Aur jab pitch se madad hi khatam ho jaaye, toh bowler sirf ek bowling machine ban jaata hai. Har ball ek hi height pe, ek hi speed pe aati hai. Batter ko bas line mein khada rehna hai. Skill kam, guesswork zyada.",
    "Yaad karo woh matches jahan 140 bhi defend ho gaya. Woh low-scoring thrillers aaj bhi log yaad karte hain. Kyunki wahan har run kamaana pada tha, aur har wicket ka matlab tha.",
    "Fantasy apps ne cricket ko ek naya audience diya, yeh sach hai. Jo log pehle cricket nahi dekhte the, woh bhi aaj team banate hain. Lekin unhone dekhne ka tareeka bhi badal diya.",
    "Pehle fan sochta tha, meri team jeetegi ya nahi. Ab sochta hai, mere captain ko kitne points mile. Ek bowler ka maiden over, jo pehle standing ovation laata tha, aaj fantasy mein bas kuch points hai. Aur ek scrappy 20 run ki innings, jo match jita de? Usse koi fantasy team nahi jeet-ti.",
    "Aaj IPL duniya ki sabse bade cricket leagues mein se ek hai. Media rights ke liye hazaaron crore lag rahe hain. Aur jab itna paisa lagta hai, toh har second ko bechna padta hai.",
    "Strategic timeout, innings break, har wicket ke baad replay ke saath ad. Match ki speed broadcast decide karta hai, cricket nahi. Aur sabse zyada kya bikta hai? Chhakka. Highlight mein chhakka chalta hai, reel mein chhakka chalta hai, ad mein chhakka chalta hai. Ek perfect yorker ka koi sponsor nahi hota.",
    "Socho. Board ko zyada viewers chahiye. Broadcaster ko zyada ad slots chahiye. Fantasy apps ko zyada points chahiye. Aur sabko ek hi cheez dene ka sabse aasaan tareeka hai: runs. Zyada runs.",
    "Purane IPL ki woh raatein yaad karo. Last over, 12 run chahiye, aur bowler ne yorker pe yorker daal ke match bacha liya. Stadium khada ho gaya tha. Woh drama runs se nahi, mukaable se aata tha.",
]
ANCHORS = {1: 16.55, 3: 39.24, 6: 91.90, 7: 102.86, 8: 119.95, 9: 134.06, 10: 146.19, 12: 177.43, 13: 188.96,
           14: 210.08, 15: 224.15}
# where each insert goes: (original line index it follows, or (line, split time) inside a line)
PLACE = [("after", 1), ("after", 6), ("after", 7), ("at", 44.33), ("after", 11), ("after", 12), ("after", 13),
         ("after", 16), ("after", 18), ("after", 20), ("after", 23), ("after", 26), ("after", 29), ("after", 31),
         ("after", 35), ("after", 40)]
PAUSE = 0.45   # breath around each insert
SR = 44100


def load(p):
    tmp = os.path.join(HERE, "vo", "_tmp.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", p, "-ar", str(SR), "-ac", "1", tmp], check=True)
    with wave.open(tmp) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    os.remove(tmp)
    return x


def main():
    base.HERE = HERE
    base.VO = os.path.join(HERE, "vo", "inserts_raw.mp3")
    base.LINES = INSERTS
    base.ANCHORS = ANCHORS
    cks, dur = base.chunks()

    def chunk_at(t):
        return min(range(len(cks)), key=lambda i: abs(cks[i][0] - t))

    bounds = [0] + sorted(ANCHORS) + [len(INSERTS)]
    cpos = [0] + [chunk_at(ANCHORS[k]) for k in sorted(ANCHORS)] + [len(cks)]
    spans = []
    for (l0, l1), (c0, c1) in zip(zip(bounds, bounds[1:]), zip(cpos, cpos[1:])):
        if l1 > l0:
            spans += base.fit(INSERTS[l0:l1], cks[c0:c1])
    for i, (a, b) in enumerate(spans):
        print(f"I{i + 1:<2d} {a:7.2f}-{b:7.2f}  {INSERTS[i][:60]}")

    orig = json.load(open(os.path.join(HERE, "vo", "timings.json")))
    lines = orig["lines"]
    vo = load(os.path.join(HERE, "vo", "vo_raw.mp3"))
    ins = load(os.path.join(HERE, "vo", "inserts_raw.mp3"))

    # cut points in the original where an insert goes
    cuts = []
    for k, (kind, v) in enumerate(PLACE):
        if kind == "after":
            t = (lines[v]["end"] + lines[v + 1]["start"]) / 2
        else:
            t = v
        cuts.append((t, k))
    cuts.sort()

    def fade(x, n=int(0.01 * SR)):
        x = x.copy()
        if len(x) > 2 * n:
            x[:n] *= np.linspace(0, 1, n)
            x[-n:] *= np.linspace(1, 0, n)
        return x

    out, pos, shift = [], 0.0, []
    tcur = 0.0
    for t, k in cuts:
        seg = vo[int(pos * SR):int(t * SR)]
        out.append(fade(seg))
        tcur += len(seg) / SR
        a, b = spans[k]
        piece = ins[int(max(0, a - 0.05) * SR):int(min(dur, b + 0.08) * SR)]
        gap = np.zeros(int(PAUSE * SR), np.float32)
        out += [gap, fade(piece), gap]
        ins_start = tcur + PAUSE
        tcur += 2 * PAUSE + len(piece) / SR
        shift.append((t, tcur - t, k, ins_start, ins_start + len(piece) / SR))
        pos = t
    out.append(fade(vo[int(pos * SR):]))
    full = np.concatenate(out)

    def new_t(t):
        s = 0.0
        for c, sh, _, _, _ in shift:
            if t >= c:
                s = sh
        return t + s

    new_lines = [{**ln, "start": round(new_t(ln["start"]), 2), "end": round(new_t(ln["end"]), 2)} for ln in lines]
    inserts = [{"i": k, "start": round(a, 2), "end": round(b, 2), "text": INSERTS[k]}
               for _, _, k, a, b in sorted(shift, key=lambda x: x[2])]
    with wave.open(os.path.join(HERE, "vo", "vo_full.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(full, -1, 1) * 32767).astype(np.int16).tobytes())
    json.dump({"duration": len(full) / SR, "lines": new_lines, "inserts": inserts},
              open(os.path.join(HERE, "vo", "timings_full.json"), "w"), indent=1)
    print(f"full VO {len(full) / SR:.1f}s")


if __name__ == "__main__":
    main()

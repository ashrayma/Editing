#!/usr/bin/env python3
"""Forced-align the voice note against the script, piece by piece -> out/words.json (raw-file seconds).

Needs `pip install pocketsphinx` (bundles its English model; no download).
"""
import json, os, subprocess, sys, wave
import numpy as np
import pocketsphinx
from pocketsphinx import Decoder

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from edl import RAW, PIECES  # noqa: E402

M = pocketsphinx.get_model_path() + "/en-us/"
EXTRA = {"thala": "T AA L AH", "chinna": "CH IH N AH", "dhoni": "D OW N IY", "yuvraj": "Y UW V R AA JH",
         "csk": "S IY EH S K EY", "ipl": "AY P IY EH L", "ipl's": "AY P IY EH L Z"}


def main():
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    tmp = os.path.join(HERE, "out", "vo16.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(HERE, RAW), "-ar", "16000", "-ac", "1", tmp], check=True)
    w = wave.open(tmp, "rb")
    a = np.frombuffer(w.readframes(w.getnframes()), np.int16)
    cmu = {}
    for line in open(M + "cmudict-en-us.dict"):
        p = line.split()
        cmu.setdefault(p[0], " ".join(p[1:]))
    words = {x for p in PIECES for x in p["say"].split()}
    dic = os.path.join(HERE, "out", "vo.dict")
    with open(dic, "w") as f:
        for x in sorted(words):
            f.write(f"{x} {EXTRA.get(x) or cmu[x]}\n")
    gram = os.path.join(HERE, "out", "p.gram")
    out = []
    for p in PIECES:
        s, t = p["src"]
        open(gram, "w").write("#JSGF V1.0;\ngrammar p;\npublic <s> = " + p["say"] + ";\n")
        d = Decoder(hmm=M + "en-us", jsgf=gram, dict=dic, samprate=16000, loglevel="FATAL")
        d.start_utt()
        d.process_raw(a[int(s * 16000):int(t * 16000)].tobytes(), full_utt=True)
        d.end_utt()
        segs = [(x.word.split("(")[0], s + x.start_frame / 100, s + (x.end_frame + 1) / 100)
                for x in d.seg() if not x.word.startswith(("<", "["))]
        ok = [x[0] for x in segs] == p["say"].split()
        print(("OK  " if ok else "MISS"), p["id"], " ".join(f"{w}@{a0:.2f}" for w, a0, _ in segs))
        out.append({"id": p["id"], "words": segs})
    json.dump(out, open(os.path.join(HERE, "out", "words.json"), "w"), indent=1)


if __name__ == "__main__":
    main()

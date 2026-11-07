#!/usr/bin/env python3
"""Word-level timestamps for a raw take (offline zipformer transducer via sherpa-onnx).

    python3 words.py vo_raw/a.m4a [from to]  ->  out/words_<take>.json + printout "t  word"
Whisper (transcribe.py) gives the cleaner text; this gives where each word starts, for exact cut points.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from transcribe import decode  # noqa: E402

M = os.path.join(HERE, "models", "sherpa-onnx-zipformer-en-2023-06-26")


def main():
    import sherpa_onnx
    rec = sherpa_onnx.OfflineRecognizer.from_transducer(
        encoder=f"{M}/encoder-epoch-99-avg-1.int8.onnx", decoder=f"{M}/decoder-epoch-99-avg-1.int8.onnx",
        joiner=f"{M}/joiner-epoch-99-avg-1.int8.onnx", tokens=f"{M}/tokens.txt", num_threads=4)
    path = sys.argv[1]
    a = decode(path, 16000)
    words, chunk = [], 20.0  # decode in overlapping chunks; keep words from each chunk's middle
    t = 0.0
    while t < len(a) / 16000:
        s0 = max(0.0, t - 2.0)
        st = rec.create_stream()
        st.accept_waveform(16000, a[int(s0 * 16000): int((t + chunk + 2.0) * 16000)])
        rec.decode_stream(st)
        r = st.result
        cur = None
        for tok, ts in zip(r.tokens, r.timestamps):
            at = s0 + ts
            if tok.startswith((" ", "▁")) or cur is None:
                if cur and t <= cur[0] < t + chunk:
                    words.append(cur)
                cur = [round(at, 2), tok.strip().lstrip("▁")]
            else:
                cur[1] += tok
        if cur and t <= cur[0] < t + chunk:
            words.append(cur)
        t += chunk
    name = os.path.splitext(os.path.basename(path))[0]
    json.dump(words, open(os.path.join(HERE, "out", f"words_{name}.json"), "w"))
    line = []
    for w in words:
        line.append(f"{w[0]:.2f} {w[1].lower()}")
    print("\n".join(line))


if __name__ == "__main__":
    main()

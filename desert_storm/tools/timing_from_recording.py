#!/usr/bin/env python3
"""Drop in your own voice recording: transcribe it, align it to script.json line by
line, and write timing.json so every caption, photo, card and sound cue follows your
delivery.

  python3 tools/timing_from_recording.py my_voice.m4a     # any audio or video file
  python3 tools/build.py && python3 tools/layout_audit.py

Silero VAD (and Whisper for --mode words) run offline through sherpa-onnx; models come from the
sherpa-onnx GitHub releases (see README). Read the lines in order with a short breath
between them; the default --mode pauses finds those breaks, so it works for Hinglish.
Times are relative to the start of your voice file; build.py places the voice right
after the hook clip.
"""
import argparse, difflib, json, os, re, subprocess, sys, tempfile, wave
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILM = os.path.join(ROOT, "film")
MODELS = os.environ.get("WHISPER_MODELS", os.path.join(ROOT, "models"))


def norm(w):
    w = w.lower().replace("\u093c", "")  # drop the nukta so ज़ and ज match
    return re.sub(r"[^a-z0-9\u0900-\u097f]", "", w)


def load_wav(wav):
    w = wave.open(wav)
    return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768, w.getframerate()


def speech_segments(a, sr):
    """Silero VAD: [(start, end, samples)] for every stretch of speech, split at pauses of 80 ms or more."""
    import sherpa_onnx
    cfg = sherpa_onnx.VadModelConfig()
    cfg.silero_vad.model = os.path.join(MODELS, "silero_vad.onnx")
    cfg.silero_vad.min_silence_duration = 0.08
    cfg.silero_vad.max_speech_duration = 6
    cfg.sample_rate = sr
    vad = sherpa_onnx.VoiceActivityDetector(cfg, buffer_size_in_seconds=600)
    segs = []

    def drain():
        while not vad.empty():
            t0 = vad.front.start / sr
            segs.append((t0, t0 + len(vad.front.samples) / sr, np.array(vad.front.samples)))
            vad.pop()
    for i in range(0, len(a), cfg.silero_vad.window_size):
        vad.accept_waveform(a[i:i + cfg.silero_vad.window_size])
        drain()
    vad.flush()
    drain()
    return segs


def align_pauses(lines, segs, expected):
    """Language-independent: pick the line breaks among the pauses so each line's length best
    fits its expected length (scaled to your pace), preferring longer pauses as breaks."""
    L, N = len(lines), len(segs)
    if N < L:
        raise SystemExit(f"only {N} speech stretches for {L} lines: leave a short pause between lines and try again")
    span = segs[-1][1] - segs[0][0]
    k = span / (sum(expected) + 0.15 * (L - 1))
    gap = [0.0] + [segs[i][0] - segs[i - 1][1] for i in range(1, N)]
    INF = float("inf")
    dp = [[INF] * (N + 1) for _ in range(L + 1)]
    back = [[0] * (N + 1) for _ in range(L + 1)]
    dp[0][0] = 0.0
    for l in range(L):
        want = k * expected[l]
        for n in range(l + 1, N - (L - l - 1) + 1):
            best, arg = INF, 0
            for j in range(l, n):
                if dp[l][j] == INF:
                    continue
                dur = segs[n - 1][1] - segs[j][0]
                c = dp[l][j] + 10 * ((dur - want) / want) ** 2 - (3 * min(gap[j], 0.8) if j else 0)
                if c < best:
                    best, arg = c, j
            dp[l + 1][n], back[l + 1][n] = best, arg
    cuts, n = [], N
    for l in range(L, 0, -1):
        j = back[l][n]
        cuts.append((j, n))
        n = j
    cuts.reverse()
    return [{"id": line["id"], "start": round(segs[j][0], 3), "end": round(segs[n - 1][1], 3)} for line, (j, n) in zip(lines, cuts)]


def transcribe(a, sr, segs, language):
    import sherpa_onnx
    m = os.path.join(MODELS, "sherpa-onnx-whisper-small")
    rec = sherpa_onnx.OfflineRecognizer.from_whisper(
        encoder=f"{m}/small-encoder.int8.onnx", decoder=f"{m}/small-decoder.int8.onnx",
        tokens=f"{m}/small-tokens.txt", language=language, task="transcribe", num_threads=4)
    words = []  # (word, start, end), spread across each VAD segment by character count
    for t0, _, s in segs:
        st = rec.create_stream()
        st.accept_waveform(sr, s)
        rec.decode_stream(st)
        toks = st.result.text.split()
        dur = len(s) / sr
        total = sum(len(t) + 1 for t in toks) or 1
        acc = t0
        for t in toks:
            d = dur * (len(t) + 1) / total
            words.append((t, acc, acc + d))
            acc += d
        print(f"[{t0:6.2f}] {st.result.text}", file=sys.stderr)
    return words


def align(lines, words):
    key = "tts" if any(re.search(r"[\u0900-\u097f]", w[0]) for w in words) else "text"
    sw = [(norm(w), li) for li, l in enumerate(lines) for w in l.get(key, l["text"]).split() if norm(w)]
    tw = [norm(w[0]) for w in words]
    sm = difflib.SequenceMatcher(None, [s[0] for s in sw], tw, autojunk=False)
    hits = {}  # line index -> list of (start, end)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            li = sw[blk.a + k][1]
            _, s, e = words[blk.b + k]
            hits.setdefault(li, []).append((s, e))
    out = []
    for li, l in enumerate(lines):
        if li in hits:
            out.append({"id": l["id"], "start": round(min(h[0] for h in hits[li]), 3), "end": round(max(h[1] for h in hits[li]), 3)})
        else:
            out.append({"id": l["id"], "start": None, "end": None})
    # lines Whisper missed: fill the gap between their neighbours
    for i, o in enumerate(out):
        if o["start"] is None:
            prev = next((out[j]["end"] for j in range(i - 1, -1, -1) if out[j]["end"] is not None), 0.3)
            nxt = next((out[j]["start"] for j in range(i + 1, len(out)) if out[j]["start"] is not None), prev + 2)
            o["start"], o["end"] = round(prev + 0.1, 3), round(max(prev + 0.6, nxt - 0.1), 3)
            print(f"warning: line '{o['id']}' not heard clearly, timed between its neighbours", file=sys.stderr)
    for a, b in zip(out, out[1:]):  # no overlaps
        a["end"] = min(a["end"], b["start"] - 0.02)
    return out


def probe(path, entry):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", entry, "-of", "csv=p=0", path], capture_output=True, text=True)
    return r.stdout.strip()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("take")
    ap.add_argument("--mode", choices=["pauses", "words"], default="pauses",
                    help="pauses: language-independent, fits line breaks to your pauses (best for Hinglish); "
                         "words: Whisper transcription matched word by word (good for English takes)")
    ap.add_argument("--language", default="en", help="whisper language for --mode words")
    args = ap.parse_args()
    script = json.load(open(os.path.join(ROOT, "script.json")))
    os.makedirs(os.path.join(FILM, "assets/audio"), exist_ok=True)
    timing = {"source": os.path.basename(args.take)}
    # voice only (a video's picture is ignored): clean low rumble, loudness to -14 LUFS for social
    dst = os.path.join(FILM, "assets/audio/voice.m4a")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", args.take, "-vn", "-af", "highpass=f=80,loudnorm=I=-14:TP=-1.5:LRA=9",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", dst], check=True)
    timing["audio"] = "assets/audio/voice.m4a"
    timing["duration"] = round(float(probe(dst, "format=duration")), 3)
    with tempfile.TemporaryDirectory() as td:
        wav = os.path.join(td, "a.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", dst, "-ac", "1", "-ar", "16000", wav], check=True)
        a, sr = load_wav(wav)
    segs = speech_segments(a, sr)
    if args.mode == "words":
        timing["lines"] = align(script["lines"], transcribe(a, sr, segs, args.language))
    else:
        ref = os.path.join(ROOT, "timing_scratch.json")
        if os.path.exists(ref):
            exp = {l["id"]: l["end"] - l["start"] for l in json.load(open(ref))["lines"]}
            expected = [exp.get(l["id"], len(l["text"]) / 14) for l in script["lines"]]
        else:
            expected = [len(l["text"]) / 14 for l in script["lines"]]  # ~14 characters a second
        timing["lines"] = align_pauses(script["lines"], segs, expected)
    for l in timing["lines"]:
        print(f"  {l['id']:<10} {l['start']:6.2f} - {l['end']:6.2f}")
    json.dump(timing, open(os.path.join(ROOT, "timing.json"), "w"), indent=1)
    print(f"timing.json written from your take ({timing['duration']}s, {len(timing['lines'])} lines). Now: python3 tools/build.py")

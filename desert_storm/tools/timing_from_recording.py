#!/usr/bin/env python3
"""Drop in your own voice recording: transcribe it, align it to script.json line by
line, and write timing.json so every caption, photo, card and sound cue follows your
delivery.

  python3 tools/timing_from_recording.py my_voice.m4a     # any audio or video file
  python3 tools/build.py && python3 tools/layout_audit.py

Whisper (small, multilingual) runs offline through sherpa-onnx; models come from the
sherpa-onnx GitHub releases (see README). Say the lines roughly as written: you can
ad-lib, the alignment only needs most words of each line to match.
"""
import argparse, difflib, json, os, re, subprocess, sys, tempfile, wave
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILM = os.path.join(ROOT, "film")
MODELS = os.environ.get("WHISPER_MODELS", os.path.join(ROOT, "models"))


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def transcribe(wav, language):
    import sherpa_onnx
    w = wave.open(wav)
    sr = w.getframerate()
    a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    m = os.path.join(MODELS, "sherpa-onnx-whisper-small")
    rec = sherpa_onnx.OfflineRecognizer.from_whisper(
        encoder=f"{m}/small-encoder.int8.onnx", decoder=f"{m}/small-decoder.int8.onnx",
        tokens=f"{m}/small-tokens.txt", language=language, task="transcribe", num_threads=4)
    cfg = sherpa_onnx.VadModelConfig()
    cfg.silero_vad.model = os.path.join(MODELS, "silero_vad.onnx")
    cfg.silero_vad.min_silence_duration = 0.08
    cfg.silero_vad.max_speech_duration = 6
    cfg.sample_rate = sr
    vad = sherpa_onnx.VoiceActivityDetector(cfg, buffer_size_in_seconds=600)
    segs = []
    for i in range(0, len(a), cfg.silero_vad.window_size):
        vad.accept_waveform(a[i:i + cfg.silero_vad.window_size])
        while not vad.empty():
            segs.append((vad.front.start / sr, np.array(vad.front.samples)))
            vad.pop()
    vad.flush()
    while not vad.empty():
        segs.append((vad.front.start / sr, np.array(vad.front.samples)))
        vad.pop()
    words = []  # (word, start, end), spread across each VAD segment by character count
    for t0, s in segs:
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
    sw = [(norm(w), li) for li, l in enumerate(lines) for w in l["text"].split() if norm(w)]
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
    ap.add_argument("--language", default="en", help="whisper language; for Hinglish takes try 'hi' and keep script.json in the same script")
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
        words = transcribe(wav, args.language)
    timing["lines"] = align(script["lines"], words)
    json.dump(timing, open(os.path.join(ROOT, "timing.json"), "w"), indent=1)
    print(f"timing.json written from your take ({timing['duration']}s, {len(timing['lines'])} lines). Now: python3 tools/build.py")

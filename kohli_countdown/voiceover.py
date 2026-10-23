#!/usr/bin/env python3
"""Build the voiceover track: one WAV per scene in out/vo/, plus manifest.json with durations.

Per scene, `vo_file` (your own recording, any format ffmpeg reads) wins; otherwise the
line in `vo_text` is spoken by the offline Kokoro TTS model (Hindi voice).

    python3 voiceover.py [config.json]

Kokoro model files (~350 MB) go in models/ — see README.
"""
import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 44100


def scenes(cfg):
    """(manifest key, scene) for every voiced scene; hooks/outros are per part when the reel is split."""
    parts = cfg.get("parts") or [{"name": "", "hook": cfg["hook"], "outro": cfg["outro"]}]
    pre = (lambda p: p["name"] + "_") if cfg.get("parts") else (lambda p: "")
    for p in parts:
        yield pre(p) + "hook", p["hook"]
    for it in cfg["items"]:
        yield str(it["rank"]), it
    for p in parts:
        yield pre(p) + "outro", p["outro"]


def load_any(path):
    """Decode any audio/video file to mono float32 at SR, trimmed of leading/trailing silence."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(SR),
                          "-af", "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                                 "silenceremove=start_periods=1:start_threshold=-45dB,areverse",
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def clean_recording(path, trim=None, tempo=1.0):
    """Phone voice note -> broadcast-ish VO: cut to the chosen take, de-noise, EQ, compress, tighten pauses."""
    chain = []
    if trim:
        chain.append(f"atrim={trim[0]}:{trim[1]},asetpts=PTS-STARTPTS")
    chain += ["highpass=f=85", "afftdn=nf=-28:nr=14", "equalizer=f=250:t=q:w=1.2:g=-2",
              "equalizer=f=3500:t=q:w=1.0:g=3",
              "acompressor=threshold=-22dB:ratio=3.5:attack=4:release=90:makeup=4"]
    if abs(tempo - 1) > 0.001:
        chain.append(f"atempo={tempo}")
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(SR),
                          "-af", ",".join(chain), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return tighten_pauses(np.frombuffer(raw, np.float32))


def voiced_regions(a, hop=441):
    """(start, end) seconds of speech, gaps under 0.25 s merged."""
    e = 20 * np.log10(np.sqrt((a[: len(a) // hop * hop].reshape(-1, hop) ** 2).mean(1)) + 1e-9)
    v = e > max(np.percentile(e, 95) - 28, np.percentile(e, 10) + 8)
    regions, i = [], 0
    while i < len(v):
        if v[i]:
            j = i
            while j < len(v) and v[j:j + 25].any():
                j += 1
            regions.append((i * hop / SR, min(j, len(v)) * hop / SR))
            i = j
        else:
            i += 1
    return [r for r in regions if r[1] - r[0] > 0.12]


def tighten_pauses(a, keep=0.28):
    """Drop leading/trailing silence and shorten any pause longer than `keep` seconds."""
    regions = voiced_regions(a)
    if not regions:
        return a
    pad = int(0.06 * SR)
    parts = []
    for k, (s0, s1) in enumerate(regions):
        parts.append(a[max(0, int(s0 * SR) - pad): int(s1 * SR) + pad])
        if k < len(regions) - 1:
            gap = regions[k + 1][0] - s1
            parts.append(np.zeros(int(min(gap, keep) * SR), np.float32))
    return np.concatenate(parts)


def main():
    cfg_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "config.json")
    with open(cfg_path) as f:
        cfg = json.load(f)
    out_dir = os.path.join(HERE, "out", "vo")
    os.makedirs(out_dir, exist_ok=True)
    voice = cfg.get("voice", {})
    tts = None
    manifest = {}
    for key, sc in scenes(cfg):
        if sc.get("vo_file"):
            src = sc["vo_file"] if os.path.isabs(sc["vo_file"]) else os.path.join(HERE, sc["vo_file"])
            audio = clean_recording(src, sc.get("vo_trim"), voice.get("recording_tempo", 1.0))
            origin = "recording"
        elif sc.get("vo_text") and voice.get("tts_fallback", True):
            if tts is None:
                from kokoro_onnx import Kokoro
                tts = Kokoro(os.path.join(HERE, "models", "kokoro-v1.0.onnx"),
                             os.path.join(HERE, "models", "voices-v1.0.bin"))
            samples, sr = tts.create(sc["vo_text"], voice=voice.get("tts_voice", "hm_omega"),
                                     speed=voice.get("tts_speed", 1.1), lang=voice.get("tts_lang", "hi"))
            tmp = os.path.join(out_dir, key + "_raw.wav")
            import soundfile as sf
            sf.write(tmp, samples, sr)
            audio = load_any(tmp)
            os.remove(tmp)
            origin = "tts"
        else:
            continue
        audio = audio / max(1e-6, np.abs(audio).max()) * 0.9
        path = os.path.join(out_dir, key + ".f32")
        audio.astype(np.float32).tofile(path)
        manifest[key] = {"path": os.path.relpath(path, HERE), "dur": round(len(audio) / SR, 3), "origin": origin,
                         "voiced": [(round(a, 2), round(b, 2)) for a, b in voiced_regions(audio)]}
        print(f"  {key:>5}: {manifest[key]['dur']:.2f}s ({origin})")
    with open(os.path.join(out_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    print("Total VO:", round(sum(m["dur"] for m in manifest.values()), 1), "s")


if __name__ == "__main__":
    main()

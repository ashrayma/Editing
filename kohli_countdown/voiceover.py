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
    yield "hook", cfg["hook"]
    for it in cfg["items"]:
        yield str(it["rank"]), it
    yield "outro", cfg["outro"]


def load_any(path):
    """Decode any audio/video file to mono float32 at SR, trimmed of leading/trailing silence."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(SR),
                          "-af", "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                                 "silenceremove=start_periods=1:start_threshold=-45dB,areverse",
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def main():
    cfg_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "config.json")
    with open(cfg_path) as f:
        cfg = json.load(f)
    out_dir = os.path.join(HERE, os.path.dirname(cfg["output"]), "vo")
    os.makedirs(out_dir, exist_ok=True)
    voice = cfg.get("voice", {})
    tts = None
    manifest = {}
    for key, sc in scenes(cfg):
        if sc.get("vo_file"):
            src = sc["vo_file"] if os.path.isabs(sc["vo_file"]) else os.path.join(HERE, sc["vo_file"])
            audio = load_any(src)
            origin = "recording"
        elif sc.get("vo_text"):
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
        manifest[key] = {"path": os.path.relpath(path, HERE), "dur": round(len(audio) / SR, 3), "origin": origin}
        print(f"  {key:>5}: {manifest[key]['dur']:.2f}s ({origin})")
    with open(os.path.join(out_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    print("Total VO:", round(sum(m["dur"] for m in manifest.values()), 1), "s")


if __name__ == "__main__":
    main()

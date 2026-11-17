#!/usr/bin/env python3
"""AI-generated B-roll stills, made locally with SD-Turbo (CPU) -> assets/ai/<name>.jpg (1920x1080).

    python3 gen_ai.py            (skips images that already exist)

No real person's likeness is generated: scenes, objects and figures seen from behind only.
Every one of these is tagged "AI-generated" on screen by gen.py.
"""
import os

import torch
from diffusers import AutoPipelineForText2Image
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "assets", "ai")
os.makedirs(OUT, exist_ok=True)

STYLE = ", cinematic documentary photograph, 35mm film grain, dramatic natural light, high detail, no text"
PROMPTS = {
    "ai_snake_boat": "aerial view of a single extremely long narrow black wooden racing canoe, over 100 feet long, packed with a hundred oarsmen in white shirts sitting in two rows, on a wide river in Kerala, coconut palms on the banks, monsoon clouds",
    "ai_capsized": "the dark wooden hull of a very long narrow canoe floating upside down, keel up, on a fast muddy brown flooded river, debris and oars floating, heavy rain, overcast",
    "ai_ghats": "a wide calm river in Kerala India at dawn with mist, coconut palms and a small Kerala-style temple with sloping red tiled roof on the bank, stone steps into the water",
    "ai_office": "an empty modern office at night, one empty desk chair under a single cold spotlight, city lights through window",
    "ai_wall": "a lone cricket bat leaning against a towering grey concrete wall, long shadow, empty ground, dusk",
    "ai_crack": "a huge dark grey concrete wall with one jagged vertical crack, bright golden sunlight shining through the crack, dust particles, close up",
    "ai_bench": "an empty cricket dressing room, a single helmet and bat resting on a wooden bench, team kit bags, soft window light",
    "ai_tv_night": "an old television glowing in a dark Indian living room at night showing a blurry cricket broadcast, sofa silhouette",
    "ai_phone": "a smartphone glowing in a dark bedroom at night lying on a bed, blue screen light, moody",
    "ai_scoreboard": "an empty cricket stadium at night under bright floodlights, deserted green outfield, empty stands, mist in the light beams",
    "ai_storm": "dark storm clouds rolling over an empty cricket stadium, floodlights on, ominous",
    "ai_hourglass": "an hourglass with falling sand on a wooden table next to a red cricket ball, warm low light",
}

MODEL = os.environ.get("AI_MODEL", "stabilityai/sd-turbo")
pipe = AutoPipelineForText2Image.from_pretrained(MODEL, torch_dtype=torch.float32)
pipe.set_progress_bar_config(disable=True)
torch.set_num_threads(4)
for k, (name, p) in enumerate(PROMPTS.items()):
    dst = os.path.join(OUT, name + ".jpg")
    if os.path.exists(dst):
        continue
    g = torch.Generator().manual_seed(303 + k)
    img = pipe(p + STYLE, num_inference_steps=int(os.environ.get("AI_STEPS", "2")), guidance_scale=0.0, width=int(os.environ.get("AI_W", "896")), height=int(os.environ.get("AI_H", "512")), generator=g).images[0]
    # upscale to 1080p (lanczos + light sharpen); it plays with a slow push-in and grain, so this holds up
    img = img.resize((1920, 1097), Image.LANCZOS).crop((0, 8, 1920, 1088))
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
    img.save(dst, quality=94)
    print("made", name, flush=True)

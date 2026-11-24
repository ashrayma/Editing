#!/usr/bin/env python3
"""AI-generated B-roll stills for the Prithvi Shaw documentary, made locally with SD-Turbo (CPU) -> assets/ai/<name>.jpg (1920x1080).

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
    "ai_school_ground": "a dusty school cricket ground in Mumbai with old pavilion and a hand-painted scoreboard, tiny distant cricketers in whites, morning haze",
    "ai_scorebook": "close-up of an old cricket scorebook page filled with handwritten pencil tallies, warm desk lamp light, shallow depth of field",
    "ai_pinkball": "a pink cricket ball resting on a dark green pitch under stadium floodlights at night, dramatic close-up, bokeh",
    "ai_medicine": "a small brown cough syrup bottle and a measuring spoon on a dark wooden table under a single spotlight, moody, no label",
    "ai_hotel_night": "exterior of a luxury hotel entrance in Mumbai at night, wet road with neon reflections, a dark car parked outside, no people",
    "ai_gavel": "a wooden auction gavel on a desk with numbered bidding paddles in the background, dramatic low light",
    "ai_empty_nets": "empty cricket practice nets at dusk with stumps and a lone kit bag, floodlights just switching on",
    "ai_fitness": "orange training cones and a stopwatch on a green cricket outfield at sunrise, shallow depth of field",
    "ai_door": "a heavy door slightly open in a dark room with bright golden light spilling through the gap, dust in the air",
    "ai_road": "an empty road leading towards a cricket stadium at dawn, long shadows, hopeful golden light",
    "ai_newspapers": "a stack of folded newspapers on a table at morning, close-up, soft window light, no readable text",
    "ai_crowd_night": "packed cricket stadium crowd at night with phone flashlights, heavily blurred bokeh, blue tones",
}

MODEL = os.environ.get("AI_MODEL", "stabilityai/sd-turbo")
pipe = AutoPipelineForText2Image.from_pretrained(MODEL, torch_dtype=getattr(torch, os.environ.get("AI_DTYPE", "float32")), variant=os.environ.get("AI_VARIANT") or None, use_safetensors=True)
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

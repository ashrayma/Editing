#!/usr/bin/env python3
"""Cut the player out of a photo (transparent PNG) with a SegFormer human-parsing model (weights only, built-in
transformers class), for the 'giant word behind the player' shots.

    python3 cutout.py debut_100 northants_244 ...   ->  assets/cutouts/<name>.png  (RGBA, original size)

A cut-out is the ONE use of that photo in the film (it's the same picture).
"""
import os
import sys

import numpy as np
import torch
from PIL import Image, ImageFilter
from transformers import SegformerForSemanticSegmentation, SegformerImageProcessor

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "assets", "cutouts")
os.makedirs(OUT, exist_ok=True)

MODEL = "mattmdjaga/segformer_b2_clothes"   # labels: 0 = background, 1..17 = hat, hair, face, clothes, limbs, bag…
proc = SegformerImageProcessor.from_pretrained(MODEL)
model = SegformerForSemanticSegmentation.from_pretrained(MODEL)
model.eval()
torch.set_num_threads(4)

for name in sys.argv[1:]:
    src = os.path.join(HERE, "assets", "photos", name + ".jpg")
    im = Image.open(src).convert("RGB")
    with torch.no_grad():
        logits = model(**proc(images=im, return_tensors="pt")).logits
    up = torch.nn.functional.interpolate(logits, size=im.size[::-1], mode="bilinear", align_corners=False)
    prob = 1 - up.softmax(1)[0, 0].numpy()          # 1 - P(background) = person (incl. bat/helmet held close)
    mask = Image.fromarray((np.clip(prob, 0, 1) * 255).astype(np.uint8))
    mask = mask.filter(ImageFilter.GaussianBlur(0.8))
    rgba = im.copy()
    rgba.putalpha(mask)
    rgba.save(os.path.join(OUT, name + ".png"))
    print("cut", name, im.size, f"{np.mean(np.array(mask) > 128):.0%} subject", flush=True)

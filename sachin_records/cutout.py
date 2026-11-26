#!/usr/bin/env python3
"""Cut the player out of a photo (transparent PNG) for the 'giant word behind the player' shots.
SegFormer body parsing -> keep only the largest solid region (drops umpires / other players behind him) -> fill holes
(keeps a raised hand + helmet) -> soft edges.

    python3 cutout.py debut_100 northants_244 ...   ->  assets/cutouts/<name>.png  (RGBA, original size)

A cut-out is the ONE use of that photo in the film (it's the same picture).
"""
import os
import sys

import numpy as np
import torch
from PIL import Image, ImageFilter
from scipy import ndimage
from transformers import SegformerForSemanticSegmentation, SegformerImageProcessor

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "assets", "cutouts")
os.makedirs(OUT, exist_ok=True)

MODEL = "mattmdjaga/segformer_b2_clothes"   # body parsing: 0 = background, everything else = the player
proc = SegformerImageProcessor.from_pretrained(MODEL)
model = SegformerForSemanticSegmentation.from_pretrained(MODEL)
model.eval()
torch.set_num_threads(4)
CROP = {}   # (kept for one-off trims; the layered look no longer needs any)

for name in sys.argv[1:]:
    src = os.path.join(HERE, "assets", "photos", name + ".jpg")
    dst = os.path.join(HERE, "assets", "cut_" + name + ".png")
    im = Image.open(src).convert("RGB")
    if name in CROP:                       # trim another player off the edge before cutting
        im = im.crop(CROP[name])
    with torch.no_grad():
        logits = model(**proc(images=im, return_tensors="pt")).logits
    up = torch.nn.functional.interpolate(logits, size=im.size[::-1], mode="bilinear", align_corners=False)
    prob = np.clip(1 - up.softmax(1)[0, 0].numpy(), 0, 1)
    # 1) only the player: the largest solid region (people behind him are faint and disconnected)
    solid = prob > 0.35
    lab, n = ndimage.label(solid)
    if n == 0:
        print("nothing found in", name)
        continue
    sizes = ndimage.sum(solid, lab, range(1, n + 1))
    keep = lab == (1 + int(np.argmax(sizes)))
    for k, sz in enumerate(sizes):          # also keep big pieces right next to him (a raised hand, helmet, bat)
        part = lab == k + 1
        if sz > 0.003 * solid.size and not (part & keep).any():
            near = ndimage.binary_dilation(keep, iterations=int(0.06 * max(im.size)))
            if (part & near).any():
                keep |= part
    # 2) fill holes inside him (a helmet held up, gloves) and close small gaps
    keep = ndimage.binary_fill_holes(ndimage.binary_closing(keep, iterations=4))
    # 3) soft edge: real probability at the border, solid inside, nothing outside
    inner = ndimage.binary_erosion(keep, iterations=3)
    zone = ndimage.binary_dilation(keep, iterations=3)
    alpha = np.where(inner, 1.0, np.where(zone, np.clip((prob - 0.2) / 0.4, 0, 1), 0.0))
    mask = Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
    rgba = im.copy()
    rgba.putalpha(mask)
    rgba.save(dst)
    print("cut", name, im.size, f"{n} regions, kept {keep.mean():.0%}", flush=True)

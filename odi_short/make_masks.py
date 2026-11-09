#!/usr/bin/env python3
"""Protected-area masks for every photo in assets/: where on-screen text must not go.

    python3 make_masks.py  ->  masks/<name>.png   (0 = free, ~150 = body / key object, 255 = face or helmet)

Bodies come from two cut-out models (human segmentation + salient object, so bats and trophies count too);
faces come from MTCNN (facenet-pytorch), padded up and out to cover helmets and caps.
"""
import os

import numpy as np
from facenet_pytorch import MTCNN
from PIL import Image, ImageDraw, ImageFilter
from rembg import new_session, remove

HERE = os.path.dirname(os.path.abspath(__file__))
NAMES = ["dhoni_2011_six", "first_odi_1971", "wc1992_captains_collage", "wc1992_captains_opera_house",
         "t20wc_trophy_floodlights", "kapil_1983", "sachin_sharjah_drive", "sachin_desert_storm_gilchrist",
         "ipl_rcb_title_wide", "ipl_rcb_title_kohli", "empty_stands"]


def main():
    os.makedirs(os.path.join(HERE, "masks"), exist_ok=True)
    human, salient = new_session("u2net_human_seg"), new_session("isnet-general-use")
    mtcnn = MTCNN(keep_all=True, device="cpu", min_face_size=14)
    for n in NAMES:
        p = os.path.join(HERE, "assets", n + "_x4.jpg")
        if not os.path.exists(p):
            p = os.path.join(HERE, "assets", n + ".jpg")
        im = Image.open(p).convert("RGB")
        s = 1000 / max(im.size)
        small = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        body = np.maximum(np.asarray(remove(small, session=human, only_mask=True), np.float32),
                          np.asarray(remove(small, session=salient, only_mask=True), np.float32))
        m = Image.fromarray((np.clip(body, 0, 255) * 150 / 255).astype(np.uint8))
        boxes, probs = mtcnn.detect(small)
        d = ImageDraw.Draw(m)
        nf = 0
        for b, pr in zip(boxes if boxes is not None else [], probs if probs is not None else []):
            if pr < 0.8:
                continue
            x0, y0, x1, y1 = b
            w, h = x1 - x0, y1 - y0
            d.rectangle((x0 - 0.4 * w, y0 - 0.7 * h, x1 + 0.4 * w, y1 + 0.35 * h), fill=255)
            nf += 1
        m = m.filter(ImageFilter.MaxFilter(7)).resize(im.size, Image.BILINEAR)
        m.save(os.path.join(HERE, "masks", n + ".png"))
        print(f"{n:32s} faces={nf}")


if __name__ == "__main__":
    main()

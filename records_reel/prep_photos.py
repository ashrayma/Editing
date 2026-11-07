#!/usr/bin/env python3
"""Per photo: a cut-out of the player (white sticker outline baked in) and a blurred full-screen fill.

    python3 prep_photos.py   ->  assets/cut/<name>.png   (RGBA, trimmed, max 1700 px tall)
                                 assets/fill/<name>.jpg  (1080x1920 cover crop, blurred + darkened)
Reads the upscaled photos in assets/hi/ (run upscale.py first). Background removal: rembg, isnet-general-use.
"""
import glob
import os

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
HI, CUT, FILL = (os.path.join(HERE, "assets", d) for d in ("hi", "cut", "fill"))
os.makedirs(CUT, exist_ok=True)
os.makedirs(FILL, exist_ok=True)
STROKE = 9  # px outline at the cut-out's final size


def fill(im, name):
    W, H = 1080, 1920
    s = max(W / im.width, H / im.height)
    f = im.convert("RGB").resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    f = f.crop(((f.width - W) // 2, (f.height - H) // 2, (f.width - W) // 2 + W, (f.height - H) // 2 + H))
    f = f.filter(ImageFilter.GaussianBlur(45))
    f = Image.fromarray((np.asarray(f, np.float32) * 0.55).astype(np.uint8))
    f.save(os.path.join(FILL, name + ".jpg"), quality=88)


def cutout(im, name, session):
    from rembg import remove
    rgba = remove(im.convert("RGB"), session=session, post_process_mask=True)
    a = rgba.getchannel("A")
    box = a.point(lambda v: 255 if v > 40 else 0).getbbox()
    rgba = rgba.crop(box)
    # sides where the player runs off the photo edge: no outline there (it would draw a straight line)
    al = np.asarray(rgba.getchannel("A"))
    edge = {"l": al[:, :3].max() > 128, "r": al[:, -3:].max() > 128, "t": al[:3].max() > 128, "b": al[-3:].max() > 128}
    if rgba.height > 1700:
        s = 1700 / rgba.height
        rgba = rgba.resize((round(rgba.width * s), 1700), Image.LANCZOS)
    pad = STROKE * 3
    canvas = Image.new("RGBA", (rgba.width + 2 * pad, rgba.height + 2 * pad))
    canvas.paste(rgba, (pad, pad))
    a = canvas.getchannel("A").point(lambda v: 255 if v > 110 else 0)
    stroke = a.filter(ImageFilter.MaxFilter(STROKE * 2 + 1)).filter(ImageFilter.GaussianBlur(1.2))
    out = Image.new("RGBA", canvas.size, (255, 255, 255, 0))
    out.putalpha(stroke)
    out.alpha_composite(canvas)
    w, h = out.size
    out = out.crop((pad if edge["l"] else 0, pad if edge["t"] else 0, w - pad if edge["r"] else w, h - pad if edge["b"] else h))
    out.save(os.path.join(CUT, name + ".png"))


def main():
    from rembg import new_session
    session = new_session("isnet-general-use")
    for f in sorted(glob.glob(os.path.join(HI, "*.png"))):
        name = os.path.basename(f)[:-4]
        im = Image.open(f)
        if not os.path.exists(os.path.join(FILL, name + ".jpg")):
            fill(im, name)
        if not os.path.exists(os.path.join(CUT, name + ".png")):
            cutout(im, name, session)
        print("ok", name)


if __name__ == "__main__":
    main()

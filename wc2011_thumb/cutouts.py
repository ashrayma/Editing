"""Upscaled (25% Lanczos blend) + background-removed player cutouts -> cut/<name>.png"""
import numpy as np
from PIL import Image, ImageFilter
from rembg import new_session, remove

sess = new_session("isnet-general-use")
# name: (crop box in ORIGINAL px or None, upscaled?)
JOBS = {"dhoni": (None, False), "sehwag": ((380, 0, 820, 538), False), "yuvraj": (None, True),
        "murali": (None, True), "sachin": ((215, 0, 560, 470), True)}
for name, (box, up) in JOBS.items():
    src = Image.open(f"clean/{name}.png").convert("RGB")
    if up:
        e = Image.open(f"up/{name}.png").convert("RGB")
        o = src.resize(e.size, Image.LANCZOS)
        im = Image.fromarray((np.asarray(e, np.float32) * 0.75 + np.asarray(o, np.float32) * 0.25).astype(np.uint8))
        k = e.width / src.width
    else:
        im, k = src.resize((src.width * 2, src.height * 2), Image.LANCZOS), 2
    if box:
        im = im.crop(tuple(int(v * k) for v in box))
    im = im.filter(ImageFilter.UnsharpMask(1.4, 35, 2))
    half = im.resize((im.width // 2, im.height // 2), Image.LANCZOS)
    a = remove(half, session=sess, only_mask=True).resize(im.size, Image.LANCZOS)
    out = im.convert("RGBA"); out.putalpha(a)
    out.save(f"cut/{name}.png"); print(name, out.size)

"""Blend Real-ESRGAN output with a plain Lanczos upscale (keeps natural skin texture), cut out, save to thumb/."""
import numpy as np
from PIL import Image, ImageFilter
from rembg import new_session, remove

S = os.environ.get("THUMB_SCRATCH", "/tmp/thumb_sr")  
U = "/root/.claude/uploads/f9639e0c-d650-5d7c-847c-d36184625aa6"
T = "/home/user/Editing/doc_video/thumb"
sess = new_session("isnet-general-use")

jobs = [  # (esrgan output, source it was made from, crop box in source px, out name, texture mix)
    ("up_sachin_cap.png", f"{U}/ea9715f3-image.webp", (40, 20, 960, 562), "cut_x4_sachin_cap.png", 0.3),
    ("up_shoaib.png", f"{S}/sr/src_shoaib.png", (0, 0, 470, 583), "cut_x4_shoaib_stare.png", 0.25),
    ("up_upper.png", f"{S}/sr/src_upper.png", None, "cut_x4_sachin_uppercut.png", 0.15),
]
for up, src, box, name, mix in jobs:
    e = Image.open(f"{S}/sr/{up}").convert("RGB")
    o = Image.open(src).convert("RGB").resize(e.size, Image.LANCZOS)
    a = np.asarray(e, np.float32) * (1 - mix) + np.asarray(o, np.float32) * mix
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8)).filter(ImageFilter.UnsharpMask(1.5, 40, 2))
    if box:
        im = im.crop(tuple(v * 4 for v in box))
    # matte at half res (rembg works at ~1k internally), then upscale the alpha
    half = im.resize((im.width // 2, im.height // 2), Image.LANCZOS)
    alpha = remove(half, session=sess, only_mask=True).resize(im.size, Image.LANCZOS)
    im.putalpha(alpha)
    im = im.crop(alpha.point(lambda v: 255 if v > 20 else 0).getbbox())
    if "shoaib" in name:  # soften the edge where Sachin's shoulder was cropped off
        al = np.asarray(im.getchannel("A"), np.float32)
        w = al.shape[1]
        al *= np.clip((w - 1 - np.arange(w)) / 160, 0, 1)[None, :]
        im.putalpha(Image.fromarray(al.astype(np.uint8)))
    im.save(f"{T}/{name}")
    print(name, im.size)

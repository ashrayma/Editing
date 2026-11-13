"""Build the two 3-player photo strips (assets/trio_dbl.jpg, assets/trio_183.jpg) from the upscaled crops."""
from PIL import Image, ImageDraw, ImageFont

FONT = ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Black.otf", 50)


def trio(names, labels, out, Wc=1530, Hc=1050):
    w = Wc // 3
    im = Image.new("RGB", (Wc, Hc), (10, 10, 12))
    for k, n in enumerate(names):
        p = Image.open(f"assets/{n}.png").convert("RGB")
        r = max(w / p.width, Hc / p.height)
        p = p.resize((int(p.width * r) + 1, int(p.height * r) + 1), Image.LANCZOS)
        x = (p.width - w) // 2
        im.paste(p.crop((x, 0, x + w, Hc)), (k * w, 0))
    d = ImageDraw.Draw(im)
    for k in (1, 2):
        d.rectangle((k * w - 4, 0, k * w + 4, Hc), fill=(254, 222, 92))
    for k, l in enumerate(labels):
        tw = d.textlength(l, font=FONT)
        cx = k * w + w / 2
        d.rounded_rectangle((cx - tw / 2 - 20, Hc - 112, cx + tw / 2 + 20, Hc - 42), 14, fill=(10, 10, 12))
        d.text((cx, Hc - 77), l, font=FONT, fill=(254, 222, 92), anchor="mm")
    im.save(out, quality=93)


trio(["sachin", "sehwag", "rohit"], ["SACHIN", "SEHWAG", "ROHIT"], "assets/trio_dbl.jpg")
trio(["ganguly", "dhoni", "kohli"], ["GANGULY", "DHONI", "KOHLI"], "assets/trio_183.jpg")

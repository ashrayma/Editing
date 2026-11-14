"""Cut the World Cup trophy alone out of the Dhoni suit photo with a traced outline -> cut/trophy.png"""
from PIL import Image, ImageDraw, ImageFilter

OX, OY = 640, 380  # crop origin in clean/dhoni.png
OUTER = [(95, 120), (150, 75), (200, 45), (255, 30), (310, 40), (360, 70), (395, 110), (430, 135), (447, 165),
         (446, 250), (432, 370), (407, 480), (382, 590), (357, 680), (335, 738), (352, 752), (366, 800), (372, 845),
         (130, 845), (140, 795), (170, 755), (212, 742), (198, 715), (166, 620), (133, 500), (103, 370), (88, 250),
         (84, 160)]
HOLE = [(258, 338), (330, 318), (372, 292), (398, 190), (424, 190), (420, 262), (404, 380), (385, 480), (360, 580), (330, 670), (302, 718), (258, 700),
        (247, 560), (244, 420), (250, 345)]
GLOBE = (132, 28, 404, 334)
im = Image.open("clean/dhoni.png").convert("RGB").crop((OX, OY, OX + 560, OY + 860))
m = Image.new("L", im.size, 0)
d = ImageDraw.Draw(m)
d.polygon(OUTER, fill=255)
d.polygon(HOLE, fill=0)
d.ellipse(GLOBE, fill=255)  # the globe overlaps the top of the gap
m = m.filter(ImageFilter.GaussianBlur(1.6))
k = 2
im = im.resize((im.width * k, im.height * k), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1.4, 40, 2))
out = im.convert("RGBA")
out.putalpha(m.resize(im.size, Image.LANCZOS))
out.crop(out.getbbox()).save("cut/trophy.png")

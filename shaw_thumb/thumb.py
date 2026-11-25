#!/usr/bin/env python3
"""Prithvi Shaw YouTube thumbnail (1280x720), two text variants.

    python3 thumb.py            ->  out/shaw_wasted.png, out/shaw_unsold.png

photos/young.*  Shaw on debut (warm, left)     photos/now.*  Shaw now (cold, right)     photos/stadium.*  optional red background
Cut-outs are made with rembg (cut/young.png, cut/now.png). Without the photos, grey silhouettes stand in (layout draft).
"""
import base64
import glob
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
CUT = os.path.join(HERE, "cut")
os.makedirs(OUT, exist_ok=True)
os.makedirs(CUT, exist_ok=True)
Y = "#FEDE5C"


def b64(path):
    ext = os.path.splitext(path)[1].lstrip(".").replace("jpg", "jpeg")
    return f"data:image/{ext};base64," + base64.b64encode(open(path, "rb").read()).decode()


def find(stem):
    fs = [f for f in glob.glob(os.path.join(HERE, "photos", stem + ".*"))]
    return fs[0] if fs else None


def cutout(stem):
    """rembg cut-out of the biggest figure, trimmed (cached)."""
    dst = os.path.join(CUT, stem + ".png")
    src = find(stem)
    if not src:
        return None
    if os.path.exists(dst) and os.path.getmtime(dst) > os.path.getmtime(src):
        return dst
    import numpy as np
    import cv2
    from PIL import Image
    from rembg import new_session, remove
    im = Image.open(src).convert("RGB")
    rgba = remove(im, session=new_session("isnet-general-use"), post_process_mask=True)
    al = np.asarray(rgba.getchannel("A")).copy()
    n, lab, st, _ = cv2.connectedComponentsWithStats((al > 40).astype(np.uint8), 8)
    if n > 2:
        big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
        al[lab != big] = 0
        rgba.putalpha(Image.fromarray(al))
    rgba = rgba.crop(rgba.getchannel("A").point(lambda v: 255 if v > 40 else 0).getbbox())
    rgba.save(dst)
    return dst


SILHOUETTE = ("data:image/svg+xml;base64," + base64.b64encode(b"""<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 400 600'>
<circle cx='200' cy='150' r='95' fill='#9a9a9a'/><path d='M40 600 C40 380 110 290 200 290 C290 290 360 380 360 600 Z' fill='#9a9a9a'/>
<text x='200' y='470' font-size='34' text-anchor='middle' fill='#555' font-family='sans-serif'>PHOTO</text></svg>""").decode())


def page(variant):
    young, now, stad = cutout("young"), cutout("now"), find("stadium")
    ysrc = b64(young) if young else SILHOUETTE
    nsrc = b64(now) if now else SILHOUETTE
    stadium = (f'<div class="stad" style="background-image:url({b64(stad)})"></div>' if stad else
               '<div class="lights">' + "".join(f'<i style="left:{x}px;top:{t}px"></i>' for x, t in ((90, 40), (300, 10), (980, 10), (1190, 40))) + "</div>")
    font = lambda n, f: f'@font-face{{font-family:"{n}";src:url({b64(os.path.join(HERE, "fonts", f))})}}'
    if variant == "wasted":
        text = f'''<div class="brush"><svg viewBox="0 0 900 220" preserveAspectRatio="none"><path d="M10 120 C110 20 300 10 470 30 C650 50 800 10 895 50 C905 120 880 170 820 190
            C640 215 420 200 240 212 C140 218 60 214 18 196 C0 170 2 140 10 120 Z" fill="#c4161c"/>
            <path d="M30 60 C200 40 420 45 700 35" stroke="#e8343a" stroke-width="14" fill="none" stroke-linecap="round" opacity=".7"/><path d="M60 175 C250 140 520 150 860 120" stroke="#000" stroke-opacity=".35"
            stroke-width="10" fill="none"/></svg></div>
            <div class="wasted"><span class="w">WASTED</span><span class="q">?</span></div>'''
    else:
        text = f'''<div class="contrast">
            <div class="num"><b>134</b><small>ON TEST DEBUT · 2018</small></div>
            <div class="arrow">→</div>
            <div class="unsold"><b>UNSOLD</b><small>IPL AUCTION · 2025</small></div></div>'''
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{font("Marker", "Marker.woff2")}{font("Anton", "Anton.woff2")}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1280px;height:720px;overflow:hidden;background:#140203;font-family:"Anton",sans-serif}}
.bg{{position:absolute;inset:0;background:radial-gradient(ellipse 70% 80% at 50% 35%,#b3151b 0%,#6d0a0e 45%,#1c0204 100%)}}
.stad{{position:absolute;inset:0;background-size:cover;background-position:center;filter:grayscale(1) contrast(1.2) brightness(.8) blur(2px);mix-blend-mode:luminosity;opacity:.55}}
.lights i{{position:absolute;width:160px;height:110px;margin-left:-80px;border-radius:50%;background:radial-gradient(#fff 0%,rgba(255,220,200,.7) 25%,rgba(255,80,60,0) 70%);filter:blur(4px)}}
.rays{{position:absolute;inset:0;background:conic-gradient(from 180deg at 50% -10%,rgba(255,255,255,0) 0deg,rgba(255,200,180,.10) 8deg,rgba(255,255,255,0) 16deg,rgba(255,200,180,.08) 30deg,rgba(255,255,255,0) 40deg,
  rgba(255,255,255,0) 320deg,rgba(255,200,180,.08) 330deg,rgba(255,255,255,0) 340deg,rgba(255,200,180,.10) 352deg,rgba(255,255,255,0) 360deg)}}
.vig{{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 45%,rgba(0,0,0,0) 40%,rgba(0,0,0,.75) 100%)}}
.grain{{position:absolute;inset:0;opacity:.10;background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><filter id='n'><feTurbulence baseFrequency='.9' numOctaves='2'/></filter><rect width='200' height='200' filter='url(%23n)'/></svg>")}}
.p{{position:absolute;bottom:0;height:690px}}
.p img{{height:100%;display:block}}
.young{{left:-10px}}
.young img{{filter:sepia(.35) saturate(1.35) brightness(1.08) contrast(1.05) drop-shadow(0 0 22px rgba(255,190,80,.55)) drop-shadow(0 20px 30px rgba(0,0,0,.6))}}
.now{{right:-10px}}
.now img{{filter:grayscale(.75) brightness(.85) contrast(1.25) hue-rotate(180deg) saturate(.5) drop-shadow(0 0 22px rgba(120,170,255,.45)) drop-shadow(0 20px 30px rgba(0,0,0,.6))}}
.coldwash{{position:absolute;right:0;top:0;bottom:0;width:640px;background:linear-gradient(90deg,rgba(40,90,170,0),rgba(40,90,170,.28));mix-blend-mode:color}}
.warmwash{{position:absolute;left:0;top:0;bottom:0;width:640px;background:linear-gradient(270deg,rgba(255,170,60,0),rgba(255,170,60,.18))}}
.tear{{position:absolute;left:600px;top:-20px;width:80px;height:760px;background:linear-gradient(90deg,rgba(0,0,0,0),rgba(0,0,0,.65) 45%,rgba(255,255,255,.9) 50%,rgba(0,0,0,.65) 55%,rgba(0,0,0,0));transform:rotate(8deg);
  clip-path:polygon(40% 0,60% 0,55% 12%,68% 22%,52% 36%,63% 50%,48% 63%,60% 76%,47% 88%,56% 100%,44% 100%,52% 88%,39% 76%,50% 63%,36% 50%,48% 36%,33% 22%,46% 12%)}}
.yrs{{position:absolute;top:150px;font:400 54px "Anton";color:rgba(255,255,255,.92);letter-spacing:.02em;text-shadow:0 4px 0 #000,0 0 20px rgba(0,0,0,.8)}}
.badge{{position:absolute;left:28px;top:26px;display:flex;align-items:center;gap:12px;background:{Y};color:#141416;padding:8px 20px 8px 10px;border-radius:10px;
  box-shadow:0 8px 20px rgba(0,0,0,.55);transform:rotate(-2deg);border:3px solid #141416}}
.badge img{{width:46px;height:46px;border-radius:50%;background:#141416;padding:4px}}
.badge span{{font:400 34px "Anton";letter-spacing:.04em}}
.badge b{{font:400 34px "Anton";background:#141416;color:{Y};padding:0 10px;border-radius:6px;margin-left:4px}}
.brush{{position:absolute;left:170px;bottom:40px;width:960px;height:240px;transform:rotate(-4deg);opacity:.95}}
.brush svg{{width:100%;height:100%}}
.wasted{{position:absolute;left:0;right:0;bottom:46px;text-align:center;transform:rotate(-4deg);font-family:"Marker";font-size:190px;line-height:1;letter-spacing:.01em}}
.wasted .w{{color:#fff;-webkit-text-stroke:6px #000;paint-order:stroke fill;text-shadow:8px 10px 0 #000,0 0 40px rgba(0,0,0,.8)}}
.wasted .q{{color:{Y};-webkit-text-stroke:6px #000;paint-order:stroke fill;text-shadow:8px 10px 0 #000;font-size:230px;margin-left:6px}}
.contrast{{position:absolute;left:0;right:0;bottom:40px;display:flex;align-items:flex-end;justify-content:center;gap:26px}}
.num,.unsold{{display:flex;flex-direction:column;align-items:center}}
.num b{{font:400 210px "Anton";line-height:.95;color:{Y};-webkit-text-stroke:5px #000;paint-order:stroke fill;text-shadow:7px 9px 0 #000,0 0 40px rgba(255,200,60,.45)}}
.unsold b{{font:400 150px "Anton";line-height:1;color:#fff;background:#c4161c;padding:6px 26px 2px;border:6px solid #fff;transform:rotate(-3deg);box-shadow:8px 10px 0 #000;letter-spacing:.02em}}
.contrast small{{font:400 26px "Anton";letter-spacing:.12em;color:#fff;background:#000;padding:2px 12px;margin-top:8px}}
.arrow{{font:400 190px "Anton";color:#fff;-webkit-text-stroke:5px #000;paint-order:stroke fill;text-shadow:6px 8px 0 #000;margin-bottom:60px}}
</style></head><body>
<div class="bg"></div>{stadium}<div class="rays"></div>
<div class="p young"><img src="{ysrc}"></div><div class="warmwash"></div>
<div class="p now"><img src="{nsrc}"></div><div class="coldwash"></div>
<div class="tear"></div>
<div class="yrs" style="left:40px">2018</div><div class="yrs" style="right:40px">NOW</div>
<div class="vig"></div><div class="grain"></div>
{text}
<div class="badge"><img src="{b64(os.path.join(HERE, "logo.png"))}"><span>UNTOLD STORIES</span><b>#4</b></div>
</body></html>"""


def render():
    for v in ("wasted", "unsold"):
        open(os.path.join(OUT, f"{v}.html"), "w").write(page(v))
    js = ("const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1280,height:720}});"
          "for(const v of ['wasted','unsold']){await p.goto('file://" + OUT + "/'+v+'.html');await p.waitForTimeout(500);"
          "await p.screenshot({path:'" + OUT + "/shaw_'+v+'.png'});console.log('out/shaw_'+v+'.png')}await b.close()})()")
    subprocess.run(["node", "-e", js], check=True)


if __name__ == "__main__":
    render()

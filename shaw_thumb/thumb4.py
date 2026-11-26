#!/usr/bin/env python3
"""Prithvi Shaw thumbnail v4 (1280x720): two big cut-outs on the left (young Shaw in front, Shaw now behind),
"NEXT / SACHIN?" on a black brush stroke on the right, red stadium with a waving Indian tricolour behind.

    python3 thumb4.py   ->  out/shaw4.png
"""
import base64
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
Y = "#FEDE5C"


def b64(path):
    ext = os.path.splitext(path)[1].lstrip(".").replace("jpg", "jpeg")
    return f"data:image/{ext};base64," + base64.b64encode(open(path, "rb").read()).decode()


def place(cw, ch, face, face_h, cx, top_y):
    """(left, top, w, h) for a cut-out of size cw x ch whose face box is face=(x,y,w,h): face height face_h, centred on cx, face top at top_y."""
    s = face_h / face[3]
    return round(cx - (face[0] + face[2] / 2) * s), round(top_y - face[1] * s), round(cw * s), round(ch * s)


YL, YT, YW, YH = place(835, 1166, (348, 94, 309, 385), 255, 300, 150)     # young Shaw (front)
NL, NT, NW, NH = place(1440, 1168, (445, 94, 324, 421), 240, 640, 105)   # Shaw now (behind)

# waving tricolour: three bands bent by the same wave, Ashoka Chakra in the middle
WAVE = lambda y0, y1: (f"M0 {y0} C300 {y0 - 60} 520 {y0 + 70} 800 {y0} S1240 {y0 - 50} 1400 {y0 + 10} "
                       f"L1400 {y1 + 10} C1240 {y1 - 50} 1080 {y1 + 70} 800 {y1} S300 {y1 - 60} 0 {y1} Z")
SPOKES = "".join(f'<line x1="700" y1="360" x2="700" y2="300" transform="rotate({k * 15} 700 360)"/>' for k in range(24))
FLAG = f"""<svg viewBox="0 0 1400 720" preserveAspectRatio="none"><defs><linearGradient id="sh" x1="0" x2="1">
<stop offset="0" stop-color="#000" stop-opacity=".35"/><stop offset=".3" stop-color="#fff" stop-opacity=".18"/><stop offset=".5" stop-color="#000" stop-opacity=".3"/>
<stop offset=".72" stop-color="#fff" stop-opacity=".16"/><stop offset="1" stop-color="#000" stop-opacity=".35"/></linearGradient></defs>
<path d="{WAVE(60, 280)}" fill="#ff8f1c"/><path d="{WAVE(280, 450)}" fill="#f4f1ea"/><path d="{WAVE(450, 660)}" fill="#1f8a3c"/>
<g stroke="#0b2d8f" stroke-width="5" fill="none"><circle cx="700" cy="360" r="62" stroke-width="9"/>{SPOKES}</g>
<rect width="1400" height="720" fill="url(#sh)"/></svg>"""


def page():
    font = lambda n, f: f'@font-face{{font-family:"{n}";src:url({b64(os.path.join(HERE, "fonts", f))})}}'
    rough = ("url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='260' height='260'><filter id='n'>"
             "<feTurbulence baseFrequency='.7' numOctaves='3' seed='7'/><feColorMatrix values='0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -2.6 2.1'/></filter>"
             "<rect width='260' height='260' filter='url(%23n)'/></svg>\")")
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{font("Anton", "Anton.woff2")}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1280px;height:720px;overflow:hidden;background:#1a0203;font-family:"Anton"}}
.bg{{position:absolute;inset:0;background:radial-gradient(ellipse 80% 70% at 60% 40%,#c0161c 0%,#7a0a0e 45%,#2a0304 100%)}}
.flag{{position:absolute;left:240px;top:-30px;width:1080px;height:640px;opacity:.88;filter:saturate(1.2);
  -webkit-mask-image:radial-gradient(ellipse 75% 75% at 55% 45%,#000 55%,transparent 100%)}}
.flag svg{{width:100%;height:100%;-webkit-mask-image:linear-gradient(90deg,transparent 0%,#000 28%,#000 88%,transparent 100%),linear-gradient(180deg,transparent 0%,#000 12%);-webkit-mask-composite:source-in}}
.redwash{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(150,10,15,0) 0%,rgba(150,10,15,0) 55%,rgba(90,5,8,.6) 100%)}}
.crowd{{position:absolute;left:0;right:0;bottom:0;height:300px;background:
  repeating-linear-gradient(0deg,rgba(0,0,0,.25) 0 6px,rgba(0,0,0,0) 6px 18px),
  radial-gradient(ellipse 100% 100% at 50% 100%,rgba(30,0,0,.85),rgba(30,0,0,0) 70%);filter:blur(1.5px)}}
.light{{position:absolute;left:34px;top:34px;width:120px;height:90px;background:
  radial-gradient(circle,#fff 0 3px,transparent 4px) 0 0/16px 16px;filter:drop-shadow(0 0 14px #fff) drop-shadow(0 0 40px #ff9a9a)}}
.lightglow{{position:absolute;left:-60px;top:-60px;width:320px;height:280px;background:radial-gradient(circle,rgba(255,230,230,.55),rgba(255,80,80,0) 65%)}}
.pole{{position:absolute;left:90px;top:120px;width:6px;height:260px;background:linear-gradient(#300,#1a0000)}}
.cut{{position:absolute}}
.cut img{{width:100%;height:100%;display:block}}
.now img{{filter:brightness(1.08) contrast(1.1) drop-shadow(-10px 0 30px rgba(0,0,0,.6))}}
.young img{{filter:brightness(1.06) contrast(1.08) saturate(1.1) drop-shadow(12px 0 34px rgba(0,0,0,.7))}}
.rimfx{{position:absolute;left:0;top:0;width:760px;height:720px;background:radial-gradient(ellipse 60% 50% at 40% 30%,rgba(255,120,90,.18),rgba(0,0,0,0) 70%);mix-blend-mode:screen}}
.slab{{position:absolute;left:760px;top:165px;width:510px;height:355px;background:#0a0a0b;transform:rotate(-4deg);
  -webkit-mask-image:{rough},linear-gradient(#000,#000);-webkit-mask-composite:source-over;
  clip-path:polygon(3% 8%,22% 2%,48% 6%,75% 0,100% 5%,98% 40%,100% 74%,96% 100%,70% 95%,45% 100%,18% 94%,0 100%,4% 60%,0 30%)}}
.txt{{position:absolute;left:760px;top:150px;transform:rotate(-4deg);text-align:center;width:510px;line-height:.92}}
.next{{font-size:178px;color:#fff;letter-spacing:.03em;-webkit-mask-image:{rough};-webkit-mask-size:260px 260px}}
.sachin{{font-size:150px;color:{Y};letter-spacing:.01em;-webkit-mask-image:{rough};-webkit-mask-size:240px 240px;text-shadow:0 0 1px {Y}}}
.under{{position:absolute;left:770px;top:520px;width:500px;height:70px;transform:rotate(-6deg)}}
.under svg{{width:100%;height:100%}}
.badge{{position:absolute;right:26px;bottom:24px;display:flex;align-items:center;gap:10px;background:{Y};color:#141416;padding:5px 14px 5px 7px;border-radius:9px;
  box-shadow:0 8px 20px rgba(0,0,0,.6);border:3px solid #141416}}
.badge img{{width:36px;height:36px;border-radius:50%;background:#141416;padding:3px}}
.badge span{{font-size:26px;letter-spacing:.04em}}
.badge b{{font-size:26px;font-weight:400;background:#141416;color:{Y};padding:0 8px;border-radius:6px;margin-left:3px}}
.vig{{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 45%,rgba(0,0,0,0) 50%,rgba(0,0,0,.6) 100%)}}
.grain{{position:absolute;inset:0;opacity:.08;background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><filter id='n'><feTurbulence baseFrequency='.9' numOctaves='2'/></filter><rect width='200' height='200' filter='url(%23n)'/></svg>")}}
</style></head><body>
<div class="bg"></div><div class="flag">{FLAG}</div><div class="redwash"></div><div class="crowd"></div>
<div class="lightglow"></div><div class="pole"></div><div class="light"></div>
<div class="cut now" style="left:{NL}px;top:{NT}px;width:{NW}px;height:{NH}px"><img src="{b64(os.path.join(HERE, "cut", "now2.png"))}"></div>
<div class="cut young" style="left:{YL}px;top:{YT}px;width:{YW}px;height:{YH}px"><img src="{b64(os.path.join(HERE, "cut", "young.png"))}"></div>
<div class="rimfx"></div><div class="vig"></div>
<div class="slab"></div>
<div class="txt"><div class="next">NEXT</div><div class="sachin">SACHIN?</div></div>
<div class="under"><svg viewBox="0 0 500 70" preserveAspectRatio="none"><path d="M6 44 C120 20 300 16 494 22 C470 34 420 40 380 42 C300 46 200 52 120 58 C70 62 30 62 6 56 Z" fill="{Y}"/>
<path d="M40 60 C180 50 330 44 470 36" stroke="{Y}" stroke-width="5" fill="none" stroke-linecap="round" opacity=".8"/></svg></div>
<div class="grain"></div>
<div class="badge"><img src="{b64(os.path.join(HERE, "logo.png"))}"><span>UNTOLD STORIES</span><b>#4</b></div>
</body></html>"""


def render():
    html = os.path.join(OUT, "v4.html")
    open(html, "w").write(page())
    js = ("const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1280,height:720}});"
          f"await p.goto('file://{html}');await p.waitForTimeout(500);await p.screenshot({{path:'{OUT}/shaw4.png'}});await b.close()}})()")
    subprocess.run(["node", "-e", js], check=True)
    print("out/shaw4.png")


if __name__ == "__main__":
    render()

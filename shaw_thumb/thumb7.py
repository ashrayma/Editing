#!/usr/bin/env python3
"""Prithvi Shaw thumbnail v7 (1280x720): "the 2018 headline, crossed out".

A taped 2018 sports-page clipping (INDIA'S NEXT SACHIN + halftone of young Shaw) scribbled over in red marker with
UNSOLD; Shaw now on the right in a moody spotlight, looking at it. Generic newsprint, no real masthead.

    python3 thumb7.py   ->  out/shaw7.png (+ out/shaw7_mobile.png at feed size)
"""
import base64
import os
import random
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
Y = "#FEDE5C"
EP = "#4"


def place(cw, ch, f, fh, cx, ty):
    s = fh / f[3]
    return round(cx - (f[0] + f[2] / 2) * s), round(ty - f[1] * s), round(cw * s), round(ch * s)


NL, NT, NW, NH = place(1440, 1168, (445, 94, 324, 421), 268, 975, 96)


def b64(path):
    ext = os.path.splitext(path)[1].lstrip(".").replace("jpg", "jpeg")
    return f"data:image/{ext};base64," + base64.b64encode(open(path, "rb").read()).decode()


def column_lines(n, w, seed):
    r = random.Random(seed)
    return "".join(f'<i style="width:{w if k % 7 != 6 else r.randint(w // 3, w - 30)}px"></i>' for k in range(n))


def page():
    font = lambda n, f: f'@font-face{{font-family:"{n}";src:url({b64(os.path.join(HERE, "fonts", f))})}}'
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{font("PF", "Playfair900.woff2")}{font("Anton", "Anton.woff2")}{font("Marker", "Marker.woff2")}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1280px;height:720px;overflow:hidden;background:#0b0b0d;font-family:"Anton"}}
.bg{{position:absolute;inset:0;background:radial-gradient(ellipse 45% 70% at 76% 30%,#3a3530 0%,#1a1816 45%,#0b0b0d 100%)}}
.spot{{position:absolute;left:700px;top:-260px;width:560px;height:900px;background:linear-gradient(180deg,rgba(255,236,200,.22),rgba(255,236,200,0) 80%);
  clip-path:polygon(38% 0,62% 0,100% 100%,0 100%);filter:blur(18px)}}
.bokeh{{position:absolute;inset:0;background:
  radial-gradient(circle at 88% 14%,rgba(255,210,150,.35) 0 14px,transparent 30px),radial-gradient(circle at 95% 34%,rgba(255,210,150,.22) 0 10px,transparent 24px),
  radial-gradient(circle at 70% 8%,rgba(255,220,170,.25) 0 9px,transparent 22px),radial-gradient(circle at 62% 26%,rgba(255,220,170,.16) 0 7px,transparent 18px);filter:blur(3px)}}
.rimS{{position:absolute;left:0;top:0;width:100%;height:100%;background:radial-gradient(ellipse 30% 45% at 64% 40%,rgba(255,150,40,.20),rgba(0,0,0,0) 70%)}}
.now{{position:absolute;left:{NL}px;top:{NT}px;width:{NW}px;height:{NH}px;
  -webkit-mask-image:linear-gradient(90deg,transparent 0%,#000 22%,#000 82%,rgba(0,0,0,.5) 89%,transparent 96%),linear-gradient(0deg,transparent 0%,#000 16%);-webkit-mask-composite:source-in}}
.now img{{position:absolute;inset:0;width:100%;height:100%}}
.now .m{{filter:contrast(1.16) saturate(.92) brightness(.98) sepia(.08)}}
.now .r{{filter:brightness(0) invert(78%) sepia(80%) saturate(900%) hue-rotate(345deg) blur(8px);opacity:.3;transform:translate(-4px,-3px);mix-blend-mode:screen}}
.shade{{position:absolute;left:0;right:0;bottom:0;height:180px;background:linear-gradient(180deg,rgba(11,11,13,0),#0b0b0d)}}
/* the clipping */
.clip{{position:absolute;left:44px;top:78px;width:600px;height:560px;transform:rotate(-4.5deg);background:#ece6d6;
  box-shadow:0 26px 50px rgba(0,0,0,.65),0 0 0 1px rgba(0,0,0,.08);padding:20px 26px;color:#1b1a18;
  clip-path:polygon(0 1%,6% 0,14% 1.2%,26% .2%,40% 1%,55% 0,70% 1.3%,84% .3%,100% 1%,99.4% 20%,100% 42%,99.3% 66%,100% 88%,99% 100%,80% 99%,62% 100%,44% 99.2%,26% 100%,10% 99%,0 100%,.6% 80%,0 56%,.7% 30%)}}
.paper{{position:absolute;inset:0;opacity:.35;mix-blend-mode:multiply;background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.02' numOctaves='4'/><feColorMatrix values='0 0 0 0 .55  0 0 0 0 .5  0 0 0 0 .4  0 0 0 -.9 1'/></filter><rect width='300' height='300' filter='url(%23n)'/></svg>")}}
.kick{{display:flex;justify-content:space-between;font:400 19px "Anton";letter-spacing:.18em;border-bottom:3px double #1b1a18;padding-bottom:6px;color:#3b3833}}
.head{{font:900 112px/0.9 "PF";letter-spacing:-.01em;margin-top:10px;position:relative}}
.head .l1{{display:block;font-size:54px;letter-spacing:.02em;margin-bottom:4px}}
.head .l2{{display:block}}
.body{{display:flex;gap:18px;margin-top:16px}}
.pic{{width:250px;height:150px;overflow:hidden;filter:grayscale(1) contrast(1.35) brightness(1.05);position:relative}}
.pic img{{width:100%;height:100%;object-fit:cover;object-position:35% 20%}}
.pic:after{{content:"";position:absolute;inset:0;background:radial-gradient(circle,rgba(0,0,0,.35) 32%,transparent 36%) 0 0/4px 4px;mix-blend-mode:multiply}}
.cap{{font:600 14px Georgia,serif;font-style:italic;margin-top:5px;color:#3b3833;width:250px}}
.cols{{flex:1;display:flex;flex-direction:column;gap:8px;padding-top:4px}}
.cols i{{display:block;height:7px;background:#5d5a54;opacity:.55}}
.tape{{position:absolute;width:140px;height:40px;background:rgba(240,236,222,.7);box-shadow:0 2px 6px rgba(0,0,0,.3)}}
/* red marker */
.scrib{{position:absolute;left:44px;top:78px;width:600px;height:560px;transform:rotate(-4.5deg);pointer-events:none}}
.unsold{{position:absolute;left:260px;top:448px;transform:rotate(-9deg);font:400 136px "Marker";color:#e3161d;letter-spacing:.02em;
  text-shadow:0 0 1px #e3161d,2px 3px 0 rgba(120,0,0,.35)}}
.badge{{position:absolute;right:26px;bottom:24px;background:#141416;color:#fff;font-size:28px;letter-spacing:.04em;padding:5px 16px 3px 20px;border-left:7px solid {Y};
  box-shadow:0 6px 16px rgba(0,0,0,.5)}}
.grain{{position:absolute;inset:0;opacity:.09;background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><filter id='n'><feTurbulence baseFrequency='.9' numOctaves='2'/></filter><rect width='200' height='200' filter='url(%23n)'/></svg>")}}
</style></head><body>
<div class="bg"></div><div class="spot"></div><div class="bokeh"></div><div class="rimS"></div>
<div class="now"><img class="r" src="{b64(os.path.join(HERE, "cut", "now2.png"))}"><img class="m" src="{b64(os.path.join(HERE, "cut", "now2.png"))}"></div>
<div class="shade"></div>
<div class="clip"><div class="paper"></div>
  <div class="kick"><span>SPORTS</span><span>OCTOBER 2018</span></div>
  <div class="head"><span class="l1">INDIA'S</span><span class="l2">NEXT</span><span class="l2">SACHIN</span></div>
  <div class="body"><div><div class="pic"><img src="{b64(os.path.join(HERE, "photos", "young_full.jpg"))}"></div>
  <div class="cap">18-year-old hits 134 on Test debut</div></div><div class="cols">{column_lines(11, 250, 4)}</div></div>
</div>
<div class="tape" style="left:20px;top:64px;transform:rotate(-38deg)"></div><div class="tape" style="left:560px;top:52px;transform:rotate(24deg)"></div>
<svg class="scrib" viewBox="0 0 600 560"><g fill="none" stroke="#e3161d" stroke-linecap="round" stroke-linejoin="round" opacity=".93">
  <path d="M24 178 C90 162 200 186 330 160" stroke-width="16"/><path d="M30 196 C120 184 230 200 322 182" stroke-width="9"/>
  <path d="M22 276 C150 256 300 284 470 250" stroke-width="16"/><path d="M34 294 C170 280 320 300 462 272" stroke-width="9"/></g></svg>
<div class="unsold">UNSOLD</div>
<div class="grain"></div>
<div class="badge">UNTOLD STORIES {EP}</div>
</body></html>"""


def render():
    html = os.path.join(OUT, "v7.html")
    open(html, "w").write(page())
    js = ("const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();"
          f"for(const [s,f] of [[1,'shaw7'],[0.25,'shaw7_mobile']]){{const p=await b.newPage({{viewport:{{width:1280,height:720}},deviceScaleFactor:s}});"
          f"await p.goto('file://{html}');await p.waitForTimeout(600);await p.screenshot({{path:'{OUT}/'+f+'.png'}})}}await b.close()}})()")
    subprocess.run(["node", "-e", js], check=True)
    print("out/shaw7.png")


if __name__ == "__main__":
    render()

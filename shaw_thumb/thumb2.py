#!/usr/bin/env python3
"""Prithvi Shaw thumbnail, 'The Miracle' style: big central face with a gold glow, taped photo prints on both sides,
gold serif title at the bottom. 1280x720.

    python3 thumb2.py   ->  out/shaw2_unsold.png, out/shaw2_wasted.png

Uses cut/now.png (centre face), photos/young_full.jpg (left print) and photos/print_r1.*, photos/print_r2.* (right prints;
grey placeholders until supplied).
"""
import base64
import glob
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
Y = "#FEDE5C"


def b64(path):
    ext = os.path.splitext(path)[1].lstrip(".").replace("jpg", "jpeg")
    return f"data:image/{ext};base64," + base64.b64encode(open(path, "rb").read()).decode()


def find(stem):
    fs = glob.glob(os.path.join(HERE, "photos", stem + ".*"))
    return b64(fs[0]) if fs else None


PLACE = ("data:image/svg+xml;base64," + base64.b64encode(b"""<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 400 280'>
<rect width='400' height='280' fill='#6b6b6b'/><text x='200' y='150' font-size='30' text-anchor='middle' fill='#bbb' font-family='sans-serif'>PHOTO</text></svg>""").decode())

# centre face: cut/now.png is 1921x2123 with the face at (630, 324, 452, 476)
FACE_H = 228
SC = FACE_H / 476
CW, CH = round(1921 * SC), round(2123 * SC)
CL, CT = round(640 - (630 + 226) * SC), round(92 - 324 * SC)


def prints(x, y, w, h, rot, src, tape=((-18, -14, -30), (None, -14, 28))):
    tapes = "".join(f'<i class="tape" style="{"left" if lx is not None else "right"}:{lx if lx is not None else -18}px;top:{ty}px;transform:rotate({r}deg)"></i>'
                    for lx, ty, r in tape)
    return (f'<div class="pr" style="left:{x}px;top:{y}px;transform:rotate({rot}deg)"><div class="pi" style="width:{w}px;height:{h}px">'
            f'<img src="{src}"></div>{tapes}</div>')


def page(variant):
    font = lambda n, f: f'@font-face{{font-family:"{n}";src:url({b64(os.path.join(HERE, "fonts", f))})}}'
    small, big = {"unsold": ("134 ON DEBUT", "UNSOLD"), "wasted": ("TALENT", "WASTED?")}[variant]
    bigsize = 196 if variant == "unsold" else 190
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{font("PF", "Playfair900.woff2")}{font("Anton", "Anton.woff2")}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1280px;height:720px;overflow:hidden;background:#0d0906}}
.bg{{position:absolute;inset:0;background:radial-gradient(ellipse 38% 55% at 50% 42%,rgba(255,196,90,.55) 0%,rgba(190,120,30,.25) 40%,rgba(0,0,0,0) 75%),
  radial-gradient(ellipse at 50% 50%,#2a1d10 0%,#140d07 60%,#070504 100%)}}
.tex{{position:absolute;inset:0;opacity:.5;mix-blend-mode:overlay;background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='400' height='400'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.012' numOctaves='4'/><feColorMatrix values='0 0 0 0 .6  0 0 0 0 .45  0 0 0 0 .3  0 0 0 1.2 -.2'/></filter><rect width='400' height='400' filter='url(%23n)'/></svg>")}}
.grain{{position:absolute;inset:0;opacity:.12;background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><filter id='n'><feTurbulence baseFrequency='.9' numOctaves='2'/></filter><rect width='200' height='200' filter='url(%23n)'/></svg>")}}
.burn{{position:absolute;inset:0;box-shadow:inset 0 0 120px 40px #000}}
.face{{position:absolute;left:{CL}px;top:{CT}px;width:{CW}px;height:{CH}px}}
.face img{{width:100%;height:100%;filter:contrast(1.08) saturate(1.05) brightness(1.02) drop-shadow(0 0 30px rgba(255,190,90,.55))}}
.fadeb{{position:absolute;left:0;right:0;bottom:0;height:330px;background:linear-gradient(180deg,rgba(13,9,6,0),rgba(13,9,6,.85) 55%,#0d0906)}}
.pr{{position:absolute;background:#f1ece0;padding:12px 12px 34px;box-shadow:0 18px 40px rgba(0,0,0,.7)}}
.pi{{overflow:hidden;background:#555}}
.pi img{{width:100%;height:100%;object-fit:cover;object-position:50% 25%}}
.tape{{position:absolute;width:110px;height:34px;background:rgba(235,232,222,.78);box-shadow:0 2px 6px rgba(0,0,0,.25)}}
.title{{position:absolute;left:0;right:0;bottom:22px;text-align:center}}
.small{{display:flex;align-items:center;justify-content:center;gap:22px;font:900 54px "PF";letter-spacing:.06em;color:#fff;text-shadow:0 4px 12px rgba(0,0,0,.9)}}
.small i{{display:block;width:180px;height:4px;background:linear-gradient(90deg,rgba(243,199,90,0),#f3c75a)}}
.small i:last-child{{background:linear-gradient(270deg,rgba(243,199,90,0),#f3c75a)}}
.big{{font:900 {bigsize}px "PF";line-height:.9;letter-spacing:.02em;background:linear-gradient(180deg,#fff7cf 0%,#ffe08a 28%,#e0a63a 52%,#9c6414 70%,#f6d27a 100%);
  -webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 6px 0 #3a2306) drop-shadow(0 12px 24px rgba(0,0,0,.9))}}
.badge{{position:absolute;left:30px;top:24px;display:flex;align-items:center;gap:10px;background:{Y};color:#141416;padding:6px 16px 6px 8px;border-radius:9px;
  box-shadow:0 8px 20px rgba(0,0,0,.6);transform:rotate(-2deg);border:3px solid #141416;z-index:5}}
.badge img{{width:40px;height:40px;border-radius:50%;background:#141416;padding:3px}}
.badge span{{font:400 30px "Anton";letter-spacing:.04em}}
.badge b{{font:400 30px "Anton";background:#141416;color:{Y};padding:0 9px;border-radius:6px;margin-left:3px}}
</style></head><body>
<div class="bg"></div><div class="tex"></div>
<div class="face"><img src="{b64(os.path.join(HERE, "cut", "now.png"))}"></div>
{prints(36, 150, 330, 300, -6, find("young_full") or PLACE)}
{prints(920, 66, 300, 210, 5, find("print_r1") or PLACE)}
{prints(935, 318, 300, 170, -4, find("print_r2") or PLACE, tape=((None, -14, 30), (-16, 160, -25)))}
<div class="fadeb"></div><div class="grain"></div><div class="burn"></div>
<div class="title"><div class="small"><i></i>{small}<i></i></div><div class="big">{big}</div></div>
<div class="badge"><img src="{b64(os.path.join(HERE, "logo.png"))}"><span>UNTOLD STORIES</span><b>#4</b></div>
</body></html>"""


def render():
    for v in ("wasted",):
        open(os.path.join(OUT, f"m_{v}.html"), "w").write(page(v))
    js = ("const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1280,height:720}});"
          "for(const v of ['wasted']){await p.goto('file://" + OUT + "/m_'+v+'.html');await p.waitForTimeout(500);"
          "await p.screenshot({path:'" + OUT + "/shaw2_'+v+'.png'});console.log('out/shaw2_'+v+'.png')}await b.close()})()")
    subprocess.run(["node", "-e", js], check=True)


if __name__ == "__main__":
    render()

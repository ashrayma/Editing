#!/usr/bin/env python3
"""Prithvi Shaw thumbnail v9 (1280x720) = direction C, refined: worn tricolour background (as the Karun thumbnail),
torn strip with NEXT SACHIN crossed out in red marker, UNSOLD in bold condensed type on a red ragged slab,
Shaw (India Test whites) big on the right.

    python3 thumb9.py   ->  out/shaw9.png (+ out/shaw9_mobile.png)
"""
import base64
import os
import random
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
Y = "#FEDE5C"
EP = "#4"


def b64(path):
    ext = os.path.splitext(path)[1].lstrip(".").replace("jpg", "jpeg")
    return f"data:image/{ext};base64," + base64.b64encode(open(path, "rb").read()).decode()


def place(cw, ch, f, fh, cx, ty):
    s = fh / f[3]
    return round(cx - (f[0] + f[2] / 2) * s), round(ty - f[1] * s), round(cw * s), round(ch * s)


FL, FT, FW, FH = place(1921, 2123, (630, 324, 452, 476), 300, 1035, 88)   # cut/now.png = 2018 Test-whites portrait


def scratches(n=22, seed=3):
    r = random.Random(seed)
    out = []
    for _ in range(n):
        x, y = r.uniform(0, 1280), r.uniform(0, 720)
        l, a = r.uniform(60, 240), r.uniform(-45, 45)
        out.append(f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{x + l:.0f}" y2="{y + l * a / 100:.0f}" stroke="rgba(0,0,0,{r.uniform(.12, .28):.2f})" stroke-width="{r.uniform(.6, 1.1):.1f}"/>')
    return "".join(out)


def jag(seed=5):
    r = random.Random(seed)
    top = [(x, r.uniform(0, 8)) for x in range(3, 98, 5)]
    right = [(r.uniform(95, 100), y) for y in range(10, 92, 8)]
    bot = [(x, r.uniform(92, 100)) for x in range(97, 2, -5)]
    left = [(r.uniform(0, 5), y) for y in range(90, 9, -8)]
    return ",".join(f"{x:.1f}% {y:.1f}%" for x, y in top + right + bot + left)


def page():
    font = lambda n, f: f'@font-face{{font-family:"{n}";src:url({b64(os.path.join(HERE, "fonts", f))})}}'
    r = random.Random(11)
    streaks = "".join(f'<i style="top:{r.uniform(6, 90):.0f}%;width:{r.uniform(30, 80):.0f}px;height:{r.uniform(3, 7):.0f}px;{side}:{-r.uniform(18, 70):.0f}px"></i>'
                      for side in ("left", "right") for _ in range(8))
    spokes = "".join(f'<line x1="100" y1="100" x2="100" y2="14" transform="rotate({k * 15} 100 100)"/>' for k in range(24))
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{font("Anton", "Anton.woff2")}{font("PF", "Playfair900.woff2")}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1280px;height:720px;overflow:hidden;background:#222;font-family:"Anton"}}
.flag{{position:absolute;inset:0;background:linear-gradient(180deg,#a85a1f 0%,#c4782f 18%,#c07433 31%,#8f8d89 34.5%,#d2d0ca 50%,#8d8b87 65.5%,#1d7a2c 69%,#17602a 85%,#0f421c 100%)}}
.chakra{{position:absolute;left:{640 - 66}px;top:{360 - 66}px;width:132px;height:132px}}
.dirt{{position:absolute;inset:0;opacity:.6;mix-blend-mode:multiply;background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='520' height='520'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.007' numOctaves='5' seed='8'/><feColorMatrix values='0 0 0 0 .32  0 0 0 0 .28  0 0 0 0 .24  0 0 0 -1.4 1.3'/></filter><rect width='520' height='520' filter='url(%23n)'/></svg>")}}
.grain{{position:absolute;inset:0;opacity:.26;mix-blend-mode:overlay;background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'><filter id='n'><feTurbulence baseFrequency='1.1' numOctaves='2'/></filter><rect width='220' height='220' filter='url(%23n)'/></svg>")}}
.scr{{position:absolute;inset:0}}
.vig{{position:absolute;inset:0;background:radial-gradient(ellipse 78% 78% at 50% 48%,rgba(0,0,0,0) 52%,rgba(0,0,0,.62) 100%)}}
.halo{{position:absolute;left:{1035 - 380}px;top:-60px;width:760px;height:800px;background:radial-gradient(ellipse at 50% 40%,rgba(0,0,0,.42) 0%,rgba(0,0,0,0) 62%)}}
.face{{position:absolute;left:{FL}px;top:{FT}px;width:{FW}px;height:{FH}px;
  -webkit-mask-image:linear-gradient(90deg,transparent 0%,#000 20%),linear-gradient(0deg,transparent 0%,#000 12%);-webkit-mask-composite:source-in}}
.face img{{width:100%;height:100%;display:block;filter:contrast(1.12) saturate(1.06) brightness(1.05) drop-shadow(-12px 8px 24px rgba(0,0,0,.55))}}
/* torn strip with the crossed-out headline */
.strip{{position:absolute;left:30px;top:96px;width:560px;height:262px;background:#f3eee1;transform:rotate(-4deg);box-shadow:0 20px 40px rgba(0,0,0,.5);
  clip-path:polygon(0 4%,9% 0,21% 4%,34% 1%,49% 4%,63% 0,77% 3%,90% 0,100% 4%,99% 50%,100% 96%,87% 100%,73% 96%,58% 100%,44% 96%,29% 100%,15% 96%,0 100%,1% 50%)}}
.paper{{position:absolute;left:30px;top:96px;width:560px;height:262px;transform:rotate(-4deg);opacity:.35;mix-blend-mode:multiply;
  background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.03' numOctaves='4'/><feColorMatrix values='0 0 0 0 .55  0 0 0 0 .5  0 0 0 0 .4  0 0 0 -.9 1'/></filter><rect width='300' height='300' filter='url(%23n)'/></svg>")}}
.hd{{position:absolute;left:58px;top:110px;transform:rotate(-4deg);font:900 112px/0.98 "PF";color:#151412;letter-spacing:-.01em}}
.x{{position:absolute;left:30px;top:96px;width:560px;height:262px;transform:rotate(-4deg)}}
.tape{{position:absolute;width:120px;height:36px;background:rgba(240,236,222,.72);box-shadow:0 2px 6px rgba(0,0,0,.3)}}
/* UNSOLD on a red ragged slab */
.slab{{position:absolute;left:26px;top:430px;width:580px;height:200px;background:#d3242a;clip-path:polygon({jag()})}}
.st{{position:absolute;left:26px;top:430px;width:580px;height:200px}}
.st i{{position:absolute;background:#d3242a}}
.uns{{position:absolute;left:26px;top:418px;width:580px;text-align:center;font-size:188px;line-height:1;color:#f8f7f4;letter-spacing:.02em;text-shadow:0 6px 0 rgba(0,0,0,.32)}}
.badge{{position:absolute;left:50%;top:24px;transform:translateX(-50%);background:#1b1b1d;color:#fff;font-size:30px;letter-spacing:.03em;padding:5px 16px 3px 22px;
  border-left:7px solid {Y};box-shadow:0 6px 16px rgba(0,0,0,.45);white-space:nowrap}}
</style></head><body>
<div class="flag"></div>
<svg class="chakra" viewBox="0 0 200 200"><g stroke="#1e2a78" fill="none"><circle cx="100" cy="100" r="92" stroke-width="9"/><circle cx="100" cy="100" r="15" fill="#1e2a78"/>
<g stroke-width="5">{spokes}</g></g></svg>
<div class="dirt"></div><svg class="scr" viewBox="0 0 1280 720">{scratches()}</svg><div class="grain"></div><div class="vig"></div>
<div class="halo"></div>
<div class="face"><img src="{b64(os.path.join(HERE, "cut", "now.png"))}"></div>
<div class="strip"></div><div class="paper"></div><div class="hd">NEXT<br>SACHIN</div>
<svg class="x" viewBox="0 0 560 262"><g fill="none" stroke="#e0161e" stroke-linecap="round" opacity=".95">
<path d="M18 84 C120 66 240 92 360 62" stroke-width="16"/><path d="M22 100 C130 88 250 104 352 84" stroke-width="7"/>
<path d="M14 196 C150 176 330 204 520 164" stroke-width="16"/><path d="M24 212 C170 198 340 216 512 186" stroke-width="7"/></g></svg>
<div class="tape" style="left:10px;top:84px;transform:rotate(-36deg)"></div><div class="tape" style="left:520px;top:62px;transform:rotate(22deg)"></div>
<div class="st">{streaks}</div><div class="slab"></div><div class="uns">UNSOLD</div>
<div class="badge">UNTOLD STORIES {EP}</div>
</body></html>"""


def render():
    html = os.path.join(OUT, "v9.html")
    open(html, "w").write(page())
    js = ("const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();"
          f"for(const [s,f] of [[1,'shaw9'],[0.25,'shaw9_mobile']]){{const p=await b.newPage({{viewport:{{width:1280,height:720}},deviceScaleFactor:s}});"
          f"await p.goto('file://{html}');await p.waitForTimeout(600);await p.screenshot({{path:'{OUT}/'+f+'.png'}})}}await b.close()}})()")
    subprocess.run(["node", "-e", js], check=True)
    from PIL import Image
    big, m = Image.open(os.path.join(OUT, "shaw9.png")), Image.open(os.path.join(OUT, "shaw9_mobile.png"))
    c = Image.new("RGB", (1280 + 40 + m.width, 720), "#1c1c1e")
    c.paste(big, (0, 0))
    c.paste(m, (1320, 0))
    c.save(os.path.join(OUT, "shaw9_check.png"))
    print("out/shaw9.png")


if __name__ == "__main__":
    render()

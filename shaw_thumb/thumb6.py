#!/usr/bin/env python3
"""Prithvi Shaw thumbnail v6 (1280x720) in the channel's proven format (Karun 'FORGOTTEN 303*', Kohli 'THE NIGHT 82*'):
worn tricolour full-bleed, big 'now' close-up right, smaller 'then' top-left, white word + red jagged slab with the number,
black UNTOLD STORIES badge top-centre.

    python3 thumb6.py   ->  out/shaw6.png
"""
import base64
import os
import random
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
Y = "#FEDE5C"
EP = "#4"

# cut/now2.png 1440x1168, face (445, 94, 324, 421);  cut/young.png 835x1166, face (348, 94, 309, 385)
def place(cw, ch, f, fh, cx, ty):
    s = fh / f[3]
    return round(cx - (f[0] + f[2] / 2) * s), round(ty - f[1] * s), round(cw * s), round(ch * s)


NL, NT, NW, NH = place(1440, 1168, (445, 94, 324, 421), 262, 1000, 128)
YL, YT, YW, YH = place(835, 1166, (348, 94, 309, 385), 150, 230, 52)


def b64(path):
    ext = os.path.splitext(path)[1].lstrip(".").replace("jpg", "jpeg")
    return f"data:image/{ext};base64," + base64.b64encode(open(path, "rb").read()).decode()


def scratches(n=26, seed=3):
    r = random.Random(seed)
    out = []
    for _ in range(n):
        x, y = r.uniform(0, 1280), r.uniform(0, 720)
        l, a = r.uniform(60, 260), r.uniform(-40, 40)
        out.append(f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{x + l:.0f}" y2="{y + l * a / 100:.0f}" stroke="rgba(0,0,0,{r.uniform(.12, .3):.2f})" stroke-width="{r.uniform(.6, 1.1):.1f}"/>')
    return "".join(out)


def jag(seed=5):
    """Ragged brush-slab outline (polygon %) with horizontal streaks on the left and right ends."""
    r = random.Random(seed)
    top = [(x, r.uniform(0, 7)) for x in range(4, 97, 6)]
    right = [(r.uniform(96, 100), y) for y in range(8, 93, 7)]
    bot = [(x, r.uniform(93, 100)) for x in range(96, 3, -6)]
    left = [(r.uniform(0, 4), y) for y in range(92, 7, -7)]
    return ",".join(f"{x:.1f}% {y:.1f}%" for x, y in top + right + bot + left)


def page():
    font = lambda n, f: f'@font-face{{font-family:"{n}";src:url({b64(os.path.join(HERE, "fonts", f))})}}'
    r = random.Random(9)
    streaks = "".join(f'<i style="top:{r.uniform(5, 92):.0f}%;width:{r.uniform(30, 90):.0f}px;height:{r.uniform(3, 7):.0f}px;{side}:{-r.uniform(20, 80):.0f}px"></i>'
                      for side in ("left", "right") for _ in range(9))
    spokes = "".join(f'<line x1="100" y1="100" x2="100" y2="14" transform="rotate({k * 15} 100 100)"/>' for k in range(24))
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{font("Anton", "Anton.woff2")}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1280px;height:720px;overflow:hidden;background:#222;font-family:"Anton"}}
.flag{{position:absolute;inset:0;background:linear-gradient(180deg,#b8692a 0%,#c47a35 30%,#9c9a97 34%,#c9c7c2 50%,#9a9894 64%,#1f6b2a 68%,#16521f 100%)}}
.flag:after{{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,0) 30%,rgba(0,0,0,.18) 33%,rgba(0,0,0,0) 36%,rgba(0,0,0,0) 64%,rgba(0,0,0,.2) 67%,rgba(0,0,0,0) 70%)}}
.chakra{{position:absolute;left:{640 - 62}px;top:{360 - 62}px;width:124px;height:124px}}
.dirt{{position:absolute;inset:0;opacity:.55;mix-blend-mode:multiply;background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='500' height='500'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.008' numOctaves='5' seed='3'/><feColorMatrix values='0 0 0 0 .35  0 0 0 0 .3  0 0 0 0 .25  0 0 0 -1.4 1.3'/></filter><rect width='500' height='500' filter='url(%23n)'/></svg>")}}
.grain{{position:absolute;inset:0;opacity:.22;mix-blend-mode:overlay;background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'><filter id='n'><feTurbulence baseFrequency='1.1' numOctaves='2'/></filter><rect width='220' height='220' filter='url(%23n)'/></svg>")}}
.scr{{position:absolute;inset:0}}
.vig{{position:absolute;inset:0;background:radial-gradient(ellipse 75% 75% at 50% 50%,rgba(0,0,0,0) 55%,rgba(0,0,0,.6) 100%)}}
.cut{{position:absolute}}
.cut img{{width:100%;height:100%;display:block}}
.now{{-webkit-mask-image:linear-gradient(90deg,transparent 0%,#000 18%,#000 100%),linear-gradient(0deg,transparent 0%,#000 10%);-webkit-mask-composite:source-in}}
.now img{{filter:contrast(1.12) saturate(1.06) brightness(1.04) drop-shadow(-14px 10px 26px rgba(0,0,0,.55))}}
.young{{-webkit-mask-image:linear-gradient(0deg,transparent 0%,#000 22%)}}
.young img{{filter:contrast(1.06) saturate(1.05) drop-shadow(10px 10px 22px rgba(0,0,0,.5))}}
.word{{position:absolute;left:46px;top:384px;font-size:136px;line-height:1;color:#f4f4f2;letter-spacing:.01em;
  text-shadow:0 6px 0 rgba(0,0,0,.45),0 0 24px rgba(0,0,0,.45)}}
.slab{{position:absolute;left:34px;top:522px;width:450px;height:200px;background:#d32a2a;clip-path:polygon({jag()})}}
.st{{position:absolute;left:34px;top:522px;width:450px;height:200px}}
.st i{{position:absolute;background:#d32a2a}}
.num{{position:absolute;left:34px;top:506px;width:450px;text-align:center;font-size:210px;line-height:1;color:#f7f7f5;letter-spacing:.01em;
  text-shadow:0 6px 0 rgba(0,0,0,.35)}}
.badge{{position:absolute;left:50%;top:26px;transform:translateX(-50%);background:#1b1b1d;color:#fff;font-size:34px;letter-spacing:.03em;padding:6px 18px 4px 24px;
  border-left:7px solid {Y};box-shadow:0 6px 16px rgba(0,0,0,.45);white-space:nowrap}}
</style></head><body>
<div class="flag"></div>
<svg class="chakra" viewBox="0 0 200 200"><g stroke="#1e2a78" fill="none"><circle cx="100" cy="100" r="92" stroke-width="9"/><circle cx="100" cy="100" r="16" fill="#1e2a78"/>
<g stroke-width="5">{spokes}</g></g></svg>
<div class="dirt"></div><svg class="scr" viewBox="0 0 1280 720">{scratches()}</svg><div class="grain"></div><div class="vig"></div>
<div class="cut young" style="left:{YL}px;top:{YT}px;width:{YW}px;height:{YH}px"><img src="{b64(os.path.join(HERE, "cut", "young.png"))}"></div>
<div class="cut now" style="left:{NL}px;top:{NT}px;width:{NW}px;height:{NH}px"><img src="{b64(os.path.join(HERE, "cut", "now2.png"))}"></div>
<div class="word">WASTED</div>
<div class="st">{streaks}</div><div class="slab"></div><div class="num">134</div>
<div class="badge">UNTOLD STORIES {EP}</div>
</body></html>"""


def render():
    html = os.path.join(OUT, "v6.html")
    open(html, "w").write(page())
    js = ("const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1280,height:720}});"
          f"await p.goto('file://{html}');await p.waitForTimeout(600);await p.screenshot({{path:'{OUT}/shaw6.png'}});await b.close()}})()")
    subprocess.run(["node", "-e", js], check=True)
    print("out/shaw6.png")


if __name__ == "__main__":
    render()

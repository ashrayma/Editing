#!/usr/bin/env python3
"""Prithvi Shaw thumbnail v5 (1280x720): one photo, clean composite.

Design (from current thumbnail practice): one big emotional face, 3 words max, high contrast, a simple background,
and the subject separated + matched to the scene with rim light and the same colours as the background.
The tricolour is used as LIGHT (saffron key glow top-left, white halo behind the head, green glow bottom-right),
not as a busy flag; the subject's edges pick up the same saffron/green so he sits inside the light.

    python3 thumb5.py   ->  out/shaw5.png
"""
import base64
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
Y = "#FEDE5C"

# cut/now2.png is 1440x1168, face box (445, 94, 324, 421)
FH = 262
S = FH / 421
PW, PH = round(1440 * S), round(1168 * S)
PL, PT = round(905 - (445 + 162) * S), round(80 - 94 * S)


def b64(path):
    ext = os.path.splitext(path)[1].lstrip(".").replace("jpg", "jpeg")
    return f"data:image/{ext};base64," + base64.b64encode(open(path, "rb").read()).decode()


def page():
    font = lambda n, f: f'@font-face{{font-family:"{n}";src:url({b64(os.path.join(HERE, "fonts", f))})}}'
    cut = b64(os.path.join(HERE, "cut", "now2.png"))
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{font("Anton", "Anton.woff2")}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1280px;height:720px;overflow:hidden;background:#07080c;font-family:"Anton"}}
/* tricolour as light */
.base{{position:absolute;inset:0;background:radial-gradient(ellipse 90% 90% at 70% 40%,#16192a 0%,#0b0c13 55%,#050509 100%)}}
.saff{{position:absolute;left:-260px;top:-300px;width:1100px;height:800px;background:radial-gradient(ellipse at center,rgba(255,140,30,.75) 0%,rgba(255,110,20,.32) 35%,rgba(255,110,20,0) 70%)}}
.green{{position:absolute;right:-300px;bottom:-380px;width:1150px;height:820px;background:radial-gradient(ellipse at center,rgba(20,170,80,.7) 0%,rgba(20,150,70,.3) 38%,rgba(20,150,70,0) 70%)}}
.halo{{position:absolute;left:{905 - 330}px;top:-120px;width:660px;height:640px;background:radial-gradient(circle,rgba(255,255,255,.55) 0%,rgba(230,236,255,.22) 35%,rgba(255,255,255,0) 68%)}}
.chakra{{position:absolute;left:{905 - 230}px;top:-10px;width:460px;height:460px;opacity:.13}}
.beams{{position:absolute;inset:0;background:conic-gradient(from 200deg at 0% 0%,rgba(255,170,80,0) 0deg,rgba(255,170,80,.10) 10deg,rgba(255,170,80,0) 18deg,rgba(255,170,80,.07) 30deg,rgba(255,170,80,0) 38deg,rgba(255,170,80,0) 360deg)}}
/* subject */
.p{{position:absolute;left:{PL}px;top:{PT}px;width:{PW}px;height:{PH}px;-webkit-mask-image:linear-gradient(90deg,transparent 0%,rgba(0,0,0,.35) 9%,#000 24%,#000 84%,rgba(0,0,0,.6) 90%,transparent 97%),linear-gradient(0deg,transparent 0%,#000 22%);-webkit-mask-composite:source-in}}
.p img{{position:absolute;inset:0;width:100%;height:100%}}
.p .main{{filter:contrast(1.12) saturate(1.08) brightness(1.06)}}
.p .rimL{{filter:brightness(0) saturate(100%) invert(62%) sepia(90%) saturate(2000%) hue-rotate(350deg) blur(6px);opacity:.55;transform:translate(-5px,-3px);mix-blend-mode:screen}}
.p .rimR{{filter:brightness(0) saturate(100%) invert(55%) sepia(60%) saturate(900%) hue-rotate(95deg) blur(6px);opacity:.4;transform:translateX(5px);mix-blend-mode:screen}}
.p .glow{{filter:brightness(0) invert(1) blur(26px);opacity:.28;transform:scale(1.02)}}
.ground{{position:absolute;left:0;right:0;bottom:0;height:200px;background:linear-gradient(180deg,rgba(5,5,9,0) 0%,rgba(5,5,9,.75) 65%,#050509 100%)}}
.textshade{{position:absolute;left:0;top:0;bottom:0;width:640px;background:linear-gradient(90deg,rgba(4,4,8,.7) 0%,rgba(4,4,8,.45) 55%,rgba(4,4,8,0) 100%)}}
/* type: 3 words */
.t{{position:absolute;left:58px;top:92px;line-height:.9}}
.t div{{text-shadow:0 8px 0 rgba(0,0,0,.55),0 0 40px rgba(0,0,0,.55)}}
.next{{font-size:150px;color:#fff;letter-spacing:.02em}}
.sachin{{font-size:176px;color:{Y};letter-spacing:.005em}}
.stamp{{position:absolute;left:66px;top:480px;transform:rotate(-7deg);font-size:112px;line-height:1;letter-spacing:.07em;color:#fff;
  background:#d9141c;padding:12px 34px 6px;border-radius:12px;box-shadow:0 0 0 6px #fff,10px 14px 0 6px rgba(0,0,0,.6)}}
.badge{{position:absolute;right:24px;top:22px;display:flex;align-items:center;gap:9px;background:rgba(10,10,12,.72);color:#fff;padding:5px 14px 5px 6px;border-radius:999px;
  border:2px solid rgba(254,222,92,.85)}}
.badge img{{width:34px;height:34px;border-radius:50%;background:#141416}}
.badge span{{font-size:24px;letter-spacing:.06em}}
.badge b{{font-size:24px;font-weight:400;color:{Y};margin-left:2px}}
.vig{{position:absolute;inset:0;background:radial-gradient(ellipse at 60% 45%,rgba(0,0,0,0) 55%,rgba(0,0,0,.55) 100%)}}
</style></head><body>
<div class="base"></div><div class="beams"></div><div class="saff"></div><div class="green"></div><div class="halo"></div>
<svg class="chakra" viewBox="0 0 200 200"><g stroke="#fff" fill="none"><circle cx="100" cy="100" r="92" stroke-width="7"/><circle cx="100" cy="100" r="12" stroke-width="6"/>
{"".join(f'<line x1="100" y1="100" x2="100" y2="12" stroke-width="3" transform="rotate({k * 15} 100 100)"/>' for k in range(24))}</g></svg>
<div class="p"><img class="glow" src="{cut}"><img class="rimL" src="{cut}"><img class="rimR" src="{cut}"><img class="main" src="{cut}"></div>
<div class="ground"></div><div class="textshade"></div><div class="vig"></div>
<div class="t"><div class="next">NEXT</div><div class="sachin">SACHIN?</div></div>
<div class="stamp">WASTED</div>
<div class="badge"><img src="{b64(os.path.join(HERE, "logo.png"))}"><span>UNTOLD STORIES</span><b>#4</b></div>
</body></html>"""


def render():
    html = os.path.join(OUT, "v5.html")
    open(html, "w").write(page())
    js = ("const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1280,height:720}});"
          f"await p.goto('file://{html}');await p.waitForTimeout(600);await p.screenshot({{path:'{OUT}/shaw5.png'}});"
          f"const q=await b.newPage({{viewport:{{width:1280,height:720}},deviceScaleFactor:0.25}});await q.goto('file://{html}');await q.waitForTimeout(600);"
          f"await q.screenshot({{path:'{OUT}/shaw5_mobile.png'}});await b.close()}})()")
    subprocess.run(["node", "-e", js], check=True)
    print("out/shaw5.png")


if __name__ == "__main__":
    render()

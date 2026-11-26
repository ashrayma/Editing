#!/usr/bin/env python3
"""Prithvi Shaw thumbnail v3 (1280x720): "NEXT SACHIN?" huge yellow on the left with a red tilted WASTED stamp,
Shaw now as a big brightened close-up filling the right 55%, UNTOLD STORIES #4 badge bottom-right.

    python3 thumb3.py   ->  out/shaw3.png      (uses photos/now_close.png: EDSR-upscaled head-and-shoulders crop)
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


def page():
    font = lambda n, f: f'@font-face{{font-family:"{n}";src:url({b64(os.path.join(HERE, "fonts", f))})}}'
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{font("Anton", "Anton.woff2")}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1280px;height:720px;overflow:hidden;background:#120607;font-family:"Anton"}}
.bg{{position:absolute;inset:0;background:radial-gradient(ellipse 60% 80% at 25% 45%,#5a0d10 0%,#2a0608 50%,#0c0304 100%)}}
.streak{{position:absolute;inset:0;background:repeating-linear-gradient(115deg,rgba(255,255,255,.025) 0 2px,transparent 2px 22px)}}
.photo{{position:absolute;right:0;top:0;width:704px;height:720px;overflow:hidden}}
.photo img{{position:absolute;left:0;top:0;width:100%;height:100%;object-fit:cover;object-position:50% 30%;
  filter:brightness(1.18) contrast(1.12) saturate(1.05)}}
.photo:after{{content:"";position:absolute;inset:0;background:linear-gradient(90deg,#1e0709 0%,rgba(30,7,9,.85) 7%,rgba(30,7,9,.4) 16%,rgba(18,6,7,0) 30%),
  linear-gradient(0deg,rgba(0,0,0,.55) 0%,rgba(0,0,0,0) 30%)}}
.rim{{position:absolute;right:0;top:0;width:704px;height:720px;box-shadow:inset 0 0 90px rgba(0,0,0,.6)}}
.next{{position:absolute;left:46px;top:60px;font-size:170px;line-height:.92;color:{Y};letter-spacing:.01em;
  -webkit-text-stroke:9px #0b0b0c;paint-order:stroke fill;text-shadow:10px 12px 0 #000,0 0 50px rgba(0,0,0,.6)}}
.next span{{display:block}}
.stamp{{position:absolute;left:70px;top:470px;transform:rotate(-8deg);padding:10px 34px 4px;border:9px solid #e0161e;border-radius:14px;
  color:#e0161e;font-size:128px;line-height:1;letter-spacing:.06em;background:rgba(224,22,30,.08);
  box-shadow:0 0 0 4px rgba(0,0,0,.35);text-shadow:0 0 1px #e0161e;
  -webkit-mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'><filter id='n'><feTurbulence baseFrequency='.55' numOctaves='3' seed='4'/><feColorMatrix values='0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -2.2 1.7'/></filter><rect width='300' height='300' filter='url(%23n)'/></svg>");
  -webkit-mask-size:300px 300px}}
.stampbg{{position:absolute;left:70px;top:470px;transform:rotate(-8deg);padding:10px 34px 4px;border:9px solid transparent;font-size:128px;line-height:1;letter-spacing:.06em;
  color:transparent;background:rgba(255,255,255,.92);border-radius:14px;box-shadow:8px 10px 0 #000}}
.badge{{position:absolute;right:28px;bottom:26px;display:flex;align-items:center;gap:10px;background:{Y};color:#141416;padding:6px 16px 6px 8px;border-radius:9px;
  box-shadow:0 8px 20px rgba(0,0,0,.6);border:3px solid #141416}}
.badge img{{width:40px;height:40px;border-radius:50%;background:#141416;padding:3px}}
.badge span{{font-size:30px;letter-spacing:.04em}}
.badge b{{font-size:30px;font-weight:400;background:#141416;color:{Y};padding:0 9px;border-radius:6px;margin-left:3px}}
.grain{{position:absolute;inset:0;opacity:.08;background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><filter id='n'><feTurbulence baseFrequency='.9' numOctaves='2'/></filter><rect width='200' height='200' filter='url(%23n)'/></svg>")}}
</style></head><body>
<div class="bg"></div><div class="streak"></div>
<div class="photo"><img src="{b64(os.path.join(HERE, "photos", "now_close.png"))}"></div><div class="rim"></div>
<div class="grain"></div>
<div class="next"><span>NEXT</span><span>SACHIN?</span></div>
<div class="stampbg">WASTED</div><div class="stamp">WASTED</div>
<div class="badge"><img src="{b64(os.path.join(HERE, "logo.png"))}"><span>UNTOLD STORIES</span><b>#4</b></div>
</body></html>"""


def render():
    html = os.path.join(OUT, "v3.html")
    open(html, "w").write(page())
    js = ("const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1280,height:720}});"
          f"await p.goto('file://{html}');await p.waitForTimeout(500);await p.screenshot({{path:'{OUT}/shaw3.png'}});await b.close()}})()")
    subprocess.run(["node", "-e", js], check=True)
    print("out/shaw3.png")


if __name__ == "__main__":
    render()

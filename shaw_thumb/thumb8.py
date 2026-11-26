#!/usr/bin/env python3
"""Three quick, very different directions for the Shaw thumbnail (1280x720 each), to pick by gut.

A  BOLD    one huge sharp face (India Test whites), complementary colour: teal-navy ground + saffron light behind the head,
           "TALENT / WASTED?" huge.
B  SPLIT   then (warm saffron side, smiling) vs now (cold teal side, frowning), "134 -> UNSOLD" across the middle.
C  HEADLINE simplified newspaper idea: no clutter, just a giant crossed-out NEXT SACHIN on a torn strip + UNSOLD, vivid red ground.

    python3 thumb8.py   ->  out/dirA.png out/dirB.png out/dirC.png  + out/dirs_grid.png (with phone-size row)
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


def place(cw, ch, f, fh, cx, ty):
    s = fh / f[3]
    return round(cx - (f[0] + f[2] / 2) * s), round(ty - f[1] * s), round(cw * s), round(ch * s)


CUT_TEST = (1921, 2123, (630, 324, 452, 476))   # 2018 Test whites portrait (sharpest face we have)
CUT_NOW = (1440, 1168, (445, 94, 324, 421))     # recent, frowning
CUT_YOUNG = (835, 1166, (348, 94, 309, 385))    # young, smiling
F = lambda n: b64(os.path.join(HERE, "cut", n + ".png"))


def cutdiv(name, spec, fh, cx, ty, cls="", extra=""):
    l, t, w, h = place(spec[0], spec[1], spec[2], fh, cx, ty)
    return f'<div class="cut {cls}" style="left:{l}px;top:{t}px;width:{w}px;height:{h}px;{extra}"><img src="{F(name)}"></div>'


def base_css():
    font = lambda n, f: f'@font-face{{font-family:"{n}";src:url({b64(os.path.join(HERE, "fonts", f))})}}'
    return f"""{font("Anton", "Anton.woff2")}{font("PF", "Playfair900.woff2")}{font("Marker", "Marker.woff2")}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1280px;height:720px;overflow:hidden;font-family:"Anton"}}
.cut{{position:absolute}}.cut img{{width:100%;height:100%;display:block}}
.grain{{position:absolute;inset:0;opacity:.07;background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><filter id='n'><feTurbulence baseFrequency='.9' numOctaves='2'/></filter><rect width='200' height='200' filter='url(%23n)'/></svg>")}}
.badge{{position:absolute;background:#111;color:#fff;font-size:26px;letter-spacing:.04em;padding:4px 14px 2px 18px;border-left:6px solid {Y};box-shadow:0 6px 16px rgba(0,0,0,.45)}}
.out{{-webkit-text-stroke:8px #0a0a0a;paint-order:stroke fill}}"""


def dir_a():
    face = cutdiv("now", CUT_TEST, 330, 850, 70, "a",
                  "-webkit-mask-image:linear-gradient(0deg,transparent 0%,#000 14%)")
    return f"""<style>{base_css()}
body{{background:#06222b}}
.bg{{position:absolute;inset:0;background:radial-gradient(circle at 66% 34%,#ffb347 0%,#ff7a1a 16%,rgba(255,110,20,.35) 34%,rgba(0,0,0,0) 55%),
  linear-gradient(135deg,#0a3a47 0%,#06222b 55%,#03141a 100%)}}
.rays{{position:absolute;inset:0;background:conic-gradient(from 0deg at 66% 34%,rgba(255,200,120,.10) 0 6deg,transparent 6deg 18deg,rgba(255,200,120,.08) 18deg 22deg,transparent 22deg 40deg,
  rgba(255,200,120,.10) 40deg 45deg,transparent 45deg 360deg)}}
.a img{{filter:contrast(1.12) saturate(1.1) brightness(1.06) drop-shadow(0 0 28px rgba(255,150,50,.55))}}
.t{{position:absolute;left:48px;top:150px;line-height:.9}}
.t1{{font-size:96px;color:#fff;letter-spacing:.04em}}
.t2{{font-size:200px;color:{Y};letter-spacing:.01em}}
.t1,.t2{{text-shadow:10px 12px 0 rgba(0,0,0,.45)}}
</style><div class="bg"></div><div class="rays"></div>{face}<div class="grain"></div>
<div class="t"><div class="t1 out">TALENT</div><div class="t2 out">WASTED?</div></div>
<div class="badge" style="left:48px;top:40px">UNTOLD STORIES #4</div>"""


def dir_b():
    young = cutdiv("young", CUT_YOUNG, 250, 320, 110, "y", "-webkit-mask-image:linear-gradient(0deg,transparent 0%,#000 18%)")
    now = cutdiv("now2", CUT_NOW, 250, 960, 100, "n",
                 "-webkit-mask-image:linear-gradient(90deg,transparent 0%,#000 20%,#000 84%,transparent 97%),linear-gradient(0deg,transparent 0%,#000 18%);-webkit-mask-composite:source-in")
    return f"""<style>{base_css()}
.l{{position:absolute;left:0;top:0;bottom:0;width:690px;background:radial-gradient(circle at 45% 35%,#ffc061 0%,#f08a1c 40%,#b4520a 100%);clip-path:polygon(0 0,100% 0,84% 100%,0 100%)}}
.r{{position:absolute;right:0;top:0;bottom:0;width:740px;background:radial-gradient(circle at 60% 35%,#2e6f86 0%,#123a4a 50%,#071c25 100%);clip-path:polygon(14% 0,100% 0,100% 100%,0 100%)}}
.y img{{filter:saturate(1.15) brightness(1.06) drop-shadow(0 18px 30px rgba(0,0,0,.4))}}
.n img{{filter:saturate(.55) contrast(1.2) brightness(.95) hue-rotate(-8deg)}}
.n:after{{content:"";position:absolute;inset:0;background:rgba(20,90,120,.25);mix-blend-mode:color}}
.lab{{position:absolute;top:40px;font-size:44px;color:#fff;letter-spacing:.08em;text-shadow:0 4px 0 rgba(0,0,0,.35)}}
.bar{{position:absolute;left:0;right:0;bottom:0;height:230px;background:linear-gradient(180deg,rgba(0,0,0,0),rgba(0,0,0,.65) 45%,rgba(0,0,0,.85))}}
.mid{{position:absolute;left:0;right:0;bottom:30px;display:flex;justify-content:center;align-items:center;gap:26px}}
.n134{{font-size:190px;color:{Y};line-height:1}}
.arr{{font-size:130px;color:#fff;line-height:1}}
.uns{{font-size:150px;color:#fff;background:#e0161e;padding:4px 26px 0;line-height:1;transform:rotate(-3deg);box-shadow:8px 10px 0 rgba(0,0,0,.5)}}
</style><div class="l"></div><div class="r"></div>{young}{now}<div class="bar"></div><div class="grain"></div>
<div class="lab" style="left:48px">2018</div><div class="lab" style="right:48px">NOW</div>
<div class="mid"><div class="n134 out">134</div><div class="arr out">→</div><div class="uns">UNSOLD</div></div>
<div class="badge" style="left:50%;top:40px;transform:translateX(-50%)">UNTOLD STORIES #4</div>"""


def dir_c():
    face = cutdiv("now", CUT_TEST, 300, 1000, 80, "c",
                  "-webkit-mask-image:linear-gradient(90deg,transparent 0%,#000 20%),linear-gradient(0deg,transparent 0%,#000 14%);-webkit-mask-composite:source-in")
    return f"""<style>{base_css()}
body{{background:#7a0a0d}}
.bg{{position:absolute;inset:0;background:radial-gradient(circle at 75% 35%,#ff3b30 0%,#c3121a 30%,#6d070b 70%,#3a0306 100%)}}
.c img{{filter:contrast(1.12) saturate(1.05) brightness(1.04) drop-shadow(0 0 30px rgba(0,0,0,.45))}}
.strip{{position:absolute;left:-20px;top:170px;width:780px;height:300px;background:#f4efe2;transform:rotate(-4deg);box-shadow:0 24px 50px rgba(0,0,0,.5);
  clip-path:polygon(0 3%,10% 0,22% 4%,35% 1%,50% 3%,64% 0,78% 3%,92% 1%,100% 4%,100% 96%,88% 100%,74% 97%,60% 100%,46% 97%,30% 100%,16% 97%,0 100%)}}
.hd{{position:absolute;left:44px;top:182px;transform:rotate(-4deg);font:900 128px/0.95 "PF";color:#151412;letter-spacing:-.01em}}
.x{{position:absolute;left:30px;top:170px;width:720px;height:300px;transform:rotate(-4deg)}}
.uns{{position:absolute;left:150px;top:470px;transform:rotate(-7deg);font:400 150px "Marker";color:#fff;text-shadow:6px 8px 0 rgba(0,0,0,.45)}}
</style><div class="bg"></div>{face}<div class="grain"></div>
<div class="strip"></div><div class="hd">NEXT<br>SACHIN</div>
<svg class="x" viewBox="0 0 720 300"><g fill="none" stroke="#e0161e" stroke-linecap="round" opacity=".95">
<path d="M10 92 C150 70 300 96 470 66" stroke-width="18"/><path d="M14 214 C200 190 400 222 640 180" stroke-width="18"/></g></svg>
<div class="uns">UNSOLD</div>
<div class="badge" style="right:30px;bottom:28px">UNTOLD STORIES #4</div>"""


def render():
    pages = {"dirA": dir_a(), "dirB": dir_b(), "dirC": dir_c()}
    for k, body in pages.items():
        open(os.path.join(OUT, k + ".html"), "w").write(f'<!doctype html><html><head><meta charset="utf-8"></head><body>{body}</body></html>')
    js = ("const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();"
          "for(const k of ['dirA','dirB','dirC']){for(const [s,suf] of [[1,''],[0.25,'_m']]){const p=await b.newPage({viewport:{width:1280,height:720},deviceScaleFactor:s});"
          f"await p.goto('file://{OUT}/'+k+'.html');await p.waitForTimeout(500);await p.screenshot({{path:'{OUT}/'+k+suf+'.png'}});await p.close()}}}}await b.close()}})()")
    subprocess.run(["node", "-e", js], check=True)
    from PIL import Image, ImageDraw
    g = Image.new("RGB", (3 * 640 + 40, 360 + 40 + 180 + 20), "#1c1c1e")
    d = ImageDraw.Draw(g)
    for i, k in enumerate(("dirA", "dirB", "dirC")):
        g.paste(Image.open(os.path.join(OUT, k + ".png")).resize((640, 360)), (i * 660, 0))
        g.paste(Image.open(os.path.join(OUT, k + "_m.png")), (i * 660, 400))
        d.text((i * 660 + 340, 470), "ABC"[i], fill="#FEDE5C")
    g.save(os.path.join(OUT, "dirs_grid.png"))
    print("out/dirs_grid.png")


if __name__ == "__main__":
    render()

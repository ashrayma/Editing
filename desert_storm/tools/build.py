#!/usr/bin/env python3
"""Build the HyperFrames project in film/ from three data files:

  script.json  -> the lines you say (captions come from this text) + highlight keywords
  timing.json  -> when each line starts/ends: from the scratch voice (tools/scratch_vo.py)
                  or from your own voice recording (tools/timing_from_recording.py)
  edit.json    -> photo-stage pictures, graphics/B-roll cards and sound cues, anchored to script line ids

Because beats point at line ids, not seconds, re-recording the voice retimes the
whole edit: run timing_from_recording.py, then this script.

usage: python3 tools/build.py            (writes film/index.html + film/compositions/*)
"""
import html, json, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FILM = os.path.join(ROOT, "film")
W, H = 1080, 1920

# Faceless story format: a big photo frame fills the upper half (where a talking head
# would be), captions sit just under it, and every card lives in the lower zone so
# nothing ever covers the photo.
STAGE = (40, 176, 1040, 936)  # the photo frame: x0, y0, x1, y1
CAPTION_Y = 958
CARD_TOP = 1092
CARD_MAX_H = 560

ACCENT = "#FFB340"

def media_duration(path):
    import subprocess
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True, check=True).stdout
    return float(out)


def r3(x):
    return round(x, 3)


def esc(s):
    return html.escape(s, quote=True)


# ---------------------------------------------------------------- shared css
FONT = "'Inter', sans-serif"
CARD_CSS = f"""
  #root {{ position:absolute; inset:0; font-family:{FONT}; color:#fff; -webkit-font-smoothing:antialiased; }}
  .card {{ position:absolute; top:{CARD_TOP}px; border-radius:44px; overflow:hidden;
          background:rgba(18,18,22,.80); backdrop-filter:blur(28px) saturate(140%);
          box-shadow:0 40px 90px rgba(0,0,0,.45), inset 0 0 0 1.5px rgba(255,255,255,.10); }}
  .card.light {{ background:rgba(250,250,252,.96); color:#1d1d1f; }}
  .eyebrow {{ font-size:28px; font-weight:700; letter-spacing:.12em; text-transform:uppercase; color:{ACCENT}; }}
  .light .eyebrow {{ color:#c26a00; }}
  .tag {{ position:absolute; top:26px; left:26px; z-index:5; padding:10px 20px; border-radius:100px; font-size:28px; font-weight:800;
          letter-spacing:.1em; background:rgba(0,0,0,.55); backdrop-filter:blur(12px); color:#fff; display:flex; gap:10px; align-items:center; }}
  .tag i {{ width:12px; height:12px; border-radius:50%; background:#ff453a; display:block; }}
  .num {{ font-weight:800; letter-spacing:-.045em; font-variant-numeric:tabular-nums; line-height:.9; }}
  .muted {{ color:rgba(255,255,255,.62); }}
  .light .muted {{ color:#6e6e73; }}
"""


def card_box(beat):
    w = beat.get("w", 820)
    h = min(beat.get("h", 520), CARD_MAX_H)
    side = beat.get("side", "left")
    x = beat.get("x", 48 if side == "left" else W - 48 - w)
    if side == "center":
        x = (W - w) // 2
    return x, w, h


ENTER_JS = """
  const dir = {dir};
  tl.fromTo("#{cid}-card", {{ x: dir * 1100, opacity: 0, filter: "blur(18px)" }},
            {{ x: 0, opacity: 1, filter: "blur(0px)", duration: 0.75, ease: "expo.out" }}, 0.0);
  tl.to("#{cid}-card", {{ x: dir * 260, opacity: 0, filter: "blur(12px)", duration: 0.34, ease: "power3.in" }}, {dur} - 0.36);
  tl.set("#{cid}-card", {{ opacity: 0 }}, {dur} - 0.01);
"""


def stagger_in(sel, t, step=0.07, y=24, blur=8):
    return (f'  tl.fromTo("{sel}", {{ y: {y}, opacity: 0, filter: "blur({blur}px)" }}, '
            f'{{ y: 0, opacity: 1, filter: "blur(0px)", duration: 0.5, ease: "power4.out", stagger: {step} }}, {t});\n')


def counter_js(sel, to, t, dur=1.1, dec=0):
    return (f'  {{ const o = {{ v: 0 }}; const el = document.querySelector("{sel}");\n'
            f'    tl.to(o, {{ v: {to}, duration: {dur}, ease: "power3.out", onUpdate: () => el.textContent = o.v.toFixed({dec}) }}, {t}); }}\n')


def seeded_particles(cid, n, seed, box_w, box_h, color="rgba(255,190,110,.55)"):
    """Deterministic sand particles: markup + linear drift tweens."""
    rnd = seed

    def rand():
        nonlocal rnd
        rnd = (rnd * 1103515245 + 12345) & 0x7FFFFFFF
        return rnd / 0x7FFFFFFF

    dots, js = [], []
    for i in range(n):
        x, y = rand() * box_w, rand() * box_h
        s = 2 + rand() * 6
        o = 0.25 + rand() * 0.6
        dx = 380 + rand() * 520
        dy = -40 + rand() * 80
        dots.append(f'<div class="p" id="{cid}-p{i}" style="left:{x:.0f}px;top:{y:.0f}px;width:{s:.1f}px;height:{s:.1f}px;opacity:{o:.2f};background:{color}"></div>')
        js.append(f'  tl.fromTo("#{cid}-p{i}", {{ x: {-dx/2:.0f}, y: 0 }}, {{ x: {dx/2:.0f}, y: {dy:.0f}, duration: DUR, ease: "none" }}, 0);')
    css = "  .p { position:absolute; border-radius:50%; }\n"
    return "".join(dots), "\n".join(js) + "\n", css


# ---------------------------------------------------------------- beat renderers
# Each returns (inner_html, extra_css, extra_js). The card shell + entrance/exit
# is shared; t is local scene time.

def r_stat(b, cid, dur):
    big = b["value"]
    unit = b.get("unit", "")
    inner = f"""
    <div style="padding:46px 52px">
      <div class="eyebrow item">{esc(b['eyebrow'])}</div>
      <div class="item" style="display:flex;align-items:baseline;gap:18px;margin-top:18px">
        <div class="num" id="{cid}-n" style="font-size:190px">0</div>
        <div style="font-size:46px;font-weight:700" class="muted">{esc(unit)}</div>
      </div>
      <div class="item" style="font-size:38px;font-weight:600;margin-top:22px;line-height:1.22">{b.get('sub_html', esc(b.get('sub','')))}</div>
    </div>"""
    js = stagger_in(f"#{cid} .item", 0.28) + counter_js(f"#{cid}-n", big, 0.35, b.get("count_dur", 1.2), b.get("dec", 0))
    return inner, "", js


def r_bars(b, cid, dur):
    rows = ""
    for i, (label, val, color) in enumerate(b["rows"]):
        pct = val / b["max"] * 100
        rows += f"""
      <div class="item" style="margin-top:{30 if i else 34}px">
        <div style="display:flex;justify-content:space-between;font-size:32px;font-weight:600"><span>{esc(label)}</span><span class="num" style="font-size:44px">{esc(str(b.get('labels',{}).get(str(i), val)))}</span></div>
        <div style="height:34px;border-radius:17px;background:rgba(255,255,255,.10);margin-top:14px;overflow:hidden">
          <div id="{cid}-b{i}" style="height:100%;width:{pct:.1f}%;border-radius:17px;background:{color};transform-origin:left center"></div>
        </div>
      </div>"""
    inner = f"""<div style="padding:46px 52px"><div class="eyebrow item">{esc(b['eyebrow'])}</div>
      <div class="item" style="font-size:44px;font-weight:800;letter-spacing:-.02em;margin-top:14px">{esc(b['title'])}</div>{rows}</div>"""
    js = stagger_in(f"#{cid} .item", 0.28)
    for i in range(len(b["rows"])):
        js += f'  tl.fromTo("#{cid}-b{i}", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 1.0, ease: "expo.out" }}, {0.55 + i * 0.35});\n'
    return inner, "", js


def r_image(b, cid, dur):
    tag = f'<div class="tag"><i></i>{esc(b["tag"])}</div>' if b.get("tag") else ""
    parts_html, parts_js, parts_css = ("", "", "")
    if b.get("dust"):
        parts_html, parts_js, parts_css = seeded_particles(cid, 26, 7, b.get("w", 820), CARD_MAX_H)
    cap = ""
    if b.get("caption"):
        cap = f"""<div style="position:absolute;left:0;right:0;bottom:0;padding:90px 40px 34px;background:linear-gradient(transparent,rgba(0,0,0,.78))">
          <div class="item" style="font-size:40px;font-weight:800;letter-spacing:-.02em">{esc(b['caption'])}</div>
          {f'<div class="item muted" style="font-size:30px;font-weight:600;margin-top:8px">{esc(b["sub"])}</div>' if b.get('sub') else ''}</div>"""
    inner = f"""<div id="{cid}-kb" style="position:absolute;inset:-6%;background:url('{b['src']}') center/cover"></div>
      {parts_html}{tag}{cap}"""
    js = (f'  tl.fromTo("#{cid}-kb", {{ scale: 1.0, x: -20 }}, {{ scale: 1.14, x: 20, duration: {dur}, ease: "none" }}, 0);\n'
          + parts_js.replace("DUR", str(dur)) + stagger_in(f"#{cid} .item", 0.45))
    return inner, parts_css, js


def r_video(b, cid, dur):
    # the <video> is timed inside the scene; the card wrapper is animated
    tag = f'<div class="tag"><i></i>{esc(b["tag"])}</div>' if b.get("tag") else ""
    inner = f"""<video id="{cid}-v" class="clip" src="{b['src']}" data-start="0" data-duration="{dur}" data-media-start="{b.get('media_start',0)}"
             data-playback-rate="{b.get('rate',1)}" muted playsinline style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:{b.get('pos','center top')}"></video>{tag}"""
    return inner, "", ""


def r_shot(b, cid, dur):
    tag = f'<div class="tag" style="background:rgba(0,0,0,.72)"><i style="background:#0a84ff"></i>{esc(b["tag"])}</div>' if b.get("tag") else ""
    hl = b.get("highlight")  # [x,y,w,h] in card px after fit
    ring = ""
    js = (f'  tl.fromTo("#{cid}-img", {{ scale: 1.0, transformOrigin: "{b.get("zoom_origin","50% 50%")}" }}, '
          f'{{ scale: {b.get("zoom",1.25)}, duration: 1.1, ease: "power2.inOut" }}, {b.get("zoom_at", 1.4)});\n')
    if hl:
        ring = f'<div id="{cid}-ring" style="position:absolute;left:{hl[0]}px;top:{hl[1]}px;width:{hl[2]}px;height:{hl[3]}px;border:5px solid {ACCENT};border-radius:18px;box-shadow:0 0 0 9999px rgba(0,0,0,.0)"></div>'
        js += f'  tl.fromTo("#{cid}-ring", {{ opacity: 0, scale: 1.15 }}, {{ opacity: 1, scale: 1, duration: 0.45, ease: "back.out(1.6)" }}, {b.get("ring_at", 2.6)});\n'
    inner = f"""<div id="{cid}-img" style="position:absolute;inset:0;background:#fff url('{b['src']}') {b.get('bgpos','center top')}/{b.get('bgsize','cover')} no-repeat">{ring}</div>{tag}"""
    return inner, "", js


def r_equation(b, cid, dur):
    cells = ""
    for i, (n, label) in enumerate(b["cells"]):
        sep = f'<div class="item muted" style="font-size:60px;font-weight:300;align-self:center">{esc(b.get("sep", "·"))}</div>' if i else ""
        cells += f"""{sep}<div class="item" style="text-align:center;flex:1">
          <div class="num" id="{cid}-c{i}" style="font-size:132px">{esc(str(n))}</div>
          <div class="muted" style="font-size:30px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;margin-top:12px">{esc(label)}</div></div>"""
    inner = f"""<div style="padding:46px 44px"><div class="eyebrow item">{esc(b['eyebrow'])}</div>
      <div style="display:flex;gap:6px;margin-top:40px">{cells}</div>
      {f'<div class="item" style="font-size:34px;font-weight:600;margin-top:40px;text-align:center">{b["foot_html"]}</div>' if b.get('foot_html') else ''}</div>"""
    js = stagger_in(f"#{cid} .item", 0.3, step=0.16, y=40)
    return inner, "", js


def r_boundaries(b, cid, dur):
    chips = ""
    for i in range(b["fours"]):
        chips += f'<div class="chip f" id="{cid}-k{i}">4</div>'
    for j in range(b["sixes"]):
        chips += f'<div class="chip s" id="{cid}-k{b["fours"]+j}">6</div>'
    css = f"""  .chip {{ width:100px; height:100px; border-radius:26px; display:flex; align-items:center; justify-content:center; font-size:56px; font-weight:800; }}
  .chip.f {{ background:rgba(255,255,255,.12); }}
  .chip.s {{ background:{ACCENT}; color:#1d1d1f; }}
"""
    inner = f"""<div style="padding:42px 46px"><div class="eyebrow item">{esc(b['eyebrow'])}</div>
      <div style="display:flex;flex-wrap:wrap;gap:14px;margin-top:30px">{chips}</div>
      <div class="item" style="font-size:36px;font-weight:700;margin-top:30px"><span class="num" style="font-size:44px">{b['fours']}</span> fours &nbsp;·&nbsp; <span class="num" style="font-size:44px;color:{ACCENT}">{b['sixes']}</span> sixes &nbsp;<span class="muted">= {b['fours']*4 + b['sixes']*6} runs in boundaries</span></div></div>"""
    js = stagger_in(f"#{cid} .item", 0.25)
    js += f'  tl.fromTo("#{cid} .chip", {{ scale: 0, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.42, ease: "back.out(1.7)", stagger: 0.055 }}, 0.35);\n'
    return inner, css, js


def r_donut(b, cid, dur):
    r = 120
    c = 2 * math.pi * r
    inner = f"""<div style="padding:46px 52px;display:flex;gap:44px;align-items:center">
      <div class="item" style="position:relative;width:300px;height:300px;flex:none">
        <svg width="300" height="300" viewBox="0 0 300 300" style="transform:rotate(-90deg)">
          <circle cx="150" cy="150" r="{r}" fill="none" stroke="rgba(255,255,255,.12)" stroke-width="34"/>
          <circle id="{cid}-arc" cx="150" cy="150" r="{r}" fill="none" stroke="{ACCENT}" stroke-width="34" stroke-linecap="round"
                  stroke-dasharray="{c:.1f}" stroke-dashoffset="{c:.1f}"/>
        </svg>
        <div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center"><span class="num" id="{cid}-n" style="font-size:96px">0</span><span style="font-size:48px;font-weight:800">%</span></div>
      </div>
      <div><div class="eyebrow item">{esc(b['eyebrow'])}</div>
        <div class="item" style="font-size:46px;font-weight:800;letter-spacing:-.02em;margin-top:14px;line-height:1.1">{esc(b['title'])}</div>
        <div class="item muted" style="font-size:30px;font-weight:600;margin-top:16px;line-height:1.3">{esc(b['sub'])}</div></div></div>"""
    js = stagger_in(f"#{cid} .item", 0.28)
    js += f'  tl.to("#{cid}-arc", {{ attr: {{ "stroke-dashoffset": {c * (1 - b["pct"] / 100):.1f} }}, duration: 1.3, ease: "expo.out" }}, 0.5);\n'
    js += counter_js(f"#{cid}-n", b["pct"], 0.5, 1.3)
    return inner, "", js


def r_vs(b, cid, dur):
    inner = f"""<div style="height:100%;display:flex;align-items:center;justify-content:space-around;padding:0 40px">
      <div class="item" style="text-align:center"><div class="num" style="font-size:{b.get('size',96)}px">{esc(b['a'])}</div><div class="muted" style="font-size:28px;font-weight:700;margin-top:12px">{esc(b['a_sub'])}</div></div>
      <div class="item" id="{cid}-vs" style="font-size:64px;font-weight:900;color:{ACCENT};font-style:italic">VS</div>
      <div class="item" style="text-align:center"><div class="num" style="font-size:{b.get('size',96)}px">{esc(b['b'])}</div><div class="muted" style="font-size:28px;font-weight:700;margin-top:12px">{esc(b['b_sub'])}</div></div></div>"""
    js = (f'  tl.fromTo("#{cid} .item:nth-child(1)", {{ x: -260, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.6, ease: "expo.out" }}, 0.25);\n'
          f'  tl.fromTo("#{cid} .item:nth-child(3)", {{ x: 260, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.6, ease: "expo.out" }}, 0.25);\n'
          f'  tl.fromTo("#{cid}-vs", {{ scale: 2.6, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.45, ease: "back.out(2)" }}, 0.55);\n')
    return inner, "", js


def r_quote(b, cid, dur):
    words = b["quote"].split()
    spans = " ".join(f'<span class="w">{esc(w)}</span>' for w in words)
    inner = f"""<div style="padding:50px 54px">
      <div style="font-size:120px;line-height:.6;color:{ACCENT};font-weight:800" class="item">&ldquo;</div>
      <div style="font-size:50px;font-weight:700;letter-spacing:-.02em;line-height:1.22;margin-top:6px">{spans}</div>
      <div class="item" style="display:flex;align-items:center;gap:18px;margin-top:34px">
        <div style="width:54px;height:4px;background:{ACCENT};border-radius:2px"></div>
        <div style="font-size:32px;font-weight:800">{esc(b['who'])}</div><div class="muted" style="font-size:28px;font-weight:600">{esc(b.get('who_sub',''))}</div></div></div>"""
    js = stagger_in(f"#{cid} .item", 0.25)
    js += f'  tl.fromTo("#{cid} .w", {{ opacity: 0.18 }}, {{ opacity: 1, duration: 0.12, ease: "none", stagger: {b.get("word_step", 0.12)} }}, 0.45);\n'
    return inner, "", js


def r_title(b, cid, dur):
    """Big kinetic title, no card: sits in the lower zone on a soft scrim."""
    lines = ""
    for i, line in enumerate(b["lines"]):
        words = " ".join(f'<span class="tw" style="display:inline-block">{w}</span>' for w in line.split())
        color = f"color:{ACCENT};" if i in b.get("accent_lines", []) else ""
        lines += f'<div style="font-size:{b.get("sizes",[118]*9)[i]}px;font-weight:900;letter-spacing:-.045em;line-height:.98;{color}">{words}</div>'
    eyebrow = f'<div class="eyebrow tw" style="display:inline-block;margin-bottom:18px">{esc(b["eyebrow"])}</div>' if b.get("eyebrow") else ""
    parts_html, parts_js, parts_css = seeded_particles(cid, 30, 11, W, 700) if b.get("dust") else ("", "", "")
    inner = f"""<div style="position:absolute;inset:0">{parts_html}</div>
      <div style="position:absolute;left:0;right:0;top:{b.get('text_top', 40)}px;text-align:center;padding:0 40px;text-shadow:0 10px 50px rgba(0,0,0,.55)">{eyebrow}{lines}</div>"""
    js = (f'  tl.fromTo("#{cid} .tw", {{ opacity: 0, filter: "blur(10px)", y: 0 }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.16, ease: "power3.out", stagger: 0.09 }}, 0.15);\n'
          + parts_js.replace("DUR", str(dur)))
    return inner, parts_css, js


def r_lower(b, cid, dur):
    inner = f"""<div style="display:flex;align-items:center;gap:22px;padding:0 34px 0 18px;height:100%">
      <div style="width:84px;height:84px;border-radius:50%;background:{ACCENT};color:#1d1d1f;display:flex;align-items:center;justify-content:center;font-size:40px;font-weight:900" class="item">{esc(b.get('icon','★'))}</div>
      <div><div class="item" style="font-size:40px;font-weight:800;letter-spacing:-.02em">{esc(b['name'])}</div>
      <div class="item muted" style="font-size:30px;font-weight:600;margin-top:4px">{esc(b['sub'])}</div></div></div>"""
    return inner, "", stagger_in(f"#{cid} .item", 0.22, step=0.08, y=12)


def r_cta(b, cid, dur):
    inner = f"""<div style="padding:48px 52px;text-align:center">
      <div class="item" style="font-size:54px;font-weight:800;letter-spacing:-.025em;line-height:1.12">{b['title_html']}</div>
      <div class="item" style="display:inline-flex;gap:16px;margin-top:34px;align-items:center;background:{ACCENT};color:#1d1d1f;border-radius:100px;padding:20px 40px;font-size:36px;font-weight:800">{esc(b['button'])}</div>
      <div class="item muted" style="font-size:28px;font-weight:600;margin-top:26px">{esc(b['sub'])}</div></div>"""
    js = stagger_in(f"#{cid} .item", 0.28, step=0.14)
    return inner, "", js


RENDER = dict(stat=r_stat, bars=r_bars, image=r_image, video=r_video, shot=r_shot, equation=r_equation,
              boundaries=r_boundaries, donut=r_donut, vs=r_vs, quote=r_quote, title=r_title, lower=r_lower, cta=r_cta)


def scene_file(b, dur):
    cid = b["id"]
    inner, css, js = RENDER[b["type"]](b, cid, dur)
    if b["type"] == "title" and not b.get("card"):
        shell = f'<div id="{cid}-card" style="position:absolute;left:0;top:{b.get("top", CARD_TOP)}px;width:{W}px;height:{b.get("h", CARD_MAX_H)}px">{inner}</div>'
        enter = (f'  tl.fromTo("#{cid}-card", {{ opacity: 1 }}, {{ opacity: 1, duration: 0.01 }}, 0);\n'
                 f'  tl.to("#{cid}-card", {{ opacity: 0, filter: "blur(10px)", duration: 0.25, ease: "power2.in" }}, {dur} - 0.27);\n'
                 f'  tl.set("#{cid}-card", {{ opacity: 0 }}, {dur} - 0.01);\n')
    else:
        x, w, h = card_box(b)
        top = b.get("top", CARD_TOP)
        light = " light" if b.get("light") else ""
        shell = f'<div id="{cid}-card" class="card{light}" style="left:{x}px;top:{top}px;width:{w}px;height:{h}px">{inner}</div>'
        d = -1 if b.get("side", "left") == "left" else 1
        enter = ENTER_JS.format(dir=d, cid=cid, dur=dur)
    return f"""<template>
  <style>
{CARD_CSS}
{css}
  </style>
  <div id="root" data-composition-id="{cid}" data-width="{W}" data-height="{H}">
    {shell}
  </div>
  <script>
  const tl = gsap.timeline({{ paused: true }});
{enter}{js}
  window.__timelines["{cid}"] = tl;
  </script>
</template>
"""



# ---------------------------------------------------------------- captions
def caption_groups(lines, timing, keywords, max_words=3):
    """Each script line -> groups of up to 3 words, broken at punctuation, timed by character share."""
    groups = []
    for line in lines:
        t = timing[line["id"]]
        words = line.get("caption", line["text"]).split()  # on-screen text is English
        chunks, cur = [], []
        for w in words:
            cur.append(w)
            if len(cur) == max_words or re.search(r"[.,?!]$", w) or len(" ".join(cur)) >= 15:
                chunks.append(cur)
                cur = []
        if cur:
            chunks.append(cur)
        if len(chunks) > 1 and len(chunks[-1]) == 1 and len(chunks[-2]) < max_words + 1 and not re.search(r"[.?!]$", chunks[-2][-1]):
            last = chunks.pop()
            chunks[-1] += last
        total = sum(len(" ".join(c)) + 2 for c in chunks)
        acc = t["start"]
        for c in chunks:
            d = (t["end"] - t["start"]) * (len(" ".join(c)) + 2) / total
            groups.append({"t0": acc, "t1": acc + d, "words": c})
            acc += d
    kw = set(keywords)
    for g in groups:
        g["hl"] = {k for k in (re.sub(r"[^\w%]", "", w.lower()) for w in g["words"]) if k in kw or re.search(r"\d", k)}
    return groups


def captions_file(groups, total):
    divs, js = [], []
    for i, g in enumerate(groups):
        spans = []
        for j, w in enumerate(g["words"]):
            key = re.sub(r"[^\w%]", "", w.lower())
            cls = "w hl" if key in g["hl"] else "w"
            spans.append(f'<span class="{cls}" id="cap{i}w{j}">{esc(w)}</span>')
        divs.append(f'<div class="grp" id="cap{i}">{" ".join(spans)}</div>')
        t0, t1 = r3(g["t0"]), r3(g["t1"])
        js.append(f'  tl.set("#cap{i}", {{ opacity: 1, visibility: "visible" }}, {t0});')
        js.append(f'  tl.fromTo("#cap{i} .w", {{ opacity: 0, scale: 0.86, filter: "blur(6px)" }}, '
                  f'{{ opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.16, ease: "back.out(2.2)", stagger: 0.06 }}, {t0});')
        js.append(f'  tl.set("#cap{i}", {{ opacity: 0, visibility: "hidden" }}, {t1});')
    return f"""<template>
  <style>
  #root {{ position:absolute; inset:0; }}
  .grp {{ position:absolute; left:0; right:0; top:{CAPTION_Y}px; text-align:center; padding:0 70px; opacity:0; visibility:hidden;
          font-family:{FONT}; font-size:70px; font-weight:800; letter-spacing:-.025em; line-height:1.05; color:#fff;
          text-shadow:0 4px 24px rgba(0,0,0,.6), 0 2px 4px rgba(0,0,0,.45); overflow:visible; }}
  .w {{ display:inline-block; }}
  .hl {{ color:{ACCENT}; }}
  </style>
  <div id="root" data-composition-id="captions" data-width="{W}" data-height="{H}">
{chr(10).join('    ' + d for d in divs)}
  </div>
  <script>
  const tl = gsap.timeline({{ paused: true }});
{chr(10).join(js)}
  tl.set({{}}, {{}}, {r3(total)});
  window.__timelines["captions"] = tl;
  </script>
</template>
"""


# ---------------------------------------------------------------- centre: the photo stage
# Where a talking head would sit, a big rounded photo frame shows the real event
# picture for each beat. A missing photo renders as a labelled slot, so the edit
# still plays and tells you exactly which picture goes where.
def blurred_backdrop(src):
    """Pre-blurred, darkened full-frame copy of a photo (blur is baked, not a CSS filter)."""
    from PIL import Image, ImageFilter, ImageEnhance
    path = os.path.join(FILM, src)
    out_rel = os.path.join("assets/photos/_backdrop", os.path.splitext(os.path.basename(src))[0] + ".jpg")
    out = os.path.join(FILM, out_rel)
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(path):
        os.makedirs(os.path.dirname(out), exist_ok=True)
        im = Image.open(path).convert("RGB")
        r = max(W / im.width, H / im.height)
        im = im.resize((int(im.width * r / 4) + 1, int(im.height * r / 4) + 1))
        im = im.filter(ImageFilter.GaussianBlur(14))
        im = ImageEnhance.Brightness(im).enhance(0.42).resize((int(im.width * 4), int(im.height * 4)))
        x, y = (im.width - W) // 2, (im.height - H) // 2
        im.crop((x, y, x + W, y + H)).save(out, quality=88)
    return out_rel


def stage_file(photos, total):
    x0, y0, x1, y1 = STAGE
    sw, sh = x1 - x0, y1 - y0
    divs, js = [], []
    for i, p in enumerate(photos):
        t0, t1 = r3(p["_t0"]), r3(p["_t1"])
        have = bool(p.get("src")) and os.path.exists(os.path.join(FILM, p["src"]))
        if p.get("kind") == "text":
            lines = "".join(f'<div class="ptx-l" style="font-size:{sz}px">{t}</div>' for t, sz in p["lines"])
            inner = (f'<div class="ptx"><div class="ptx-e">{esc(p.get("eyebrow", ""))}</div>{lines}'
                     f'<div class="ptx-s">{esc(p.get("sub", ""))}</div></div>')
            backdrop = ""
        elif have:
            bd = blurred_backdrop(p["src"])
            tag = f'<div class="ptag">{esc(p["tag"])}</div>' if p.get("tag") else ""
            credit = f'<div class="pcred">{esc(p["credit"])}</div>' if p.get("credit") else ""
            inner = (f'<div id="pk{i}" class="pkb" style="background-image:url(\'{p["src"]}\');background-position:{p.get("pos", "center")}"></div>{tag}{credit}')
            backdrop = f'<div id="pb{i}" class="pbd" style="background-image:url(\'{bd}\')"></div>'
        else:
            inner = f"""<div class="pslot"><svg width="120" height="120" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,.45)" stroke-width="1.4">
                <rect x="2.5" y="5" width="19" height="15" rx="3"/><circle cx="12" cy="12.5" r="4"/><path d="M8 5l1.6-2h4.8L16 5"/></svg>
                <div class="pslot-k">PHOTO SLOT</div><div class="pslot-d">{esc(p["need"])}</div><div class="pslot-f">{esc(p["src"])}</div></div>"""
            backdrop = ""
        divs.append(f'<div id="p{i}" class="clip" data-start="{t0}" data-duration="{r3(t1 - t0)}" style="position:absolute;inset:0;z-index:{i + 1}">'
                    f'{backdrop}<div id="pf{i}" class="pframe">{inner}</div></div>')
        d = -1 if i % 2 == 0 else 1
        js.append(f'  tl.fromTo("#pf{i}", {{ x: {d} * 1150, opacity: 0, filter: "blur(16px)" }}, '
                  f'{{ x: 0, opacity: 1, filter: "blur(0px)", duration: 0.8, ease: "expo.out" }}, {t0});')
        if i + 1 < len(photos):  # push: leave toward the side the next picture comes from's opposite
            js.append(f'  tl.to("#pf{i}", {{ x: {d} * 700, opacity: 0, filter: "blur(14px)", duration: 0.42, ease: "power3.in" }}, '
                      f'{r3(photos[i + 1]["_t0"])});')
        if backdrop:
            js.append(f'  tl.fromTo("#pb{i}", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.6, ease: "power2.out" }}, {t0});')
        if have and p.get("kind") != "text":
            z0, z1 = p.get("zoom", [1.0, 1.12])
            js.append(f'  tl.fromTo("#pk{i}", {{ scale: {z0}, x: {-14 * d} }}, {{ scale: {z1}, x: {14 * d}, duration: {r3(t1 - t0)}, ease: "none" }}, {t0});')
    return f"""<template>
  <style>
  #root {{ position:absolute; inset:0; font-family:{FONT}; }}
  .pbd {{ position:absolute; inset:0; background-size:cover; background-position:center; }}
  .pframe {{ position:absolute; left:{x0}px; top:{y0}px; width:{sw}px; height:{sh}px; border-radius:52px; overflow:hidden;
             background:#141417; box-shadow:0 50px 120px rgba(0,0,0,.6), inset 0 0 0 1.5px rgba(255,255,255,.10); }}
  .pkb {{ position:absolute; inset:-3%; background-size:cover; }}
  .ptag {{ position:absolute; top:28px; left:28px; padding:10px 20px; border-radius:100px; background:rgba(0,0,0,.55); color:#fff;
           font-size:28px; font-weight:800; letter-spacing:.1em; }}
  .pcred {{ position:absolute; right:26px; bottom:20px; color:rgba(255,255,255,.7); font-size:22px; font-weight:600; text-shadow:0 1px 6px rgba(0,0,0,.7); }}
  .ptx {{ position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; gap:10px;
          background:radial-gradient(90% 80% at 50% 40%, #3a2a14 0%, #1a140c 45%, #0c0b0a 100%); color:#fff; }}
  .ptx-e {{ color:{ACCENT}; font-size:30px; font-weight:800; letter-spacing:.16em; text-transform:uppercase; }}
  .ptx-l {{ font-weight:900; letter-spacing:-.04em; line-height:1.04; }}
  .ptx-s {{ color:rgba(255,255,255,.62); font-size:34px; font-weight:600; margin-top:10px; }}
  .pslot {{ position:absolute; inset:26px; border:4px dashed rgba(255,255,255,.22); border-radius:36px; display:flex; flex-direction:column;
            align-items:center; justify-content:center; gap:14px; text-align:center; padding:0 60px;
            background:radial-gradient(90% 70% at 50% 35%, #2b2b31 0%, #151518 100%); }}
  .pslot-k {{ color:{ACCENT}; font-size:28px; font-weight:800; letter-spacing:.14em; }}
  .pslot-d {{ color:rgba(255,255,255,.85); font-size:44px; font-weight:800; letter-spacing:-.02em; line-height:1.12; }}
  .pslot-f {{ color:rgba(255,255,255,.4); font-size:28px; font-weight:600; font-family:'JetBrains Mono', monospace; }}
  </style>
  <div id="root" data-composition-id="stage" data-width="{W}" data-height="{H}">
    <div style="position:absolute;inset:0;background:radial-gradient(120% 70% at 50% 25%, #26262b 0%, #0d0d10 60%, #050506 100%)"></div>
{chr(10).join('    ' + d for d in divs)}
  </div>
  <script>
  const tl = gsap.timeline({{ paused: true }});
{chr(10).join(js)}
  tl.set({{}}, {{}}, {r3(total)});
  window.__timelines["stage"] = tl;
  </script>
</template>
"""


def anchor(ref, timing, edge):
    """'lineid' -> that line's start/end; 'lineid+0.8' / 'lineid-0.3' offsets it."""
    m = re.match(r"^([\w-]+)(?:([+-][\d.]+))?$", ref)
    t = timing[m.group(1)][edge]
    return t + float(m.group(2) or 0)


# ---------------------------------------------------------------- root
def build():
    script = json.load(open(os.path.join(ROOT, "script.json")))
    tim = json.load(open(os.path.join(ROOT, "timing.json")))
    edit = json.load(open(os.path.join(ROOT, "edit.json")))
    hook = edit.get("hook")
    offset = r3(hook["duration"] - hook.get("overlap", 0.0)) if hook else 0.0
    timing = {l["id"]: {"start": l["start"] + offset, "end": l["end"] + offset} for l in tim["lines"]}
    total = r3(offset + tim["duration"])
    os.makedirs(os.path.join(FILM, "compositions"), exist_ok=True)
    for f in os.listdir(os.path.join(FILM, "compositions")):
        if f.endswith(".html"):
            os.remove(os.path.join(FILM, "compositions", f))

    # photo stage: each photo runs from its line until the next photo has landed
    photos = edit.get("photos", [])
    for i, p in enumerate(photos):
        p["_t0"] = max(0.0, anchor(p["at"], timing, "start") - p.get("lead", 0.15))
    for i, p in enumerate(photos):
        p["_t1"] = photos[i + 1]["_t0"] + 0.85 if i + 1 < len(photos) else total
    with open(os.path.join(FILM, "compositions", "stage.html"), "w") as fh:
        fh.write(stage_file(photos, total))
    cam_js = []
    voice = (f'    <audio id="vo" class="clip" src="{tim["audio"]}" data-start="{offset}" data-duration="{r3(total - offset)}" '
             f'data-track-index="1" data-volume="1"></audio>')
    # the hook: a full-screen clip with its own sound, whipped off to the left as the story starts
    hook_html = ""
    if hook:
        hd = r3(hook["duration"])
        hook_html = (f'    <div id="hookwrap" style="position:absolute;inset:0;z-index:4">\n'
                     f'      <video id="hookclip" class="clip" src="{hook["src"]}" data-start="0" data-duration="{hd}" data-track-index="0" '
                     f'data-has-audio="true" playsinline style="position:absolute;left:0;top:0;width:{W}px;height:{H}px;object-fit:cover"></video>\n    </div>')
        cam_js.append(f'  tl.fromTo("#hookwrap", {{ x: 0, opacity: 1, filter: "blur(0px)" }}, '
                      f'{{ x: -700, opacity: 0, filter: "blur(18px)", duration: 0.32, ease: "power3.in" }}, {r3(hd - 0.3)});')
    tight, origin = 1.0, "540px 560px"

    hosts, sfx = [], []
    for k, b in enumerate(edit["beats"]):
        t0 = anchor(b["at"], timing, "start") - b.get("lead", 0.12)
        t1 = anchor(b.get("until", b["at"]), timing, "end") + b.get("tail", 0.3)
        t0, t1 = max(0.0, t0), min(total, t1)
        b["_t0"], b["_t1"] = r3(t0), r3(t1)
        dur = r3(t1 - t0)
        if b.get("fit"):  # play the whole clip inside the beat
            b["rate"] = round(media_duration(os.path.join(FILM, b["src"])) / dur, 3)
        with open(os.path.join(FILM, "compositions", f"{b['id']}.html"), "w") as fh:
            fh.write(scene_file(b, dur))
        hosts.append(f'    <div id="{b["id"]}" data-composition-id="{b["id"]}" data-composition-src="compositions/{b["id"]}.html" '
                     f'data-start="{r3(t0)}" data-duration="{dur}" data-track-index="{3 + k % 2}" data-track-kind="graphics" '
                     f'data-width="{W}" data-height="{H}" style="z-index:{10 + k}"></div>')
        if b.get("sfx", True) and not (b["type"] == "title" and not b.get("card")):
            sfx.append({"t": t0 - 0.12, "file": ["whoosh.mp3", "whoosh-short.mp3"][k % 2], "vol": 0.42})
        for extra in b.get("sfx_extra", []):
            sfx.append({"t": t0 + extra["at"], "file": extra["file"], "vol": extra.get("vol", 0.4)})
    for i, p in enumerate(photos):
        if i:
            sfx.append({"t": p["_t0"] - 0.1, "file": p.get("sfx", ["whoosh-short.mp3", "whoosh.mp3"][i % 2]), "vol": 0.3})
    for s in edit.get("sfx", []):
        t = s["t"] if "t" in s else anchor(s["at"], timing, s.get("edge", "start")) + s.get("offset", 0)
        sfx.append({"t": t, "file": s["file"], "vol": s.get("vol", 0.4)})

    audio, lane_free = [], [0.0] * 6
    for i, s in enumerate(sorted(sfx, key=lambda s: s["t"])):
        t = max(0.0, r3(s["t"]))
        if t >= total - 0.2:
            continue
        d = r3(min(media_duration(os.path.join(FILM, "assets/sfx", s["file"])), total - t))
        lane = next((k for k, free in enumerate(lane_free) if free <= t), 0)
        lane_free[lane] = t + d
        audio.append(f'    <audio id="sfx{i}" class="clip" src="assets/sfx/{s["file"]}" data-start="{t}" data-duration="{d}" '
                     f'data-track-index="{10 + lane}" data-volume="{s["vol"]}"></audio>')

    index = f"""<!doctype html>
<html lang="en" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <script src="assets/vendor/gsap.min.js"></script>
    <style>
      * {{ margin:0; padding:0; box-sizing:border-box; }}
      html, body {{ width:{W}px; height:{H}px; overflow:hidden; background:#000; }}
      #bg {{ position:absolute; inset:0; background:#000; }}
      #grade {{ position:absolute; inset:0; pointer-events:none; background:
                linear-gradient(180deg, rgba(0,0,0,.22) 0%, rgba(0,0,0,0) 14%, rgba(0,0,0,0) 50%, rgba(0,0,0,.38) 62%, rgba(0,0,0,.5) 100%); }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="{W}" data-height="{H}">
    <div id="bg"></div>
    <div id="stage" data-composition-id="stage" data-composition-src="compositions/stage.html" data-start="0" data-duration="{total}"
         data-track-index="0" data-track-kind="graphics" data-width="{W}" data-height="{H}" style="z-index:1"></div>
    <div id="grade"></div>
{hook_html}
{chr(10).join(hosts)}
    <div id="captions" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" data-duration="{total}"
         data-track-index="2" data-track-kind="captions" data-width="{W}" data-height="{H}" style="z-index:5"></div>
{voice}
{chr(10).join(audio)}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
{chr(10).join('    ' + j for j in cam_js)}
      tl.set({{}}, {{}}, {total});
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
    with open(os.path.join(FILM, "index.html"), "w") as fh:
        fh.write(index)
    lines = [dict(l) for l in script["lines"]]
    hook_caps = []
    if hook:
        for i, c in enumerate(hook.get("captions", [])):
            timing[f"_hook{i}"] = {"start": c["t0"], "end": c["t1"]}
            hook_caps.append({"id": f"_hook{i}", "text": c["text"]})
    groups = caption_groups(hook_caps + lines, timing, script.get("keywords", []))
    with open(os.path.join(FILM, "compositions", "captions.html"), "w") as fh:
        fh.write(captions_file(groups, total))
    # layout manifest for the face-safety audit
    lay = []
    for b in edit["beats"]:
        if b["type"] == "title" and not b.get("card"):
            box = [0, b.get("top", CARD_TOP), W, b.get("h", CARD_MAX_H)]
        else:
            x, w, h = card_box(b)
            box = [x, b.get("top", CARD_TOP), w, h]
        lay.append({"id": b["id"], "t0": b["_t0"], "t1": b["_t1"], "box": box})
    lay.append({"id": "captions", "t0": 0, "t1": total, "box": [70, CAPTION_Y, W - 140, 90]})
    json.dump({"total": total, "face": STAGE, "tight": tight, "origin": origin, "boxes": lay},
              open(os.path.join(ROOT, "out_layout.json"), "w"), indent=1)
    print(f"built {len(hosts)} graphic scenes, {len(groups)} caption groups, {len(audio)} sfx, total {total}s")


if __name__ == "__main__":
    build()

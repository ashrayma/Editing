#!/usr/bin/env python3
"""Render the Raina "Mr. IPL" reel: 1080x1920, 30 fps, VO + music + SFX.

    python3 align.py   # once: word timings from the voice note -> out/words.json
    python3 build.py   # -> out/raina_mr_ipl.mp4

Look follows the reference: black background, title on top, photo card in the middle with a slow
Ken Burns move, word-by-word yellow captions underneath. Brand: TheCricketLounge, yellow #FFDE59.
Text stays inside Instagram's safe zone (top ~250 px, bottom ~420 px clear).
"""
import json
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "kohli_countdown"))
import music  # noqa: E402
import sfx  # noqa: E402
from edl import PIECES, RAW  # noqa: E402

W, H, FPS = 1080, 1920, 30
SR = sfx.SR
YEL = (255, 222, 89)
WHITE = (255, 255, 255)
BLACK = (8, 8, 10)
TEMPO = 1.05          # gentle speed-up of the whole narration (pitch kept)
LEAD = 0.25           # silence before the first word
GAP_JOIN = 0.10       # "He's not" + "IPL's top run-scorer": same sentence
GAP = 0.26            # between lines
END_CARD = 2.4
OUT = os.path.join(HERE, "out")
FONT = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
FONT_XB = "/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf"
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

# The retake says "87 off thirty-five balls"; it was 25. Swap in "twenty" from the hook (same session).
SPLICE = {"smash": [(61.85, 63.44), (2.27, 2.57), (63.75, 70.25)]}
SPLICE_WORD = {"smash": (63.44, 2.27)}   # raw time of "thirty" -> raw time of the "twenty" put in its place

# On-screen caption text per piece. "^n" = this token covers n spoken words.
DISPLAY = {
    "hook": "25^2 balls, 87^2 runs... and the guy who did it never even won an Orange Cap.",
    "not": "He's not",
    "why": "IPL's top run-scorer^2 either. So why does everyone call Suresh Raina Mr. IPL?",
    "simple": "Simple. The bigger the match, the better he got.",
    "playoffs": "In the playoffs alone he scored 714^3 runs in just 24^2 innings, with 7 fifties, and nobody has gone past that.",
    "final": "Go back to the 2010^2 final against Mumbai. CSK were in trouble, and Raina walked in and made 57^2 not out off 35^2 balls.",
    "title": "That gave Chennai their first-ever^2 title, and he was Player of the Match.",
    "q2": "Then came 2014^2 Qualifier 2 against Punjab.",
    "smash": "He smashed 87^2 off 25^2 balls at a strike rate of 348^4 and took 33^2 runs off a single over.",
    "fivek": "He was also the first player in IPL history to reach 5000^2 runs.",
    "thala": "And if Dhoni was Thala, Raina was Chinna Thala. Together they were the heartbeat of Chennai.",
    "cap": "He never needed the Orange Cap. He just needed a big match.",
    "end": "So who's the real Mr. IPL? Raina or Kohli? Tell me in the comments, and follow!",
}

# (piece, spoken-word index where the shot starts, photo, zoom in?, focus x, focus y)
SHOTS = [
    ("hook", 0, "roar.jpg", True, 0.45, 0.35),
    ("not", 0, "batting.jpg", False, 0.5, 0.35),
    ("why", 5, "standing.jpg", True, 0.5, 0.3),
    ("simple", 0, "look_up.jpg", True, 0.5, 0.25),
    ("playoffs", 0, "bat_raise.jpg", False, 0.5, 0.45),
    ("final", 0, "arm_up_run.jpg", True, 0.5, 0.3),
    ("final", 18, "fist_pump.jpg", True, 0.4, 0.4),
    ("title", 0, "raina_dhoni_wave.jpg", False, 0.5, 0.4),
    ("q2", 0, "batting.jpg", True, 0.45, 0.2),
    ("smash", 0, "roar.jpg", False, 0.42, 0.3),
    ("fivek", 0, "no3_back.jpg", True, 0.5, 0.35),
    ("thala", 0, "raina_dhoni_run.jpg", True, 0.5, 0.4, 600),
    ("cap", 0, "trophy_family.jpg", False, 0.4, 0.45),
    ("end", 0, "standing.jpg", False, 0.5, 0.3),
]

# Chips on the photo: (piece, word index, text, kind). kind: big | small | count. A chip replaces the
# previous one unless it has stack=True (then they pile up, for the stat panels).
CHIPS = [
    ("hook", 0, "25 BALLS", "big", False),
    ("hook", 3, "87 RUNS", "big", False),
    ("hook", 16, "0 ORANGE CAPS", "small", False),
    ("why", 12, "MR. IPL?", "big", False),
    ("simple", 1, "BIG-MATCH PLAYER", "small", False),
    ("playoffs", 2, "IPL PLAYOFFS", "small", False),
    ("playoffs", 6, "714 RUNS", "big", True),
    ("playoffs", 12, "24 INNINGS", "small", True),
    ("playoffs", 16, "7 FIFTIES", "small", True),
    ("final", 4, "2010 FINAL vs MI", "small", False),
    ("final", 19, "57* (35)", "big", False),
    ("title", 4, "CSK'S FIRST TITLE", "small", False),
    ("title", 10, "PLAYER OF THE MATCH", "big", False),
    ("q2", 2, "QUALIFIER 2 · 2014", "small", False),
    ("smash", 2, "87 (25)", "big", False),
    ("smash", 13, "SR 348", "big", False),
    ("smash", 19, "33 IN ONE OVER", "big", False),
    ("fivek", 4, "FIRST IN IPL HISTORY", "small", False),
    ("fivek", 11, "5000", "count", True),
    ("thala", 4, "THALA", "small", False),
    ("thala", 8, "CHINNA THALA", "big", True),
    ("end", 6, "RAINA or KOHLI?", "big", False),
]
IMPACTS = {("hook", 3), ("playoffs", 6), ("final", 19), ("smash", 2), ("smash", 13), ("fivek", 11), ("end", 6)}


# ---------------------------------------------------------------- audio
def load_clean():
    chain = ["highpass=f=85", "afftdn=nf=-28:nr=14", "equalizer=f=250:t=q:w=1.2:g=-2",
             "equalizer=f=3500:t=q:w=1.0:g=3", "acompressor=threshold=-22dB:ratio=3.5:attack=4:release=90:makeup=4"]
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(HERE, RAW), "-vn", "-ac", "1", "-ar", str(SR),
                          "-af", ",".join(chain), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def fade(x, n=int(0.012 * SR)):
    x = x.copy()
    n = min(n, len(x) // 2)
    r = np.linspace(0, 1, n, dtype=np.float32)
    x[:n] *= r
    x[-n:] *= r[::-1]
    return x


def build_vo(words):
    """Cut the takes together. Returns (vo, timeline) where timeline[piece] = list of (word, t0, t1) in output seconds."""
    src = load_clean()
    parts = [np.zeros(int(LEAD * SR), np.float32)]
    t = LEAD
    timeline = {}
    wmap = {p["id"]: p["words"] for p in words}
    for k, p in enumerate(PIECES):
        if k:
            g = GAP_JOIN if p["id"] == "why" else GAP
            parts.append(np.zeros(int(g * SR), np.float32))
            t += g
        segs = SPLICE.get(p["id"], [p["src"]])
        # raw -> output time mapping for this piece
        offsets, acc = [], t
        for s0, s1 in segs:
            offsets.append((s0, s1, acc))
            clip = fade(src[int(s0 * SR):int(s1 * SR)])
            parts.append(clip)
            acc += len(clip) / SR

        def map_t(x, pid=p["id"]):
            if pid in SPLICE_WORD and abs(x - SPLICE_WORD[pid][0]) < 0.02:
                x = SPLICE_WORD[pid][1]
            for s0, s1, o in offsets:
                if s0 - 0.02 <= x <= s1 + 0.02:
                    return o + max(0.0, x - s0)
            return offsets[-1][2]

        timeline[p["id"]] = [(w, map_t(a), map_t(b)) for w, a, b in wmap[p["id"]]]
        t = acc
    vo = np.concatenate(parts)
    # speed up with atempo (pitch kept), scale the timeline the same way
    tmp_in, tmp_out = os.path.join(OUT, "vo_cut.wav"), os.path.join(OUT, "vo.wav")
    write_wav(tmp_in, vo)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp_in, "-af", f"atempo={TEMPO},loudnorm=I=-15:TP=-1.5:LRA=7",
                    "-ar", str(SR), "-ac", "1", tmp_out], check=True)
    vo = read_wav(tmp_out)
    timeline = {k: [(w, a / TEMPO, b / TEMPO) for w, a, b in v] for k, v in timeline.items()}
    return vo, timeline


def write_wav(path, x, ch=1):
    x = np.clip(x, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(ch)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def read_wav(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def mix(vo, total, cuts, impacts):
    n = int(total * SR)
    v = np.zeros(n, np.float32)
    v[:len(vo)] = vo[:n]
    bed = music.track(total)[:n]
    bed = np.pad(bed, (0, n - len(bed)))
    # duck the music under the voice
    env = np.abs(v)
    k = int(0.25 * SR)
    env = np.convolve(env, np.ones(k) / k, mode="same")
    duck = 0.20 - 0.12 * np.clip(env / 0.05, 0, 1)
    out = v + bed * duck
    def put(sig, t, g):
        i = int(t * SR)
        if i >= n:
            return
        s = sig[: n - i] * g
        out[i:i + len(s)] += s
    wh = sfx.whoosh(0.4)
    for c in cuts[1:]:
        put(wh, max(0, c - 0.18), 0.22)
    imp = sfx.impact(0.8)
    for t in impacts:
        put(imp, t, 0.28)
    put(sfx.riser(1.2), max(0, total - END_CARD - 1.2), 0.15)
    return out / max(1.0, np.abs(out).max() / 0.97)


# ---------------------------------------------------------------- visuals
def font(sz, path=FONT):
    return ImageFont.truetype(path, sz)


def tokens(piece, words):
    """Display tokens with their (t0, t1) from the spoken-word timeline."""
    out, i = [], 0
    for tok in DISPLAY[piece].split():
        n = 1
        if "^" in tok:
            tok, n = tok.split("^")
            n = int(n)
        seg = words[i:i + n]
        out.append((tok, seg[0][1], seg[-1][2]))
        i += n
    assert i == len(words), (piece, i, len(words))
    return out


def caption_groups(tl):
    groups = []
    for p in PIECES:
        cur = []
        for tok in tokens(p["id"], tl[p["id"]]):
            cur.append(tok)
            if len(cur) == 3 or tok[0][-1] in ".?!,":
                groups.append(cur)
                cur = []
        if cur:
            groups.append(cur)
    # each group shows from its first word until the next group starts (max 0.6 s after its last word)
    res = []
    for k, g in enumerate(groups):
        end = g[-1][2] + 0.6
        if k + 1 < len(groups):
            end = min(end, groups[k + 1][0][1])
        res.append((g[0][1] - 0.04, end, g))
    return res


def rounded_mask(w, h, r):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], r, fill=255)
    return m


class Shot:
    CARD_W, MAX_H, MIN_H, CY = 920, 980, 760, 880

    def __init__(self, path, zoom_in, fx, fy, min_h=MIN_H):
        im = Image.open(os.path.join(HERE, "assets", path)).convert("RGB")
        # upscale once, gently sharpen: sources are web-sized
        s = max(1.0, 1500 / im.width)
        im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        self.im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=70, threshold=2))
        self.w = self.CARD_W
        self.h = int(np.clip(self.CARD_W * im.height / im.width, min_h, self.MAX_H))
        self.x = (W - self.w) // 2
        self.y = self.CY - self.h // 2
        self.zoom_in, self.fx, self.fy = zoom_in, fx, fy
        self.mask = rounded_mask(self.w, self.h, 42)
        bg = self.im.resize((W, int(W * im.height / im.width)))
        bg = bg.resize((int(bg.width * max(1, H / bg.height)), int(bg.height * max(1, H / bg.height))))
        l, t = (bg.width - W) // 2, (bg.height - H) // 2
        bg = bg.crop((l, t, l + W, t + H)).filter(ImageFilter.GaussianBlur(40))
        self.bg = Image.blend(bg, Image.new("RGB", (W, H), BLACK), 0.72)

    def card(self, p):
        """p: 0..1 progress through the shot."""
        z = 1.0 + 0.10 * (p if self.zoom_in else 1 - p)
        iw, ih = self.im.size
        ar = self.w / self.h
        cw = min(iw, ih * ar) / z
        ch = cw / ar
        cx = np.clip(self.fx * iw, cw / 2, iw - cw / 2)
        cy = np.clip(self.fy * ih + (ch / 2 if ch < ih else 0) * 0, ch / 2, ih - ch / 2)
        box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
        return self.im.resize((self.w, self.h), Image.BICUBIC, box=box)


def draw_chip(img, text, kind, cx, cy, scale=1.0, alpha=1.0):
    big = kind in ("big", "count")
    f = font(int((80 if big else 48) * scale))
    d = ImageDraw.Draw(img)
    tw = d.textlength(text, font=f)
    padx, pady = int((34 if big else 26) * scale), int((16 if big else 12) * scale)
    asc, desc = f.getmetrics()
    th = asc + desc * 0.2
    bw, bh = tw + 2 * padx, th + 2 * pady
    layer = Image.new("RGBA", (int(bw) + 20, int(bh) + 20), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    fill = YEL + (255,) if big else (10, 10, 12, 235)
    ld.rounded_rectangle([10, 10, 10 + bw, 10 + bh], int(18 * scale), fill=fill,
                         outline=None if big else YEL + (255,), width=max(2, int(3 * scale)))
    ld.text((10 + padx, 10 + pady - desc * 0.1), text, font=f, fill=BLACK if big else YEL)
    if alpha < 1:
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * alpha)))
    img.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))
    return bh


def ease_pop(u):
    """0..1 -> scale with a little overshoot."""
    if u >= 1:
        return 1.0
    return 0.6 + 0.4 * (1 - (1 - u) ** 3) + 0.12 * np.sin(np.pi * u)


def title_layer():
    L = Image.new("RGBA", (W, 200), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    f = font(66)
    a, b = "WHY IS HE ", "MR. IPL?"
    wa, wb = d.textlength(a, font=f), d.textlength(b, font=f)
    em = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    try:
        ImageDraw.Draw(em).text((0, 0), "🏆", font=ImageFont.truetype(EMOJI, 109), embedded_color=True)
        em = em.crop(em.getbbox()).resize((70, 70), Image.LANCZOS)
    except Exception:
        em = None
    total = wa + wb + (86 if em else 0)
    x = (W - total) / 2
    for dx, dy in [(-3, 0), (3, 0), (0, -3), (0, 3)]:
        d.text((x + dx, 60 + dy), a + b, font=f, fill=(0, 0, 0, 200))
    d.text((x, 60), a, font=f, fill=WHITE)
    d.text((x + wa, 60), b, font=f, fill=YEL)
    if em:
        L.alpha_composite(em, (int(x + wa + wb + 16), 60))
    return L


def draw_caption(img, group, t):
    f = font(70)
    d = ImageDraw.Draw(img)
    words = [g[0] for g in group]
    space = d.textlength(" ", font=f)
    widths = [d.textlength(w, font=f) for w in words]
    total = sum(widths) + space * (len(words) - 1)
    if total > 980:
        f = font(int(70 * 980 / total))
        widths = [d.textlength(w, font=f) for w in words]
        space = d.textlength(" ", font=f)
        total = sum(widths) + space * (len(words) - 1)
    x, y = (W - total) / 2, 1440
    for (w, a, b), wd in zip(group, widths):
        col = YEL if a - 0.03 <= t else WHITE
        d.text((x, y), w, font=f, fill=col, stroke_width=6, stroke_fill=(0, 0, 0))
        x += wd + space


def main():
    os.makedirs(OUT, exist_ok=True)
    words = json.load(open(os.path.join(OUT, "words.json")))
    vo, tl = build_vo(words)
    vo_end = len(vo) / SR
    total = vo_end + END_CARD
    nfr = int(total * FPS)

    def at(piece, idx):
        return tl[piece][idx][1]

    shots = [(at(s[0], s[1]) - 0.12, Shot(*s[2:])) for s in SHOTS]
    shots[0] = (0.0, shots[0][1])
    starts = [s for s, _ in shots] + [total]
    chips = [(at(p, i) - 0.05, txt, kind, stack, p) for p, i, txt, kind, stack in CHIPS]
    caps = caption_groups(tl)
    impacts = [at(p, i) for p, i in IMPACTS]
    title = title_layer()
    logo = Image.open(os.path.join(HERE, "assets", "logo.png")).convert("RGBA")
    logo_s = logo.resize((210, int(210 * logo.height / logo.width)), Image.LANCZOS)
    logo_s.putalpha(logo_s.getchannel("A").point(lambda v: int(v * 0.85)))
    logo_b = logo.resize((560, int(560 * logo.height / logo.width)), Image.LANCZOS)

    audio = mix(vo, total, starts[:-1], impacts)
    write_wav(os.path.join(OUT, "mix.wav"), audio)

    def compose(t, with_caption=True):
        k = max(i for i, s in enumerate(starts[:-1]) if s <= t)
        s0, sh = shots[k]
        s1 = starts[k + 1]
        p = (t - s0) / max(0.1, s1 - s0)
        img = sh.bg.copy().convert("RGBA")
        # card with a slide-up on entry
        u = min(1.0, (t - s0) / 0.22) if k else 1.0
        e = 1 - (1 - u) ** 3
        card = sh.card(min(1, p)).convert("RGBA")
        card.putalpha(sh.mask.point(lambda v: int(v * e)))
        dy = int(40 * (1 - e))
        shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(shadow).rounded_rectangle([sh.x - 6, sh.y + dy + 14, sh.x + sh.w + 6, sh.y + dy + sh.h + 22], 46,
                                                fill=(0, 0, 0, int(150 * e)))
        img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(18)))
        img.alpha_composite(card, (sh.x, sh.y + dy))
        ImageDraw.Draw(img).rounded_rectangle([sh.x, sh.y + dy, sh.x + sh.w - 1, sh.y + dy + sh.h - 1], 42,
                                              outline=YEL + (int(200 * e),), width=4)
        img.alpha_composite(logo_s, (sh.x + 28, sh.y + dy + 26))
        # chips belonging to this shot's time range
        live = [c for c in chips if s0 - 0.01 <= c[0] <= t and c[0] < s1]
        shown = []
        for c in live:
            if not c[3]:          # a non-stacking chip replaces whatever was there
                shown = []
            shown.append(c)
        if t >= vo_end:
            shown = []
        yb = sh.y + dy + sh.h - 40
        for c in reversed(shown):
            ct, txt, kind, stack, _ = c
            uu = (t - ct) / 0.25
            sc = ease_pop(min(1, uu))
            if kind == "count":
                v = int(5000 * min(1, (t - ct) / 0.7) ** 0.6)
                txt = f"{v:,}".replace(",", "") + " RUNS"
            h = draw_chip(img, txt, kind, W / 2, yb - (60 if kind != "small" else 40), sc, min(1, uu * 2))
            yb -= h + 18
        img.alpha_composite(title, (0, 200))
        if with_caption:
            for a, b, g in caps:
                if a <= t < b:
                    draw_caption(img, g, t)
                    break
        if t >= vo_end:   # end card over the last photo
            u2 = min(1, (t - vo_end) / 0.35)
            ov = Image.new("RGBA", (W, H), (6, 6, 8, int(215 * u2)))
            img.alpha_composite(ov)
            if u2 > 0.2:
                d = ImageDraw.Draw(img)
                lg = logo_b.copy()
                lg.putalpha(lg.getchannel("A").point(lambda v: int(v * u2)))
                img.alpha_composite(lg, ((W - lg.width) // 2, 640))
                draw_chip(img, "RAINA or KOHLI?", "big", W / 2, 900, ease_pop(min(1, (t - vo_end) / 0.3)), u2)
                f2 = font(50, FONT_XB)
                for txt, y, col in [("Comment 👇 and follow", 1030, WHITE), ("Next: Dhoni vs Yuvraj", 1110, YEL)]:
                    txt = txt.replace(" 👇", "")
                    tw = d.textlength(txt, font=f2)
                    d.text(((W - tw) / 2, y), txt, font=f2, fill=col + (int(255 * u2),))
        return img.convert("RGB")

    if os.environ.get("STILLS"):   # quick look: STILLS=1,5.5,20 python3 build.py
        for x in os.environ["STILLS"].split(","):
            compose(float(x)).save(os.path.join(OUT, f"still_{x}.png"))
        return
    video_tmp = os.path.join(OUT, "video.mp4")
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                           "-pix_fmt", "yuv420p", video_tmp], stdin=subprocess.PIPE)
    for i in range(nfr):
        ff.stdin.write(compose(i / FPS).tobytes())
        if i % 300 == 0:
            print(f"frame {i}/{nfr}", flush=True)
    ff.stdin.close()
    ff.wait()
    final = os.path.join(OUT, "raina_mr_ipl.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video_tmp, "-i", os.path.join(OUT, "mix.wav"), "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", final], check=True)
    json.dump({"duration": total, "shots": [s for s, _ in shots]}, open(os.path.join(OUT, "timeline.json"), "w"), indent=1)
    print("done", final, f"{total:.1f}s")


if __name__ == "__main__":
    main()

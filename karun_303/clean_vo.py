#!/usr/bin/env python3
"""Clean the creator's take (vo/vo_raw.m4a) into vo/vo_clean.wav, in ONE pass on the raw recording.

Rules that keep every word whole:
  * silence = audio within SIL_DB of the room's own noise floor (the room is very quiet, about -64 dB, so a breath or
    a soft word ending is NOT silence);
  * every edit point (retake cut, re-record splice, insert point) is snapped into real silence; if no silence is
    near, the script stops and says where;
  * a pause is shortened only inside silence, keeping TAIL after the last word and the rest before the next one.

Writes vo/vo_map.json: [{"raw": [r0, r1], "clean": pos} | {"fix": n, "clean": pos, "len": seconds}].
"""
import json
import os
import subprocess
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000
RAW = os.path.join(HERE, "vo", "vo_raw.m4a")

START, END = 10.45, 817.9
CUTS = [                                   # raw seconds removed: false starts and retakes (the better take is kept)
    (104.00, 113.85),   # "aur paanch mahine baad Chennai mein kismat…" stopped half-way; retake follows
    (298.05, 302.40),   # "Lekin ek baat saaf samajh lijiye" said twice
    (463.00, 477.80),   # "jis ladke ka Test average 62 tha…" first take trailed off
    (508.70, 521.38),   # "Aur sach ye bhi hai" x2 + a take with the wrong word
    (572.85, 579.90),   # Vijay Hazare line with wrong numbers (789 / 399); retake has 779 / 389
    (703.60, 715.60),   # "aath saal baad bhi England ki us har pari ko" stopped; retake follows
    (733.20, 758.20),   # "Toh asli sach kya hai…" - false starts + two full takes; the last clean take starts at 758.3
    # found by a word-level re-transcription (first attempt removed, clean retake kept)
    (75.85, 87.21),     # "Aranmula ke mandir ki taraf… snake boat paani mein palat gayi" said twice
    (152.13, 158.66),   # "aur phir Adil Rashid ki gend par chauka… score hua 300" said twice
    (258.68, 261.56),   # "kabhi dohraya na…" restarted
    (289.02, 291.51),   # "Len Hutton aur…" restarted
    (311.25, 314.85),   # "aur ye sirf main nahi keh raha, Karun ne…" stopped; whole line retaken
    (328.56, 333.70),   # "lekin asli baat ye thi, 303 banane wale aadmi ko" said twice
    (400.18, 406.12),   # "kyunki iske baad jo hua… zyada ajeeb tha" said twice
    (484.30, 487.50),   # "303 ki chamak se nikal kar" said twice
    (408.95, 413.55),   # "2018 England ka…" false start before "2018, India ka England tour"
    (444.51, 454.85),   # "Chief selector MSK Prasad ne kaha baat" said twice (7 s pause between)
    (430.20, 434.30),   # "aur tour ke baad West Indies series ki…" said twice
    (538.16, 542.00),   # "aur cricket ne pehle…" restarted
    (616.85, 620.21),   # "poore desh ne kaha, ab bas kahani poori hogi" said twice
]
# re-recorded line spliced in place of the original (raw from, raw to, file, file from, file to)
REPLACE = [(167.55, 178.85, "vo/fix_759.m4a", 1.45, 6.55)]   # "569" said for 759; the re-record says 759
# lines recorded separately, inserted at a raw time (best takes only)
INSERTS = [
    (207.60, "vo/ins_a.m4a", [(2.15, 17.85)]),                                   # "Match ke baad… wahi 303"
    (599.75, "vo/ins_b.m4a", [(0.85, 13.40), (18.55, 44.75)]),                  # IPL 2025 (2nd "40 balls" take)
    (774.60, "vo/ins_c.m4a", [(2.0, 8.5), (13.75, 17.10), (24.45, 27.15), (27.45, 30.30)]),  # "…wo humara ho gaya"
]
# where the words run together, the cut goes in the gap between these two words (raw seconds), never elsewhere
WORD_GAPS = {            # read off the 10 ms loudness curve of the raw take (word end -> next word onset)
    104.00: (103.98, 104.02),   # "...nadi se bachaya" | "aur paanch mahine..." (false start); checked both sides
    328.56: (328.58, 328.64),   # "...koi khalnayak nahi" runs into "lekin" (first take) at 328.62
    484.30: (484.10, 484.17),   # "...sirf dekh raha tha" | "303 ki chamak..." (first take) starts 484.15
    599.75: (599.73, 599.77),   # "...Vidarbha champion" | "aur phir England mein..." (checked by transcribing each side)
    444.51: (444.48, 444.55),   # "...koi jawab nahi" | "Chief selector MSK Prasad ne kaha baat" (first take)
    703.60: (703.32, 703.39),   # "...wahi kahani, wahi chakkar" ends 703.36 | "lekin dhyan dijiye..." (stopped take)
    408.95: (409.06, 409.10),   # "...zyada ajeeb tha" | "2018 England ka" (false start); checked both sides
}
SIL_DB = 13.0       # silence: within this many dB of the room floor
PAUSE = 0.42        # an ordinary pause becomes this long
TAIL = 0.20         # silence kept after a word before a cut (lets the word ring out)
BREAK = 0.80        # pause kept before a new section
BREAKS = [68.9, 118.0, 208.0, 253.5, 267.0, 346.6, 405.0, 414.0, 493.0, 557.3, 608.2, 680.5, 721.0, 727.7, 750.35,
          806.2]
JOIN_PAD = 0.30     # silence around a spliced re-record / insert

CHAIN = ("highpass=f=80,afftdn=nf=-30:nr=10,equalizer=f=220:t=q:w=1.2:g=-2,"
         "equalizer=f=3200:t=q:w=1.0:g=2.5,acompressor=threshold=-22dB:ratio=3:attack=5:release=120:makeup=3")


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-af", CHAIN, "-ac", "1", "-ar", str(SR), "-f", "f32le",
                          "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


class Env:
    """10 ms energy envelope with a silence mask relative to the recording's own floor."""

    def __init__(self, x):
        hop = int(0.01 * SR)
        n = len(x) // hop
        self.db = 20 * np.log10(np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-9)
        self.floor = np.percentile(self.db[self.db > -100], 10)
        sil = self.db < self.floor + SIL_DB
        # a silent frame only counts inside a run of at least 60 ms (never inside a word's stop consonant)
        self.sil = np.zeros_like(sil)
        i = 0
        while i < len(sil):
            if sil[i]:
                j = i
                while j < len(sil) and sil[j]:
                    j += 1
                if j - i >= 6:
                    self.sil[i:j] = True
                i = j
            else:
                i += 1

    def quiet(self, t):
        i = int(round(t / 0.01))
        return bool(self.db[max(0, i - 1):i + 2].max() < self.floor + 30)

    def silent(self, t):
        i = int(round(t / 0.01))
        return bool(self.sil[max(0, i - 2):i + 3].all())

    def snap(self, t, what, reach=0.8):
        if t in WORD_GAPS:
            lo, hi = WORD_GAPS[t]
            i0, i1 = int(lo / 0.01), int(hi / 0.01) + 1
            k = i0 + int(np.argmin(self.db[i0:i1]))
            print(f"  word gap {what}: {k * 0.01:.2f} ({self.db[k] - self.floor:.0f} dB over floor)")
            return round(k * 0.01, 2)
        if self.silent(t):
            return t
        for d in np.arange(0.01, reach, 0.01):
            for c in (t - d, t + d):
                if c > 0 and self.silent(c):
                    print(f"  snapped {what}: {t:.2f} -> {c:.2f}")
                    return round(float(c), 2)
        # words run together here: cut at the quietest 10 ms between them (never louder than a breath)
        i0, i1 = int((t - 0.25) / 0.01), int((t + 0.25) / 0.01)
        k = i0 + int(np.argmin(self.db[i0:i1]))
        if self.db[k] > self.floor + 30:
            sys.exit(f"no gap near {t:.2f} ({what}) - fix this edit point by ear")
        print(f"  tight gap {what}: {t:.2f} -> {k * 0.01:.2f} ({self.db[k] - self.floor:.0f} dB over floor)")
        return round(k * 0.01, 2)

    def runs(self, a, b, min_len=0.1):
        i, j1, out = int(a / 0.01), int(b / 0.01), []
        while i < j1:
            if self.sil[i]:
                j = i
                while j < j1 and self.sil[j]:
                    j += 1
                if (j - i) * 0.01 >= min_len:
                    out.append((i * 0.01, j * 0.01))
                i = j
            else:
                i += 1
        return out


def shorten(env, a, b, breaks=()):
    """Keep-ranges inside [a, b] with every long silence cut down to PAUSE (BREAK before a section)."""
    pieces, cur = [], a
    for r0, r1 in env.runs(a, b):
        if r0 <= a + 0.01 or r1 >= b - 0.01:
            continue                                   # edges are handled by the joins
        want = BREAK if any(abs(bt - r1) < 2.0 for bt in breaks) else PAUSE
        if r1 - r0 > want + 0.06:
            tail = min(TAIL, want / 2)
            pieces.append((cur, r0 + tail))
            cur = r1 - (want - tail)
    pieces.append((cur, b))
    return pieces


def fade(x, ms=20):
    f = int(ms / 1000 * SR)
    if len(x) > 2 * f:
        x = x.copy()
        x[:f] *= np.linspace(0, 1, f)
        x[-f:] *= np.linspace(1, 0, f)
    return x


def rms_voiced(x):
    e = np.sqrt(np.convolve(x ** 2, np.ones(2400) / 2400, "same"))
    return np.sqrt(np.mean(x[e > np.percentile(e, 60)] ** 2))


def clip_from(path, parts):
    """Best-take parts of a separately recorded file, edges snapped to silence, pauses shortened."""
    x = load(os.path.join(HERE, path))
    env = Env(x)
    segs = []
    for p0, p1 in parts:
        p0, p1 = env.snap(p0, f"{path} {p0}"), env.snap(p1, f"{path} {p1}")
        for s0, s1 in shorten(env, p0, p1):
            segs.append(fade(x[int(s0 * SR):int(s1 * SR)]))
        segs.append(np.zeros(int(PAUSE * SR)))
    return np.concatenate(segs[:-1])


def main():
    a = load(RAW)
    env = Env(a)
    print(f"room floor {env.floor:.1f} dB; silence below {env.floor + SIL_DB:.1f} dB")

    ref = rms_voiced(a[int(150 * SR):int(200 * SR)])
    removed, fixes = [], []
    for c0, c1 in CUTS:
        removed.append((env.snap(c0, f"cut start {c0}"), env.snap(c1, f"cut end {c1}")))
    for r0, r1, f, f0, f1 in REPLACE:
        r0, r1 = env.snap(r0, f"replace {r0}"), env.snap(r1, f"replace {r1}")
        removed.append((r0, r1))
        b = clip_from(f, [(f0, f1)])
        fixes.append((r1, b * ref / rms_voiced(b)))
    for at, f, parts in INSERTS:
        at = env.snap(at, f"insert {at}")
        removed.append((at, at))
        b = clip_from(f, parts)
        fixes.append((at, b * ref / rms_voiced(b)))

    keep, t = [], START
    for c0, c1 in sorted(removed):
        if c0 > t:
            keep.append((t, c0))
        t = max(t, c1)
    keep.append((t, END))

    events = []                                   # (raw time, kind, payload); a fix sits before audio at the same time
    for k0, k1 in keep:
        for s0, s1 in shorten(env, k0, k1, BREAKS):
            if s1 - s0 > 0.02:
                events.append((s0, 1, (s0, s1)))
    for n, (at, seg) in enumerate(sorted(fixes, key=lambda f: f[0])):
        events.append((at, 0, (n, seg)))
    events.sort(key=lambda e: (e[0], e[1]))

    out, vmap, pos = [], [], 0.0
    for at, kind, p in events:
        if kind == 0:
            n, seg = p
            pad = np.zeros(int(JOIN_PAD * SR))
            out += [pad, fade(seg), pad]
            vmap.append({"fix": n, "clean": round(pos + JOIN_PAD, 3), "len": round(len(seg) / SR, 3)})
            pos += len(seg) / SR + 2 * JOIN_PAD
            continue
        s0, s1 = p
        out.append(fade(a[int(s0 * SR):int(s1 * SR)]))
        vmap.append({"raw": [round(s0, 3), round(s1, 3)], "clean": round(pos, 3)})
        pos += (int(s1 * SR) - int(s0 * SR)) / SR

    bad = 0                                       # every join must sit in silence
    for p in vmap:
        for t in p.get("raw", []):
            if START + 0.1 < t < END - 0.1 and not env.quiet(t):
                bad += 1
                print(f"  join not in silence at raw {t:.2f}")
    y = np.concatenate(out)
    y = y / (np.abs(y).max() + 1e-9) * 0.92
    with wave.open(os.path.join(HERE, "vo", "vo_clean.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((y * 32767).astype(np.int16).tobytes())
    json.dump(vmap, open(os.path.join(HERE, "vo", "vo_map.json"), "w"), indent=0)
    print(f"clean VO: {int(pos // 60)}:{pos % 60:04.1f}  ({len(vmap)} pieces, {bad} joins outside silence)")


if __name__ == "__main__":
    main()

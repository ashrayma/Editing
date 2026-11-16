#!/usr/bin/env python3
"""Karun 303 long-form, v2: fast-paced, busy, many styles (fx.py). Same voice/timing source as make_long.py.

    python3 make_v2.py           -> out/Karun_303_v2.mp4
    python3 make_v2.py --sheet   -> out/chk/sheet_v2.jpg

Shot times are written in first-pass clean-VO seconds (vo/clean_lines.txt) and mapped onto the final voice
(vo/retime.json, + vo/retime2.json if present) so the edit follows every pause/retake cut automatically.
"""
import json
import math
import os
import subprocess
import sys
import wave
from multiprocessing import Pool

import numpy as np
from PIL import Image

import fx
import make_long as L
from fx import (BLACK, BOLD, GREEN, GREY, INK, RED, WHITE, Y, bars, boxline, count_up, flip_board, kinetic,
                lower_third, odometer, outline_fill, quote_card, stack, stamp, ticker_pop, typewriter)

HERE = L.HERE
W, H, FPS = L.W, L.H, L.FPS
OUT = L.OUT


# ============================================================================ time maps (old clean s -> final s)

def load_maps():
    maps = []
    for f in ("retime.json", "retime2.json"):
        p = os.path.join(HERE, "vo", f)
        if os.path.exists(p):
            maps.append(json.load(open(p)))
    return maps


MAPS = load_maps()


def fwd(t):
    for m in MAPS:
        best = None
        for a0, a1, n0 in m:
            if a0 <= t <= a1:
                best = n0 + (t - a0)
                break
            if t < a0:
                best = n0
                break
        t = best if best is not None else m[-1][2] + (m[-1][1] - m[-1][0])
    return t


def back(t):
    for m in reversed(MAPS):
        best = None
        for a0, a1, n0 in m:
            if n0 <= t <= n0 + (a1 - a0):
                best = a0 + (t - n0)
                break
            if t < n0:
                best = a0
                break
        t = best if best is not None else m[-1][1]
    return t


# ============================================================================ sources

def P(name):
    return lambda lt: L.photo(name)


def C(name, speed=0.5, start=0.0):
    return lambda lt: L.clip_frame(name, lt, speed, start)


def full(src, z0=1.04, z1=1.18, f=(0.5, 0.35), f2=None, gray=0.0, dark=1.0):
    return lambda lt, dur: fx.fs_full(src(lt), lt, dur, z0=z0, z1=z1, f=f, f2=f2, gray=gray, dark=dark)


def pol(src, tilt=-4, label=None, fy=0.35):
    return lambda lt, dur: fx.fs_polaroid(src(lt), lt, dur, tilt, label=label, fy=fy)


def card(src, fy=0.4, fx_=0.5):
    return lambda lt, dur: fx.fs_card(src(lt), lt, dur, fy=fy, fx=fx_)


def split(srcs, labels=None):
    return lambda lt, dur: fx.fs_split([s(lt) for s in srcs], lt, dur, labels)


def circ(src, fy=0.3, fx_=0.5):
    return lambda lt, dur: fx.fs_circle(src(lt), lt, dur, fy=fy, fx=fx_)


def film(names):
    return lambda lt, dur: fx.fs_film([L.photo(n) for n in names], lt, dur)


def cut(name, word="303", col=Y, size=640, x=0.5, tx=None):
    if tx is None and len(word) <= 4:          # short words sit beside the subject, not hidden behind him
        x, tx = 0.33, 0.66
    return lambda lt, dur: fx.fs_cutout(name, L.photo(name), lt, dur, word, col, size, tx=tx, x=x)


def tv(src, tag="REPLAY", fy=0.4):
    return lambda lt, dur: fx.fs_tv(src(lt), lt, dur, tag, fy=fy)


def pl(tint=(1.0, 0.82, 0.35)):
    return lambda lt, dur: L.plate(lt * 1.3 + 5, tint)


def panel(name, w=1180):
    f = L.BG_PANEL(name, w)
    return lambda lt, dur: f(0, lt, dur)


# ============================================================================ the shot list (old clean seconds)
# S(t0, t1, background, transition, overlays...) ; overlay = callable(base, t) with t in old clean seconds

SH = []


def S(t0, t1, bg, tr="zoom", *ovs, hit=None):
    SH.append((t0, t1, bg, tr, ovs, hit))


def K(t0, t1, text, size=120, cy=520, **k):
    return lambda b, t: kinetic(b, t, t0, t1, text, size, cy, **k)


def CAP(t0, t1, l1, l2=None):
    return L.cap(t0, t1, l1, l2)


def BX(t0, t1, text, cy=860, size=66, col=Y, fg=INK, cx=W / 2):
    return lambda b, t: boxline(b, t, t0, t1, text, size, cx, cy, col, fg)


def CNT(t0, t1, v, sub=None, size=300, cy=470, col=Y, **k):
    return lambda b, t: count_up(b, t, t0, t1, v, sub, size, cy, col, **k)


def ODO(t0, t1, text, sub=None, size=280, cy=470, col=Y):
    return lambda b, t: odometer(b, t, t0, t1, text, size, cy, col, sub)


def FLIP(t0, t1, text, sub=None, cy=470):
    return lambda b, t: flip_board(b, t, t0, t1, text, cy, sub)


def OUTL(t0, t1, text, size=260, cy=500, col=Y):
    return lambda b, t: outline_fill(b, t, t0, t1, text, size, cy, col)


def TYPE(t0, t1, text, size=72, cy=520, col=WHITE):
    return lambda b, t: typewriter(b, t, t0, t1, text, size, cy, col)


def STK(t0, t1, rows, cy=520):
    return lambda b, t: stack(b, t, t0, t1, rows, cy)


def LT(t0, t1, name, role):
    return lambda b, t: lower_third(b, t, t0, t1, name, role)


def Q(t0, t1, who, text, cy=520, ins="rise"):
    return lambda b, t: quote_card(b, t, t0, t1, who, text, cy, ins)


def STP(t0, t1, word, cx=W / 2, cy=540, color=RED, angle=-8, size=150):
    return lambda b, t: stamp(b, t, t0, t1, word, cx, cy, color, angle, size)


def BARS(t0, t1, vals, labels, hot=None, title=None, maxv=None):
    return lambda b, t: bars(b, t, t0, t1, vals, labels, hot, title, maxv)


def TICK(t0, t1, vals, label=None, cy=500, last=None):
    return lambda b, t: ticker_pop(b, t, t0, t1, vals, label, cy, WHITE, last)


def TWEET(t0, t1):
    return L.photo_card(t0, t1, "dear_cricket_post", 1050, 500)


# ---- HOOK
S(0.0, 4.2, panel("sehwag_triple_bat_helmet", 760), "flash", BX(0.3, 4.1, "ONLY TWO INDIANS HAVE SCORED 300", 920, 60))
S(4.2, 8.4, pl(), "whip", K(4.3, 8.3, "ONE: *SEHWAG.* TWO: …?", 130, 500))
S(8.4, 13.5, full(C("closeD", 0.45)), "glitch", ODO(9.6, 13.4, "3", "TESTS AFTER THE 303", 340, 440), hit=9.6)
S(13.5, 17.2, tv(C("broad", 0.5)), "zoom", CAP(13.6, 17.1, "381 balls.", "Three dropped chances."))
S(17.2, 21.1, pl((0.7, 0.7, 0.9)), "whip", K(17.3, 21.0, "EVERY *MISTAKE* COST ENGLAND", 110, 500))
S(21.1, 27.8, card(C("dressing100", 0.5)), "zoom", BX(21.3, 27.7, "\"INDIA'S NO.5 FOR THE NEXT 10 YEARS\"", 900, 56))
S(27.8, 31.2, pl((0.6, 0.6, 0.75)), "flash", FLIP(28.0, 31.1, "3 MONTHS", "TO HIS LAST TEST"), hit=28.0)
S(31.2, 35.2, pl((0.9, 0.5, 0.4)), "glitch", OUTL(31.3, 35.1, "8 YEARS", 300), BX(32.4, 35.1, "AND HE DIDN'T EVEN KNOW", 780, 56, WHITE), hit=31.3)
S(35.2, 41.5, cut("karun_303_chennai_2016", "303", Y, 700), "flash", hit=35.4)
S(41.5, 45.6, pl((0.7, 0.7, 0.85)), "whip", TYPE(41.6, 45.5, "\"Dropped. A huge injustice.\"", 104))
S(45.6, 49.3, pl((0.9, 0.5, 0.4)), "zoom", STP(45.8, 49.2, "NOT THE WHOLE STORY", angle=-6, size=110), hit=45.8)
S(49.3, 53.3, split([C("closeA", 0.2), P("karun_2025_portrait_fence")], ["2016", "2025"]), "whip")
S(53.3, 58.2, pl(), "zoom", K(53.4, 58.1, "303 WASN'T HIS DEFENCE. IT WAS HIS *SENTENCE.*", 104, 520))
# ---- RIVER
S(58.2, 65.0, full(P("pampa_river"), 1.05, 1.25, (0.5, 0.6), (0.5, 0.4), dark=0.9), "black", CAP(61.9, 64.9, "Pampa river, Kerala", "July 2016"))
S(65.0, 71.0, pol(P("pampa_river"), -5, "ARANMULA · JULY 2016", 0.55), "whip", BX(65.4, 70.9, "A SNAKE BOAT CAPSIZED", 900, 58, RED, WHITE))
S(71.0, 75.2, pl((0.4, 0.6, 0.9)), "zoom", CNT(71.2, 75.1, 100, "PEOPLE ON BOARD", 300, 440, WHITE, prefix="~"))
S(75.2, 78.9, pl((0.4, 0.6, 0.9)), "flash", ODO(75.4, 78.8, "2", "NEVER CAME BACK", 340, 440, RED))
S(78.9, 85.4, circ(C("closeA", 0.18), 0.25), "zoom", LT(79.6, 85.3, "KARUN NAIR, 24", "on board · rescued"))
S(85.4, 89.0, full(C("sweep", 0.45), dark=0.8), "whip", K(85.5, 88.9, "SAVED BY THE *RIVER.*", 120, 470))
S(89.0, 92.9, full(C("sweep", 0.45, 1.2), dark=0.8), "zoom", K(89.1, 92.8, "FIVE MONTHS LATER: *CHENNAI.*", 110, 470))
# ---- CHENNAI
S(92.9, 97.8, pl(), "flash", FLIP(93.2, 97.7, "4 13", "TEST DEBUT · NOV 2016"))
S(97.8, 102.0, tv(C("closeC", 0.4), "NOV 2016"), "whip", CAP(97.9, 101.9, "A slow start.", "Nobody noticed."))
S(102.0, 106.5, full(C("crowd", 0.5)), "zoom", LT(102.3, 106.4, "CHENNAI · DEC 2016", "5th Test vs England"))
S(106.5, 111.8, tv(C("drop34", 0.38), "DROPPED ON 34"), "glitch", BX(108.0, 111.7, "ALASTAIR COOK · FIRST SLIP", 900, 58), hit=106.6)
S(111.8, 115.3, full(C("hundred", 0.45)), "flash", ODO(112.0, 115.2, "100", "MAIDEN HUNDRED · 185 BALLS", 260, 440), hit=112.0)
S(115.3, 121.4, panel("kl_rahul_199_reuters_credit", 1180), "whip", BX(115.6, 121.3, "KL RAHUL · 199 · ONE RUN SHORT", 960, 58, RED, WHITE))
S(121.4, 125.9, full(C("bat150", 0.45)), "zoom", K(121.5, 125.8, "DROPPED *AGAIN* ON 217", 120, 480))
S(125.9, 135.6, full(C("shot300", 0.42)), "whip", CAP(126.0, 132.0, "A four off Adil Rashid…", None), CNT(132.2, 135.5, 300, None, 360, 470, Y, dur=1.4), hit=132.2)
S(135.6, 140.0, cut("karun_303_chennai_2016", "303*", Y, 600), "flash", BX(136.0, 139.9, "381 BALLS · 32 FOURS · 4 SIXES", 960, 58), hit=135.7)
S(140.0, 145.4, tv(C("hug300", 0.45), "INDIA 759/7 DEC"), "whip", FLIP(140.2, 145.3, "759/7", "INDIA'S HIGHEST TEST TOTAL (THEN)", 430))
S(145.4, 151.0, full(C("kohli300", 0.4)), "zoom", STK(145.5, 150.9, [("WON BY AN INNINGS & 75", 110, WHITE), ("SERIES 4-0", 140, Y)]))
S(151.0, 160.9, panel("sehwag_getty_credit", 820), "whip", Q(153.2, 160.8, "Virender Sehwag", "Welcome to the 300 club. It was lonely here for 12 years 8 months.", 520))
S(160.9, 165.2, pl(), "flash", STK(161.0, 165.1, [("MAIDEN HUNDRED", 100, WHITE), ("→ TRIPLE HUNDRED", 100, Y)]))
S(165.2, 169.4, pl(), "glitch", ODO(165.3, 169.3, "3RD", "EVER · AFTER SOBERS & SIMPSON", 300, 440))
S(169.4, 173.3, pl((0.9, 0.7, 0.3)), "flash", CNT(169.5, 173.2, 160, "TEST AVERAGE AFTER 3 TESTS", 320, 450), hit=169.5)
S(173.3, 178.0, full(C("walk381", 0.4), dark=0.8), "zoom", BX(173.6, 177.9, "\"NO PRESSURE AT 300?\"", 900, 60, WHITE))
S(178.0, 185.0, pl((0.4, 0.6, 0.9)), "whip", Q(178.1, 184.9, "Karun Nair, Dec 2016", "What's the pressure of a ton after cheating death?", 500, "drop"))
S(185.0, 189.9, full(C("closeB", 0.4), dark=0.75), "zoom", K(185.1, 189.8, "BUT SOMETHING ELSE WAS COMING: *303*", 104, 480))
# ---- CEILING
S(189.9, 197.9, pl(), "flash", K(190.0, 197.8, "HOW IS A BATTER JUDGED? *BY* *HIS* *LAST* *SCORE.*", 104, 500))
S(197.9, 209.0, pl((0.8, 0.8, 0.9)), "whip", BARS(198.0, 208.9, [4, 13, 303], ["MOHALI", "MUMBAI", "CHENNAI"], 2, "NEXT INNINGS: COMPARED TO 30? OR 303?"))
S(209.0, 214.5, split([C("closeA", 0.2), C("closeD", 0.3)], ["BEFORE: A YOUNG BATTER", "AFTER: THE 303 GUY"]), "zoom")
S(214.5, 220.2, pl(), "glitch", STK(214.6, 220.1, [("YOUNG BATTER → SCORE RUNS", 84, WHITE), ("303 GUY → PROVE IT WASN'T ONE DAY", 84, Y)]))
S(220.2, 224.0, pl((0.9, 0.5, 0.4)), "flash", K(220.3, 223.9, "WHY *NO* RUNS?", 160, 500), hit=220.3)
S(224.0, 228.0, pl((0.9, 0.5, 0.4)), "flash", K(224.1, 227.9, "WHY *NO* 300?", 160, 500), hit=224.1)
S(228.0, 232.6, cut("karun_303_chennai_2016", "BENCHMARK", WHITE, 300), "zoom", BX(228.3, 232.5, "NOT A CROWN.", 140, 70, WHITE))
S(232.6, 238.5, full(C("armclose", 0.4), dark=0.85), "whip", TYPE(232.8, 238.4, "Your best day, declared \"never to be repeated\"…", 64, 880))
S(238.5, 244.9, pl((0.6, 0.6, 0.8)), "zoom", K(238.6, 244.8, "…HOW WOULD *TOMORROW* FEEL?", 120, 500))
# ---- NEXT TEST
S(244.9, 251.3, pl((0.7, 0.7, 0.85)), "flash", LT(245.2, 251.2, "HYDERABAD · 9 FEB 2017", "the very next Test"), K(245.0, 251.2, "303 → NEXT TEST", 140, 440))
S(251.3, 255.5, pl((0.9, 0.5, 0.4)), "glitch", STP(251.4, 255.4, "BENCHED", size=190), hit=251.4)
S(255.5, 262.4, card(P("kohli_presser_2017"), 0.35), "whip", BX(255.8, 262.3, "KOHLI: \"RAHANE WILL COME BACK\"", 960, 60))
S(262.4, 268.5, split([P("sehwag_triple_bat_helmet"), P("karun_303_chennai_2016")], ["HUTTON · INZAMAM: INJURED", "KARUN: FIT"]), "zoom")
S(268.5, 275.5, pl((0.9, 0.5, 0.4)), "flash", K(268.6, 275.4, "FIT. *STILL* *OUT.*", 170, 500), hit=272.6)
S(275.5, 284.2, pl((0.6, 0.7, 0.8)), "whip", STK(275.6, 284.1, [("RAHANE DID NOTHING WRONG.", 100, WHITE), ("SENIOR. PROVEN.", 90, GREY), ("THE TEAM CHOSE EXPERIENCE.", 100, Y)]))
S(284.2, 293.2, pl(), "zoom", Q(284.3, 293.1, "Karun's father", "It was fair to pick Rahane.", 520, "drop"))
S(293.2, 299.1, pl((0.5, 0.6, 0.9)), "whip", Q(293.3, 299.0, "Karun Nair", "One game doesn't overshadow two years of hard work.", 520, "pop"))
S(299.1, 305.0, pl(), "flash", STK(299.2, 304.9, [("NO CONSPIRACY.", 120, WHITE), ("NO VILLAIN.", 140, Y)]))
S(305.0, 311.5, full(C("dressing150", 0.4), gray=0.6, dark=0.75), "zoom", K(305.1, 311.4, "NOBODY HAD TO BE *WORSE* THAN HIM", 104, 480))
S(311.5, 318.8, pl((0.9, 0.7, 0.3)), "whip", K(311.6, 318.7, "WHAT HE DIDN'T HAVE: *TIME.*", 130, 500))
# ---- AUSTRALIA
S(318.8, 323.0, full(P("karun_bowled_bengaluru_2017"), 1.04, 1.14, (0.62, 0.45)), "flash", LT(319.0, 322.9, "vs AUSTRALIA", "March 2017"), hit=319.0)
S(323.0, 328.9, pl(), "whip", TICK(323.1, 328.8, [26, 0, 23, 5], "54 RUNS · 4 INNINGS", 480, RED))
S(328.9, 335.4, pl((0.4, 0.8, 0.5)), "zoom", FLIP(329.0, 335.3, "2-1", "INDIA WON THE SERIES"))
S(335.4, 341.4, full(C("closeC", 0.35), gray=0.5, dark=0.75), "whip", K(335.5, 341.3, "THE QUESTIONS FOUND *HIM.*", 120, 480))
S(341.4, 350.8, pl(), "flash", BARS(341.5, 350.7, [303, 30], ["THE RULER", "NORMAL"], 0, "HIS FAILURE WAS MEASURED AGAINST 303"))
S(350.8, 358.0, pl((0.7, 0.7, 0.8)), "zoom", STK(350.9, 357.9, [("4 BAD INNINGS: NORMAL.", 100, WHITE), ("FOR THE 303 GUY?", 100, Y)]))
S(358.0, 366.0, pl((0.9, 0.5, 0.4)), "glitch", STP(358.1, 362.4, "NOT FORM", W / 2, 420, GREY, -6, 120), OUTL(361.0, 365.9, "PROOF.", 280, 620, RED), hit=361.0)
S(366.0, 374.4, full(P("karun_bowled_bengaluru_2017"), 1.2, 1.32, (0.66, 0.5), gray=0.9, dark=0.7), "black", LT(366.3, 374.3, "DHARAMSALA · 25 MAR 2017", "his last Test (for 8 years)"))
S(374.4, 383.2, pl(), "flash", K(374.5, 383.1, "THE STORY SHOULD HAVE ENDED HERE. *IT* *DIDN'T.*", 104, 500))
# ---- 2018
S(383.2, 392.1, pl((0.6, 0.65, 0.8)), "whip", FLIP(383.4, 392.0, "0", "TESTS PLAYED · ENGLAND TOUR 2018 (IN THE SQUAD)"))
S(392.1, 398.5, circ(P("vihari_batting_2021era"), 0.3), "zoom", LT(392.5, 398.4, "HANUMA VIHARI", "debut at The Oval"))
S(398.5, 406.0, pl((0.9, 0.5, 0.4)), "glitch", BX(398.6, 405.9, "WEST INDIES SQUAD: KARUN — DROPPED", 540, 70, RED, WHITE), hit=398.7)
S(406.0, 412.0, card(P("msk_prasad_kohli"), 0.35, 0.3), "whip", Q(406.1, 411.9, "Karun Nair", "No communication.", 820, "slide_l"))
S(412.0, 422.0, full(P("msk_prasad_kohli"), 1.05, 1.15, (0.25, 0.35)), "zoom", Q(412.1, 421.9, "Chief selector MSK Prasad", "We spoke to him. He's in the plans.", 820, "slide_r"))
S(422.0, 430.2, pl(), "flash", CNT(422.2, 430.1, 62.33, "TEST AVERAGE · WATCHING FROM THE DRESSING ROOM", 260, 450, Y, fmt=2))
S(430.2, 438.8, pl((0.8, 0.8, 0.85)), "whip", TYPE(430.3, 438.7, "From 303… to a name on a squad list.", 80))
# ---- LOST YEARS
S(438.8, 443.8, pl((0.75, 0.75, 0.8)), "flash", ODO(439.0, 443.7, "2018", "2019 · 2020 · 2021 · 2022", 260, 450, WHITE))
S(443.8, 449.0, pl((0.75, 0.75, 0.8)), "glitch", OUTL(443.9, 448.9, "CONSISTENCY", 200, 500, WHITE), hit=443.9)
S(449.0, 454.3, pl(), "whip", STK(449.1, 454.2, [("FITNESS? CONSISTENCY.", 80, GREY), ("TECHNIQUE? CONSISTENCY.", 80, GREY), ("COMBINATION? CONSISTENCY.", 80, Y)]))
S(454.3, 462.6, pol(P("karun_karnataka_helmet_raised"), 4, "KARNATAKA", 0.25), "zoom", BX(454.6, 462.5, "DEC 2022: OUT OF KARNATAKA'S SIDE", 960, 58, RED, WHITE))
S(462.6, 470.8, pl(), "flash", TWEET(462.7, 470.7))
S(470.8, 480.0, film(["karun_northants_hundred", "karun_karnataka_bat_raised", "karun_nets_2025"]), "whip", LT(471.0, 479.9, "NORTHAMPTONSHIRE", "county cricket · 2023"))
S(480.0, 490.5, full(P("karun_northants_hundred"), 1.04, 1.16, (0.5, 0.3)), "zoom", K(480.1, 490.4, "FIRST COUNTY HUNDRED vs *SURREY*", 104, 300))
# ---- VIDARBHA
S(490.5, 495.2, split([P("karun_karnataka_bat_raised"), P("karun_vidarbha_hundred")], ["KARNATAKA", "VIDARBHA"]), "whip")
S(495.2, 499.5, pl(), "zoom", CNT(495.3, 499.4, 690, "YEAR ONE · RANJI FINAL LOST", 300, 450, WHITE))
S(499.5, 503.6, pl((0.9, 0.7, 0.3)), "flash", K(499.6, 503.5, "THEN 2024-25 WAS LIKE A *FILM*", 120, 500))
S(503.6, 508.6, pl((0.9, 0.7, 0.3)), "glitch", ODO(503.8, 508.5, "779", "VIJAY HAZARE · AVG 389", 320, 440), hit=503.8)
S(508.6, 511.8, pl((0.9, 0.7, 0.3)), "zoom", TICK(508.7, 511.7, [100, 100, 100, 100, 100], "5 HUNDREDS · RECORD-EQUALLING", 480))
S(511.8, 519.8, cut("karun_vidarbha_hundred", "135", Y, 560), "whip", BX(512.5, 519.7, "RANJI FINAL vs KERALA: 86 & 135", 960, 58))
S(519.8, 522.3, cut("karun_vidarbha_hundred", "CHAMPIONS", Y, 300), "flash", hit=519.9)
# ---- IPL 2025 (insert)
S(522.3, 526.0, pl((0.4, 0.55, 1.0)), "whip", LT(522.5, 525.9, "IPL 2025", "Delhi Capitals"), K(522.4, 525.9, "ANOTHER *DOOR* OPENED", 120, 440))
S(526.0, 530.6, pl((0.4, 0.55, 1.0)), "flash", ODO(526.1, 530.5, "1,077", "DAYS SINCE HIS LAST IPL GAME", 280, 440), hit=526.1)
S(530.6, 535.2, pl((0.4, 0.55, 1.0)), "zoom", STK(530.7, 535.1, [("vs MUMBAI INDIANS", 110, WHITE), ("BALL IN BUMRAH'S HAND", 110, Y)]))
S(535.2, 538.9, pl((0.4, 0.55, 1.0)), "glitch", FLIP(535.3, 538.8, "89(40)", "12 FOURS · 5 SIXES"), hit=535.3)
S(538.9, 545.4, pl((0.4, 0.55, 1.0)), "flash", CNT(539.0, 545.3, 18, "OFF ONE BUMRAH OVER · MOST BY AN INDIAN IN THE IPL", 380, 440, Y), hit=539.0)
S(545.4, 548.2, pl((0.9, 0.5, 0.4)), "glitch", STP(545.5, 548.1, "LOST BY 12", size=150), hit=545.5)
S(548.2, 554.0, pl(), "whip", Q(548.3, 553.9, "Karun Nair", "No value of individual runs if the team loses.", 520, "drop"))
S(554.0, 561.9, pl((0.9, 0.7, 0.3)), "zoom", K(554.1, 561.8, "THE MAN MEASURED BY *ONE* *SCORE* SAYS SCORES DON'T MATTER", 96, 500))
S(561.9, 566.5, pl(), "flash", ODO(562.0, 566.4, "204", "INDIA A vs ENGLAND LIONS", 320, 440), hit=562.0)
S(566.5, 569.7, pl((0.9, 0.5, 0.4)), "glitch", K(566.6, 569.6, "THE WALL *BROKE.*", 160, 500), hit=566.6)
# ---- 2025 RETURN
S(569.7, 572.5, full(P("karun_arrival_2025"), 1.04, 1.14), "whip", LT(569.9, 572.4, "HEADINGLEY", "20 June 2025"))
S(572.5, 575.9, pl(), "flash", ODO(572.6, 575.8, "3,006", "DAYS · BACK IN AN INDIA TEST CAP", 280, 440), hit=572.6)
S(575.9, 581.6, card(P("karun_nets_2025"), 0.3), "zoom", BX(576.2, 581.5, "\"NOW THE STORY WILL BE COMPLETE\"", 960, 58, WHITE))
S(581.6, 586.0, tv(P("karun_duck_headingley_2025"), "4 BALLS · 0", 0.35), "glitch", hit=581.7)
S(586.0, 594.5, pl(), "whip", BARS(586.1, 594.4, [0, 20, 31, 26, 40, 14], ["HDG", "HDG", "EDG", "EDG", "LORD'S", "LORD'S"], None, "A START. EVERY TIME. \"THAT'S IT?\"", 60))
S(594.5, 598.4, full(P("karun_walkoff_lords_2025"), 1.05, 1.16), "zoom", K(594.6, 598.3, "4TH TEST: *LEFT* *OUT*", 120, 300))
S(598.4, 603.9, pl(), "flash", LT(598.6, 603.8, "THE OVAL", "5th Test · Aug 2025"), OUTL(599.5, 603.8, "57", 360, 470))
S(603.9, 607.5, full(P("karun_oval_fifty_2025"), 1.04, 1.14), "whip", BX(604.2, 607.4, "FIRST TEST FIFTY IN ~9 YEARS", 960, 58))
S(607.5, 611.8, panel("dk_getty_credit", 1000), "zoom", Q(607.6, 611.7, "Dinesh Karthik", "His career is well and truly back.", 880, "slide_l"))
S(611.8, 618.0, tv(P("karun_dejected_2025_close"), "LBW · REVIEW LOST", 0.3), "glitch", CAP(612.0, 617.9, "Josh Tongue.", "Then 17."), hit=612.0)
S(618.0, 623.6, pl(), "flash", BARS(618.1, 623.5, [205, 303], ["8 INNINGS · 2025", "ONE INNINGS · 2016"], 1, "AVERAGE 25.62"))
S(623.6, 627.6, circ(P("karun_nets_2025"), 0.3), "whip", Q(623.7, 627.5, "Karun Nair", "I wasn't trying to prove anything.", 880, "rise"))
S(627.6, 638.3, pl((0.8, 0.7, 0.6)), "zoom", K(627.7, 638.2, "EVERYONE AROUND HIM WAS PROVING ONE THING: *303* WASN'T *ONE* *DAY*", 96, 500))
# ---- VERDICT
S(638.3, 643.4, card(P("agarkar_presser"), 0.35), "flash", BX(638.6, 643.3, "WEST INDIES SQUAD: NOT PICKED", 960, 60, RED, WHITE))
S(643.4, 650.2, full(P("agarkar_presser"), 1.06, 1.18, (0.5, 0.3)), "zoom", Q(643.5, 650.1, "Chief selector Ajit Agarkar", "We expected more from Karun in England.", 820, "drop"), hit=647.9)
S(650.2, 654.6, pl(), "whip", Q(650.3, 654.5, "Karun Nair", "I deserved more than one series.", 520, "pop"))
S(654.6, 660.8, pol(P("karun_karnataka_bat_raised"), -3, "BACK TO KARNATAKA", 0.3), "zoom", BX(655.0, 660.7, "BACK-TO-BACK RANJI HUNDREDS", 960, 58))
S(660.8, 666.3, pl((0.9, 0.7, 0.3)), "flash", K(660.9, 666.2, "8 YEARS LATER, STILL MEASURED BY *303*", 110, 500), hit=665.2)
S(666.3, 671.3, pl(), "whip", STK(666.4, 671.2, [("RAHANE?", 120, WHITE), ("THE SELECTORS?", 120, WHITE), ("LUCK?", 120, WHITE)]))
S(671.3, 672.9, pl((0.9, 0.5, 0.4)), "glitch", STP(671.4, 672.8, "ALL WRONG", size=170), hit=671.4)
S(672.9, 680.0, pl(), "flash")
# ---- TRUTH
S(680.0, 686.0, cut("karun_303_chennai_2016", "?", WHITE, 700), "zoom", K(680.1, 685.9, "WHO ENDED KARUN NAIR'S *CAREER?*", 104, 160))
S(686.0, 690.5, pl(), "whip", STK(686.1, 690.4, [("NOT RAHANE.", 120, WHITE), ("NOT THE SELECTORS.", 120, WHITE)]))
S(690.5, 694.0, pl((0.9, 0.7, 0.3)), "flash", K(690.6, 693.9, "HIS BIGGEST BATTLE: HIS BIGGEST *INNINGS*", 100, 500))
S(694.0, 698.0, film(["pampa_river", "msk_prasad_kohli", "karun_karnataka_helmet_raised"]), "whip", STK(694.1, 697.9, [("NOT A RIVER. NOT A LIST. NOT 8 YEARS.", 80, WHITE)], 880))
S(698.0, 702.1, pl((0.9, 0.5, 0.4)), "glitch", OUTL(698.1, 702.0, "A NUMBER.", 260, 500, Y), hit=698.1)
S(702.1, 704.6, pl(), "flash", K(702.2, 704.5, "KARUN NEVER CALLED 303 A *BURDEN*", 110, 500))
S(704.6, 710.7, pl((0.5, 0.6, 0.9)), "zoom", Q(704.7, 710.6, "Karun Nair", "It is definitely not a burden.", 520, "pop"))
S(710.7, 715.1, pl((0.5, 0.6, 0.9)), "whip", Q(710.8, 715.0, "Karun Nair", "It is something that is never going to go away from me.", 520, "drop"))
S(715.1, 719.1, pl(), "flash", STK(715.2, 719.0, [("IT NEVER WENT AWAY.", 110, WHITE), ("IT JUST STOPPED BEING HIS.", 110, Y)]))
S(719.1, 730.4, full(P("karun_dejected_2025_close"), 1.04, 1.2, (0.5, 0.25), gray=0.5, dark=0.75), "zoom", K(719.2, 730.3, "WE MADE HIM A *CHARACTER*", 120, 300))
S(730.4, 735.0, pl(), "whip", OUTL(730.5, 734.9, "\"THE 303 GUY\"", 200, 500, WHITE))
S(735.0, 740.8, pl((0.9, 0.5, 0.4)), "glitch", STK(735.1, 740.7, [("\"THE VICTIM\"", 140, GREY), ("ASKED FOR ONE THING: ANOTHER 303", 80, Y)]))
S(740.8, 750.0, cut("karun_2025_portrait_fence", "KARUN NAIR", Y, 260), "flash", STP(745.3, 748.0, "THE 303 GUY", W / 2, 300, GREY, -4, 110))
S(750.0, 9999, full(C("arms300", 0.3), dark=0.7), "zoom", K(750.1, 9999, "OUT FOR *30* IN CHENNAI — WOULD HE STILL BE PLAYING?", 104, 480))


# ============================================================================ holds (old clean s): sub-shots inside

def hold_title(base, t, lt, dur):
    outline_fill(base, lt, 0.1, dur, "KARUN NAIR", 220, 450, Y)
    boxline(base, lt, 0.9, dur, "303 DIDN'T SAVE HIM. IT ENDED HIM.", 62, W / 2, 640, WHITE, INK)


def hold_chapter(n, title, sub):
    def ov(base, t, lt, dur):
        boxline(base, lt, 0.0, dur, f"CHAPTER {n}", 46, W / 2, 400)
        kinetic(base, lt, 0.2, dur, title, 150, 560, step=0.1, ins="drop")
        if sub:
            fx.place(base, fx.shadowed(fx.word_img(sub, 50, GREY, BOLD)), W / 2, 710, lt, 0.6, dur, "rise", "fade")
    return ov


def hold_card(txt, sub, col=Y):
    def ov(base, t, lt, dur):
        odometer(base, lt, 0.0, dur, txt, 300, 450, col, sub) if any(c.isdigit() for c in txt) else \
            kinetic(base, lt, 0.0, dur, txt, 190, 470, ins="slam")
    return ov


def hold_end(base, t, lt, dur):
    L.hold_end(base, t, lt, dur)


NO = lambda base, t, lt, dur: None  # noqa: E731

# (at, dur, [ (sub_t0, sub_t1, background, transition, overlay) ], sound)
HOLDS = [
    (0.0, 8.0, [(0, 2.6, full(C("closeB", 0.4)), "black", NO), (2.6, 5.0, full(C("crowd", 0.45)), "whip", NO),
                (5.0, 8.0, full(C("arms300", 0.3)), "flash",
                 lambda b, t, lt, d: L.T and fx.place(b, fx.shadowed(fx.word_img("CHENNAI · 19 DECEMBER 2016", 54, WHITE, BOLD)), W / 2, 930, lt, 0.2, d, "rise", "fade"))], "cold"),
    (58.2, 4.5, [(0, 4.5, pl(), "flash", hold_title)], "title"),
    (75.2, 2.0, [(0, 2.0, full(P("pampa_river"), 1.2, 1.25, (0.5, 0.5), dark=0.7), "black", NO)], "water"),
    (115.3, 2.5, [(0, 2.5, full(C("dressing100b", 0.5)), "flash", NO)], "crowd_s"),
    (135.55, 10.0, [(0, 3.4, full(C("armclose", 0.42)), "flash", NO), (3.4, 6.6, full(C("hug300", 0.42)), "whip", NO),
                   (6.6, 10.0, full(C("dressing150", 0.45)), "zoom", NO)], "crowd"),
    (173.3, 3.0, [(0, 3.0, full(C("walkoff", 0.45)), "zoom", NO)], "crowd_s"),
    (255.5, 1.8, [(0, 1.8, pl((0.9, 0.5, 0.4)), "glitch", hold_card("BENCHED", None, RED))], "hit"),
    (328.9, 1.8, [(0, 1.8, pl(), "flash", hold_card("54", "RUNS · 4 INNINGS", WHITE))], "hit"),
    (470.8, 2.0, [(0, 2.0, pl(), "flash", hold_card("ONE MORE CHANCE", None, WHITE))], "hit"),
    (522.3, 2.0, [(0, 2.0, full(P("karun_vidarbha_hundred"), 1.1, 1.14), "flash", NO)], "crowd_s"),
    (603.9, 2.5, [(0, 2.5, full(P("karun_oval_fifty_2025"), 1.14, 1.2), "zoom", NO)], "crowd_s"),
    (623.6, 1.8, [(0, 1.8, pl(), "flash", hold_card("205", "8 INNINGS · 2025", WHITE))], "hit"),
    (679.99, 3.5, [(0, 3.5, pl(), "none", NO)], "cta"),
    (750.0, 2.0, [(0, 2.0, full(P("karun_2025_portrait_fence"), 1.2, 1.24, (0.55, 0.3)), "zoom", NO)], "none"),
    (9999, 22.0, [(0, 22.0, pl(), "black", hold_end)], "end"),
]
for at, n, title, sub in [(92.9, 1, "CHENNAI", "December 2016"), (189.9, 2, "THE CEILING", None),
                          (244.9, 3, "THE VERY NEXT TEST", "Hyderabad, 2017"), (318.8, 4, "AUSTRALIA", "March 2017"),
                          (383.2, 5, "THE TOUR WITHOUT A MATCH", "England, 2018"), (438.8, 6, "THE LOST YEARS", None),
                          (490.5, 7, "VIDARBHA", "2023–25"), (569.7, 8, "THE RETURN", "England, 2025"),
                          (638.3, 9, "THE VERDICT", None), (680.0, 10, "THE TRUTH", None)]:
    HOLDS.append((at - 0.001, 2.2, [(0, 2.2, pl(), "whip", hold_chapter(n, title, sub))], "chapter"))
HOLDS.sort(key=lambda h: h[0])
CTA_OLD = 672.6


# ============================================================================ timeline (final seconds)

TL, VO_LEN, TOTAL = None, None, None


def setup():
    global TL, VO_LEN, TOTAL
    w = wave.open(os.path.join(HERE, "vo", "vo_clean.wav"))
    VO_LEN = w.getnframes() / w.getframerate()
    tl, out, vo = [], 0.0, 0.0
    for h in HOLDS:
        at = VO_LEN if h[0] >= 9999 else fwd(h[0])
        if at > vo + 1e-3:
            tl.append((out, out + at - vo, "vo", vo))
            out += at - vo
            vo = at
        tl.append((out, out + h[1], "hold", h))
        out += h[1]
    if vo < VO_LEN:
        tl.append((out, out + VO_LEN - vo, "vo", vo))
        out += VO_LEN - vo
    TL, TOTAL = tl, out
    L.TL = [(a, b, k, p) for a, b, k, p in tl]    # for make_long helpers that look at the timeline
    return out


def locate(t):
    for seg in TL:
        if seg[0] <= t < seg[1]:
            return seg
    return TL[-1]


def out_of_old(v_old):
    v = fwd(v_old)
    for t0, t1, kind, p in TL:
        if kind == "vo" and p <= v < p + (t1 - t0):
            return t0 + (v - p)
    return 0.0


_logo = None


def frame(i):
    global _logo
    t = i / FPS
    t0, t1, kind, p = locate(t)
    if kind == "hold":
        lt = t - t0
        sub = next((s for s in p[2] if s[0] <= lt < s[1]), p[2][-1])
        slt, sdur = lt - sub[0], sub[1] - sub[0]
        a = sub[2](slt, sdur)
        a = fx.transition(a, sub[3], slt)
        base = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
        sub[4](base, t, slt, sdur)
    else:
        v_old = back(p + (t - t0))
        sh = next((s for s in SH if s[0] <= v_old < s[1]), SH[-1])
        # shot-relative time measured in FINAL seconds so motion stays smooth across tightened pauses
        s_start = out_of_old(sh[0])
        lt = max(0.0, t - s_start)
        dur = max(0.5, out_of_old(min(sh[1], back(VO_LEN))) - s_start)
        a = sh[2](lt, dur)
        a = fx.transition(a, sh[3], lt)
        if sh[5] is not None:
            a = fx.shake(a, t, out_of_old(sh[5]))
        base = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
        for ov in sh[4]:
            ov(base, v_old)
    cs = out_of_old(CTA_OLD)
    if cs <= t < cs + 11.0:
        sys.path.insert(0, os.path.join(L.ROOT, "ipl_killed"))
        import hook as ipl_hook
        if _logo is None:
            _logo = Image.open(L.LOGO).convert("RGBA")
        base.alpha_composite(ipl_hook.cta_layer((t - cs) * 1.05, _logo))
    if t < 0.5:
        base = Image.fromarray((np.asarray(base.convert("RGB"), np.float32) * (t / 0.5)).astype(np.uint8)).convert("RGBA")
    out = np.asarray(base.convert("RGB")).copy()
    out[:L.BAR] = 0
    out[H - L.BAR:] = 0
    return out


def render_chunk(args):
    i0, i1 = args
    return b"".join(frame(i).tobytes() for i in range(i0, i1))


# ============================================================================ sound

def soundtrack(path):
    n = int(TOTAL * L.SR)
    w = wave.open(os.path.join(HERE, "vo", "vo_clean.wav"))
    vo = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
    if w.getframerate() != L.SR:
        import scipy.signal as ss
        vo = ss.resample_poly(vo, L.SR, w.getframerate())
    voice, fxa = np.zeros(n), np.zeros(n)
    at = L.at_
    for t0, t1, kind, p in TL:
        if kind == "vo":
            at(voice, vo[int(p * L.SR):int((p + t1 - t0) * L.SR)], t0, 1.0)
        else:
            snd = p[3]
            if snd == "crowd":
                at(fxa, L.sfx.crowd(min(p[1], 10)), t0 + 0.1, 0.55)
                at(fxa, L.braam(weight=1.2), t0, 0.45)
            elif snd == "crowd_s":
                at(fxa, L.sfx.crowd(p[1]), t0, 0.28)
            elif snd in ("hit", "chapter", "title"):
                at(fxa, L.sfx.whoosh(0.4), t0 - 0.2, 0.25)
                at(fxa, L.braam(weight=0.9), t0 + 0.02, 0.38)
            elif snd == "cold":
                at(fxa, L.sfx.crowd(p[1]), t0 + 0.5, 0.45)
            for sub in p[2][1:]:
                at(fxa, L.sfx.whoosh(0.3), t0 + sub[0] - 0.15, 0.18)
    for sh in SH:                       # a whoosh on every cut, a hit on marked moments
        ts = out_of_old(sh[0])
        if ts > 0:
            at(fxa, L.sfx.whoosh(0.3), ts - 0.15, 0.12 if sh[3] != "glitch" else 0.18)
        if sh[5] is not None:
            at(fxa, L.braam(weight=0.8), out_of_old(sh[5]), 0.32)
    tt = np.arange(n) / L.SR
    o = out_of_old
    sad = L.st.pad(L.st.D_MINOR, TOTAL, cutoff=1100)[:n]
    warm = L.st.pad(L.st.WARM, TOTAL, cutoff=1600)[:n]
    pulse = L.st.pulse(TOTAL, 100, lambda x: 0.6)[:n]
    m_sad = np.interp(tt, [0, o(58), o(92), o(244), o(366), o(490), o(569), o(638), o(680), o(719), TOTAL],
                      [0.28, 0.3, 0.2, 0.32, 0.4, 0.15, 0.2, 0.35, 0.15, 0.3, 0.2])
    m_warm = np.interp(tt, [0, o(92), o(125), o(170), o(244), o(490), o(522), o(569), o(604), o(638), TOTAL],
                       [0.0, 0.1, 0.4, 0.3, 0.05, 0.15, 0.45, 0.35, 0.3, 0.05, 0.1])
    m_pulse = np.interp(tt, [0, o(8), o(58), o(92), o(189), o(244), o(366), o(490), o(569), o(680), o(750), TOTAL],
                        [0.2, 0.45, 0.2, 0.45, 0.3, 0.45, 0.25, 0.5, 0.45, 0.15, 0.1, 0.0])
    bed = sad * m_sad + warm * m_warm + pulse * m_pulse * 0.7 + L.drone(TOTAL)[:n] * 0.05
    duck = 1 - 0.55 * np.convolve(np.abs(voice) > 0.02, np.ones(int(0.25 * L.SR)) / int(0.25 * L.SR), "same")
    mix = voice + (bed * 0.5 + fxa * 0.7) * duck
    mix[-int(2 * L.SR):] *= np.linspace(1, 0, int(2 * L.SR))
    mix = np.tanh(mix * 1.05) * 0.95
    pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w2:
        w2.setnchannels(2)
        w2.setsampwidth(2)
        w2.setframerate(L.SR)
        w2.writeframes(np.repeat(pcm[:, None], 2, axis=1).tobytes())


def sheet(ts=None):
    setup()
    ts = ts or list(np.linspace(1, TOTAL - 2, 48))
    ims = [Image.fromarray(frame(int(s * FPS))).resize((320, 180)) for s in ts]
    sh = Image.new("RGB", (320 * 8, 180 * ((len(ims) + 7) // 8)))
    for k, im in enumerate(ims):
        sh.paste(im, ((k % 8) * 320, (k // 8) * 180))
    os.makedirs(os.path.join(OUT, "chk"), exist_ok=True)
    sh.save(os.path.join(OUT, "chk", "sheet_v2.jpg"))
    print(f"total {int(TOTAL // 60)}:{TOTAL % 60:04.1f}")


def main():
    if "--sheet" in sys.argv:
        return sheet()
    setup()
    print(f"total {int(TOTAL // 60)}:{TOTAL % 60:04.1f}", flush=True)
    wav = os.path.join(OUT, "mix_v2.wav")
    soundtrack(wav)
    silent = os.path.join(OUT, "video_v2.mp4")
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                            "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    nfr = int(TOTAL * FPS)
    chunks = [(i, min(i + 15, nfr)) for i in range(0, nfr, 15)]
    with Pool(os.cpu_count()) as pool:
        for k, buf in enumerate(pool.imap(render_chunk, chunks)):
            enc.stdin.write(buf)
            if k % 200 == 0:
                print(f"  {k * 15}/{nfr}", flush=True)
    enc.stdin.close()
    enc.wait()
    full_ = os.path.join(OUT, "Karun_303_v2.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", silent, "-i", wav, "-c:v", "copy",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
                    "-shortest", full_], check=True)
    print("V2_DONE", full_)


if __name__ == "__main__":
    main()

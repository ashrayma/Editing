"""Kohli: first to 13,000 ODI runs at No. 3 — the script, split into lines.

(id, spoken text, caption text or None for "same as spoken", pause after in seconds)
Until the voiceover recording arrives this is voiced by TTS (python3 build_vo.py --tts) for timing.
"""
LINES = [
    ("l1", "Fifty five years of ODI cricket.", "55 years of ODI cricket.", 0.2),
    ("l2", "Nobody had ever done this at number three.", "Nobody had ever done this at No. 3.", 0.3),
    ("l3", "Thirteen thousand runs.", "13,000 runs.", 0.1),
    ("l4", "Virat Kohli is the first ever.", None, 0.4),
    ("p1", "The record used to belong to Ricky Ponting.", None, 0.1),
    ("p2", "Twelve thousand six hundred and sixty two runs, in three hundred and thirty innings.",
     "12,662 runs, in 330 innings.", 0.2),
    ("p3", "Kohli went past it in just two hundred and fifty one innings.", "Kohli went past it in just 251 innings.", 0.3),
    ("p4", "Ponting averaged forty two at number three.", "Ponting averaged 42 at No. 3.", 0.1),
    ("p5", "Kohli averages over sixty one.", "Kohli averages over 61.", 0.3),
    ("p6", "Ponting made twenty nine hundreds there.", "Ponting made 29 hundreds there.", 0.1),
    ("p7", "Kohli has forty eight.", "Kohli has 48.", 0.4),
    ("r1", "Sangakkara, Kallis, Williamson. Nobody else is even close.", None, 0.3),
    ("r2", "And he did all of it a day before his thirty eighth birthday.", "And he did all of it a day before his 38th birthday.", 0.4),
    ("q1", "So, is Virat the greatest number three of all time? Tell me in the comments, and follow for more.",
     "So, is Virat the greatest No. 3 of all time? Tell me in the comments, and follow for more.", 0.2),
]

TAKES = {"A": "vo_raw/a_190819.m4a"}
PIECES = {
    "l1": [("A", 1.6, 3.35)], "l2": [("A", 3.35, 6.0)], "l3": [("A", 6.4, 8.45)], "l4": [("A", 8.45, 10.05)],
    "p1": [("A", 10.05, 12.3)], "p2": [("A", 12.3, 18.2)], "p3": [("A", 20.8, 24.7)],
    "p4": [("A", 24.8, 27.2)], "p5": [("A", 27.2, 29.3)], "p6": [("A", 29.3, 31.4)], "p7": [("A", 31.4, 33.2)],
    "r1": [("A", 33.3, 36.75)], "r2": [("A", 39.9, 43.9)], "q1": [("A", 43.9, 48.2)],
}

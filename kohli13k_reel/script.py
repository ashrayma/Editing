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
    ("p3", "Kohli went past it in just two hundred and fifty one.", "Kohli went past it in just 251.", 0.3),
    ("p4", "Ponting averaged forty two at number three.", "Ponting averaged 42 at No. 3.", 0.1),
    ("p5", "Kohli averages over sixty one.", "Kohli averages over 61.", 0.3),
    ("p6", "Ponting made twenty nine hundreds there.", "Ponting made 29 hundreds there.", 0.1),
    ("p7", "Kohli has forty eight.", "Kohli has 48.", 0.4),
    ("r1", "Sangakkara, Kallis, Williamson. Nobody else is even close.", None, 0.3),
    ("r2", "And he did all of it a day before his thirty eighth birthday.", "And he did all of it a day before his 38th birthday.", 0.4),
    ("q1", "So, is Virat Kohli the greatest number three of all time? Tell me in the comments, and follow for more.",
     "So, is Virat Kohli the greatest No. 3 of all time? Tell me in the comments, and follow for more.", 0.2),
]

TAKES = {}
PIECES = {}

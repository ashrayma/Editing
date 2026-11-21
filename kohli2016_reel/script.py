"""2016: The Year of the King — the script as recorded (best takes), split into lines.

(id, spoken text, caption text or None for "same as spoken", pause after in seconds)
"""
LINES = [
    ("h1", "Was 2016 Virat Kohli the greatest peak a cricketer has ever had?", None, 0.3),
    ("h2", "Because that year he was so ruthless, so relentless, so utterly ridiculous, that a decade later the world is still trying to explain it.", None, 0.3),
    ("c1", "Now yes, there are some other contenders. Viv Richards ruled Test cricket in 1976. AB de Villiers tore ODIs apart in 2015.", None, 0.2),
    ("c2", "But their peaks lived in a single format. In 2016, Virat Kohli peaked in all 3 formats at the same time.", None, 0.4),
    ("t1", "In Test cricket, he was a monster. 1,215 runs at a staggering average of 75.", None, 0.2),
    ("t2", "And then, something truly historic. 3 double hundreds in back-to-back series.", None, 0.1),
    ("t3", "Majestic, merciless and magnificent.", None, 0.3),
    ("o1", "In ODIs, he was even more absurd. An average of 92.", None, 0.1),
    ("o2", "In T20Is, a jaw-dropping 106.", None, 0.3),
    ("w1", "At the T20 World Cup, he was simply unplayable. Player of the tournament, averaging 136,", None, 0.05),
    ("w2", "with that breathtaking 82* against Australia in Mohali.", None, 0.3),
    ("f1", "Stories like these are exactly why this page exists. So if you're a true cricket fan, you must follow this page.", None, 0.3),
    ("i1", "Then came the IPL. 973 runs. 4 dazzling hundreds. A record so absurd, nobody has come close to it in 10 years.", None, 0.2),
    ("i2", "And as captain, India played 12 Tests that year and lost none.", None, 0.3),
    ("a1", "2,595 international runs at an average of 86. Hundreds of players have crossed 2,000 runs in a year. Nobody has ever averaged more than Kohli.", None, 0.4),
    ("x1", "But the fairy tale had a cruel twist.", None, 0.2),
    ("x2", "India fell in the World Cup semi-final against West Indies.", None, 0.1),
    ("x3", "RCB lost the IPL final by just 8 runs. The most extraordinary year of his life ended without a single trophy.", None, 0.4),
    ("x4", "Still, for 12 glorious months, Virat Kohli wasn't just the best in the world.", None, 0.1),
    ("x5", "He was unstoppable, in every format.", None, 0.4),
    ("q1", "So, was 2016 the greatest peak in cricket history? Tell me in the comments, and follow for more.", None, 0.2),
]

TAKES = {"A": "vo_raw/a_115409.m4a"}
PIECES = {
    "h1": [("A", 3.1, 7.02)], "h2": [("A", 7.02, 13.72)], "c1": [("A", 13.72, 21.32)], "c2": [("A", 21.32, 27.62)],
    "t1": [("A", 34.7, 40.05)], "t2": [("A", 40.2, 44.5)], "t3": [("A", 44.5, 47.6)],
    "o1": [("A", 49.1, 52.75)], "o2": [("A", 53.7, 56.75)], "w1": [("A", 57.85, 63.42)], "w2": [("A", 65.4, 68.98)],
    "f1": [("A", 75.1, 81.0)], "i1": [("A", 87.3, 94.15)], "i2": [("A", 94.15, 98.35)], "a1": [("A", 98.35, 107.65)],
    "x1": [("A", 107.7, 110.2)], "x2": [("A", 111.4, 115.35)], "x3": [("A", 116.65, 123.3)], "x4": [("A", 123.3, 128.15)],
    "x5": [("A", 128.15, 131.05)], "q1": [("A", 131.1, 136.98)],
}

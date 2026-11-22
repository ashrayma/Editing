"""Rishabh Pant: "They Said He Was Finished" — the script as recorded (best takes), split into lines.

(id, spoken text, caption text or None for "same as spoken", pause after in seconds)
"""
LINES = [
    ("h1", "They said he might never play cricket again.", None, 0.2),
    ("h2", "Today, he passed Brendon McCullum and Adam Gilchrist in a single innings.", None, 0.3),
    ("h3", "This is the story of Rishabh Pant.", None, 0.5),
    ("c1", "30th December 2022. A dark morning on the Delhi–Dehradun highway. A car engulfed in flames, and trapped inside, India's most fearless cricketer.", None, 0.3),
    ("c2", "Torn knee ligaments. A battered body. Hospital beds. Silent doctors. And 1 question across the entire nation: will Pant ever hold a bat again?", None, 0.6),
    ("r1", "Every single step was a battle. Every day was pain. But the man who broke Australia's pride at the Gabba was never going to surrender.", None, 0.3),
    ("r2", "In 2024, a spectacular IPL return. A T20 World Cup triumph. And when he walked into Test cricket, a century in Chennai. As if nothing had ever happened.", None, 0.3),
    ("e1", "Then came England. Headingley. 2 centuries in a single Test, only the 2nd wicketkeeper in the history of cricket to do it. And in Manchester, with a fractured foot, limping, he walked out to bat again.", None, 0.5),
    ("f1", "And what records he has broken today in Wellington… before you find out, if you're a true cricket fan, you must follow this page.", None, 0.05),
    ("w1", "Basin Reserve. A fast, hostile New Zealand pitch. 153 balls. 128 runs. 10 fours. 6 sky-scraping sixes.", None, 0.2),
    ("w2", "His 9th Test century, and his 1st ever on New Zealand soil.", None, 0.2),
    ("w3", "And with that 1 innings, history bowed down.", None, 0.4),
    ("s1", "6 monstrous sixes took him past Brendon McCullum. Now only 1 man in the history of Test cricket has hit more sixes than Rishabh Pant. Ben Stokes.", None, 0.3),
    ("s2", "A century in England, in South Africa, in Australia, and now in New Zealand. A Test hundred in every SENA country.", None, 0.3),
    ("g1", "And those 128 runs took him past Adam Gilchrist himself. The most away Test runs by any wicketkeeper. Ever.", None, 0.6),
    ("q1", "They said he might never play again. Today, he's rewriting history.", None, 0.3),
]

# One take with retakes: the last clean take of each line (seconds into the raw file).
TAKES = {"A": "vo_raw/a_140909.m4a"}
PIECES = {
    "h1": [("A", 2.0, 4.2)], "h2": [("A", 4.2, 7.95)], "h3": [("A", 7.95, 9.75)],
    "c1": [("A", 9.75, 17.15)], "c2": [("A", 17.45, 25.75)],
    "r1": [("A", 28.25, 36.25)], "r2": [("A", 36.6, 46.5)], "e1": [("A", 46.95, 58.2)],
    "f1": [("A", 68.3, 74.5)], "w1": [("A", 74.5, 81.9)], "w2": [("A", 82.3, 85.78)], "w3": [("A", 86.15, 88.55)],
    "s1": [("A", 89.0, 98.15)], "s2": [("A", 98.6, 103.95)], "g1": [("A", 115.9, 122.6)],
    "q1": [("A", 123.1, 126.95)],
}

"""Rishabh Pant: "They Said He Was Finished" — the script as recorded (best takes), split into lines.

(id, spoken text, caption text or None for "same as spoken", pause after in seconds)
"""
LINES = [
    ("h1", "They said he might never play cricket again.", None, 0.2),
    ("h2", "Today he passed Brendon McCullum and Adam Gilchrist in a single innings.", None, 0.3),
    ("h3", "This is the story of Rishabh Pant.", None, 0.5),
    ("c1", "30th December 2022. A dark morning on the Delhi–Dehradun highway. A car engulfed in flames, and trapped inside, India's most fearless cricketer.", None, 0.3),
    ("c2", "Torn knee ligaments. A battered body. Hospital beds. Silent doctors. And 1 question across the entire nation: will Pant ever hold a bat again?", None, 0.6),
    ("r1", "Every single step was a battle. Every day was pain. But the man who broke Australia's pride at the Gabba was never going to surrender.", None, 0.3),
    ("r2", "In 2024, a spectacular IPL return. A T20 World Cup dream. And when he walked back into Test cricket, a century in Chennai. As if nothing had ever happened.", None, 0.3),
    ("e1", "Then came England. Headingley. 2 centuries in a single Test, and the 2nd wicketkeeper in the history of cricket to do it. In Manchester, with a fractured foot, limping, he walked out to bat again.", None, 0.5),
    ("f1", "And what records he broke today in Wellington… before you find it out, if you're a true cricket fan, you must follow this page.", None, 0.05),
    ("w1", "Basin Reserve. A fast, hostile New Zealand pitch. 153 balls. 128 runs. 10 fours. 6 sky-scraping sixes.", None, 0.2),
    ("w2", "His 9th Test century, and his 1st ever on the New Zealand soil.", None, 0.2),
    ("w3", "And with that 1 innings, history bowed down.", None, 0.4),
    ("s1", "6 monstrous sixes took him past Brendon McCullum. Now only 1 man in the history of Test cricket has hit more sixes than Rishabh Pant. That is Ben Stokes.", None, 0.3),
    ("s2", "A century in England, in South Africa, in Australia, and now in New Zealand. A Test hundred in every SENA country.", None, 0.3),
    ("g1", "And those 128 runs took him past Adam Gilchrist himself. The most away Test runs by any wicketkeeper. Ever.", None, 0.6),
    ("q1", "They said he might never play again. Today, he's rewriting the history.", None, 0.3),
]

# One take with retakes: the last clean take of each line (seconds into the raw file).
TAKES = {"B": "vo_raw/b_150536.m4a"}
PIECES = {
    "h1": [("B", 1.85, 3.92)], "h2": [("B", 3.92, 7.3)], "h3": [("B", 7.45, 9.9)],
    "c1": [("B", 9.95, 17.6)], "c2": [("B", 18.4, 26.2)],
    "r1": [("B", 27.6, 34.8)], "r2": [("B", 35.1, 45.0)], "e1": [("B", 45.7, 56.25)],
    "f1": [("B", 67.75, 73.85)], "w1": [("B", 74.2, 81.9)], "w2": [("B", 83.2, 86.55)], "w3": [("B", 86.6, 89.2)],
    "s1": [("B", 89.2, 98.1)], "s2": [("B", 98.3, 104.4)], "g1": [("B", 104.7, 111.95)],
    "q1": [("B", 112.35, 116.3)],
}

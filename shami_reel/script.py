"""Mohammed Shami retires from Tests: was it finished too soon? — the script as voiced (ElevenLabs), split into lines.

(id, spoken text, caption text or None for "same as spoken", pause after in seconds)
"""
LINES = [
    ("a1", "Mohammed Shami has announced his retirement from Test cricket.", None, 0.3),
    ("a2", "He hadn't played a Test for India in over three years.", "He hadn't played a Test for India in over 3 years.", 0.05),
    ("a3", "And nobody was talking about it.", None, 0.3),
    ("a4", "Think about what India has lost.", None, 0.3),
    ("b1", "Shami had the most beautiful seam position in world cricket.", None, 0.1),
    ("b2", "Bolt upright.", None, 0.05),
    ("b3", "Every single ball.", None, 0.2),
    ("b4", "On flat pitches, where other bowlers got nothing,", None, 0.05),
    ("b5", "that seam still found movement.", None, 0.3),
    ("c1", "Two hundred and twenty nine Test wickets, at an average under twenty eight.", "229 Test wickets, at an average under 28.", 0.2),
    ("c2", "And overseas, when India needed a breakthrough,", None, 0.05),
    ("c3", "the ball went to Shami.", None, 0.3),
    ("d1", "Remember Lord's, twenty twenty one?", "Remember Lord's, 2021?", 0.1),
    ("d2", "He didn't just bowl.", None, 0.05),
    ("d3", "He batted.", None, 0.05),
    ("d4", "Fifty six not out, alongside Bumrah, and India won.", "56* alongside Bumrah, and India won.", 0.4),
    ("e1", "Then came the injuries.", None, 0.1),
    ("e2", "Ankle surgery. Months out of the game.", None, 0.2),
    ("e3", "He came back.", None, 0.05),
    ("e4", "He took wickets.", None, 0.05),
    ("e5", "But the Test call never came.", None, 0.4),
    ("f1", "This is the man who took seven wickets in a World Cup semi-final, and twenty four in that World Cup.",
     "This is the man who took 7 wickets in a World Cup semi-final, and 24 in that World Cup.", 0.3),
    ("q1", "So here's the question.", None, 0.1),
    ("q2", "Was Mohammed Shami's Test career finished too soon?", None, 0.3),
    ("q3", "Tell me in the comments, and follow for more.", None, 0.2),
]

TAKES = {"A": "vo_raw/a_054443.mp3"}
PIECES = {
    "a1": [("A", 0.0, 3.35)], "a2": [("A", 3.35, 6.55)], "a3": [("A", 6.55, 8.7)], "a4": [("A", 8.7, 11.0)],
    "b1": [("A", 11.0, 14.75)], "b2": [("A", 14.75, 16.2)], "b3": [("A", 16.2, 17.85)], "b4": [("A", 17.85, 20.75)],
    "b5": [("A", 20.75, 22.95)], "c1": [("A", 22.95, 27.6)], "c2": [("A", 27.6, 30.35)], "c3": [("A", 30.35, 31.95)],
    "d1": [("A", 31.95, 34.0)], "d2": [("A", 34.0, 35.28)], "d3": [("A", 35.28, 36.27)], "d4": [("A", 36.27, 40.25)],
    "e1": [("A", 40.25, 42.0)], "e2": [("A", 42.0, 44.6)], "e3": [("A", 44.6, 45.66)], "e4": [("A", 45.66, 46.78)],
    "e5": [("A", 46.78, 48.8)], "f1": [("A", 48.8, 54.55)], "q1": [("A", 54.55, 56.0)], "q2": [("A", 56.0, 59.15)],
    "q3": [("A", 59.15, 61.57)],
}

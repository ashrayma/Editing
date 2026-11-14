"""AB de Villiers: two innings, one year (Johannesburg 2015 vs Delhi 2015) — the script as recorded, split into lines.

(id, spoken text, caption text or None for "same as spoken", pause after in seconds)
"""
LINES = [
    ("h1", "Who's the toughest batter of this generation to bowl to?", None, 0.2),
    ("h2", "There's only one answer. AB de Villiers.", None, 0.1),
    ("h3", "And I'll prove it with two innings.", "And I'll prove it with 2 innings.", 0.3),
    ("j1", "January twenty fifteen. Johannesburg.", "January 2015. Johannesburg.", 0.05),
    ("j2", "AB walks out against the West Indies.", None, 0.2),
    ("j3", "Fifty off sixteen balls.", "50 off 16 balls.", 0.05),
    ("j4", "A hundred off thirty one balls.", "100 off 31 balls.", 0.1),
    ("j5", "Both still ODI world records.", None, 0.1),
    ("j6", "He finishes on one forty nine, off just forty four balls.", "He finishes on 149, off just 44 balls.", 0.4),
    ("d1", "Now December, the same year. Delhi.", None, 0.05),
    ("d2", "South Africa are fighting to save a Test.", None, 0.3),
    ("d3", "AB faces two hundred and ninety seven balls, for forty three runs.", "AB faces 297 balls, for 43 runs.", 0.5),
    ("s1", "Same man. Same year.", None, 0.1),
    ("s2", "The fastest hundred in ODI history, and one of the most stubborn Test innings you'll ever see.", None, 0.3),
    ("p1", "That's the problem for bowlers.", None, 0.1),
    ("p2", "You never knew which AB was walking out.", None, 0.2),
    ("p3", "Bowl full, he drives you.", None, 0.05),
    ("p4", "Bowl short, he pulls you.", None, 0.05),
    ("p5", "Bowl wide, he walks across and scoops you over fine leg.", None, 0.3),
    ("p6", "Most batters can either attack you or outlast you.", None, 0.1),
    ("p7", "AB could do both.", None, 0.4),
    ("q1", "That's why he's the toughest batter of this generation. Agree or disagree? Tell me in the comments, and follow for more stories like this.", None, 0.2),
]

TAKES = {"A": "vo_raw/a_131532.m4a"}
PIECES = {
    "h1": [("A", 2.6, 5.55)], "h2": [("A", 5.55, 7.45)], "h3": [("A", 7.45, 8.95)],
    "j1": [("A", 8.95, 10.85)], "j2": [("A", 10.85, 12.9)], "j3": [("A", 12.9, 14.6)], "j4": [("A", 14.6, 16.8)],
    "j5": [("A", 16.8, 18.8)], "j6": [("A", 18.8, 22.6)],
    "d1": [("A", 23.5, 25.9)], "d2": [("A", 25.9, 28.1)], "d3": [("A", 33.3, 37.95)],
    "s1": [("A", 54.1, 56.0)], "s2": [("A", 56.0, 61.1)],
    "p1": [("A", 61.1, 62.9)], "p2": [("A", 63.0, 66.0)], "p3": [("A", 66.0, 67.95)], "p4": [("A", 67.95, 69.15)],
    "p5": [("A", 69.15, 73.4)], "p6": [("A", 73.7, 77.05)], "p7": [("A", 77.05, 78.6)],
    "q1": [("A", 79.7, 86.4)],
}

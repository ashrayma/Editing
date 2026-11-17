"""Why Sachin's ICC Test rating peak is 'only' 898 — the script as recorded, split into lines.

(id, spoken text, caption text or None for "same as spoken", pause after in seconds)
"""
LINES = [
    ("h1", "Sachin Tendulkar scored more Test runs than anyone in history.", None, 0.05),
    ("h2", "But according to the ICC, at least 30 batters had a better peak than him.", None, 0.3),
    ("h3", "His highest ever Test rating? 898.", None, 0.05),
    ("h4", "Virat Kohli peaked at 937.", None, 0.05),
    ("h5", "Even Sunil Gavaskar went past 900.", None, 0.3),
    ("h6", "So how is the greatest run-scorer of all time not even in the top 30?", None, 0.2),
    ("f1", "But before we understand why, if you're a true cricket fan, you must follow this page.", None, 0.3),
    ("w1", "Here's how the rating works.", None, 0.05),
    ("w2", "It's not a career score. It's a moving average, and your recent matches count the most.", None, 0.2),
    ("w3", "And it doesn't treat every run the same.", None, 0.05),
    ("w4", "Runs against strong teams, and runs that win matches, earn more.", None, 0.3),
    ("r1", "That's problem number 1. Some of Sachin's greatest Test hundreds came in losses.", None, 0.1),
    ("r2", "114 in Perth.", None, 0.05),
    ("r3", "169 in Cape Town.", None, 0.05),
    ("r4", "136 in Chennai, against Pakistan. India lost all of them.", None, 0.3),
    ("t1", "Problem number 2. Right after his peak in 2002, tennis elbow hit him.", None, 0.1),
    ("t2", "The bad matches dragged the average down, and it never recovered to that height.", None, 0.3),
    ("t3", "He became number 1 again in 2010.", None, 0.05),
    ("t4", "But even then, 898 stayed his ceiling.", None, 0.3),
    ("m1", "So the rating says Sachin never had a monster peak.", None, 0.1),
    ("m2", "But 24 years, 200 Tests and 15,921 runs.", None, 0.2),
    ("m3", "Maybe his greatness was never the peak. It was the mountain range.", None, 0.3),
    ("q1", "Peak or longevity, what matters most? Tell me in the comments, and follow for more.", None, 0.2),
]

TAKES = {"A": "vo_raw/a_131930.m4a"}
PIECES = {
    "h1": [("A", 0.8, 4.3)], "h2": [("A", 4.3, 8.55)], "h3": [("A", 8.55, 11.35)], "h4": [("A", 11.35, 13.35)],
    "h5": [("A", 13.35, 15.95)], "h6": [("A", 15.95, 20.6)], "f1": [("A", 20.6, 25.1)],
    "w1": [("A", 27.15, 28.45)], "w2": [("A", 28.45, 33.6)], "w3": [("A", 33.6, 36.3)], "w4": [("A", 36.3, 40.8)],
    "r1": [("A", 41.0, 46.35)], "r2": [("A", 46.35, 47.95)], "r3": [("A", 47.95, 49.5)], "r4": [("A", 49.5, 53.3)],
    "t1": [("A", 54.5, 58.55)], "t2": [("A", 58.55, 62.95)], "t3": [("A", 63.2, 65.65)], "t4": [("A", 65.65, 69.45)],
    "m1": [("A", 69.45, 72.55)], "m2": [("A", 72.55, 76.95)], "m3": [("A", 84.8, 89.2)],
    "q1": [("A", 99.7, 103.9)],
}

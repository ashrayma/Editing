"""Karun Nair: "The cruellest injustice in Indian cricket" — the script as recorded (best takes), split into lines.

(id, spoken text, caption text or None for "same as spoken", pause after in seconds)
"""
LINES = [
    ("h1", "The biggest injustice in Indian cricket? It wasn't Sanju Samson, in and out of the team for years. It wasn't Shreyas Iyer, brutally ignored for the Asia Cup after leading Punjab to a thrilling IPL final.", None, 0.4),
    ("h2", "It is a man you have already forgotten. Karun Nair. December 2016. Chennai. A mighty England on the other side. A quiet, fearless 25-year-old, playing only his 3rd Test.", None, 0.3),
    ("t1", "The 1st hundred comes. The crowd erupts. Then a glorious 200. The entire stadium rises. And then, a breathtaking, historic 300.", None, 0.4),
    ("t2", "303 not out. Only the 2nd Indian ever to score a Test triple century, after the legendary Sehwag.", None, 0.3),
    ("t3", "That magical night, a proud nation said the same thing: India has found its next superstar.", None, 0.6),
    ("d1", "But cricket had written a cold, heartless script. Within months, he was out of the team. No calls. No chance. No explanations. Long, painful years passed. Selectors forgot. Fans forgot.", None, 0.5),
    ("k1", "10 December 2022. The whole of India was celebrating Ishan Kishan's explosive double hundred. And on the same day, a broken, desperate Karun quietly typed: Dear cricket, give me 1 more chance.", None, 0.6),
    ("k2", "That same week, his own state, Karnataka, coldly dropped him from their Ranji team too.", None, 0.3),
    ("f1", "And what happened next, before you find it out, if you're a true cricket fan, make sure you follow this page.", None, 0.2),
    ("v1", "But Karun didn't break. A new state, Vidarbha. And then, a relentless, unstoppable storm of runs.", None, 0.3),
    ("v2", "And 8 years later, the same India that forgot him was forced to call him back. Now think about it.", None, 0.4),
    ("x1", "Only the 2nd Indian ever to score a historic Test triple hundred. Ruthlessly dropped within months. Abandoned by his own state. And a painful, lonely 8-year wait to come back.", None, 0.3),
    ("x2", "Sanju got chances. Shreyas came back. Karun waited 8 years for just 1 more chance.", None, 0.3),
    ("q1", "So tell me, has the Indian cricket faced an injustice than this?", None, 0.5),
    ("c1", "Drop your answer in the comments. And send this to a friend who never, ever gives up.", None, 0.3),
    ("c2", "The full untold story of Karun Nair is linked below this video.", None, 0.3),
]

# One take with retakes: the last clean take of each line (seconds into the raw file).
TAKES = {"A": "vo_raw/a_234207.m4a"}
PIECES = {
    "h1": [("A", 3.0, 13.67)], "h2": [("A", 14.3, 24.02)], "t1": [("A", 24.5, 32.56)], "t2": [("A", 32.9, 39.57)],
    "t3": [("A", 39.7, 45.12)], "d1": [("A", 46.6, 57.04)], "k1": [("A", 57.72, 69.88)], "k2": [("A", 76.0, 81.86)],
    "f1": [("A", 81.86, 87.3)], "v1": [("A", 87.65, 93.68)], "v2": [("A", 94.4, 100.81)], "x1": [("A", 101.0, 111.32)],
    "x2": [("A", 111.6, 116.75)], "q1": [("A", 116.8, 120.48)], "c1": [("A", 122.6, 127.3)], "c2": [("A", 133.0, 136.85)],
}

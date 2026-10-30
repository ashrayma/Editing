"""The reel's script (numbers are on screen, not spoken), split into lines: one caption group / timing unit each.

(id, spoken text, caption text or None for "same as spoken", pause after in seconds)
"""
LINES = [
    ("i1", "Rohit Sharma is not from this planet, and if you stay till the end, I'll prove it.", None, 0.35),
    ("i2", "Let's count down the five biggest six-hitters in the history of international cricket.", None, 0.6),

    ("n5", "At number five, it's Martin Guptill.", None, 0.25),
    ("g5", "Tall, strong, with enormous reach, he cleared the rope for New Zealand.", None, 0.5),

    ("n4", "At number four, it's his old teammate Brendon McCullum.", None, 0.25),
    ("g4a", "All forearms and pure aggression,", None, 0.1),
    ("g4b", "he walked out to attack from the very first ball.", None, 0.5),

    ("n3", "At number three, we're entering the big league.", None, 0.2),
    ("a3a", "Shahid Afridi.", None, 0.2),
    ("a3b", "They didn't call him Boom Boom for nothing.", None, 0.2),
    ("a3c", "He swung at everything with pure muscle and sent it into the crowd.", None, 0.5),

    ("n2", "At number two, it's the Universe Boss himself, Chris Gayle.", None, 0.25),
    ("c2a", "Six foot and two inches, and built like a heavyweight.", None, 0.2),
    ("c2b", "For years, everyone believed that record would never be broken.", None, 0.6),

    ("n1", "And at number one...", "And at number one…", 0.4),
    ("r1", "it's the man who loves his dal chawal.", None, 0.25),
    ("r2", "A man who is never in a hurry,", None, 0.1),
    ("r3", "and who bats like he's in slow motion.", None, 0.5),
    ("r4", "Rohit Sharma.", None, 1.0),
    ("r5", "Almost a hundred more sixes than Gayle.", None, 0.25),
    ("r6", "And he hits more sixes per innings than anyone else in the list.", None, 0.5),

    ("s1", "Here is what makes him so special.", None, 0.25),
    ("s2", "Every other name on the list hits sixes with muscle.", None, 0.25),
    ("s3", "In cricket, timing is supposed to be the gentle art,", None, 0.1),
    ("s4", "the thing Rahul Dravid and Kane Williamson used to stroke the ball along the ground for four.", None, 0.3),
    ("s5", "Rohit took the same soft timing and aimed it at the sky.", None, 0.25),
    ("s6", "He turned the most graceful skill in the game into a six-hitting weapon.", None, 0.5),

    ("e1", "So while the giants were muscling it over the rope,", None, 0.1),
    ("e2", "Rohit beat every one of them, and he made it look effortless.", None, 0.35),
    ("e3", "That's why I say he's not from this planet.", None, 0.5),
    ("q1", "Muscle or timing? Drop one word below, and follow for more stories like this.", None, 0.2),
]

# Your recording (take 2, 30 Oct): best take of every line, seconds into the raw file, from transcribe.py / words.py.
# Dropped: the "and who bay-" stumble and the ad-lib "But what makes him so special from any other in the list is he".
TAKES = {"A": "vo_raw/b_182156.m4a"}
PIECES = {
    "i1": [("A", 3.10, 7.14)], "i2": [("A", 7.14, 10.95)],
    "n5": [("A", 10.95, 12.75)], "g5": [("A", 12.75, 16.70)],
    "n4": [("A", 17.40, 20.85)], "g4a": [("A", 20.85, 22.46)], "g4b": [("A", 22.46, 25.55)],
    "n3": [("A", 25.65, 28.00)], "a3a": [("A", 28.00, 29.30)], "a3b": [("A", 29.30, 31.26)], "a3c": [("A", 31.26, 35.55)],
    "n2": [("A", 35.70, 39.42)], "c2a": [("A", 39.42, 43.00)], "c2b": [("A", 43.20, 46.55)],
    "n1": [("A", 46.90, 48.38)], "r1": [("A", 48.38, 50.98)], "r2": [("A", 50.98, 52.65)],
    "r3": [("A", 55.00, 57.95)], "r4": [("A", 58.20, 59.95)],
    "r5": [("A", 59.95, 62.78)], "r6": [("A", 62.78, 66.15)],
    "s1": [("A", 73.85, 75.74)], "s2": [("A", 75.74, 78.62)], "s3": [("A", 78.62, 81.30)],
    "s4": [("A", 81.30, 86.68)], "s5": [("A", 86.68, 90.08)], "s6": [("A", 90.08, 94.05)],
    "e1": [("A", 94.05, 96.85)], "e2": [("A", 96.85, 100.60)], "e3": [("A", 100.80, 103.85)],
    "q1": [("A", 103.85, 108.00)],
}

"""The reel's script (numbers are on screen, not spoken), split into lines: one caption group / timing unit each.

(id, spoken text, caption text or None for "same as spoken", pause after in seconds)
"""
LINES = [
    ("i1", "Rohit Sharma is not from this planet, and if you stay till the end, I'll prove it.", None, 0.35),
    ("i2", "Let's count down the five biggest six-hitters in the history of international cricket.", None, 0.6),

    ("n5", "At number five, it's Martin Guptill.", None, 0.25),
    ("g5", "Tall, strong and with an enormous reach, he cleared the rope for New Zealand.", None, 0.5),

    ("n4", "At number four, it's his old teammate Brendon McCullum.", None, 0.25),
    ("g4a", "All forearms and pure aggression,", None, 0.1),
    ("g4b", "he walked out to attack from the very first ball.", None, 0.5),

    ("n3", "At number three, we're entering the big league.", None, 0.2),
    ("a3a", "Shahid Afridi.", None, 0.2),
    ("a3b", "They didn't call him Boom Boom for nothing.", None, 0.2),
    ("a3c", "He swung at everything with pure muscle and sent it into the crowd.", None, 0.5),

    ("n2", "At number two, it's the Universe Boss himself, Chris Gayle.", None, 0.25),
    ("c2a", "Six foot two and built like a heavyweight.", None, 0.2),
    ("c2b", "For years, everyone believed that record would never be broken.", None, 0.6),

    ("n1", "And at number one...", "And at number one…", 0.4),
    ("r1", "is the man who loves his dal chawal.", None, 0.25),
    ("r2", "A man who is never in a hurry.", None, 0.5),
    ("r4", "Rohit Sharma.", None, 1.0),
    ("r5", "Almost a hundred more than Gayle.", None, 0.25),
    ("r6", "And he hits more sixes per innings than anyone else in the list.", None, 0.5),

    ("s1", "Here is what makes him so special.", None, 0.25),
    ("s2", "Every other name on the list hits sixes with muscle.", None, 0.25),
    ("s3", "In cricket, timing is supposed to be the gentle art,", None, 0.1),
    ("s4", "the thing Rahul Dravid and Kane Williamson used to stroke the ball along the ground for four.", None, 0.3),
    ("s5", "Rohit took that same soft timing and aimed it at the sky.", None, 0.25),
    ("s6", "He turned the most graceful skill in the game into a six-hitting weapon.", None, 0.5),

    ("e1", "So while the giants were muscling it over the rope,", None, 0.1),
    ("e2", "Rohit beat every one of them, and he made it look effortless.", None, 0.35),
    ("e3", "That's why I say he's not from this planet.", None, 0.5),
    ("q1", "Muscle or timing? Drop one word below, and follow for more stories like this.", None, 0.2),
]

# Your recording: one long take with retakes; the best take of every line (seconds into the raw file),
# picked from transcribe.py / words.py. "Rohit Sharma." for the reveal is reused from the opening line
# (the reveal and the "family wedding" line weren't in the recording).
TAKES = {"A": "vo_raw/a_174840.m4a"}
PIECES = {
    "i1": [("A", 1.0, 4.62)], "i2": [("A", 4.62, 8.50)],
    "n5": [("A", 8.50, 10.18)], "g5": [("A", 10.18, 13.95)],
    "n4": [("A", 13.95, 17.10)], "g4a": [("A", 17.10, 18.82)], "g4b": [("A", 18.82, 21.70)],
    "n3": [("A", 22.10, 24.42)], "a3a": [("A", 24.42, 25.54)], "a3b": [("A", 25.54, 27.58)], "a3c": [("A", 27.58, 31.85)],
    "n2": [("A", 32.25, 36.02)], "c2a": [("A", 36.02, 38.66)], "c2b": [("A", 42.90, 46.10)],
    "n1": [("A", 53.15, 54.82)], "r1": [("A", 54.82, 57.02)], "r2": [("A", 57.02, 58.98)],
    "r4": [("A", 1.0, 1.78)],
    "r5": [("A", 62.45, 65.05)], "r6": [("A", 69.85, 73.62)],
    "s1": [("A", 76.75, 79.34)], "s2": [("A", 79.34, 82.05)], "s3": [("A", 82.05, 84.94)],
    "s4": [("A", 84.94, 89.92)], "s5": [("A", 89.92, 93.54)], "s6": [("A", 93.54, 97.95)],
    "e1": [("A", 113.05, 116.14)], "e2": [("A", 116.14, 119.86)], "e3": [("A", 119.86, 122.45)],
    "q1": [("A", 122.45, 126.70)],
}

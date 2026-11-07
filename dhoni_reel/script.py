"""The reel's script, split into lines. Each line is one caption group and one timing unit.

(id, spoken text, caption text or None for "same as spoken", pause after in seconds)
"""
LINES = [
    ("h1", "Growing up, I had one hot take I would not shut up about.", None, 0.3),
    ("h2", "MS Dhoni is the greatest of all time.", None, 0.4),
    ("h3", "And every adult told me the same thing...", "And every adult told me the same thing…", 0.2),
    ("h4", "You will grow out of it.", "“You will grow out of it.”", 0.6),

    ("l1", "Because look who else was playing back then.", None, 0.3),
    ("l2", "Jacques Kallis.", None, 0.1), ("l3", "Shane Warne.", None, 0.1), ("l4", "Muttiah Muralitharan.", None, 0.25),
    ("l5", "Rahul Dravid.", None, 0.1), ("l6", "Brian Lara.", None, 0.1), ("l7", "Dale Steyn.", None, 0.3),
    ("l8", "And Ricky Ponting... two World Cups as captain.", "And Ricky Ponting… 2 World Cups as captain.", 0.3),
    ("l9", "Proper, proper legends.", None, 0.25),
    ("l10", "Every one of them could walk into any all-time eleven.", "Every one of them could walk into any all-time XI.", 0.6),

    ("b1", "So I grew up.", None, 0.3),
    ("b2", "I watched every one of them. I went through every record.", None, 0.25),
    ("b3", "I really tried to change my mind.", None, 0.4),
    ("b4", "And now... I can finally tell you something.", "And now… I can finally tell you something.", 0.9),

    ("t1", "I did not grow out of it.", None, 0.7),

    ("p1", "First tournament as captain? He wins the T20 World Cup.", None, 0.3),
    ("p2", "Then he takes India to number one in Test cricket.", "Then he takes India to No. 1 in Test cricket.", 0.35),
    ("p3", "Twenty eleven World Cup final, ninety-one not out, and he finishes it off in style.",
     "2011 World Cup final… 91 not out, and he finishes it off in style.", 0.4),
    ("p4", "Twenty thirteen, the Champions Trophy.", "2013, the Champions Trophy.", 0.3),
    ("p5", "That makes him the only captain in history to win all three ICC white-ball trophies.",
     "That makes him the only captain in history to win all 3 ICC white-ball trophies.", 0.45),
    ("p6", "Five IPL titles as captain.", "5 IPL titles as captain.", 0.3),
    ("p7", "The most stumpings in international cricket.", None, 0.3),
    ("p8", "The most not-outs in ODI history,", None, 0.1),
    ("p9", "because when Dhoni is out there, the match is not over yet.", None, 0.6),

    ("o1", "So no, I never grew out of it.", None, 0.3),
    ("o2", "MS Dhoni is the greatest of all time.", None, 0.35),
    ("o3", "I said it back then. I'm saying it now.", None, 0.4),
    ("o4", "Who was your childhood GOAT? Tell me in the comments.", None, 0.2),
]

# Your recording: one take, cut by line from transcribe.py / words.py (seconds into the raw file).
# Dropped: "that" in "told me [that] the same thing" and the stray "so" before the last line.
TAKES = {"A": "vo_raw/a_175420.m4a"}
PIECES = {
    "h1": [("A", 1.15, 5.70)], "h2": [("A", 5.70, 7.62)],
    "h3": [("A", 7.62, 8.86), ("A", 9.10, 10.25)], "h4": [("A", 10.25, 11.95)],
    "l1": [("A", 11.95, 14.92)], "l2": [("A", 14.92, 15.62)], "l3": [("A", 15.62, 16.26)],
    "l4": [("A", 16.26, 17.06)], "l5": [("A", 17.06, 17.98)], "l6": [("A", 17.98, 18.70)],
    "l7": [("A", 18.70, 19.22)], "l8": [("A", 19.22, 22.05)], "l9": [("A", 22.40, 24.35)],
    "l10": [("A", 24.45, 27.85)], "b1": [("A", 27.85, 29.02)], "b2": [("A", 29.02, 32.86)],
    "b3": [("A", 32.86, 34.30)], "b4": [("A", 34.30, 36.75)], "t1": [("A", 36.75, 39.15)],
    "p1": [("A", 39.30, 42.30)], "p2": [("A", 42.30, 44.84)], "p3": [("A", 44.84, 49.45)],
    "p4": [("A", 49.45, 51.32)], "p5": [("A", 51.32, 55.42)], "p6": [("A", 55.42, 57.50)],
    "p7": [("A", 57.50, 59.66)], "p8": [("A", 59.66, 61.53)], "p9": [("A", 61.53, 64.95)],
    "o1": [("A", 64.95, 67.20)], "o2": [("A", 67.20, 69.46)], "o3": [("A", 69.46, 71.85)],
    "o4": [("A", 72.95, 76.40)],
}

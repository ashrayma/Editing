"""2016 Kohli vs 2026 Kohli — the script as voiced (ElevenLabs, two parts), split into lines.

(id, spoken text, caption text or None for "same as spoken", pause after in seconds)
"""
LINES = [
    ("s1", "How does Virat Kohli keep doing this?", None, 0.3),
    ("s2", "He's thirty eight years old.", "He's 38 years old.", 0.1),
    ("s3", "And what he's doing in ODI cricket right now will blow your mind.", None, 0.3),
    ("s4", "But that's not even the wild part.", None, 0.3),
    ("s5", "This could be the best ODI year of his entire career.", None, 0.3),
    ("s6", "Think about it.", None, 0.1),
    ("s7", "His strike rate this year is over one twenty.", "His strike rate this year is over 120.", 0.1),
    ("s8", "He has never scored this fast in his whole ODI career.", None, 0.3),
    ("s9", "Thirty eight years old.", "38 years old.", 0.1),
    ("s10", "The fag end of his career.", None, 0.1),
    ("s11", "He's already achieved everything.", None, 0.1),
    ("s12", "And he's still pulling out his best.", None, 0.2),
    ("s13", "Incredible.", None, 0.1),
    ("s14", "It's insane!", None, 0.3),
    ("e1", "Let me explain.", None, 0.2),
    ("e2", "The old Kohli formula was simple.", None, 0.1),
    ("e3", "Settle in first, then attack.", None, 0.2),
    ("e4", "Now? He attacks from ball one.", None, 0.2),
    ("e5", "He changed his intent completely.", None, 0.1),
    ("e6", "At the stage where most players slow down,", None, 0.05),
    ("e7", "Kohli got even more aggressive.", None, 0.2),
    ("e8", "And just when you think there's nothing left for him to prove,", None, 0.05),
    ("e9", "he finds something more.", None, 0.3),
    ("y1", "If you watched twenty sixteen Virat Kohli, you know how special he was.", "If you watched 2016 Virat Kohli, you know how special he was.", 0.2),
    ("y2", "But I genuinely think twenty twenty six Virat Kohli, in ODIs, is even better.", "But I genuinely think 2026 Virat Kohli, in ODIs, is even better.", 0.3),
    ("o1", "He's on another level.", None, 0.1),
    ("o2", "He is one of one.", None, 0.2),
    ("o3", "And as Indians, we're lucky to call him our own.", None, 0.3),
    ("q1", "So what do you think? Twenty sixteen Kohli, or twenty twenty six Kohli? Comment below, and follow for more!",
     "So what do you think? 2016 Kohli, or 2026 Kohli? Comment below, and follow for more!", 0.2),
]

# ElevenLabs voice, delivered in two files: B = first half (hook -> "settle in first, then attack"), A = second half.
TAKES = {"B": "vo_raw/b_151501.mp3", "A": "vo_raw/a_151603.mp3"}
PIECES = {
    "s1": [("B", 0.0, 2.45)], "s2": [("B", 2.45, 4.1)], "s3": [("B", 4.1, 8.5)], "s4": [("B", 8.5, 10.4)],
    "s5": [("B", 10.4, 14.4)], "s6": [("B", 14.45, 15.45)], "s7": [("B", 15.45, 18.5)], "s8": [("B", 18.5, 22.35)],
    "s9": [("B", 22.35, 24.0)], "s10": [("B", 24.0, 25.75)], "s11": [("B", 25.75, 27.9)], "s12": [("B", 27.9, 30.1)],
    "s13": [("B", 30.1, 31.2)], "s14": [("B", 31.2, 32.5)], "e1": [("B", 32.5, 33.75)], "e2": [("B", 33.75, 36.0)],
    "e3": [("B", 36.0, 38.27)], "e4": [("A", 0.0, 2.55)], "e5": [("A", 2.55, 5.0)], "e6": [("A", 5.0, 7.7)],
    "e7": [("A", 7.7, 9.85)], "e8": [("A", 9.85, 13.05)], "e9": [("A", 13.05, 14.7)], "y1": [("A", 14.7, 19.3)],
    "y2": [("A", 19.3, 25.35)], "o1": [("A", 25.35, 27.05)], "o2": [("A", 27.05, 28.8)], "o3": [("A", 28.8, 31.8)],
    "q1": [("A", 31.8, 38.84)],
}

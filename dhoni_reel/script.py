"""The reel's script, split into lines. Each line is one caption group and one timing unit.

(id, spoken text, caption text or None for "same as spoken", pause after in seconds)
"""
LINES = [
    ("h1", "Growing up, I had one hot take I would not shut up about.", None, 0.3),
    ("h2", "MS Dhoni is the greatest of all time.", None, 0.4),
    ("h3", "And every adult told me the same thing...", "And every adult told me the same thing…", 0.2),
    ("h4", "You'll grow out of it.", "“You'll grow out of it.”", 0.6),

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

    ("t1", "I didn't grow out of it.", None, 0.7),

    ("p1", "First tournament as captain? He wins the T20 World Cup.", None, 0.3),
    ("p2", "Then he takes India to number one in Test cricket.", "Then he takes India to No. 1 in Test cricket.", 0.35),
    ("p3", "Twenty eleven World Cup final... ninety-one not out, and he finishes it with a six.",
     "2011 World Cup final… 91 not out, and he finishes it with a six.", 0.4),
    ("p4", "Twenty thirteen, the Champions Trophy.", "2013, the Champions Trophy.", 0.3),
    ("p5", "That makes him the only captain in history to win all three ICC white-ball trophies.",
     "That makes him the only captain in history to win all 3 ICC white-ball trophies.", 0.45),
    ("p6", "Five IPL titles as captain.", "5 IPL titles as captain.", 0.3),
    ("p7", "The most stumpings in international cricket.", None, 0.3),
    ("p8", "The most not-outs in ODI history,", None, 0.1),
    ("p9", "because when Dhoni was there at the end... the match was over.",
     "because when Dhoni was there at the end… the match was over.", 0.6),

    ("o1", "So no, I never grew out of it.", None, 0.3),
    ("o2", "MS Dhoni. Greatest of all time.", None, 0.35),
    ("o3", "I said it back then. I'm saying it now.", None, 0.4),
    ("o4", "Who was your childhood GOAT? Tell me in the comments.", None, 0.2),
]

# Your recording (filled in once the takes arrive): best take of every line, seconds into the raw files.
TAKES = {}
PIECES = {}

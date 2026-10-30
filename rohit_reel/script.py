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

    ("n3", "At number three, we're entering the big leagues.", None, 0.2),
    ("a3a", "Shahid Afridi.", None, 0.2),
    ("a3b", "They didn't call him Boom Boom for nothing.", None, 0.2),
    ("a3c", "He swung at everything with pure muscle and sent it into the crowd.", None, 0.5),

    ("n2", "At number two, it's the Universe Boss himself, Chris Gayle.", None, 0.25),
    ("c2a", "Six foot two and built like a heavyweight.", None, 0.2),
    ("c2b", "For years, everyone believed that record would never be broken.", None, 0.6),

    ("n1", "And at number one...", "And at number one…", 0.4),
    ("r1", "is a man who loves his dal chawal.", None, 0.25),
    ("r2", "A man who's never in a hurry,", None, 0.1),
    ("r3", "and who looks just like any regular guy you'd bump into at a family wedding.", None, 0.5),
    ("r4", "Rohit Sharma.", None, 0.4),
    ("r5", "Almost a hundred more than Gayle.", None, 0.25),
    ("r6", "And he hits more sixes per innings than anyone else on this list.", None, 0.5),

    ("s1", "Here's what makes it so special.", None, 0.25),
    ("s2", "Every other name on this list hit sixes with muscle.", None, 0.25),
    ("s3", "In cricket, timing is supposed to be the gentle art,", None, 0.1),
    ("s4", "the thing Rahul Dravid and Kane Williamson use to stroke the ball along the ground for four.", None, 0.3),
    ("s5", "Rohit took that same soft timing and aimed it at the sky.", None, 0.25),
    ("s6", "He turned the most graceful skill in the game into a six-hitting weapon.", None, 0.5),

    ("e1", "So while the giants were muscling it over the rope,", None, 0.1),
    ("e2", "Rohit beat every one of them, and he made it look effortless.", None, 0.35),
    ("e3", "That's why I say he's not from this planet.", None, 0.5),
    ("q1", "Muscle or timing? Drop one word below, and follow for more stories like this.", None, 0.2),
]

# Your recording (filled in once it arrives): best take of every line, seconds into the raw file.
TAKES = {}
PIECES = {}

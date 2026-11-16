"""Scariest primes in cricket, #3: Shoaib Akhtar — the script as recorded (fast cut), split into lines.

(id, spoken text, caption text or None for "same as spoken", pause after in seconds)
"""
LINES = [
    ("h1", "Who had the scariest prime in the history of cricket?", None, 0.2),
    ("h2", "There are many contenders, like Sachin Tendulkar, Rahul Dravid, Virat Kohli, Sir Vivian Richards.", None, 0.1),
    ("h3", "But at number three, it's a bowler.", "But at No. 3, it's a bowler.", 0.05),
    ("h4", "A bowler who made the greatest batters on earth look helpless.", None, 0.05),
    ("h5", "Shoaib Akhtar.", None, 0.4),
    ("e1", "Eden Gardens, in nineteen ninety nine.", "Eden Gardens, in 1999.", 0.05),
    ("e2", "A hundred thousand roaring Indian fans pack the stands.", "100,000 roaring Indian fans pack the stands.", 0.1),
    ("e3", "The Rawalpindi Express begins his long, menacing run-up,", None, 0.05),
    ("e4", "hair flying, arms wide, like a storm charging straight at you.", None, 0.1),
    ("e5", "His first thunderbolt rips Rahul Dravid's leg stump clean out of the ground.", None, 0.2),
    ("s1", "And then Sachin Tendulkar walks out, the greatest batter of his generation.", None, 0.1),
    ("s2", "Shoaib Akhtar fires in a blistering, lethal yorker,", None, 0.05),
    ("s3", "and the very first ball Sachin faces smashes into his middle stump.", None, 0.3),
    ("s4", "A hundred thousand people fall into stunned, deafening silence.", "100,000 people fall into stunned, deafening silence.", 0.5),
    ("p1", "That was Shoaib Akhtar in his prime. Raw, ferocious, brutally fast and absolutely fearless.", None, 0.1),
    ("p2", "Batters weren't just facing him.", None, 0.05),
    ("p3", "They were trying to survive him.", None, 0.3),
    ("r1", "And a few years later, he did something no human had ever done before.", None, 0.05),
    ("r2", "He bowled the fastest delivery in the history of cricket,", None, 0.05),
    ("r3", "a jaw-dropping one hundred and sixty one point three kilometres an hour.", "a jaw-dropping 161.3 km/h.", 0.1),
    ("r4", "More than twenty years on, nobody has bowled faster.", "More than 20 years on, nobody has bowled faster.", 0.3),
    ("f1", "If you're a true cricket fan, you must follow this page.", None, 0.2),
    ("t1", "But here's the scariest part. He's only number three.", "But here's the scariest part. He's only No. 3.", 0.3),
    ("t2", "Number two could swing the ball at a hundred and fifty kilometres an hour.", "No. 2 could swing the ball at 150 km/h.", 0.05),
    ("t3", "And number one never wore a helmet.", "And No. 1 never wore a helmet.", 0.2),
    ("q1", "Guess who they are in the comments, and follow so you don't miss Part 2.", None, 0.2),
]

# One take with retakes: the last clean take of each line (seconds into the raw file).
TAKES = {"A": "vo_raw/a_104813.m4a"}
PIECES = {
    "h1": [("A", 3.2, 5.9)], "h2": [("A", 5.9, 10.15)], "h3": [("A", 10.15, 12.2)], "h4": [("A", 12.2, 15.8)],
    "h5": [("A", 15.8, 16.45)],
    "e1": [("A", 16.45, 18.95)], "e2": [("A", 18.95, 22.3)], "e3": [("A", 22.3, 26.2)], "e4": [("A", 26.2, 30.2)],
    "e5": [("A", 30.2, 34.5)],
    "s1": [("A", 34.5, 38.4)], "s2": [("A", 52.4, 55.6)], "s3": [("A", 55.6, 60.1)], "s4": [("A", 66.55, 71.7)],
    "p1": [("A", 72.4, 78.3)], "p2": [("A", 79.1, 81.7)], "p3": [("A", 81.7, 83.7)],
    "r1": [("A", 86.6, 91.05)], "r2": [("A", 91.05, 94.35)], "r3": [("A", 94.35, 99.2)], "r4": [("A", 99.2, 102.7)],
    "f1": [("A", 104.4, 108.05)],
    "t1": [("A", 112.8, 116.95)], "t2": [("A", 116.95, 121.2)], "t3": [("A", 121.2, 123.6)], "q1": [("A", 123.6, 128.6)],
}

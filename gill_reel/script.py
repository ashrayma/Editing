"""Shaw vs Gill: "The prediction" — the script as recorded (best takes), split into lines.

(id, spoken text, caption text or None for "same as spoken", pause after in seconds)
"""
LINES = [
    ("h1", "India won the 2018 Under-19 World Cup with 2 extraordinary batting talents in the same team. One was its captain, Prithvi Shaw, who was being called the next Sachin Tendulkar.", None, 0.2),
    ("h2", "And the other one was Shubman Gill.", None, 0.35),
    ("h3", "But during that very tournament, a former New Zealand cricketer made a shocking prediction that is hard to ignore today.", None, 0.2),
    ("h4", "He said Gill was a far better player than Shaw.", None, 0.35),
    ("h5", "And looking at their careers today, that prediction is almost unbelievable.", None, 0.3),
    ("f1", "But if you're a true cricket fan, you must follow this page.", None, 0.3),
    ("s1", "Back in 2018, Shaw was already a sensation. At the age of 14, he had scored a staggering 546 runs in a single school innings.", None, 0.2),
    ("s2", "And in his first 7 first-class matches, he had already smashed 5 centuries.", None, 0.35),
    ("g1", "But Gill was about to make his own statement. In the Under-19 World Cup, he scored 372 runs in just 5 innings, averaging an incredible 124.", None, 0.35),
    ("g2", "And that's when Simon explained why he had rated Gill so high.", None, 0.2),
    ("g3", "He believed Shaw had technical flaws, while Gill was a much more technically complete batter.", None, 0.35),
    ("a1", "And then came the 2020 Australia tour. In Adelaide, Shaw managed just 4 runs across 2 innings.", None, 0.25),
    ("a2", "Gill made his debut in the very next Test, and scored 45 and 35 in Melbourne, looking remarkably composed against Australia's bowling attack.", None, 0.35),
    ("d1", "From there, their careers took completely different directions.", None, 0.2),
    ("d2", "Gill kept rising, becoming one of India's leading batters.", None, 0.2),
    ("d3", "While Shaw, despite all his extraordinary talent, struggled to establish himself in international cricket.", None, 0.45),
    ("e1", "2 players. 1 World Cup. 2 completely different destinies. But how did a player once considered India's next superstar lose his way? The complete story of Prithvi Shaw is in my last documentary. Please check it out.", None, 0.3),
    ("e2", "And for more incredible stories from the world of cricket, follow The Cricket Lounge.", None, 0.3),
]

# One take with retakes: the last clean take of each line (seconds into the raw file).
TAKES = {"A": "vo_raw/a.m4a"}
PIECES = {
    "h1": [("A", 4.7, 13.04)], "h2": [("A", 13.2, 14.95)], "h3": [("A", 15.35, 21.26)], "h4": [("A", 21.4, 24.58)],
    "h5": [("A", 25.5, 29.44)], "f1": [("A", 30.25, 34.63)], "s1": [("A", 34.9, 43.35)], "s2": [("A", 49.2, 53.88)],
    "g1": [("A", 54.05, 63.18)], "g2": [("A", 64.0, 68.12)], "g3": [("A", 71.3, 76.68)], "a1": [("A", 76.9, 82.48)],
    "a2": [("A", 94.6, 102.89)], "d1": [("A", 103.0, 106.8)], "d2": [("A", 106.9, 110.45)], "d3": [("A", 115.6, 121.72)],
    "e1": [("A", 123.8, 136.11)], "e2": [("A", 140.5, 144.55)],
}

"""Kane Williamson: "The Quiet Genius" — the script as recorded (best takes), split into lines.

(id, spoken text, caption text or None for "same as spoken", pause after in seconds)
"""
LINES = [
    ("h1", "Every era has its loud superstars. Virat Kohli had the fire. Joe Root has the volume. Steve Smith has the madness. But the most underrated of the Fab 4?", None, 0.25),
    ("h2", "He never needed any of it. Kane Williamson.", None, 0.4),
    ("n1", "Here is the catch nobody talks about.", None, 0.2),
    ("n2", "Root has played 169 Tests. Smith has played 127.", None, 0.2),
    ("n3", "Kohli finished on 123.", None, 0.25),
    ("n4", "Williamson? Just 110.", None, 0.3),
    ("n5", "Because New Zealand don't get the 5-Test blockbuster. They get 2-Test series. Fail twice, and the tour is gone.", None, 0.4),
    ("y1", "And yet, 33 Test hundreds. More than Kohli's 30. 1 in every 3.3 Tests.", None, 0.25),
    ("y2", "So how does a man from a country of 5 million outscore the giants?", None, 0.1),
    ("f1", "Before I tell you, if you're a true cricket fan, you must follow this page.", None, 0.25),
    ("p1", "He plays the ball later than anyone alive. Soft hands. No slog. No ego.", None, 0.25),
    ("p2", "2019 World Cup final. 578 runs. Player of the Tournament. He lost the trophy on a boundary count, and still walked off smiling.", None, 0.35),
    ("p3", "2 years later, at Southampton, he got his answer. 52 not out. World Test Championship. New Zealand's greatest day in Test cricket.", None, 0.4),
    ("r1", "No tantrums. No headlines. Just runs, and respect.", None, 0.3),
    ("r2", "Kohli had the fire. Joe Root has the volume. Smith has the madness. Kane had something rarer: calm.", None, 0.4),
    ("q1", "So tell me, who is the greatest of the Fab 4? Drop it in the comments.", None, 0.3),
]

# One take with retakes: the last clean take of each line (seconds into the raw file).
TAKES = {"A": "vo_raw/a_223713.m4a"}
PIECES = {
    "h1": [("A", 0.7, 10.28)], "h2": [("A", 10.5, 13.13)], "n1": [("A", 13.3, 15.3)], "n2": [("A", 15.3, 19.73)],
    "n3": [("A", 20.0, 21.7)], "n4": [("A", 23.4, 25.71)], "n5": [("A", 26.0, 32.83)], "y1": [("A", 43.4, 49.31)],
    "y2": [("A", 55.28, 59.22)], "f1": [("A", 59.22, 62.75)], "p1": [("A", 62.75, 67.25)], "p2": [("A", 67.25, 75.17)],
    "p3": [("A", 75.5, 82.9)], "r1": [("A", 83.0, 86.12)], "r2": [("A", 90.0, 97.36)], "q1": [("A", 97.6, 101.46)],
}

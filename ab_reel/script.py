"""AB de Villiers at World Cups — the script as recorded, split into lines (one caption group / timing unit each).

(id, spoken text, caption text or None for "same as spoken", pause after in seconds)
"""
LINES = [
    ("h1", "AB de Villiers was a cheater,", "AB de Villiers was a “cheater”,", 0.2),
    ("h2", "because his numbers just are not normal.", None, 0.4),
    ("h3", "He scored twelve hundred and seven runs in World Cups at an average of sixty three point five,",
     "He scored 1,207 runs in World Cups at an average of 63.5,", 0.15),
    ("h4", "which is the highest in the tournament's history,", None, 0.15),
    ("h5", "higher than even the great Sir Viv Richards.", None, 0.4),
    ("h6", "And he scored those runs faster than almost anyone who has ever made a thousand World Cup runs.",
     "And he scored those runs faster than almost anyone who has ever made 1,000 World Cup runs.", 0.3),
    ("h7", "Being the most consistent batter and one of the fastest at the same time shouldn't even be possible.", None, 0.6),

    ("b0", "But the crazy part is how it all started.", None, 0.3),
    ("b1", "At his first World Cup in two thousand seven, AB was out for a duck four times.",
     "At his first World Cup in 2007, AB was out for a duck 4 times.", 0.3),
    ("b2", "Any other young player might have been dropped for good.", None, 0.3),
    ("b3", "Instead, in the middle of all those failures, he smashed one forty six against the West Indies,",
     "Instead, in the middle of all those failures, he smashed 146 against the West Indies,", 0.1),
    ("b4", "and everyone got their first glimpse of what he could really do.", None, 0.6),

    ("c1", "By twenty eleven, he had moved into the middle order, and that's when he became truly dangerous.",
     "By 2011, he had moved into the middle order, and that's when he became truly dangerous.", 0.3),
    ("c2", "He hit back-to-back hundreds and finished the tournament averaging eighty eight.",
     "He hit back-to-back hundreds and finished the tournament averaging 88.", 0.6),

    ("d1", "But the best was saved for twenty fifteen.", "But the best was saved for 2015.", 0.3),
    ("d2", "AB was now captain, and he went on an absolute rampage.", None, 0.3),
    ("d3", "He scored four eighty two runs at an average of ninety six and a strike rate of one forty four.",
     "He scored 482 runs at an average of 96 and a strike rate of 144.", 0.3),
    ("d4", "Against the West Indies in Sydney, he smashed one sixty two not out off just sixty six balls",
     "Against the West Indies in Sydney, he smashed 162* off just 66 balls", 0.1),
    ("d5", "and reached one fifty in only sixty four deliveries.", "and reached 150 in only 64 deliveries.", 0.25),
    ("d6", "Nobody in the history of ODI cricket had ever got there faster.", None, 0.6),

    ("e1", "He dragged South Africa all the way to the semi-final, where he fought hard for sixty five not out.",
     "He dragged South Africa all the way to the semi-final, where he fought hard for 65*.", 0.3),
    ("e2", "But New Zealand won the match with just one ball to spare, and AB's dream was over.", None, 0.7),

    ("f1", "So he went from four ducks to the fastest one fifty the world has ever seen,",
     "So he went from 4 ducks to the fastest 150 the world has ever seen,", 0.15),
    ("f2", "yet he never played in a World Cup final and never lifted the trophy.", None, 0.4),
    ("f3", "And still, no one in history has a better World Cup average than AB de Villiers.", None, 0.6),

    ("q1", "Is he the greatest player never to win a World Cup?", None, 0.3),
    ("q2", "Tell me yes or no in the comments, and follow for more stories like this.", None, 0.2),
]

# Your recording: one long take with retakes; the best take of every line (seconds into the raw file),
# picked from transcribe.py / words.py.
TAKES = {"A": "vo_raw/a_203223.m4a"}
PIECES = {
    "h1": [("A", 1.70, 3.66)], "h2": [("A", 3.66, 5.90)], "h3": [("A", 5.90, 10.86)],
    "h4": [("A", 10.86, 13.18)], "h5": [("A", 13.18, 16.30)], "h6": [("A", 16.95, 22.78)],
    "h7": [("A", 22.78, 29.10)],
    "b0": [("A", 38.55, 41.15)], "b1": [("A", 41.15, 46.12)], "b2": [("A", 46.12, 49.66)],
    "b3": [("A", 49.66, 55.18)], "b4": [("A", 55.18, 59.40)],
    "c1": [("A", 67.05, 73.58)], "c2": [("A", 73.58, 78.00)],
    "d1": [("A", 87.15, 89.46)], "d2": [("A", 89.46, 94.62)], "d3": [("A", 94.62, 100.30)],
    "d4": [("A", 100.30, 105.66)], "d5": [("A", 105.66, 108.42)], "d6": [("A", 108.42, 112.70)],
    "e1": [("A", 121.45, 127.26)], "e2": [("A", 127.26, 132.85)],
    "f1": [("A", 133.75, 139.32)], "f2": [("A", 139.32, 143.05)], "f3": [("A", 143.75, 148.80)],
    "q1": [("A", 148.95, 152.80)], "q2": [("A", 153.05, 157.10)],
}

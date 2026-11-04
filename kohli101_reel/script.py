"""Kohli and the 38 problem: can he still get to 101? — the script as recorded, split into lines.

(id, spoken text, caption text or None for "same as spoken", pause after in seconds)
"""
LINES = [
    ("a1", "Sachin Tendulkar scored his hundredth international century at the age of thirty eight.",
     "Sachin Tendulkar scored his 100th international century at the age of 38.", 0.1),
    ("a2", "Virat Kohli has just turned thirty eight.", "Virat Kohli has just turned 38.", 0.1),
    ("a3", "And he's on eighty six.", "And he's on 86.", 0.4),
    ("b1", "So, can he still get there?", None, 0.1),
    ("b2", "Let's do the math.", None, 0.3),
    ("b3", "He needs fourteen to equal Sachin,", "He needs 14 to equal Sachin,", 0.05),
    ("b4", "and fifteen to stand alone at one hundred and one.", "and 15 to stand alone at 101.", 0.3),
    ("b5", "But he only plays one format now. ODIs.", "But he only plays 1 format now. ODIs.", 0.1),
    ("b6", "No Tests. No T20Is.", None, 0.3),
    ("c1", "Across his career, Kohli has scored an ODI hundred roughly once every six innings.",
     "Across his career, Kohli has scored an ODI hundred roughly once every 6 innings.", 0.2),
    ("c2", "Fifteen hundreds at the same rate means about ninety innings.", "15 hundreds at the same rate means about 90 innings.", 0.1),
    ("c3", "India play around twenty ODIs a year.", "India play around 20 ODIs a year.", 0.05),
    ("c4", "That's four and a half years.", "That's 4.5 years.", 0.2),
    ("c5", "He'd be forty two, at the twenty thirty one World Cup.", "He'd be 42, at the 2031 World Cup.", 0.05),
    ("c6", "Sounds impossible, right?", None, 0.2),
    ("d1", "But here's the twist.", None, 0.1),
    ("d2", "Sachin needed four hundred and fifty two innings for forty nine ODI centuries.",
     "Sachin needed 452 innings for 49 ODI centuries.", 0.1),
    ("d3", "Kohli got to fifty in just two hundred and seventy nine.", "Kohli got to 50 in just 279.", 0.4),
    ("d4", "So the question is not whether he is good enough.", None, 0.05),
    ("d5", "It is whether time gives him enough games.", None, 0.4),
    ("q1", "Will Virat Kohli get to one hundred and one? Yes or no, tell me in the comments. And follow for more stories like this.",
     "Will Virat Kohli get to 101? Yes or no, tell me in the comments. And follow for more stories like this.", 0.2),
]

TAKES = {"A": "vo_raw/a_191117.m4a"}
PIECES = {
    "a1": [("A", 2.3, 6.3)], "a2": [("A", 6.3, 8.35)], "a3": [("A", 8.35, 10.1)],
    "b1": [("A", 10.1, 11.5)], "b2": [("A", 11.5, 12.7)], "b3": [("A", 12.7, 14.75)], "b4": [("A", 14.75, 18.6)],
    "b5": [("A", 18.6, 21.6)], "b6": [("A", 21.6, 23.6)],
    "c1": [("A", 23.7, 29.7)], "c2": [("A", 34.9, 39.5)], "c3": [("A", 39.5, 42.35)], "c4": [("A", 42.35, 44.4)],
    "c5": [("A", 44.9, 48.95)], "c6": [("A", 48.95, 50.45)],
    "d1": [("A", 50.45, 51.6)], "d2": [("A", 51.6, 56.95)], "d3": [("A", 56.95, 60.45)],
    "d4": [("A", 63.2, 66.0)], "d5": [("A", 66.2, 69.5)], "q1": [("A", 69.5, 76.9)],
}

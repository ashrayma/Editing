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

TAKES = {"B": "vo_raw/b_192721.m4a"}  # second recording (the first, vo_raw/a_191117.m4a, is kept for reference)
PIECES = {
    "a1": [("B", 5.5, 9.7)], "a2": [("B", 9.7, 11.8)], "a3": [("B", 11.8, 13.6)],
    "b1": [("B", 13.9, 15.5)], "b2": [("B", 15.5, 16.9)], "b3": [("B", 17.0, 19.2)], "b4": [("B", 19.2, 22.4)],
    "b5": [("B", 22.5, 25.6)], "b6": [("B", 25.6, 27.4)],
    "c1": [("B", 30.5, 36.2)], "c2": [("B", 36.2, 39.5)], "c3": [("B", 39.5, 42.5)], "c4": [("B", 42.5, 44.1)],
    "c5": [("B", 49.4, 52.47)], "c6": [("B", 55.2, 57.3)],
    "d1": [("B", 57.3, 58.8)], "d2": [("B", 62.0, 66.6)], "d3": [("B", 66.8, 70.2)],
    "d4": [("B", 71.9, 74.45)], "d5": [("B", 74.45, 77.3)], "q1": [("B", 77.7, 84.0)],
}

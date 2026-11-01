"""Virat Kohli's greatest chase: 183 in Mirpur vs 82* at the MCG — the script as recorded, split into lines.

(id, spoken text, caption text or None for "same as spoken", pause after in seconds)
"""
LINES = [
    ("h1", "Virat Kohli's greatest chase wasn't the eighty two not out at the MCG.", "Virat Kohli's greatest chase wasn't the 82* at the MCG.", 0.1),
    ("h2", "It was one eighty three, in Mirpur.", "It was 183, in Mirpur.", 0.3),
    ("h3", "Now I know what you're thinking.", None, 0.1),
    ("h4", "Nothing beats that night against Pakistan in Melbourne, right?", None, 0.1),
    ("h5", "But hear me out.", None, 0.4),
    ("m1", "March twenty twelve.", "March 2012.", 0.1),
    ("m2", "Asia Cup. Mirpur. India versus Pakistan.", "Asia Cup. Mirpur. India vs Pakistan.", 0.2),
    ("m3", "Pakistan smashed three twenty nine.", "Pakistan smashed 329.", 0.1),
    ("m4", "Two hundreds, from Hafeez and Nasir Jamshed.", "2 hundreds, from Hafeez and Nasir Jamshed.", 0.1),
    ("m5", "Back then, chasing three thirty against Pakistan felt almost impossible.",
     "Back then, chasing 330 against Pakistan felt almost impossible.", 0.4),
    ("g1", "And it got worse. Gambhir was gone for a duck.", None, 0.1),
    ("g2", "India were zero for one,", "India were 0 for 1,", 0.1),
    ("g3", "and in walked a twenty three year old Virat Kohli.", "and in walked a 23 year old Virat Kohli.", 0.4),
    ("r1", "He didn't panic.", None, 0.1),
    ("r2", "He batted alongside Sachin Tendulkar, in one of Sachin's last ODIs,", None, 0.1),
    ("r3", "and then built a massive partnership with Rohit Sharma.", None, 0.3),
    ("r4", "Umar Gul, Saeed Ajmal, Shahid Afridi. He took all of them on.", None, 0.1),
    ("r5", "Twenty two fours.", "22 fours.", 0.1),
    ("r6", "And the faster the asking rate went up, the calmer he got.", None, 0.4),
    ("n1", "One eighty three off one forty eight balls.", "183 off 148 balls.", 0.1),
    ("n2", "His highest ever ODI score.", None, 0.1),
    ("n3", "India chased it down with thirteen balls to spare.", "India chased it down with 13 balls to spare.", 0.4),
    ("c1", "For me, the MCG was pure magic. But Mirpur was where the Chase Master was born.", None, 0.4),
    ("q1", "So, one eighty three in Mirpur, or eighty two not out at the MCG? Which one gets your vote? Comment below, and follow for more.",
     "So, 183 in Mirpur, or 82* at the MCG? Which one gets your vote? Comment below, and follow for more.", 0.2),
]

TAKES = {"A": "vo_raw/a_183119.m4a"}
PIECES = {
    "h1": [("A", 1.36, 5.3)], "h2": [("A", 5.3, 7.8)], "h3": [("A", 7.8, 9.8)], "h4": [("A", 9.8, 13.1)], "h5": [("A", 13.1, 14.5)],
    "m1": [("A", 14.6, 16.4)], "m2": [("A", 16.4, 19.2)], "m3": [("A", 19.2, 21.95)], "m4": [("A", 21.95, 23.85)], "m5": [("A", 23.85, 29.1)],
    "g1": [("A", 29.4, 32.0)], "g2": [("A", 32.0, 33.6)], "g3": [("A", 33.6, 37.2)],
    "r1": [("A", 42.1, 43.15)], "r2": [("A", 43.15, 47.5)], "r3": [("A", 47.5, 50.75)],
    "r4": [("A", 62.0, 65.6)], "r5": [("A", 65.6, 66.7)], "r6": [("A", 66.7, 70.8)],
    "n1": [("A", 74.6, 77.4)], "n2": [("A", 77.4, 79.4)], "n3": [("A", 79.4, 82.1)],
    "c1": [("A", 82.3, 88.5)], "q1": [("A", 88.5, 96.0)],
}

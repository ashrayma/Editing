"""RCB: no trades, and the one move they still need (spin) — the script as recorded (fast cut), split into lines.

(id, spoken text, caption text or None for "same as spoken", pause after in seconds)
"""
LINES = [
    ("o1", "9 teams were busy in the IPL trade window.", None, 0.05),
    ("o2", "1 team didn't move at all.", None, 0.05),
    ("o3", "The 2-time defending champions, RCB.", None, 0.2),
    ("o4", "And honestly, why would they? 2 titles in a row, 2025 and 2026.", None, 0.2),
    ("o5", "But silence in the trade window doesn't mean the squad is perfect.", None, 0.05),
    ("o6", "So let's do a health check.", None, 0.2),
    ("f1", "But before that, if you're a true cricket fan, you must follow this page.", None, 0.2),
    ("c1", "Batting? Loaded.", None, 0.05),
    ("c2", "Pace? Sorted.", None, 0.05),
    ("c3", "Spin? That's where it gets worrying.", None, 0.2),
    ("k1", "Their best spinner, Krunal Pandya, turns 36 next season.", None, 0.05),
    ("k2", "He's brilliant, but every season from here is a bonus.", None, 0.2),
    ("s1", "Their leg-spinner, Suyash Sharma, picked up just 8 wickets in 2025, and 9 in 2026.", None, 0.05),
    ("s2", "That's not a strike weapon. That's a holding pattern.", None, 0.2),
    ("n1", "And there's no plan B.", None, 0.05),
    ("n2", "If Krunal gets injured or loses rhythm, RCB walk into the middle overs with nobody to take wickets.", None, 0.1),
    ("n3", "On the dry pitches of Chennai and Lucknow, that's the phase that decides the match.", None, 0.2),
    ("a1", "They didn't fix it in the trade window.", None, 0.05),
    ("a2", "So the auction is their last chance.", None, 0.2),
    ("q1", "Should RCB go all in for a wicket-taking spinner, or trust the squad that just won 2 titles?", None, 0.1),
    ("q2", "Tell me in the comments, and follow for more.", None, 0.2),
]

TAKES = {"A": "vo_raw/a_032528.m4a"}
PIECES = {
    "o1": [("A", 2.7, 4.95)], "o2": [("A", 4.95, 6.3)], "o3": [("A", 6.3, 8.75)], "o4": [("A", 8.75, 12.5)],
    "o5": [("A", 12.5, 15.9)], "o6": [("A", 15.9, 17.4)], "f1": [("A", 17.55, 21.6)],
    "c1": [("A", 22.35, 23.55)], "c2": [("A", 23.55, 24.55)], "c3": [("A", 24.55, 27.2)],
    "k1": [("A", 27.8, 31.4)], "k2": [("A", 31.4, 34.6)], "s1": [("A", 34.6, 40.2)], "s2": [("A", 40.2, 43.1)],
    "n1": [("A", 43.4, 45.0)], "n2": [("A", 45.0, 50.3)], "n3": [("A", 56.2, 60.9)],
    "a1": [("A", 66.0, 68.9)], "a2": [("A", 68.9, 70.5)],
    "q1": [("A", 74.5, 80.6)], "q2": [("A", 80.6, 83.5)],
}

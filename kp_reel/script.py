"""Case File: Kevin Pietersen (Hinglish thriller) — the script as recorded, split into the recorded phrases.

(id, spoken text, caption text or None for "same as spoken", pause after in seconds)
Hinglish read: on-screen headlines carry the words (no running word captions), so phrase-level ids are enough.
"""
LINES = [
    ("o1", "Ek aisa player, jisne apne ego ke saamne apne career ko daav par laga diya. Yeh kahani hai cricket ke asli bad boy ki.", None, 0.25),
    ("o2", "August 2012. Headingley. Usne abhi abhi 149 banaye hain. Lekin dressing room mein koi taali nahi baja raha.", None, 0.1),
    ("o3", "Kyunki uske phone mein kuch aisa hai, jo England cricket ko hila dega.", None, 0.1),
    ("o4", "Lekin is kahani ko samajhne ke liye, humein shuru se chalna hoga.", None, 0.3),
    ("s1", "Strike 1. Saal 2000. Ek 20 saal ka ladka South Africa chhod deta hai.", None, 0.2),
    ("s2", "Strike 2. 2008. England ki captaincy. 5 mahine mein apne hi coach se jung. Nayi captaincy, Andrew Strauss ko.", None, 0.3),
    ("f1", "Agar aap sach mein cricket fan ho, toh is page ko follow karo, kyunki asli kahani ab shuru hoti hai.", None, 0.2),
    ("s3", "Strike 3. Ab KP ko khelna tha ek aise captain ke under, jise woh apne se chhota samajhta tha. Dressing room do hisson mein bant gaya.", None, 0.2),
    ("s4", "Strike 4. Wapas 2012. South Africa ke against 149. Aur press ke saamne ek line: is dressing room mein mera hona bahut mushkil hai.", None, 0.3),
    ("t1", "Aur phir, Kevin Pietersen South African players ko texts bhej raha tha. Apne hi captain, Andrew Strauss ke baare mein.", None, 0.1),
    ("t2", "Aur kaha jaata hai, un texts mein Strauss ki kamzori bhi thi.", None, 0.3),
    ("d1", "England ne use drop kar diya.", None, 0.35),
    ("e1", "Woh chahta, toh jhuk jaata. Sab theek ho sakta tha. Lekin KP jhukne wala insaan nahi tha.", None, 0.2),
    ("e2", "Aur yahi ego, uske career ko le dooba.", None, 0.1),
    ("e3", "2014 mein, England ne use hamesha ke liye nikaal diya.", None, 0.1),
    ("e4", "Aur uski wapsi ka darwaza kisne band kiya?", None, 0.2),
    ("e5", "England ke naye director of cricket. Andrew Strauss.", None, 0.35),
    ("x1", "104 Tests. 8,181 runs. 23 hundreds. Sirf 33 saal ki umar.", None, 0.3),
    ("x2", "Usse kisi bowler ne out nahi kiya. Usse out kiya, uske ego ne.", None, 0.35),
    ("q1", "Toh aap batao, Kevin Pietersen villain tha ya victim? Comments mein likho, aur aise aur cases ke liye follow karo.", None, 0.2),
]

TAKES = {"A": "vo_raw/a_131545.m4a"}
PIECES = {
    "o1": [("A", 3.25, 10.82)], "o2": [("A", 10.82, 18.0)], "o3": [("A", 18.0, 21.73)], "o4": [("A", 21.73, 25.75)],
    "s1": [("A", 25.75, 31.3)], "s2": [("A", 31.7, 40.3)], "f1": [("A", 43.05, 48.4)], "s3": [("A", 48.4, 57.4)],
    "s4": [("A", 61.1, 71.05)], "t1": [("A", 90.55, 98.55)], "t2": [("A", 99.8, 102.55)],
    "d1": [("A", 103.1, 104.9)], "e1": [("A", 113.9, 119.62)], "e2": [("A", 119.62, 124.2)], "e3": [("A", 124.4, 128.0)],
    "e4": [("A", 128.35, 130.85)], "e5": [("A", 133.4, 136.6)], "x1": [("A", 136.85, 142.5)], "x2": [("A", 142.9, 147.1)],
    "q1": [("A", 147.55, 153.32)],
}

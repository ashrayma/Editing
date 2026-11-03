"""The script, one beat per line of voiceover. Everything else (cut, captions, B-roll, sound) keys off these ids.

VO is Hinglish (what you record); on-screen text is English (gen.py). When your recording arrives, build_vo.py
cuts it into these same beats, so the edit re-times itself to your voice.
"""

BEATS = [
    # ── COLD OPEN: tease the Rauf sixes, cut away before the ball lands ─────────────────────────────
    ("open_equation", "8 gendein. 28 runs. Aur saamne Haris Rauf."),
    ("open_rauf",     "Pakistan ka sabse tez bowler. 3 overs, sirf 21 runs, 2 wickets."),
    ("open_tease",    "Iske baad jo do gendein aayi, unhe aaj bhi log shot of the century kehte hain. "
                      "Lekin un do gendon ko samajhne ke liye, teen saal peeche chalna padega."),

    # ── 01 THE SILENCE (context, under 40 s) ────────────────────────────────────────────────────────
    ("drought_70",    "November 2019. Kolkata. Virat Kohli ki 70th international century. Aur phir... kuch nahi."),
    ("drought_days",  "Ek saal. Do saal. Ek hazaar bees din, bina century ke."),
    ("drought_capt",  "T20 captaincy chhodi. Phir Test captaincy. Aur Dubai 2021 mein, Pakistan ne World Cup mein "
                      "India ko pehli baar haraya. Das wickets se."),
    ("drought_voices", "Log kehne lage, Kohli khatam ho gaya."),
    ("comeback_71",   "September 2022, Dubai. Afghanistan ke khilaaf, 71st century. 122 not out. "
                      "Lekin ek century se sab theek nahi hota. Asli imtihaan abhi baaki tha."),

    # ── 02 THE STAGE ────────────────────────────────────────────────────────────────────────────────
    ("mcg",           "Ek mahine baad. Melbourne Cricket Ground. T20 World Cup, India versus Pakistan. "
                      "Stadium mein 90,293 log. Aur TV pe crore."),
    ("pak_innings",   "Pakistan ne pehle batting ki. Arshdeep ne pehle hi over mein Babar ko LBW kiya. Phir Rizwan bhi gaye. "
                      "Lekin Iftikhar aur Shan Masood ki fifties ne score pahunchaya 159 tak."),
    ("target",        "Target 160. Aur saamne Shaheen, Naseem aur Rauf."),

    # ── 03 31 FOR 4 ─────────────────────────────────────────────────────────────────────────────────
    ("collapse",      "Aur phir shuru hua nightmare. KL Rahul, 4. Rohit, 4. Suryakumar, 15. Axar, run out."),
    ("31_4",          "31 for 4. Sirf saat overs mein."),
    ("silence",       "Aadha stadium chup. Aur crease pe woh aadmi, jiske baare mein teen saal se kaha ja raha tha "
                      "ki uska time khatam ho gaya."),
    ("rehook_2",      "Lekin asli drama abhi shuru bhi nahi hua tha."),

    # ── 04 THE PLAN ─────────────────────────────────────────────────────────────────────────────────
    ("hardik",        "Saath mein Hardik Pandya. Plan simple tha. Wicket mat do, match ko last tak le jao."),
    ("asking_rate",   "Par required rate badhta gaya. 10 overs ke baad India 45 for 4."),
    ("eighteen",      "17 overs ke baad, 18 gendon mein 48 chahiye the. Shaheen ka 18th over, 17 runs."),
    ("equation_12",   "Ab 12 gendon mein 31."),

    # ── 05 28 OFF 8 (the payoff of the cold open) ──────────────────────────────────────────────────
    ("rauf_over",     "19th over. Haris Rauf. Pehli chaar gendon mein sirf 3 runs. 8 gendein, 28 runs."),
    ("tv_off",        "Gharon mein log TV band kar rahe the. Kuch so bhi gaye."),
    ("six_one",       "Paanchvi gend. Back of a length. Kohli back foot pe gaye, aur seedha bowler ke sir ke upar se. Six."),
    ("six_one_why",   "Na koi slog, na koi swing. Bas ek seedha bat. Isliye isse shot of the century kehte hain."),
    ("six_two",       "Aur agli hi gend, fine leg ke upar se. Ek aur six."),
    ("equation_6",    "Ab 6 gendon mein 16."),

    # ── 06 THE LAST OVER ────────────────────────────────────────────────────────────────────────────
    ("nawaz",         "Last over. Mohammad Nawaz. Pehli gend, Hardik out. Phir ek single. Phir do runs."),
    ("no_ball",       "Chauthi gend. Kamar ki height pe full toss. Six! Aur umpire ka ishaara, no-ball."),
    ("free_hit",      "Phir wide. Free hit pe Kohli bowled. Lekin free hit pe bowled out nahi hota. "
                      "Gend third man ki taraf gayi, aur dono ne daud ke teen runs le liye."),
    ("dk_out",        "Phir DK stumped. Ek gend, do runs."),
    ("ashwin",        "Aur aaye Ashwin. Nawaz ki wide. Ab ek gend, ek run. Ashwin ne mid-off ke upar se uthaya. "
                      "Aur India jeet gaya!"),

    # ── 07 THE MEANING (end within 40 s of the win) ────────────────────────────────────────────────
    ("punch",         "Kohli ne zameen pe mukka maara. Rohit ne unhe kandhe pe utha liya."),
    ("82",            "82 not out. 53 gendein. Us din jab sab kuch khatam lag raha tha."),
    ("own_words",     "Match ke baad Kohli ne khud kaha. Ab tak Mohali meri best innings thi. Aaj se yeh hai."),
    ("close",         "Ek hazaar bees din log puchte rahe, kya Kohli wapas aayega? Us raat, MCG ne jawab de diya."),
    ("cta",           "Aapke hisaab se Kohli ki best innings? MCG ya Mohali? Comment karo. Aur agli story: Hobart 2012."),
]

IDS = [b[0] for b in BEATS]
TEXT = dict(BEATS)

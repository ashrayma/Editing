"""The reel's script, split into lines. Each line is one caption group and one timing unit.

(id, spoken text, caption text or None for "same as spoken", pause after in seconds)
Long pauses (0.7 s) sit where the script says "(pause)" and between sections.
"""
LINES = [
    ("h1", "Sachin is the God of cricket.", None, 0.25),
    ("h2", "Nobody's arguing that.", None, 0.35),
    ("h3", "But there are three records Virat Kohli owns...", "But there are 3 records Virat Kohli owns…", 0.3),
    ("h4", "that Sachin never touched.", None, 0.6),

    ("n1a", "Number one.", None, 0.7),
    ("n1b", "The Chase Master.", None, 0.4),
    ("c1", "When India are chasing, Kohli becomes a different player.", None, 0.3),
    ("c2", "Twenty-five ODI hundreds in successful chases.", "25 ODI hundreds in successful chases.", 0.25),
    ("c3", "The most by anyone. Ever.", None, 0.4),
    ("c4", "Sachin? Fourteen.", "Sachin? 14.", 0.4),
    ("c5", "And in those wins, Kohli averages over ninety.", "And in those wins, Kohli averages over 90.", 0.3),
    ("c6", "Ninety.", "90.", 0.4),
    ("c7", "That's not batting. That's a cheat code.", None, 0.6),

    ("n2a", "Number two.", None, 0.7),
    ("n2b", "The Captain.", None, 0.4),
    ("k1", "Kohli led India in sixty-eight Tests...", "Kohli led India in 68 Tests…", 0.25),
    ("k2", "and won forty.", "and won 40.", 0.25),
    ("k3", "The most by any Indian captain.", None, 0.35),
    ("k4", "He gave India their first ever Test series win in Australia.", None, 0.4),
    ("k5", "Sachin captained twenty-five Tests...", "Sachin captained 25 Tests…", 0.25),
    ("k6", "and won four.", "and won 4.", 0.4),
    ("k7", "Different job? Sure.", None, 0.25),
    ("k8", "But Kohli built a team that expected to win away from home.", None, 0.6),

    ("n3a", "Number three.", None, 0.7),
    ("n3b", "The biggest stage.", None, 0.4),
    ("w1", "Two thousand three World Cup: Sachin scores six hundred and seventy-three runs.",
     "2003 World Cup: Sachin scores 673 runs.", 0.25),
    ("w2", "A record that stood for twenty years.", "A record that stood for 20 years.", 0.4),
    ("w3", "Twenty twenty-three: Kohli scores seven hundred and sixty-five.", "2023: Kohli scores 765.", 0.4),
    ("w4", "And in the semi-final, at the Wankhede,", None, 0.15),
    ("w5", "with Sachin watching from the stands,", None, 0.15),
    ("w6", "he hits his fiftieth ODI hundred,", "he hits his 50th ODI hundred,", 0.15),
    ("w7", "passing Sachin's forty-nine.", "passing Sachin's 49.", 0.4),
    ("w8", "He's on fifty-five now.", "He's on 55 now.", 0.6),

    ("o1", "So is Kohli better than Sachin? No.", None, 0.35),
    ("o2", "A hundred international hundreds. Twenty-four years.", "100 international hundreds. 24 years.", 0.25),
    ("o3", "Sachin is still the benchmark.", None, 0.4),
    ("o4", "But these three? These belong to Virat.", "But these 3? These belong to Virat.", 0.4),
    ("o5", "Which one surprised you most? Tell me in the comments.", None, 0.2),
]

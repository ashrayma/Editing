#!/usr/bin/env python3
"""Line timings for the "IPL Ko Kisne Maara?" voiceover -> vo/timings.json.

Same method as sandpaper/align_vo.py: speech chunks from silence detection, anchors where the recogniser caught
"suspect", "guilty", "fantasy" etc., and the lines between anchors fitted to the chunks by character count.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "sandpaper"))
import align_vo as base  # noqa: E402

base.HERE = HERE
base.VO = os.path.join(HERE, "vo", "vo_raw.mp3")
base.LINES = [
    "2022 mein IPL mein 200+ score bane the 18 baar. 2026 mein? 61.",
    "Chhakke badh gaye, runs badh gaye… phir bhi stadium mein log phone dekh rahe hain.",
    "Kuch toh mar raha hai IPL mein. Aaj hum dhoondhenge, kisne maara.",
    "Chaar suspects hain. Teen pe shak hai.",
    "Lekin asli culprit… woh aapne kabhi socha bhi nahi hoga.",
    "Pehle IPL mein 160 defend hota tha. Last over tak saans ruki rehti thi.",
    "Aaj 220 bhi safe nahi, aur 6th over tak pata chal jaata hai match kidhar jaayega.",
    "Problem runs nahi hai. Problem hai, suspense mar gaya.",
    "Suspect number ek. Impact Player.",
    "Rule simple hai: ek extra player. Lekin asar?",
    "Ab har team ke paas number 8 tak batting hai.",
    "Wicket girne ka darr khatam. Darr khatam, toh risk unlimited.",
    "Pehle all-rounder ki value thi. Ab specialist batter khelo, bowling ke time swap kar lo.",
    "Matlab cricket ka sabse bada balance, bat vs ball, ek rule ne tod diya.",
    "Case close? Guilty?",
    "Itna aasaan nahi. Kyunki 2023 se pehle bhi scores badh rahe the… matlab koi aur bhi hai iss crime mein.",
    "Suspect number do. The pitch.",
    "Flat pitch: na swing, na seam, bounce bilkul predictable.",
    "Bowler ke paas bachaane ke liye kuch nahi.",
    "Chepauk jaisa ground, jahan 170 safe tha, aaj wahan 200 chase ho raha hai.",
    "Aur jab ek do match mein ball thoda ghooma, wahi match yaad reh gaye. Kyunki mushkil mein hi drama hai.",
    "Lekin pitch banata kaun hai? Aur flat pitch se fayda kisko hota hai?",
    "Yeh sawaal yaad rakhna. Climax mein yahi kaam aayega.",
    "Suspect number teen. Fantasy apps.",
    "Aaj crore log match dekhte nahi, apni team dekhte hain.",
    "Kohli out hua? Gham nahi, mere captain ne 3 wicket le liye.",
    "Match ka result matter hi nahi karta.",
    "Jab fan team ke liye nahi, points ke liye dekhta hai, toh match ki kahani marr jaati hai, sirf scorecard bachta hai.",
    "Aur iska ek andhera side bhi hai. Kai log isme apni savings tak gawa chuke hain.",
    "Suspect number chaar. The broadcast.",
    "2008 mein IPL ek event tha. Aaj 74 matches, har din, do-do.",
    "Har over ke baad ad, har chhakke pe sponsor ka naam.",
    "Boundary ab cricket ka moment nahi, ek inventory hai.",
    "Jitne zyada chhakke, utne zyada sixes brought to you by…",
    "Ruko. Notice kiya? Chaaron suspects ek hi cheez ki taraf ishaara kar rahe hain…",
    "Impact Player: zyada runs. Flat pitch: zyada runs. Fantasy: zyada points. Broadcast: zyada chhakke, zyada ads.",
    "Yeh chaar alag criminals nahi hain. Yeh ek hi plan ke chaar haath hain.",
    "Sach yeh hai: IPL boring nahi ho raha. IPL ko predictable banaya gaya hai, kyunki 220 ka score bikta hai, 140 ka nahi.",
    "Har decision runs ke liye liya gaya.",
    "Lekin ek cheez bhool gaye. Cricket mein maza chhakke ka nahi, chhakke ke darr ka hai.",
    "Jab bowler ke paas jeetne ka chance hi nahi, toh batter ka chhakka bhi khokhla hai.",
    "IPL ko kisne maara? Kisi player ne nahi. Balance ke khatam hone ne.",
    "Fix simple hai: thoda grass, Impact Player hatao ya limit karo, aur bowler ko ek weapon wapas do. Tab 180 bhi thriller hoga.",
    "Ab aap batao: Impact Player, rakhein ya hatayein? Ek word mein comment karo.",
    "Agla video: Bumrah vs Abhishek, kaun jeetega?",
]
base.ANCHORS = {3: 16.88, 8: 39.00, 14: 64.56, 16: 74.44, 23: 104.84, 29: 130.83, 34: 152.67, 35: 157.23,
                36: 166.85}

if __name__ == "__main__":
    base.main()

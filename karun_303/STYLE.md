# 303: edit notes

## Your Sachin "Peak or Longevity" reel, decoded (the style this film uses)

Transcript (your VO, 73 s): "Sachin Tendulkar scored more Test runs than anyone in history, but according to the ICC
at least 30 batters had a better peak than him. His highest-ever Test rating: 898. Virat Kohli peaked at 937, even Sunil
Gavaskar went past 900. So how is the greatest run-scorer of all time not even in the top 30? But before we understand
why, if you're a true cricket fan you must follow this page. Here's how the rating works… Problem number one… 114 in
Perth, 169 in Cape Town, 136 in Chennai… India lost all of them. Problem number two… tennis elbow… 898 stayed his
ceiling. 24 years, 200 Tests, 15,921 runs. Maybe his greatness was never the peak, it was the mountain range. Peak or
longevity? Tell me in the comments."

| Element | What the reel does | How this film uses it |
|---|---|---|
| Palette | Near-black stage alternating with warm grey paper; yellow #FEDE5C + red accents | Same: dark stage, paper scenes for "the story everyone tells", villains, squad lists |
| Type | Condensed bold caps headline, small spaced red/yellow kicker ("PROBLEM #1") | Anton headlines, Inter kickers, line-by-line mask reveals |
| Captions | One short bold caption box at the bottom, key word in yellow | Same band on every line, English, key word in yellow |
| Numbers | Huge italic yellow numbers that roll in (776→898, 937) | Rolling odometers: 381, 199, 759/7, 160, 62, 779, 1,077, 3,006, 89, 57, 204; gold 3D hero "303" |
| Photos | Polaroid cards, slight tilt, caption | Polaroids for young Karun; glass cards sliding in from left/right with 3D turn |
| Labels | Typewriter score tickets with red "LOST" stamps, AI newspaper tagged | Score tickets (MOHALI 4, NAIR 26/0/23/5) with stamps (NOT IN XI, POPE CATCH, REVIEW LOST, LEFT OUT) |
| Proof | Screen recording of the ICC table in a dark browser | Real screen recordings of Wikipedia (triple-century list, Karun's page) + screenshots |
| Charts | Bar window, line graph with a "ceiling" dashed line | Innings bar chart with the 303 bar and a red "benchmark" line |
| CTA | Follow card mid-video (logo ring, Follow → Following) | Subscribe card exactly where you say it (Subscribe → Subscribed + bell) |
| End | One-word question + comment bubble | "Team India mein hote? HAAN ya NAHI" + comment box + logo |
| Pace | New visual every ~2–3 s, hard cuts with whooshes | ~400 elements in 11.5 min: something new every 1.5–3 s |
| Sound | Whoosh on every slide, ticks on numbers, hits on stamps, soft bed | Same SFX map + chapter-based music bed ducked under the voice + the match's own crowd |

## Voiceover
`build_vo.py` holds the edit decision list: best take per line (usually the last clean one), the four pickups replace
the fluffed lines, every cut sits on a pause with 12 ms fades. 13:40 of raw takes → 11:24 of clean VO.

## Rules enforced in code
- Every photo, clip, AI image and screen grab is used once (`gen.py` stops if one repeats).
- Cards share the frame with text on the other side; full-frame footage carries only the caption band.
- AI images are tagged "AI-GENERATED" on screen.

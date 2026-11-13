# 3 Coincidences That Look Scripted (Short / Reel)

Our own version of the "weird coincidences in cricket history" reel: 3 items max (playbook rule 5),
legends paired (rule 7), one shareable number per item (153, 311, 183), faces on the first frame.

```
python3 make_trios.py   # photo strips from the upscaled crops in assets/
python3 voiceover.py    # out/vo/ (your recording if vo_file is set, else the offline AI draft voice)
python3 render.py       # out/coincidences.mp4 (+ _sfx_only.mp4 for a trending sound on IG)
```

## Voiceover script (record in ElevenLabs, one line per file, put in vo/)

| file | line |
|---|---|
| vo/hook | Ye 3 coincidences dekh ke lagega cricket scripted hai. Number 1: teen captain, ek number. |
| vo/3 | Number 3. Sachin ka 200, Sehwag ka 219, Rohit ka 264. Teeno match India jeeta... aur teeno baar 153 runs se. |
| vo/2 | Number 2. Zaheer Khan, 311 Test wickets. Ishant Sharma, 311 Test wickets. Dono ke 11 five-fors, dono ka ek ten-for. |
| vo/1 | Aur number 1. Ganguly ka highest ODI score, 183. Dhoni ka, 183 not out. Kohli ka, 183. Aur teeno bane India ke captain. |
| vo/outro | 183 ya 311? Comment karo. Part 2: 11/11/11 wala Test. |

Then set `"vo_file": "vo/hook.mp3"` etc. on each scene in config.json and re-run voiceover.py + render.py.

## Facts (checked)
- Sachin 200* vs SA, Gwalior 2010: India 401/3, SA 248, won by 153. Sehwag 219 vs WI, Indore 2011: 418/5 vs 265, won by 153.
  Rohit 264 vs SL, Kolkata 2014: 404/5 vs 251, won by 153.
- Zaheer Khan 311 Test wkts (92 Tests), Ishant Sharma 311 (105 Tests); both 11 five-fors and one 10-wicket match.
- 183 is the highest ODI score of Ganguly (vs SL, 1999 WC), Dhoni (183* vs SL, Jaipur 2005) and Kohli (vs Pak, Asia Cup 2012); all three captained India.
- Part 2 tease: Cape Town Test, 11/11/11 at 11:11, South Africa needed 111.

Photos are upscaled crops from the reference reel (720p source). Swap in originals when you have them.

# The Desert Storm: a faceless story reel

A ~72 s, 9:16 story reel built with [HyperFrames](https://github.com/heygen-com/hyperframes) (HTML + GSAP rendered to MP4).
The concept: Virat Kohli was asked which innings he wishes he had played, and he picked Sachin's "Desert Storm" in Sharjah, 1998.

There is no face on screen. A large rounded **photo stage** holds the real event picture for each beat, with captions under it
and stat, screenshot and screen-recording cards sliding in from the left and right in the lower half. Nothing ever covers the photo
(`tools/layout_audit.py` checks this).

`out/desert_storm_preview.mp4` is the current cut. It uses a **scratch AI voice** and **labelled photo slots** as stand-ins until
your recording and photos arrive.

## What you send me / what you drop in

**1. Your voice.** Record the script below as one take (phone voice memo is fine), then:
```
python3 tools/timing_from_recording.py my_voice.m4a   # transcribes it, aligns each script line, writes timing.json
python3 tools/build.py                               # every caption, photo, card and sound cue retimes to your delivery
```
You can ad-lib a little: alignment only needs most words of each line to match. If you change a line, edit it in `script.json` first.

**2. Real event photos.** Put them at these paths in `film/assets/photos/` (any aspect works; they're cropped to the frame):

| file | picture | on screen during |
|---|---|---|
| `01_virat_kohli.jpg` | Virat Kohli, interview or press conference | "Virat Kohli was asked…" |
| `02_sachin_sharjah_1998.jpg` | Sachin raising his bat, Sharjah 1998 | "His answer? Sharjah. 1998." |
| `03_sharjah_stadium.jpg` | Sharjah Cricket Stadium under lights | "April 22nd, 1998…" |
| `04_australia_innings.jpg` | Australia batting, 22 Apr 1998 (Bevan 101*) | "Australia put up 284" |
| `05_australia_team_90s.jpg` | Australia team, late 1990s | "Any team. Any ground. Beaten." |
| *(AI image, already in)* | sandstorm over the stadium | "Then, mid-chase…" |
| `07_after_the_storm.jpg` | players back out after the sandstorm | "When the dust settled…" |
| `08_sachin_six.jpg` | Sachin hitting a six, 22 Apr 1998 | "And then the real storm…" |
| `09_sachin_down_the_track.jpg` | Sachin charging down the track | "Nine fours. Five sixes." |
| `10_sachin_crowd.jpg` | Sachin raising his bat to the crowd after 143 | "India lost that match…" |
| `11_final_century.jpg` | Sachin's century in the final, 24 Apr 1998 | "…on his 25th birthday" |
| `12_cup_trophy.jpg` | India with the Coca-Cola Cup trophy | "134 in the final…" |
| `13_warne_vs_sachin.jpg` | Shane Warne bowling to Sachin | the Warne line |
| `14_virat_kohli.jpg` | Virat Kohli | "I get why Virat…" |
| `15_sachin_portrait.jpg` | Sachin, 1998 portrait | the CTA |

Only use photos you have the rights to (most 1998 match photos belong to agencies such as Getty/AFP). To change a slot's
picture, timing or crop, edit `photos` in `edit.json` (`pos` sets the crop focus, e.g. `"center 30%"`, and `zoom` sets the Ken Burns range).

Then rebuild and render:
```
python3 tools/build.py && python3 tools/layout_audit.py
cd film && npx hyperframes render -o ../out/render.mp4 && cd ..
ffmpeg -i out/render.mp4 -c:v copy -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 192k -movflags +faststart out/desert_storm.mp4
```
(The last step brings the mix to −14 LUFS, the level Reels/Shorts play at.)

## Script (what to record)

Short lines, no pauses longer than a breath. Hit the **bold** words; that's where the highlight colour and the cards land.

1. Virat Kohli was asked one question.
2. Which innings in cricket history do you wish you had played?
3. His answer? **Sharjah. 1998. The Desert Storm.**
4. April 22nd, 1998. Coca-Cola Cup, Sharjah.
5. Australia put up **284**.
6. Today that sounds normal. Back then, an average ODI score was around **230**.
7. And this was the late-90s Australia. Any team. Any ground. **Beaten.**
8. Then, mid-chase, something nobody planned for.
9. A **sandstorm** swallowed the stadium. Play stopped for twenty-five minutes.
10. When the dust settled, the target was **276 off 46 overs**.
11. And then **the real storm** arrived.
12. Sachin Tendulkar. **143 off 131 balls.**
13. Nine fours. Five sixes.
14. India lost that match, but Sachin dragged them into the final, almost alone.
15. Two days later, on his **25th birthday**, he did it again.
16. **134** in the final. India won the cup.
17. Shane Warne later joked he'd have **nightmares** of Sachin hitting him over his head.
18. So yeah. I get why Virat wishes this one was his.
19. **Which knock would you pick?** Tell me in the comments.

Facts used: Australia 284/7 (Bevan 101*); sandstorm stopped play for ~25 min; India's target revised to 276 in 46 overs;
India 250/5, lost by 26 runs but qualified on net run rate; Tendulkar 143 (131 balls, 9×4, 5×6). Final, 24 April 1998
(his 25th birthday): Australia 272/9, Tendulkar 134 (131), India won by 6 wickets. The Warne card quotes him on camera after the series.

## B-roll in this edit

| kind | what | how it was made |
|---|---|---|
| Screen recording | search → open the match → scorecard → chase bar crossing the qualifying line | `tools/record_screen.cjs` drives headless Chromium through `tools/innings_explorer.html` and records it |
| Screenshot | Tendulkar's scorecard row, ringed and zoomed | same page, 2× screenshot |
| AI image | sandstorm over a floodlit stadium | Canva AI image generation (tagged **AI-GENERATED** on screen) |
| Motion graphics | count-up stats, comparison bars, boundary chips, VS card, quote card, kinetic titles with drifting sand | `tools/build.py` → HyperFrames sub-compositions |

The Innings Explorer page is a small local page built for this reel (cricket sites were unreachable from the build machine), filled with the real match figures.

## Style: what the edit borrows from Ankur Warikoo's Shorts

The specific Short (`youtube.com/shorts/y_55hihwr00`) could not be downloaded from the build machine (YouTube is blocked there),
so this is his recognisable Shorts style in general, not a frame-by-frame breakdown of that video:

- **Hook in the first line** with a question or a claim, and the payoff named early ("Sharjah. 1998. The Desert Storm.").
- **Captions are the spine**: 2–3 words at a time, centred, heavy sans-serif, white with the key word in one accent colour, each word popping in. Here: Inter 800, 70 px, amber `#FFB340` on numbers and names, 60 ms word stagger.
- **No dead air**: lines butt up against each other (0.14 s gaps in the scratch VO).
- **A visual change every 2–4 s**: here a new photo, card or title arrives on almost every line.
- **Numbers become graphics**: every stat gets its own card with a count-up.
- **Clean and quiet design**: one accent colour, lots of dark space, no clutter. That matches the Apple-style brief: frosted dark glass cards, 44–52 px corner radii, `expo.out` arrivals (0.75 s) and fast `power3.in` exits (0.34 s), horizontal entrances alternating left and right.
- **Sound**: soft whooshes on every card and photo change, pops on chips, a ping when a big number lands, a low riser into "the real storm" with a bass impact on the drop, and a sparkle on the trophy and CTA.
- **CTA as a question** in the last line, mirrored by an on-screen card.

Music: no royalty-free music source was available on the build machine, so the render has voice and SFX only.
Add a trending sound in the Instagram/YouTube editor at about 10–15% under the voice.

## Files

```
script.json            the lines (captions come from here) + highlight keywords
timing.json            when each line is spoken (scratch voice, or your take)
edit.json              photos, cards, sound cues, anchored to line ids
tools/build.py         generates film/index.html + film/compositions/*
tools/scratch_vo.py    offline Kokoro scratch voice (models: ../kohli_countdown/README.md)
tools/timing_from_recording.py   your take -> timing.json (offline Whisper via sherpa-onnx)
tools/layout_audit.py  fails if any card or caption overlaps the photo stage
tools/record_screen.cjs + innings_explorer.html   the screen recording + screenshot
film/                  the HyperFrames project (npx hyperframes preview / render)
```

One-time setup: `npm install` here (HyperFrames + GSAP), `npx hyperframes browser ensure`,
`pip install sherpa-onnx kokoro-onnx soundfile pillow`, and for alignment download into `models/`:
`sherpa-onnx-whisper-small.tar.bz2` and `silero_vad.onnx` from https://github.com/k2-fsa/sherpa-onnx/releases/tag/asr-models.

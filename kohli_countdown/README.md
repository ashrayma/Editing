# Kohli Countdown Reel

A ~75-second, 9:16 motion-graphics countdown with voiceover, word-by-word captions and event photos: *"Ranking the best days as a Kohli fan"*.
It reworks the idea of a reference reel with fixed numbering, tighter pacing, animated stats and sound design.

```
python3 voiceover.py           # 1. build the voice lines  -> out/vo/
python3 render.py              # 2. renders out/part1.mp4 (#10-#6) and out/part2.mp4 (#5-#1)
python3 render.py --part=part2 #    just one part
python3 render.py --preview    #    half-res quick check
```

Each scene stretches to fit its voice line, and SFX/music duck under the voice.

### Voiceover: your own voice (recommended)
Record each line from the script below as its own file (phone voice memo is fine), put them in `vo/`,
and set `vo_file` on that scene in `config.json`, e.g. `"vo_file": "vo/10.m4a"`. Silence at the start/end is
trimmed automatically. `vo_file` can also be a list of `{"file", "trim": [start, end], "gap_after"}` pieces:
that's how fumbles, retakes and false starts are cut out of a long take (see config.json for the current edit list). Any scene without a `vo_file` falls back to the AI voice (offline Kokoro, Hindi `hm_omega`).
Keep `caption` matching what you actually say. The captions are timed proportionally across the line.

AI voice setup (one-time, ~350 MB):
```
pip install kokoro-onnx soundfile
curl -L -o models/kokoro-v1.0.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
curl -L -o models/voices-v1.0.bin  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
```

### Photos and clips
`items[].image` is a photo. `items[].clip` is a video clip (plays muted inside the card from `clip_start` seconds),
and it overrides `image`. Portrait or square photos sit on a blurred copy of themselves, so any shape works.
The current `assets/ref_*.jpg` are 720p frames cropped from the reference reel. Replace them with original,
higher-res photos when you can.

The reel is split into two posts (`parts` in config.json: each has its own ranks, hook and outro).
Voice files for a part's hook/outro are keyed `part1_hook`, `part2_outro` etc.; the countdown lines are shared.

Outputs, in `out/`:
- `part1.mp4`, `part2.mp4`: SFX plus a light synthesised beat
- `part1_sfx_only.mp4`, `part2_sfx_only.mp4`: SFX only. **Upload this one and add a trending sound inside Instagram** (trending audio gets more reach).

Requirements: Python 3, Pillow, NumPy, ffmpeg. Fonts: Inter / Inter Display.

## Personalising it

Everything lives in `config.json`:

| field | what it does |
|---|---|
| `items[].image` / `items[].clip` | photo / video clip for that moment |
| `vo_file` / `vo_text` / `caption` | your recording / AI-voice text (Devanagari) / on-screen captions |
| `hook.image` | photo behind the opening title |
| `facecam` | your green-screen face-cam clip; it's chroma-keyed into the bottom-right, and your voice is mixed over the SFX |
| `facecam_chroma` | key colour (default `0x00FF00`) |
| `items[].duration` | seconds per moment; match it to your voiceover |
| `title`, `sub`, `stat`, `stat_suffix`, `stat_label`, `chips`, `quote`, `balls` | on-screen text |
| `accent` | per-item colour (default: blue for #10–#4, gold for the top 3, RCB red for #1) |
| `music` | `false` → no beat in the main file |

Use photos you have the rights to (your own screenshots/edits, licensed images). Raw broadcast footage gets muted or taken down.

## Brand theme and music

`theme` in config.json sets the accent colour, the background gradient and the logo (`assets/logo.png`). The logo
wipes on in the hook, sits in every scene's header and opens the outro. The colours are taken from the
theCricketLounge logo: #FEDE5C yellow on charcoal.

`music.py` writes the background track itself: an original, royalty-free, feel-good house/pop groove (118 BPM,
G-D-Em-C). It is side-chained to the kick and ducked under the voice. `python3 music.py 30 preview.wav` writes a 30 s preview.

## Timeline (60.7 s)

| t | scene | motion / SFX |
|---|---|---|
| 0–3.2 | Hook: "RANKING THE BEST DAYS AS A KOHLI FAN" + TOP 10 badge + "#1 made the whole nation cry" | 3 text slams (impacts), badge spin (whoosh + ding), typewriter tease |
| 3.2–51 | #10 → #2, about 5 s each | whip-in + flash (whoosh), rank slam + shake (impact), word pops, stat counter (ticks → ding), check-mark chips (pops) |
| #7 | ball-by-ball 2 6 4 4 4 4 | each ball pops in, impacts on boundaries |
| #9, #5 | quote typewriter | soft key ticks |
| 51–52 | "AND AT #1..." black screen | riser + heartbeat |
| 52–57 | #1 RCB, red accent | big impact, crowd roar, camera shutter, confetti |
| 57–60.7 | "WHAT'S YOUR #1?" + comment CTA | slam, pulsing #1, bouncing arrow |

## Voiceover script (what to record; same text as `caption` in config.json)

- **Hook** (`vo/hook`): Ranking my best days as a Kohli fan... and number 1 made the whole nation cry.
- **#10** (`vo/10`): 2014 mein England mein sirf 134 runs. 2018 mein wapas gaya aur 593 thok diye.
- **#9** (`vo/9`): Lord's 2021. For 60 overs, they should feel hell out there. Aur England 120 pe all out.
- **#8** (`vo/8`): 1020 din ka intezaar. Phir Dubai mein aayi 71st century.
- **#7** (`vo/7`): Hobart. 40 overs mein 321 chahiye the. Malinga ke ek over mein 24 maar diye.
- **#6** (`vo/6`): Mohali 2016. Must-win match, 82 not out, aur twos aise bhaage jaise singles.
- **#5** (`vo/5`): 2011. 28 saal ka intezaar khatam. Aur Sachin ko apne kandhon pe uthaya.
- **#4** (`vo/4`): 50th ODI hundred. Sachin ke saamne, unka hi record, Wankhede mein.
- **#3** (`vo/3`): World Cup final, 34 for 3. Kohli ke 76. Aur hum World Champions.
- **#2** (`vo/2`): MCG. 31 for 4. Rauf ko back-to-back sixes. Aaj bhi goosebumps aate hain.
- **#1** (`vo/1`): 18 saal. Jersey number 18. Ee sala cup... NAMDU. Hum sab roye the.
- **Outro** (`vo/outro`): Aapka number 1 kya hai? Comment karo.

## Review of the reference reel and what this version changes

1. **Numbering was broken.** It shows 5, 4, 4, 3, 3, 2, 2, 1, 1 (ten moments, but two of each number). Viewers notice, and it kills the "countdown" payoff. → Clean 10 → 1 with a progress bar at the top.
2. **97 s is too long** for a talking-head list, and retention drops hard after about 30 s. → 60 s, about 5 s per moment.
3. **Weak hook.** The first frame is "Ranking the Best days as a Kohli Fan" over a talking face, with no stakes. → Title slam plus a curiosity tease ("#1 made the whole nation cry") in the first 1.5 s.
4. **Text is tiny and sits in the top strip**, partly under Instagram's UI. Captions like "Surpassed Sachin's record ✅" are about 20 px tall at phone size. → Big rank/title, high-contrast chips, everything kept inside the safe zone.
5. **Static photos only**, with no motion. → Ken Burns on photos, animated stat counters, ball-by-ball graphics, confetti on #1.
6. **No stats.** "133* vs SL" means nothing to a casual viewer. → Every moment gets one hero number plus context (balls, venue, year).
7. **No sound design.** It's voice plus a quiet bed, and the audio peaks at 0 dBFS, so it clips. → Whooshes, impacts, ticks, risers and a crowd roar, normalised loudness.
8. **No build-up to #1.** → A suspense beat (black screen, heartbeat, riser) before #1.
9. **Weak CTA.** The caption asks for comments but the video doesn't. → On-screen "What's your #1? Comment it below" with a pointing arrow.
10. **Keep the good part:** the creator's face and personality drive the original. Record your own face-cam on green (or use CapCut's background remover) and drop it in via `facecam` for the best result.

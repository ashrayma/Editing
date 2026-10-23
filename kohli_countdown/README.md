# Kohli Countdown Reel

A 60-second, 9:16 motion-graphics countdown: *"Ranking the best days as a Kohli fan"*.
It reworks the idea of a reference reel with fixed numbering, tighter pacing, animated stats and sound design.

```
python3 render.py              # full 1080x1920 render  (~2 min on 4 cores)
python3 render.py --preview    # half-res quick check
```

Outputs, in `out/`:
- `kohli_countdown.mp4`: SFX plus a light synthesised beat
- `kohli_countdown_sfx_only.mp4`: SFX only. **Upload this one and add a trending sound inside Instagram** (trending audio gets more reach).

Requirements: Python 3, Pillow, NumPy, ffmpeg. Fonts: Inter / Inter Display.

## Personalising it

Everything lives in `config.json`:

| field | what it does |
|---|---|
| `items[].image` | path to a photo for that moment; it gets a Ken Burns zoom inside the card, with the stat laid over it |
| `hook.image` | photo behind the opening title |
| `facecam` | your green-screen face-cam clip; it's chroma-keyed into the bottom-right, and your voice is mixed over the SFX |
| `facecam_chroma` | key colour (default `0x00FF00`) |
| `items[].duration` | seconds per moment; match it to your voiceover |
| `title`, `sub`, `stat`, `stat_suffix`, `stat_label`, `chips`, `quote`, `balls` | on-screen text |
| `accent` | per-item colour (default: blue for #10–#4, gold for the top 3, RCB red for #1) |
| `music` | `false` → no beat in the main file |

Use photos you have the rights to (your own screenshots/edits, licensed images). Raw broadcast footage gets muted or taken down.

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

## Voiceover script (Hinglish, ~5 s per moment)

- **Hook:** "Ranking my best days as a Kohli fan... and #1 made the whole nation cry."
- **10:** "2014 mein England mein sirf 134 runs. 2018 mein wapas gaya aur 593 thok diye."
- **9:** "Lord's 2021. 'For 60 overs they should feel hell out there.' And they did."
- **8:** "1020 days. Har match mein wait kiya. 71st century finally aayi."
- **7:** "Hobart. 321 chahiye the 40 overs mein. Malinga ke ek over mein 24 maar diye."
- **6:** "Mohali 2016. Must-win game, 82 not out, and twos run like singles."
- **5:** "2011. Sachin ko kandhe pe uthaya. 'He carried the nation for 21 years.'"
- **4:** "50th ODI hundred. Sachin ke saamne. Unka record. Wankhede mein."
- **3:** "34 for 3 in a World Cup final. 76 runs. World champions."
- **2:** "MCG. 31 for 4. Rauf ko back-to-back sixes. Mujhe aaj bhi goosebumps aate hain."
- **1:** "18 saal. Jersey number 18. Ee sala cup... NAMDU. We all cried."
- **Outro:** "Your #1 kya hai? Comment karo."

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

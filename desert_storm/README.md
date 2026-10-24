# The Desert Storm: a faceless story reel

An 89 s, 9:16 story reel built with [HyperFrames](https://github.com/heygen-com/hyperframes) (HTML + GSAP rendered to MP4).

**Structure:** a 5.2 s hook clip (the host asks *"the one knock in international cricket you wish you had played"*, Virat answers
*"Sharjah 98, Desert Storm"*), then a Hinglish voiceover tells the story over real event photos, with English captions and on-screen text.

There is no face on screen. A large rounded **photo stage** holds the picture for each beat, sliding in from alternating sides with a slow
Ken Burns zoom. Captions sit under it, and stat, screenshot and screen-recording cards slide in below. `tools/layout_audit.py`
fails the build if anything covers the photo stage.

`out/desert_storm_final.mp4` is the finished reel: your Hinglish voiceover (`voice_raw/voiceover_take1.m4a`), cut and cleaned,
with original background music.

## Voiceover

The script is in **[SCRIPT.md](SCRIPT.md)**. Your take went through:
1. `tools/clean_vo.py` cuts the ranges listed in `vo_edit.json`: 4 s of lead-in silence and three false starts
   ("Ek zabar…", "Bowler koi bh…", "Ek sau… na"), each followed by your clean retake. Then rumble filter, gentle
   noise reduction, presence EQ, compression, −16 LUFS. 96.8 s raw → 84.0 s clean, your natural pace otherwise untouched.
2. `timing.json` holds where each of the 17 lines sits in the cleaned take. These were set by hand from a phrase-level
   transcript because several lines run together without a pause. `tools/timing_from_recording.py` can fit them
   automatically for a future take with clear pauses between lines.
3. Everything (captions, photos, cards, sound effects, music sections) is anchored to those line ids.

To redo with a new take: edit `vo_edit.json` (or keep everything), then
```
python3 tools/clean_vo.py voice_raw/new_take.m4a
python3 tools/timing_from_recording.py film/assets/audio/voice_clean.wav   # or set timing.json by hand
python3 tools/make_music.py && python3 tools/build.py && python3 tools/layout_audit.py
cd film && npx hyperframes render -o ../out/render.mp4 && cd ..
ffmpeg -i out/render.mp4 -c:v copy -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 192k -movflags +faststart out/desert_storm_final.mp4
```

## Music

`tools/make_music.py` composes an original track from scratch in code (no samples, no third-party audio, so it's
copyright-free): 128 BPM, A minor (Am–F–C–G). The arrangement follows the story. Soft pad under the hook; kick, hats,
bass and pluck arpeggio through the story; drums drop out for the sandstorm; a riser into a full drop that lands on
a bar line exactly on "asli toofan"; a half-time breakdown and fade from the Warne line. It ducks 7 dB wherever
you speak, and in the mix it sits 8–11 dB under your voice (16–20 dB in the quiet sections).

## Pictures

| file in `film/assets/photos/` | used for |
|---|---|
| `sachin_vs_waugh.jpg` | Virat's answer · Australia (crop on the bowler) · "Nine fours, five sixes" · CTA |
| `sachin_lofted_drive.jpg` | Australia's 284 (crop on the bowler) · "the real storm" |
| `trophy_celebration.jpg` | 134 in the final, India win the cup |
| `team_victory_lap.jpg` | "I get why Virat…" |
| `assets/img/ai_sandstorm.png` | the sandstorm (AI-generated, labelled on screen) |
| typographic panels | 22.04.1998 · LOST BY 26 / QUALIFIED · THE FINAL 24.04.1998 · NIGHT-MARES |

Your photos are small (370–588 px wide), so they're upscaled 2.5–4× with Lanczos and light sharpening. Higher-resolution
versions of the same photos would look noticeably crisper. To add or swap a picture, drop it in `film/assets/photos/` and edit
`photos` in `edit.json` (`at` = the script line, `pos` = crop focus such as `"85% 55%"`, `zoom` = Ken Burns range), then rebuild.

## B-roll in this edit

| kind | what | how it was made |
|---|---|---|
| Hook video | host asks the question, Virat answers | your clip, with its burned-in captions blurred and replaced (`tools/prep_hook.py`) |
| Screen recording | search → open the match → scorecard → chase bar crossing the qualifying line | `tools/record_screen.cjs` drives headless Chromium through `tools/innings_explorer.html` and records it |
| Screenshot | Tendulkar's scorecard row, ringed and zoomed | same page, 2× screenshot |
| AI image | sandstorm over a floodlit stadium | Canva AI image generation (tagged **AI-GENERATED** on screen) |
| Motion graphics | count-up stats, comparison bars, boundary chips, VS card, quote card, kinetic titles with drifting sand | `tools/build.py` → HyperFrames sub-compositions |

The Innings Explorer page is a small local page built for this reel (cricket sites were unreachable from the build machine), filled with the real match figures.

Facts used: Australia 284/7 (Bevan 101*); sandstorm stopped play for ~25 min; India's target revised to 276 in 46 overs;
India 250/5, lost by 26 runs but qualified on net run rate; Tendulkar 143 (131 balls, 9×4, 5×6). Final, 24 April 1998
(his 25th birthday): Australia 272/9, Tendulkar 134 (131), India won by 6 wickets.

## Style: what the edit borrows from Ankur Warikoo's Shorts

The specific Short (`youtube.com/shorts/y_55hihwr00`) could not be downloaded from the build machine (YouTube is blocked there),
so this follows his recognisable Shorts style in general, not a frame-by-frame breakdown of that video:

- **Hook in the first line**, a question with the payoff named at once (the hook clip ends on "Sharjah 98, Desert Storm").
- **Captions are the spine**: 2–3 words at a time, centred, heavy sans-serif, white with key words in one accent colour, each word popping in. Here: Inter 800, 70 px, amber `#FFB340` on numbers and names, 60 ms word stagger.
- **No dead air**: lines butt up against each other.
- **A visual change every 2–4 s**: a new photo, card or title on almost every line.
- **Numbers become graphics**: every stat gets its own card with a count-up.
- **Clean and quiet design** to match the Apple-style brief: frosted dark glass cards, 44–52 px corner radii, `expo.out` arrivals (0.75–0.8 s), fast `power3.in` exits, push transitions between photos, alternating left and right.
- **Sound**: soft whooshes on every card and photo change, pops on chips, a ping when a big number lands, a low riser into "the real storm" with a bass impact on the drop, and a sparkle on the trophy and CTA.
- **CTA as a question** in the last line, mirrored by an on-screen card.

Music: an original synthesised bed (see Music above). If you'd rather ride a trending sound on Instagram, set the
`music` entry's `volume` in `edit.json` to 0, rebuild, and add the sound in the app.

## Files

```
SCRIPT.md              the voiceover script to record
script.json            the lines: text (Hinglish, spoken), caption (English, on screen), tts (Devanagari, scratch voice)
timing.json            when each line is spoken (scratch voice, or your take); timing_scratch.json = reference rhythm
edit.json              hook, photos, cards, sound cues, anchored to line ids
tools/build.py         generates film/index.html + film/compositions/*
tools/clean_vo.py      raw take -> cut + cleaned voice (cut list in vo_edit.json)
tools/make_music.py    the original background music, arranged to the story
tools/scratch_vo.py    offline Kokoro scratch voice (Hindi hm_omega; models: ../kohli_countdown/README.md)
tools/timing_from_recording.py   your take -> timing.json (Silero VAD pause alignment, offline)
tools/prep_hook.py     hook clip -> 1080x1920 with its burned-in captions blurred
tools/layout_audit.py  fails if any card or caption overlaps the photo stage
tools/record_screen.cjs + innings_explorer.html   the screen recording + screenshot
film/                  the HyperFrames project (npx hyperframes preview / render)
```

One-time setup: `npm install` here (HyperFrames + GSAP), `npx hyperframes browser ensure`,
`pip install sherpa-onnx kokoro-onnx soundfile pillow`, and download into `models/`:
`silero_vad.onnx` (and `sherpa-onnx-whisper-small.tar.bz2` for `--mode words`) from
https://github.com/k2-fsa/sherpa-onnx/releases/tag/asr-models.

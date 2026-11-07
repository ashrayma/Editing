# 3 Records Kohli Owns That Sachin Never Touched

A ~80-second 9:16 reel (1080×1920, 30 fps) for theCricketLounge, edited in the style of the reference reel
(dark grain stages, outlined cut-out players, typed stat blocks, chapter numbers, word-by-word captions,
fast cuts, glitches and light leaks), with original 3D, motion graphics, music and SFX.

```
python3 upscale.py               # 1. 4x EDSR upscale of assets/photos -> assets/hi
python3 prep_photos.py           # 2. cut-outs (rembg) with white outline + blurred fills
blender/render.sh                # 3. Blender 3D shots (EEVEE on CPU) -> blender/renders/*.mp4
blender/finish.sh                #    held last frames + clip lengths
node capture/record.js           # 4. screen recordings + screenshots of the record-book page
python3 transcribe.py vo_raw/*    # 5. phrase-level transcript of the raw takes (Whisper small.en, offline)
python3 words.py vo_raw/<take>   #    word timestamps (zipformer) for exact cut points
python3 build_vo.py              #    narration from the edit list in script.py (--tts: temporary AI voice)
python3 faces.py                 # 6. find the players' faces in every photo / cut-out (YuNet)
node measure.js && python3 layout.py   # 7. move any type off faces, hide the logo over faces (repeat until 0)
./make.sh                        # 8. composition -> HyperFrames render -> soundtrack -> final mux
```

## Your voiceover
`vo_raw/` holds the two takes. `script.py` has the line-by-line text as actually spoken (captions come from it)
and `PIECES`, the best take of every line in seconds: take A for the hook to "cheat code", take B from
"Number two" on; the title read-in, the "Number two" false start and the "in the same- / and in the" stumble
are dropped, and "twenty [three] years" is spliced to "twenty years". `build_vo.py` only cuts where there is
a real pause (lines spoken in one breath stay joined, only the captions split), except after "Number
one/two/three", where the 3D chapter card needs the beat. Models (sherpa-onnx, from GitHub releases):
`models/sherpa-onnx-whisper-small.en`, `models/sherpa-onnx-zipformer-en-2023-06-26`.

## Pieces
| file | what |
|---|---|
| `script.py` | the script, one entry per line: spoken text, caption text, pause after |
| `reel.py` | the edit: every visual beat, timed off `out/timeline.json` |
| `soundtrack.py` | original half-time beat (D minor), risers/booms on the chapter numbers, all SFX, ducking |
| `blender/shots.py` | 3D: chapter numbers 1/2/3, the cricket ball, 49 → 50, logo end card |
| `capture/` | the record-book page and the Playwright script that screen-records a browser session on it |
| `assets/ai/` | AI-generated B-roll (Canva) |

Outputs in `out/`: `ThreeRecords_reel.mp4` (full mix) and `ThreeRecords_music_sfx.mp4` (no voice).

Stats as reported up to Sep 2026: Kohli 25 ODI hundreds in successful chases (Sachin 14), average 90+ in
won chases; 68 Tests as captain, 40 wins (Sachin 25, 4); World Cup 765 (2023) vs 673 (2003);
50th ODI hundred in the 2023 semi-final at the Wankhede; 55 ODI hundreds.

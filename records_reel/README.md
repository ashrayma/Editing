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
python3 build_vo.py [take.m4a]   # 5. narration: your recording, or the temporary AI voice
./make.sh                        # 6. composition -> HyperFrames render -> soundtrack -> final mux
```

## Your voiceover
Record the whole script in one take (phone voice memo is fine), with a clear pause (~1 s) between lines,
and run `python3 build_vo.py path/to/take.m4a`. It cleans the audio (de-noise, EQ, compression), splits it
at the pauses and maps the pieces onto the script lines in `script.py`; the whole edit re-times itself.
Keep `script.py` matching what you actually said (the captions come from it).

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

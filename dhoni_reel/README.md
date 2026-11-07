# "I didn't grow out of it" — MS Dhoni, greatest of all time

~80-second 9:16 reel (1080×1920, 30 fps) for theCricketLounge, same pipeline and look as `records_reel/`:
hook → the legends → the build → the twist (a beat of silence, then the 3D #7) → eight receipts → G.O.A.T. outro.

```
python3 upscale.py && python3 prep_photos.py && python3 faces.py   # photos: 4x upscale, cut-outs, faces
blender/render.sh && blender/finish.sh                             # 3D: seven, stumps, trophies, n91, goat (+ logo)
node capture/record.js                                             # record-book screen recordings + screenshots
python3 build_vo.py --tts            # temporary AI voice; with your takes: fill TAKES/PIECES in script.py, then build_vo.py
node measure.js && python3 layout.py # keep type and the logo off faces (repeat until 0 conflicts)
./make.sh                            # composition -> HyperFrames render -> soundtrack -> final mux (-14 LUFS)
```

Legends photos: drop `kallis/warne/murali/dravid/lara/steyn/ponting.jpg` into `assets/photos/` and rerun the photo
steps; each name card switches from type-only to the full-screen photo automatically.

Stats as checked Oct 2026: T20 World Cup 2007 (first tournament as captain), Test No. 1 Dec 2009, 2011 final 91*
finished with a six, Champions Trophy 2013, only captain with all three ICC white-ball trophies, 5 IPL titles
(2010, 2011, 2018, 2021, 2023), 195 international stumpings (Sangakkara 139), 84 ODI not-outs (Pollock, Vaas 72).

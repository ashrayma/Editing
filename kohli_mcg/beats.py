"""The script, one beat per numbered line of SCRIPT_15MIN.md (the recording script). Edit the script there.

Each beat id is "l001".."l100" (line number); CHAPTER maps every beat to its chapter heading. VO is Hinglish;
"(pause)" and "(...)" are recording cues, so they're dropped from the spoken text.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))


def _parse():
    beats, chapter_of, chapters = [], {}, []
    cur = None
    for raw in open(os.path.join(HERE, "SCRIPT_15MIN.md"), encoding="utf-8"):
        ln = raw.strip()
        m = re.match(r"^##\s+(.*?)(?:\s+\(.*\))?$", ln)
        if m:
            cur = m.group(1).strip()
            chapters.append(cur)
            continue
        m = re.match(r"^(\d+)([a-z]?)\.\s+(.*)$", ln)
        if m and cur:
            bid = f"l{int(m.group(1)):03d}{m.group(2)}"
            text = re.sub(r"\(pause\)\s*", "", m.group(3)).strip()
            beats.append((bid, text))
            chapter_of[bid] = cur
    return beats, chapter_of, chapters


BEATS, CHAPTER, CHAPTERS = _parse()
IDS = [b[0] for b in BEATS]

# music-only breathers (seconds of extra silence after a line) so the big moments land
BREATH = {"l004": 1.2, "l006": 2.6, "l015": 1.5, "l032": 2.0, "l043": 1.5, "l053": 1.5, "l059": 2.5, "l063": 1.5,
          "l069": 1.2, "l074": 3.0, "l077": 2.5, "l079": 1.5, "l084": 1.5, "l086": 1.0, "l092": 5.0, "l094": 2.0,
          "l098": 1.5,
          # 15-minute version: a little more air around the big moments
          "l011e": 2.0, "l025c": 1.8, "l048a": 1.2, "l058a": 1.2, "l075b": 2.2, "l087a": 1.0, "l094a": 2.0,
          "l013": 1.0, "l041": 1.5, "l047": 1.2, "l062": 1.2, "l072": 1.5, "l078": 1.5, "l091": 1.0, "l097": 1.5}
for _k, _v in {"l006": 1.0, "l032": 1.0, "l043": 1.0, "l053": 1.0, "l059": 1.0, "l063": 1.0, "l069": 1.0,
               "l074": 1.5, "l077": 1.0, "l079": 1.0, "l084": 1.0, "l092": 1.5, "l098": 1.0}.items():
    BREATH[_k] = BREATH.get(_k, 0.0) + _v          # +14 s of music-only air: lands the cut on 15:00
NEW = [b for b in [x[0] for x in BEATS] if b[-1].isalpha()]   # lines added for the 15-minute cut
TEXT = dict(BEATS)

if __name__ == "__main__":
    print(len(BEATS), "beats,", len(CHAPTERS), "chapters:", CHAPTERS)
    print(sum(len(t.split()) for _, t in BEATS), "words")

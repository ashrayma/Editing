"""The script, one beat per numbered line of SCRIPT.md (ids l01..l25)."""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
BEATS = [((m.group(1).lower() if m.group(1).startswith("H") else f"l{int(m.group(1)):02d}"), m.group(2).strip())
         for m in (re.match(r"^(H\d|\d+)\.\s+(.*)$", ln.strip()) for ln in open(os.path.join(HERE, "SCRIPT.md"), encoding="utf-8"))
         if m]
IDS = [b for b, _ in BEATS]
TEXT = dict(BEATS)
BREATH = {"h3": 0.4, "l02": 0.6, "l10": 0.5, "l13": 0.4, "l17": 0.8, "l24": 0.4}

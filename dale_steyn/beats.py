"""The script, one beat per numbered line of SCRIPT.md (ids l01..l24)."""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
BEATS = [(f"l{int(m.group(1)):02d}", m.group(2).strip())
         for m in (re.match(r"^(\d+)\.\s+(.*)$", ln.strip()) for ln in open(os.path.join(HERE, "SCRIPT.md"), encoding="utf-8"))
         if m]
IDS = [b for b, _ in BEATS]
TEXT = dict(BEATS)
DROP = set()
BREATH = {"l03": 0.2, "l08": 0.4, "l12": 0.25, "l19": 0.3, "l21": 0.3}

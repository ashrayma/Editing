#!/usr/bin/env python3
"""Cut every clip the edit needs, in parallel: a planning pass of gen.py lists the cuts, then 4 at a time.

    python3 cut_all.py && python3 gen.py
"""
import concurrent.futures as cf
import importlib.util
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ["PLAN_ONLY"] = "1"
sys.path.insert(0, HERE)
import footage  # noqa: E402

spec = importlib.util.spec_from_file_location("gen", os.path.join(HERE, "gen.py"))
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)                     # runs the film code; take() records instead of cutting
jobs = list({tuple(c): c for c in footage.PLAN}.values())
print(len(jobs), "clips to cut", flush=True)
with cf.ThreadPoolExecutor(int(os.environ.get("JOBS", "4"))) as ex:
    for k, _ in enumerate(ex.map(lambda c: subprocess.run(c, check=True), jobs), 1):
        if k % 10 == 0:
            print(k, "done", flush=True)
print("CUT_ALL_DONE")

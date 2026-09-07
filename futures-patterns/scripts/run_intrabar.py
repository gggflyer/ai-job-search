#!/usr/bin/env python3
"""Intrabar path analysis: high-first vs low-first inside each N-minute bar."""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import add_data_args, resolve  # noqa: E402
from analysis.intrabar import build_path_bars, path_report  # noqa: E402

p = argparse.ArgumentParser(description=__doc__)
add_data_args(p)
p.add_argument("--minutes", type=int, default=5, help="size of the bar to analyse, built from the source bars")
a = p.parse_args()
bars, tick, _ = resolve(a)
pbs = build_path_bars(bars, a.minutes, tick, a.tol)
print(f"{a.csv}: {a.minutes}-minute bars built from {len(bars)} source bars")
print()
print(path_report(pbs))

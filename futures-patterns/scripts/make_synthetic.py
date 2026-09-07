#!/usr/bin/env python3
"""Generate random-walk 1-minute bars (the null model)."""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from analysis.synthetic import generate, write_csv  # noqa: E402

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--days", type=int, default=60)
p.add_argument("--tick", type=float, default=0.25)
p.add_argument("--sd", type=float, default=4.0, help="ticks per minute std-dev")
p.add_argument("--seed", type=int, default=42)
p.add_argument("--out", default="data/synthetic_1m.csv")
a = p.parse_args()
bars = generate(a.days, tick=a.tick, ticks_per_min_sd=a.sd, seed=a.seed)
os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
write_csv(bars, a.out)
print(f"wrote {len(bars)} 1-minute bars over {a.days} sessions to {a.out}")

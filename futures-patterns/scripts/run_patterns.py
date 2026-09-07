#!/usr/bin/env python3
"""Conditional next-bar outcome tables keyed by the last k bars."""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import add_data_args, resolve  # noqa: E402
from analysis.bars import resample, label_bars  # noqa: E402
from analysis.patterns import (build_setups, conditional_table, format_table,  # noqa: E402
                               split_by_date, summarise, time_bucket)

p = argparse.ArgumentParser(description=__doc__)
add_data_args(p)
p.add_argument("--resample", type=int, default=5, help="bar size in minutes to analyse")
p.add_argument("--lookback", type=int, default=2, help="how many bars form the key (1..3 sensible)")
p.add_argument("--key", default="range", choices=["range", "range_dir", "range_close", "closepos"],
               help="range: I/O/U/D. range_dir: adds +/-/0. range_close: adds A/B/W. closepos: adds H/L/m (closes on own high/low/middle)")
p.add_argument("--min-n", type=int, default=30, help="hide keys with fewer setups than this")
p.add_argument("--low-n", type=int, default=200, help="flag rows under this count")
p.add_argument("--allow-cross-day", action="store_true", help="let a setup span the session break")
p.add_argument("--oos", type=float, default=0.0, help="hold out the last FRACTION of setups and print both halves")
p.add_argument("--by-time", type=int, default=0, help="also print the ALL row per N-minute time-of-day bucket")
p.add_argument("--slip", type=float, default=1.0, help="extra slippage in ticks per round trip added to costs (stop entries fill through the price)")
p.add_argument("--all-outcomes", action="store_true", help="show every outcome column")
a = p.parse_args()

bars, tick, cost = resolve(a)
cost += a.slip
bars = resample(bars, a.resample) if a.resample > 1 else bars
labelled = label_bars(bars, tick, a.tol)
setups = build_setups(labelled, a.lookback, a.key, tick, a.tol, same_day_only=not a.allow_cross_day)
print(f"{a.csv}: {len(bars)} bars of {a.resample}m, {len(setups)} setups, key={a.key}, lookback={a.lookback}, tick={tick}, cost={cost:.2f}t")
print(f"date range {bars[0].ts} .. {bars[-1].ts}")
print()
outs = None
if a.all_outcomes:
    from analysis.patterns import OUTCOMES
    outs = OUTCOMES

def show(title, ss):
    print(f"=== {title} ({len(ss)} setups) ===")
    base, rows = conditional_table(ss, a.min_n)
    print(format_table(base, rows, low_n=a.low_n, cost_ticks=cost, **({"outcomes": outs} if outs else {})))
    print()

if a.oos > 0:
    ins, oos = split_by_date(setups, 1 - a.oos)
    show("IN-SAMPLE", ins)
    show("OUT-OF-SAMPLE", oos)
else:
    show("ALL DATA", setups)

if a.by_time:
    print(f"=== base rates by {a.by_time}-minute time-of-day bucket ===")
    from collections import defaultdict
    g = defaultdict(list)
    for s in setups:
        g[time_bucket(s, a.by_time)].append(s)
    rows = [summarise(v, k) for k, v in sorted(g.items())]
    print(format_table(summarise(setups), rows, low_n=a.low_n, cost_ticks=cost))

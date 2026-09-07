#!/usr/bin/env python3
"""Merge per-contract exports (e.g. NinjaTrader 'ES 03-26.Last.txt', 'ES 06-26.Last.txt')
into one continuous, UNADJUSTED front-month CSV.

Roll rule: for each calendar day, keep the contract with the highest total
volume that day. Days where the chosen contract changes are listed so they can
be excluded (`--drop-roll-days`). Output is in the preferred CSV format with
whatever timestamp convention the inputs had (convert afterwards with the
--ts-is-close / --tz-from flags on the analysis scripts, or pass them here).
"""
import argparse
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from analysis.bars import load_csv, shift_close_to_open, convert_tz  # noqa: E402
from analysis.synthetic import write_csv  # noqa: E402

p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
p.add_argument("files", nargs="+", help="one export per contract")
p.add_argument("--out", required=True)
p.add_argument("--drop-roll-days", action="store_true", help="omit the days on which the front contract changes")
p.add_argument("--ts-is-close", action="store_true", help="inputs are close-stamped (NinjaTrader); shift to open time")
p.add_argument("--src-minutes", type=int, default=1)
p.add_argument("--tz-from", help="convert from this IANA zone ...")
p.add_argument("--tz-to", default="America/New_York", help="... to this one")
a = p.parse_args()

by_day = defaultdict(dict)        # date -> contract -> bars
vol_by_day = defaultdict(dict)    # date -> contract -> volume
for f in a.files:
    bars = load_csv(f)
    if a.ts_is_close:
        bars = shift_close_to_open(bars, a.src_minutes)
    if a.tz_from:
        bars = convert_tz(bars, a.tz_from, a.tz_to)
    name = os.path.basename(f)
    for b in bars:
        by_day[b.ts.date()].setdefault(name, []).append(b)
        vol_by_day[b.ts.date()][name] = vol_by_day[b.ts.date()].get(name, 0.0) + b.volume

out = []
prev = None
roll_days = []
for day in sorted(by_day):
    best = max(vol_by_day[day], key=vol_by_day[day].get)
    if prev is not None and best != prev:
        roll_days.append((day, prev, best))
        if a.drop_roll_days:
            prev = best
            continue
    out.extend(by_day[day][best])
    prev = best

out.sort(key=lambda b: b.ts)
write_csv(out, a.out)
print(f"wrote {len(out)} bars over {len(by_day)} days to {a.out}")
for day, frm, to in roll_days:
    print(f"  roll {day}: {frm} -> {to}{'  (dropped)' if a.drop_roll_days else ''}")
if not roll_days and len(a.files) > 1:
    print("  WARNING: no roll detected across multiple files; check that volumes are present")

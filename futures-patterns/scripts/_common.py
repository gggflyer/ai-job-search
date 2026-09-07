import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from analysis import instruments  # noqa: E402
from analysis.bars import load_csv, shift_close_to_open, filter_session, parse_session, convert_tz  # noqa: E402


def add_data_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("csv", help="1-minute (or finer) OHLC CSV, see data/README.md")
    p.add_argument("--symbol", help="instrument symbol from analysis/instruments.py (sets tick and costs)")
    p.add_argument("--tick", type=float, help="tick size, overrides --symbol")
    p.add_argument("--tol", type=int, default=0, help="tolerance in ticks for 'closes on high/low' tests")
    p.add_argument("--session", help="keep bars with open time in HH:MM-HH:MM (file's own clock), e.g. 09:30-16:00")
    p.add_argument("--ts-is-close", action="store_true", help="source stamps bars with CLOSE time (NinjaTrader default)")
    p.add_argument("--tz-from", help="IANA zone the file's timestamps are in, e.g. UTC (NinjaTrader exports)")
    p.add_argument("--tz-to", default="America/New_York", help="zone to convert to before session filtering")
    p.add_argument("--src-minutes", type=int, default=1, help="bar size of the source file in minutes (for --ts-is-close)")


def resolve(args):
    tick = args.tick
    cost = 0.0
    if args.symbol:
        ins = instruments.get(args.symbol)
        tick = tick or ins.tick
        cost = ins.commission_ticks
    if tick is None:
        raise SystemExit("Need --tick or --symbol")
    bars = load_csv(args.csv)
    if args.ts_is_close:
        bars = shift_close_to_open(bars, args.src_minutes)
    if args.tz_from:
        bars = convert_tz(bars, args.tz_from, args.tz_to)
    if args.session:
        bars = filter_session(bars, *parse_session(args.session))
    return bars, tick, cost

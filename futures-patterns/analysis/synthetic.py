"""Random-walk 1-minute bars: the null model. Prices move by an integer number
of ticks per minute with no drift and no memory, so any 'pattern' found here
is sampling noise."""
from __future__ import annotations

import random
from datetime import datetime, time, timedelta

from .bars import Bar


def generate(days: int, tick: float = 0.25, start_price: float = 5000.0,
             session=(time(9, 30), time(16, 0)), ticks_per_min_sd: float = 4.0,
             sub_steps: int = 8, seed: int = 42, start_date: datetime = datetime(2026, 1, 5)) -> list[Bar]:
    rng = random.Random(seed)
    bars: list[Bar] = []
    price = start_price
    day = start_date
    made = 0
    while made < days:
        if day.weekday() < 5:
            t = datetime.combine(day.date(), session[0])
            end = datetime.combine(day.date(), session[1])
            while t < end:
                o = price
                hi = lo = price
                for _ in range(sub_steps):
                    price += round(rng.gauss(0, ticks_per_min_sd / sub_steps ** 0.5)) * tick
                    hi = max(hi, price)
                    lo = min(lo, price)
                bars.append(Bar(t, round(o, 6), round(hi, 6), round(lo, 6), round(price, 6), float(rng.randint(50, 500))))
                t += timedelta(minutes=1)
            made += 1
        day += timedelta(days=1)
    return bars


def write_csv(bars: list[Bar], path: str) -> None:
    with open(path, "w") as f:
        f.write("timestamp,open,high,low,close,volume\n")
        for b in bars:
            f.write(f"{b.ts:%Y-%m-%d %H:%M:%S},{b.open},{b.high},{b.low},{b.close},{int(b.volume)}\n")

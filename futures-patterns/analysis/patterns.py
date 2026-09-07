"""Next-bar outcomes, trigger simulation and conditional probability tables."""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Optional

from .bars import Bar, Labelled

OUTCOMES = (
    "cross_high", "close_above_high", "cross_high_fail",
    "cross_low", "close_below_low", "cross_low_fail",
    "inside", "outside", "next_closes_on_high", "next_closes_on_low",
)


@dataclass
class Outcome:
    flags: dict
    long_filled: bool
    long_pnl: Optional[float]   # ticks, before costs
    long_mfe: Optional[float]
    long_mae: Optional[float]
    short_filled: bool
    short_pnl: Optional[float]
    short_mfe: Optional[float]
    short_mae: Optional[float]


def next_bar_outcome(s: Bar, n: Bar, tick: float, tol_ticks: int = 0) -> Outcome:
    eps = tol_ticks * tick + tick * 1e-6
    ch = n.high > s.high
    cl = n.low < s.low
    cah = n.close > s.high
    cbl = n.close < s.low
    flags = {
        "cross_high": ch, "close_above_high": cah, "cross_high_fail": ch and not cah,
        "cross_low": cl, "close_below_low": cbl, "cross_low_fail": cl and not cbl,
        "inside": not ch and not cl, "outside": ch and cl,
        "next_closes_on_high": (n.high - n.close) <= eps,
        "next_closes_on_low": (n.close - n.low) <= eps,
    }
    # Long: buy stop at s.high + tick, exit at n.close
    entry_l = s.high + tick
    lf = n.high >= entry_l - tick * 1e-6
    l_pnl = (n.close - entry_l) / tick if lf else None
    l_mfe = (n.high - entry_l) / tick if lf else None
    l_mae = (n.low - entry_l) / tick if lf else None
    entry_s = s.low - tick
    sf = n.low <= entry_s + tick * 1e-6
    s_pnl = (entry_s - n.close) / tick if sf else None
    s_mfe = (entry_s - n.low) / tick if sf else None
    s_mae = (entry_s - n.high) / tick if sf else None
    return Outcome(flags, lf, l_pnl, l_mfe, l_mae, sf, s_pnl, s_mfe, s_mae)


@dataclass
class Setup:
    idx: int
    key: str
    labelled: Labelled
    outcome: Outcome


def build_setups(labelled: list[Labelled], lookback: int, key_kind: str, tick: float,
                 tol_ticks: int = 0, same_day_only: bool = True,
                 setup_filter: Optional[Callable[[Labelled], bool]] = None) -> list[Setup]:
    """For each bar i with `lookback` fully labelled bars ending at i, key it by
    those bars and measure bar i+1. No lookahead: key uses bars <= i only."""
    setups: list[Setup] = []
    for i in range(lookback, len(labelled) - 1):
        window = labelled[i - lookback + 1: i + 1]
        if any(w.rng == "?" for w in window):
            continue
        nxt = labelled[i + 1]
        if same_day_only and (nxt.new_day or any(w.new_day for w in window[1:])):
            continue
        if setup_filter is not None and not setup_filter(labelled[i]):
            continue
        key = " ".join(w.key(key_kind) for w in window)
        setups.append(Setup(i, key, labelled[i], next_bar_outcome(labelled[i].bar, nxt.bar, tick, tol_ticks)))
    return setups


# ------------------------------------------------------------------ tables

@dataclass
class Row:
    key: str
    n: int
    rates: dict          # outcome -> rate
    long_fill: float
    long_n: int
    long_mean: float
    long_win: float
    short_fill: float
    short_n: int
    short_mean: float
    short_win: float


def _mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def summarise(setups: list[Setup], key: str = "ALL") -> Row:
    n = len(setups)
    rates = {o: sum(1 for s in setups if s.outcome.flags[o]) / n for o in OUTCOMES} if n else {o: float("nan") for o in OUTCOMES}
    lp = [s.outcome.long_pnl for s in setups if s.outcome.long_filled]
    sp = [s.outcome.short_pnl for s in setups if s.outcome.short_filled]
    return Row(key, n, rates,
               len(lp) / n if n else float("nan"), len(lp), _mean(lp), _mean([p > 0 for p in lp]),
               len(sp) / n if n else float("nan"), len(sp), _mean(sp), _mean([p > 0 for p in sp]))


def conditional_table(setups: list[Setup], min_n: int = 1) -> tuple[Row, list[Row]]:
    groups: dict[str, list[Setup]] = defaultdict(list)
    for s in setups:
        groups[s.key].append(s)
    base = summarise(setups)
    rows = [summarise(g, k) for k, g in groups.items() if len(g) >= min_n]
    rows.sort(key=lambda r: -r.n)
    return base, rows


def zscore(p: float, p0: float, n: int) -> float:
    if n == 0 or p0 <= 0 or p0 >= 1:
        return float("nan")
    return (p - p0) / math.sqrt(p0 * (1 - p0) / n)


def format_table(base: Row, rows: list[Row], outcomes=("cross_high", "close_above_high", "cross_low",
                                                       "close_below_low", "inside", "outside"),
                 low_n: int = 200, cost_ticks: float = 0.0) -> str:
    """Plain-text table. Rate columns show percent and z vs base in brackets."""
    head = ["key", "n"] + [o for o in outcomes] + ["L fill", "L mean", "L win", "S fill", "S mean", "S win", "flag"]
    lines = []

    def fmt_row(r: Row, is_base: bool) -> list[str]:
        cells = [r.key, str(r.n)]
        for o in outcomes:
            p = r.rates[o]
            if is_base or math.isnan(p):
                cells.append(f"{p*100:5.1f}%")
            else:
                cells.append(f"{p*100:5.1f}% [{zscore(p, base.rates[o], r.n):+.1f}]")
        cells += [f"{r.long_fill*100:4.0f}%", f"{r.long_mean - cost_ticks:+.2f}t", f"{r.long_win*100:4.0f}%",
                  f"{r.short_fill*100:4.0f}%", f"{r.short_mean - cost_ticks:+.2f}t", f"{r.short_win*100:4.0f}%",
                  "" if (is_base or r.n >= low_n) else "low-n"]
        return cells

    table = [head, fmt_row(base, True)] + [fmt_row(r, False) for r in rows]
    widths = [max(len(row[i]) for row in table) for i in range(len(head))]
    for i, row in enumerate(table):
        lines.append("  ".join(c.ljust(w) if j == 0 else c.rjust(w) for j, (c, w) in enumerate(zip(row, widths))))
        if i == 0:
            lines.append("-" * len(lines[-1]))
    lines.append("")
    lines.append("Rates are P(outcome on the NEXT bar | key). [z] is a rough binomial z-score vs the ALL row.")
    lines.append(f"L/S = long/short stop trigger one tick beyond the setup bar, exit at next close; means in ticks after {cost_ticks:.2f}t costs.")
    return "\n".join(lines)


def split_by_date(setups: list[Setup], frac: float = 0.7) -> tuple[list[Setup], list[Setup]]:
    cut = int(len(setups) * frac)
    return setups[:cut], setups[cut:]


def time_bucket(setup: Setup, minutes: int = 30) -> str:
    t = setup.labelled.bar.ts
    m = (t.hour * 60 + t.minute) // minutes * minutes
    return f"{m // 60:02d}:{m % 60:02d}"

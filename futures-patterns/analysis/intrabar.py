"""Intrabar path analysis: which extreme was visited first inside a bar built
from finer bars, and what that implied for the close. Tests H1 from
docs/RESEARCH_PLAN.md."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

from .bars import Bar, bucket_start


@dataclass
class PathBar:
    bar: Bar
    n_sub: int
    high_first: Optional[bool]    # None if both extremes in the same sub-bar
    open_is_high: bool
    open_is_low: bool
    close_is_high: bool
    close_is_low: bool
    first_sub_dir: str

    @property
    def path(self) -> str:
        return "same" if self.high_first is None else ("high_first" if self.high_first else "low_first")


def build_path_bars(minute_bars: list[Bar], minutes: int, tick: float, tol_ticks: int = 0) -> list[PathBar]:
    eps = tol_ticks * tick + tick * 1e-6
    groups: dict = defaultdict(list)
    order: list = []
    for b in minute_bars:
        k = bucket_start(b.ts, minutes)
        if k not in groups:
            order.append(k)
        groups[k].append(b)
    out: list[PathBar] = []
    for k in order:
        subs = groups[k]
        if len(subs) < 2:
            continue
        H = max(s.high for s in subs)
        L = min(s.low for s in subs)
        ih = next(i for i, s in enumerate(subs) if s.high == H)
        il = next(i for i, s in enumerate(subs) if s.low == L)
        bar = Bar(k, subs[0].open, H, L, subs[-1].close, sum(s.volume for s in subs))
        out.append(PathBar(
            bar, len(subs),
            None if ih == il else ih < il,
            (H - bar.open) <= eps, (bar.open - L) <= eps,
            (H - bar.close) <= eps, (bar.close - L) <= eps,
            subs[0].direction,
        ))
    return out


def _rate(xs) -> float:
    xs = list(xs)
    return sum(xs) / len(xs) if xs else float("nan")


def path_report(pbs: list[PathBar]) -> str:
    n = len(pbs)
    lines = [f"Bars: {n}   (sub-bars per bar: min {min(p.n_sub for p in pbs)}, max {max(p.n_sub for p in pbs)})", ""]
    lines.append("Path frequencies")
    for p in ("high_first", "low_first", "same"):
        lines.append(f"  {p:11s} {_rate(x.path == p for x in pbs)*100:5.1f}%")
    lines.append("")
    lines.append("Where the open sits")
    lines.append(f"  open is high    {_rate(x.open_is_high for x in pbs)*100:5.1f}%")
    lines.append(f"  open is low     {_rate(x.open_is_low for x in pbs)*100:5.1f}%")
    lines.append(f"  close is high   {_rate(x.close_is_high for x in pbs)*100:5.1f}%")
    lines.append(f"  close is low    {_rate(x.close_is_low for x in pbs)*100:5.1f}%")
    lines.append("")
    lines.append("H1: given the bar went to its high FIRST ...")
    hf = [x for x in pbs if x.high_first is True]
    lf = [x for x in pbs if x.high_first is False]
    base_down = _rate(x.bar.close < x.bar.open for x in pbs)
    lines.append(f"  n = {len(hf)}")
    lines.append(f"  P(close < open | high first) = {_rate(x.bar.close < x.bar.open for x in hf)*100:5.1f}%   base P(close < open) = {base_down*100:5.1f}%")
    lines.append(f"  P(open is low | high first)  = {_rate(x.open_is_low for x in hf)*100:5.1f}%   base = {_rate(x.open_is_low for x in pbs)*100:5.1f}%")
    lines.append(f"  P(close is low | high first) = {_rate(x.close_is_low for x in hf)*100:5.1f}%")
    lines.append("  ... and the mirror, given the bar went to its LOW first")
    lines.append(f"  n = {len(lf)}")
    lines.append(f"  P(close > open | low first)  = {_rate(x.bar.close > x.bar.open for x in lf)*100:5.1f}%   base P(close > open) = {_rate(x.bar.close > x.bar.open for x in pbs)*100:5.1f}%")
    lines.append(f"  P(open is high | low first)  = {_rate(x.open_is_high for x in lf)*100:5.1f}%")
    lines.append("")
    lines.append("First sub-bar direction as a predictor of the whole bar")
    for d in ("+", "-"):
        grp = [x for x in pbs if x.first_sub_dir == d]
        lines.append(f"  first minute {d}: n={len(grp):6d}  P(bar closes {d}) = {_rate((x.bar.close > x.bar.open) if d == '+' else (x.bar.close < x.bar.open) for x in grp)*100:5.1f}%"
                     f"   P(high first) = {_rate(x.high_first is True for x in grp)*100:5.1f}%")
    lines.append("")
    lines.append("Caveat: 'high first' is only knowable after the bar closes. To trade it you need a")
    lines.append("real-time proxy (e.g. first minute direction, or price at minute k), which is what the last block tests.")
    return "\n".join(lines)

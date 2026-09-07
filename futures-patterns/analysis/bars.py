"""Loading, resampling and labelling of OHLC bars.

Definitions follow docs/BAR_TAXONOMY.md exactly. Keep them in sync.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from typing import Iterable, Optional

_TS_FORMATS = (
    "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M",
    "%Y%m%d %H%M%S", "%Y%m%d %H%M", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M",
    "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S%z",
)


@dataclass
class Bar:
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    @property
    def range(self) -> float:
        return self.high - self.low

    @property
    def direction(self) -> str:
        return "+" if self.close > self.open else "-" if self.close < self.open else "0"


def parse_ts(s: str) -> datetime:
    s = s.strip()
    for fmt in _TS_FORMATS:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        raise ValueError(f"Unrecognised timestamp {s!r}")


def load_csv(path: str, delimiter: Optional[str] = None) -> list[Bar]:
    """Load OHLC bars from CSV. Column names are matched case-insensitively.

    Accepts a single timestamp column (timestamp/time/datetime/date) or a
    separate date + time pair. Also accepts NinjaTrader's headerless
    'yyyyMMdd HHmmss;open;high;low;close;volume' export.
    """
    with open(path, newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        if delimiter is None:
            delimiter = ";" if sample.count(";") > sample.count(",") else ","
        first = sample.splitlines()[0] if sample else ""
        has_header = any(c.isalpha() for c in first.split(delimiter)[0])
        reader = csv.reader(f, delimiter=delimiter)
        bars: list[Bar] = []
        if has_header:
            header = [h.strip().lower() for h in next(reader)]
            col = {name: i for i, name in enumerate(header)}
            ts_col = next((col[c] for c in ("timestamp", "datetime", "time", "date") if c in col), None)
            date_col = col.get("date")
            time_col = col.get("time")
            o, h, l, c = (col[k] for k in ("open", "high", "low", "close"))
            v = col.get("volume", col.get("vol"))
            for row in reader:
                if not row or not row[0].strip():
                    continue
                if date_col is not None and time_col is not None and date_col != ts_col:
                    ts = parse_ts(f"{row[date_col]} {row[time_col]}")
                else:
                    ts = parse_ts(row[ts_col])
                bars.append(Bar(ts, float(row[o]), float(row[h]), float(row[l]), float(row[c]),
                                float(row[v]) if v is not None and row[v] else 0.0))
        else:
            for row in reader:
                if not row or not row[0].strip():
                    continue
                ts = parse_ts(row[0])
                vol = float(row[5]) if len(row) > 5 and row[5] else 0.0
                bars.append(Bar(ts, float(row[1]), float(row[2]), float(row[3]), float(row[4]), vol))
    bars.sort(key=lambda b: b.ts)
    return bars


def shift_close_to_open(bars: list[Bar], minutes: int) -> list[Bar]:
    """If the source stamps bars with their CLOSE time, convert to open time."""
    d = timedelta(minutes=minutes)
    return [Bar(b.ts - d, b.open, b.high, b.low, b.close, b.volume) for b in bars]


def convert_tz(bars: list[Bar], from_tz: str, to_tz: str) -> list[Bar]:
    """Re-stamp naive timestamps from one IANA zone to another (e.g. UTC ->
    America/New_York). Needs the `tzdata` package on Windows."""
    from zoneinfo import ZoneInfo
    src, dst = ZoneInfo(from_tz), ZoneInfo(to_tz)
    return [Bar(b.ts.replace(tzinfo=src).astimezone(dst).replace(tzinfo=None),
                b.open, b.high, b.low, b.close, b.volume) for b in bars]


def bucket_start(ts: datetime, minutes: int) -> datetime:
    floored_min = (ts.minute // minutes) * minutes
    return ts.replace(minute=floored_min, second=0, microsecond=0)


def resample(bars: Iterable[Bar], minutes: int) -> list[Bar]:
    """Aggregate open-time-stamped bars into `minutes`-minute bars."""
    out: list[Bar] = []
    cur: Optional[Bar] = None
    cur_key = None
    for b in bars:
        key = bucket_start(b.ts, minutes)
        if key != cur_key:
            if cur is not None:
                out.append(cur)
            cur = Bar(key, b.open, b.high, b.low, b.close, b.volume)
            cur_key = key
        else:
            cur.high = max(cur.high, b.high)
            cur.low = min(cur.low, b.low)
            cur.close = b.close
            cur.volume += b.volume
    if cur is not None:
        out.append(cur)
    return out


def filter_session(bars: Iterable[Bar], start: time, end: time) -> list[Bar]:
    """Keep bars whose open time is in [start, end). Handles overnight sessions."""
    if start <= end:
        return [b for b in bars if start <= b.ts.time() < end]
    return [b for b in bars if b.ts.time() >= start or b.ts.time() < end]


def parse_session(s: str) -> tuple[time, time]:
    a, b = s.split("-")
    return time.fromisoformat(a), time.fromisoformat(b)


# ---------------------------------------------------------------- labelling

@dataclass
class Labelled:
    bar: Bar
    prev: Optional[Bar]
    rng: str = "?"        # I / O / U / D  (taxonomy s.1), '?' for the first bar
    close_rel: str = "?"  # A / B / W      (taxonomy s.2)
    close_pos: Optional[float] = None
    closes_on_high: bool = False
    closes_on_low: bool = False
    opens_on_high: bool = False
    opens_on_low: bool = False
    new_day: bool = False

    @property
    def dir(self) -> str:
        return self.bar.direction

    def key(self, kind: str) -> str:
        if kind == "range":
            return self.rng
        if kind == "range_dir":
            return self.rng + self.dir
        if kind == "range_close":
            return self.rng + self.close_rel
        if kind == "closepos":
            return self.rng + ("H" if self.closes_on_high else "L" if self.closes_on_low else "m")
        raise ValueError(kind)


def range_label(b: Bar, p: Bar) -> str:
    up = b.high > p.high
    dn = b.low < p.low
    if up and dn:
        return "O"
    if up:
        return "U"
    if dn:
        return "D"
    return "I"


def close_rel_label(b: Bar, p: Bar) -> str:
    if b.close > p.high:
        return "A"
    if b.close < p.low:
        return "B"
    return "W"


def label_bars(bars: list[Bar], tick: float, tol_ticks: int = 0) -> list[Labelled]:
    eps = tol_ticks * tick + tick * 1e-6   # float safety
    out: list[Labelled] = []
    prev: Optional[Bar] = None
    for b in bars:
        L = Labelled(bar=b, prev=prev)
        if prev is not None:
            L.rng = range_label(b, prev)
            L.close_rel = close_rel_label(b, prev)
            L.new_day = b.ts.date() != prev.ts.date()
        if b.range > 0:
            L.close_pos = (b.close - b.low) / b.range
        L.closes_on_high = (b.high - b.close) <= eps
        L.closes_on_low = (b.close - b.low) <= eps
        L.opens_on_high = (b.high - b.open) <= eps
        L.opens_on_low = (b.open - b.low) <= eps
        out.append(L)
        prev = b
    return out

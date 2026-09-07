"""Tick sizes, point values and cost assumptions per instrument.

CORRECT THESE against your broker's statement. Commission is a round-trip
estimate in USD per contract and is the number most likely to be wrong.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Instrument:
    symbol: str
    name: str
    exchange: str
    tick: float          # minimum price increment
    point_value: float   # USD per 1.0 move in price, per contract
    commission_rt: float # USD round trip per contract, estimate

    @property
    def tick_value(self) -> float:
        return self.tick * self.point_value

    @property
    def commission_ticks(self) -> float:
        return self.commission_rt / self.tick_value


INSTRUMENTS = {
    "ES":  Instrument("ES",  "E-mini S&P 500",       "CME",   0.25,  50.0,   4.00),
    "MES": Instrument("MES", "Micro E-mini S&P 500", "CME",   0.25,  5.0,    1.20),
    "NQ":  Instrument("NQ",  "E-mini Nasdaq-100",    "CME",   0.25,  20.0,   4.00),
    "MNQ": Instrument("MNQ", "Micro E-mini Nasdaq",  "CME",   0.25,  2.0,    1.20),
    "GC":  Instrument("GC",  "Gold",                 "COMEX", 0.10,  100.0,  4.50),
    "MGC": Instrument("MGC", "Micro Gold",           "COMEX", 0.10,  10.0,   1.50),
    "CL":  Instrument("CL",  "Light Sweet Crude",    "NYMEX", 0.01,  1000.0, 4.50),
    "MCL": Instrument("MCL", "Micro Crude",          "NYMEX", 0.01,  100.0,  1.50),
    "BTC": Instrument("BTC", "Bitcoin futures",      "CME",   5.0,   5.0,    12.00),
    "MBT": Instrument("MBT", "Micro Bitcoin",        "CME",   5.0,   0.1,    3.00),
    "KC":  Instrument("KC",  "Coffee C",             "ICE",   0.05,  375.0,  5.00),
}


def get(symbol: str) -> Instrument:
    try:
        return INSTRUMENTS[symbol.upper()]
    except KeyError:
        raise SystemExit(f"Unknown instrument {symbol!r}. Add it to analysis/instruments.py "
                         f"or pass --tick explicitly.")

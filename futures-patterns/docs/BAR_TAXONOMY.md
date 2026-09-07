# Bar taxonomy

All definitions are tick-aware. `tick` is the instrument's minimum price
increment. `S` is the **setup bar** (the bar already closed), `N` is the
**next bar**. Every comparison below is strict unless a tolerance is stated.

## 1. Range relationship of a bar to the previous bar

Exactly one of these applies to every bar after the first. Ties count toward
"inside" (a tie is not a break).

| Label | Name | Definition |
|---|---|---|
| `I` | Inside | `high <= prev.high` and `low >= prev.low` |
| `O` | Outside | `high > prev.high` and `low < prev.low` |
| `U` | Up-range | `high > prev.high` and `low >= prev.low` |
| `D` | Down-range | `low < prev.low` and `high <= prev.high` |

These four are exhaustive and mutually exclusive.

## 2. Close relationship to the previous bar's range

| Label | Name | Definition |
|---|---|---|
| `A` | Closes above prior high | `close > prev.high` |
| `B` | Closes below prior low | `close < prev.low` |
| `W` | Closes within prior range | otherwise (inclusive of the boundaries) |

"Crosses the high and stays there" is `U` or `O` **and** `A`.
"Crosses the high and fails" is `U` or `O` **and not** `A`.

## 3. Close position within the bar's own range

`close_pos = (close - low) / (high - low)` in `[0, 1]`. Undefined when
`high == low` (a doji tick), which is recorded separately.

| Name | Definition |
|---|---|
| Closes on own high | `high - close <= tol * tick` (default `tol = 0`) |
| Closes on own low | `close - low <= tol * tick` |
| Opens on own high | `high - open <= tol * tick` |
| Opens on own low | `open - low <= tol * tick` |
| Direction | `+` if `close > open`, `-` if `close < open`, `0` if equal |

## 4. Next-bar outcomes measured for every setup bar `S`

| Outcome | Definition |
|---|---|
| `cross_high` | `N.high > S.high` |
| `close_above_high` | `N.close > S.high` (implies `cross_high`) |
| `cross_high_fail` | `cross_high and not close_above_high` |
| `cross_low` | `N.low < S.low` |
| `close_below_low` | `N.close < S.low` |
| `cross_low_fail` | `cross_low and not close_below_low` |
| `inside` | `not cross_high and not cross_low` |
| `outside` | `cross_high and cross_low` |
| `next_closes_on_high` | `N.high - N.close <= tol * tick` |
| `next_closes_on_low` | `N.close - N.low <= tol * tick` |

## 5. Trigger simulation (single-bar hold)

**Long trigger.** Entry stop at `S.high + tick`. Filled if `N.high >= entry`.
Exit at `N.close`. Result in ticks: `(N.close - entry) / tick`, minus slippage
and commission.

**Short trigger.** Entry stop at `S.low - tick`. Filled if `N.low <= entry`.
Exit at `N.close`.

Recorded per filled trigger: `pnl_ticks`, `mfe_ticks` (best excursion inside
`N`), `mae_ticks` (worst excursion inside `N`).

A known limitation: the single-bar simulation cannot know whether `N` hit the
entry before or after its adverse excursion. The intrabar path analysis on
1-minute bars (section 6) is how that gets resolved for the 5-minute setups.

## 6. Intrabar path (needs finer bars inside each setup bar)

For a 5-minute bar built from five 1-minute bars:

| Feature | Definition |
|---|---|
| `high_first` | the 1-minute bar that set the high comes before the one that set the low |
| `low_first` | the reverse |
| `same_minute` | both extremes set in the same 1-minute bar (unresolvable at this resolution) |
| `open_is_high` / `open_is_low` | open within `tol` ticks of the extreme |
| `first_minute_dir` | direction of the first 1-minute bar |

The owner's stated intuition, restated as a testable hypothesis:

> H1: When a 5-minute bar goes to its high first, the bar is more likely than
> the base rate to close below its open, because the low is rarely the open.

Measured as `P(close < open | high_first)` vs `P(close < open)` and
`P(open_is_low)` vs `P(open_is_low | high_first)`.

## 7. Sequence keys

Setups are keyed by the concatenated labels of the last `k` bars, oldest first.

- `range` key: e.g. `II` = two inside bars in a row.
- `range_dir` key: e.g. `I+I-` = inside bar closing up, then inside bar closing down.
- `range_close` key: e.g. `IW UA` = inside bar closing within, then up-range bar closing above.

`k = 1, 2, 3` are reported by default. Each key's row shows the count and the
rate of each next-bar outcome next to the unconditional base rate.

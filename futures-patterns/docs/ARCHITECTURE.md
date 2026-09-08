# Architecture: intrabar path states and short-horizon triggers

Status: **discussion draft**, 2026-09-07. Nothing in this document is built
yet beyond the 1-minute prototype in `analysis/`. The purpose is to pin down
the owner's logic precisely enough that we can argue about it, then decide
what to build.

## 1. The owner's logic, restated

1. A bar is not four numbers. It is a **path**: open, then a sequence of visits
   to levels, ending at the close. "Open, up to the high, down to the low,
   close in the middle" and "open, down to the low, up to the high, back
   down, then close on the high" are different bars even when their OHLC are
   identical.
2. That path, observed tick by tick, is the **state** we know at the moment
   the bar closes. It is the whole input. Nothing older than a few bars.
3. We do **not** predict direction. We wait for a **trigger**: price crossing
   the bar's high or the bar's low. The state tells us what to do *when* that
   happens: go with it, fade it, or stand aside.
4. The trade is tiny and short: 5 to 10 ticks, 10 to 60 seconds. So the
   question is not "where is the market going" but "**given state S and
   trigger T, what is the distribution of the next N ticks / seconds**", and
   from that distribution, the target and stop that give positive expectancy
   after costs.

Everything below is the machinery to answer question 4 honestly.

## 2. Layers

```
ticks  ->  bar builder (keeps the tick path per bar)
       ->  path features (order of extremes, swings, timing, touches, close position)
       ->  state alphabet (a small set of named states, computable in real time)
       ->  trigger detection on the following ticks (cross high / cross low)
       ->  outcome measurement (MFE / MAE, target-before-stop, by horizon)
       ->  conditional tables: state x trigger x reaction -> P(win), expectancy after costs, n
       ->  null model comparison, in-sample / out-of-sample
       ->  (later) NinjaScript indicator computing the SAME state on the live chart
```

Two hard rules that shape every layer:

- **Causality.** A state may only use ticks up to the bar close (or, for
  intrabar triggers, up to the trigger tick). Outcomes only use later ticks.
- **Live-computability.** Every feature must be computable incrementally from
  a tick stream with O(1) memory per bar, because the end product is a
  NinjaTrader indicator running on a forming bar. If a feature needs the
  whole bar in hindsight (e.g. "position of the high as a fraction of the
  final range"), it is only valid at bar close, and the trigger it feeds must
  fire after that close.

## 3. Data layer

Tick-level analysis needs tick data. 1-minute OHLC cannot tell "high first"
from "low first", let alone swings or timing. Requirements:

| Need | Why |
|---|---|
| Trade prints with millisecond timestamps, price, size | build the path, measure time-to-extreme, hold times in seconds |
| Bid/ask at each print (or at least at trigger time) | a stop order fills at the ask/bid, not at "the high"; a 5-tick target with a 1-tick spread is a 20% haircut |
| Contract identity | roll handling as in the 1-minute pipeline |
| At least one year, ideally several | a state x trigger x reaction cell needs hundreds of events; 390 RTH minutes/day x 250 days = ~100k bars/year, spread over ~20 states x 2 triggers x 2 reactions |

Sources (details in `DATA_SOURCES.md`):

- **NinjaTrader 8 + Rithmic**: tick export, roughly the last 366 days. Enough
  to start. Export Period **Tick**, Data type **Last**; Bid and Ask series can
  be exported separately and joined by timestamp.
- **NinjaTrader Market Replay** downloads carry last/bid/ask together.
- **Databento GLBX.MDP3** `trades` or `mbp-1` schema for multi-year history
  with the book's top level. Paid, quoted before purchase.

Storage: one file per instrument per day (`data/ticks/ES/2026-03-02.csv` or
parquet once pandas is added). Bars are derived, never stored as the source of
truth.

## 4. Path features (per bar)

Computed from the bar's ticks. `R` = final range in ticks. All positions are
in ticks from the bar's low, so bars of different size are comparable.

**Extremes**
- `order`: `HL` (high before low), `LH`, or `same` (both on the same tick, i.e. `R = 0`)
- `t_high`, `t_low`: seconds from bar open to first touch of the high / low
- `touches_high`, `touches_low`: number of separate visits to the extreme (a
  visit ends when price moves away by >= `r` ticks)
- `open_pos`, `close_pos`: position of open and close within `[0, R]`

**Swings**
- Zigzag with reversal threshold `r` ticks (proposal: `r = 2` for ES 1-minute;
  to be tuned). The bar becomes a sequence of turning points
  `(t_i, p_i)`. `n_swings` = number of turning points.
- `swing_string`: turning-point positions quantised into fifths of `R`,
  e.g. `O2 H4 L0 C2` for "open mid, high, low, close mid" or
  `O1 L0 H4 3 C4` for the owner's second example (down to low, up to high,
  pull back, close on the high).

**Time and volume**
- `t_high / 60`, `t_low / 60`: when in the minute the extremes happened
  (a high in the first 5 seconds is a different animal from one at second 55)
- `vol_at_high`, `vol_at_low`: share of the bar's volume traded within 1 tick
  of each extreme (proxy for absorption vs rejection)
- `ticks_n`: number of prints (activity)

## 5. State alphabet (v0 proposal, for discussion)

The full feature vector fragments the sample. The first alphabet should be
small, about 16 to 24 states, and human-readable so the owner can look at a
chart and name the state by eye. Proposal, as a decision tree at bar close:

1. `order` in {HL, LH}, and
2. `close_pos` bucket in {top (>= 0.8), mid, bottom (<= 0.2)}, and
3. `n_swings` bucket in {2 (one round trip), 3, 4+}, and
4. `first extreme timing` in {early (< 15 s), late}

That is 2 x 3 x 3 x 2 = 36 cells; several will be near-empty and merge. The
owner's two examples map to:

- "opens, goes to the high, then the low, closes in the middle" = `HL / mid / 2 / *`
- "opens, low, high, back down, closes on the high" = `LH / top / 4+ / *`

Degenerate bars (`R <= 2` ticks) get their own state `flat` and are excluded
from breakout statistics.

Open question for the owner: is the **prior bar's** relationship (inside /
outside / cross, from the 1-minute prototype) part of the state, or is this a
strictly 1-bar analysis at first? Proposal: strictly 1-bar first, add the
prior-bar label as a second key only for states that show something.

## 6. Triggers and reactions

At the close of bar `S` with known state, two levels are armed:
`H = S.high + 1 tick` and `L = S.low - 1 tick`. The trigger is the first tick
of the next bar(s) at or beyond either level. Both are always measured; the
state decides which we would act on.

| Reaction | On cross of H | On cross of L |
|---|---|---|
| **follow** | buy at H (stop) | sell at L (stop) |
| **fade** | sell at H | buy at L |

Parameters to grid over:
- trigger validity window: next bar only (default), or up to `k` bars / `T` seconds
- target `t` and stop `s` in ticks: `(2,2) (3,3) (4,4) (5,5) (5,10) (10,5) (3,6) (6,3)`
- time cap: 10 s, 15 s, 30 s, 60 s, end of bar; at the cap, exit at market

## 7. Outcomes and the risk-reward table

For each event (state, trigger, reaction, parameters), from the ticks after
the trigger:

- `filled_at`: actual fill price given the tick sequence and the bid/ask at
  that moment (a stop crossing on a 3-tick jump fills 3 ticks worse)
- `mfe`, `mae` at each horizon in seconds and in ticks
- `first_hit`: target, stop, or time cap
- `pnl_ticks` after **costs**: commission (`instruments.py`), entry slippage
  from the fill model, exit slippage 1 tick when the exit is at market

Reported per cell:

| n | P(target first) | mean pnl after costs | median | P(pnl > 0) | avg seconds in trade | max adverse run |

The cell is worth discussing only when `n >= 300` and the mean is positive in
both the in-sample and out-of-sample halves. A "risk-reward ratio" is then
read straight off the table: for the chosen `(t, s)`, `P(target first)`
against `s / t`.

## 8. Null model at tick level

The 1-minute prototype already showed how much structure pure noise produces
(`FINDINGS.md`). At tick level the same trap exists: a state defined by "went
to the high late and closed on it" mechanically raises P(cross H next bar).
The tick null model should be a **bootstrapped tick path**: shuffle the signed
tick moves within each day (keeps the day's volatility, kills all sequence
information) and rerun the whole pipeline. Any cell that looks as good on the
shuffled data as on the real data is structure, not edge.

## 9. Where costs bite

For ES with a 1-tick spread, a follow-breakout at a stop pays roughly:
commission 0.3 tick + entry slippage 1 to 2 ticks + exit at market 1 tick.
That is 2.3 to 3.3 ticks against a 5-tick target. The table will show most
`(5,5)` cells negative on that basis even at 55% hit rates. This is the
central reason the owner's framing (state-conditional, short hold) has to
show a **large** lift, not a small one, and why limit exits at the target
(no spread paid, but a fill is not guaranteed) must be modelled as a variant.

## 10. What the NinjaScript side will need (later)

- Indicator on a 1-minute chart with an added 1-tick data series
  (`AddDataSeries(BarsPeriodType.Tick, 1)`), computing the path features in
  `OnBarUpdate` for the tick series and the state at the primary bar's close.
- Paints the state label under each closed bar and draws the armed `H` / `L`
  levels; fires an alert when a trigger crosses, with the cell's stats in
  the alert text.
- Reads the state definitions and cell statistics from a file exported by the
  research code, so research and chart never disagree.
- No order placement.

## 11. Proposed build order, once we agree

1. Tick loader + bar builder that retains ticks per bar (Python, add pandas).
2. Path features and the v0 state alphabet, with a unit test per state on
   hand-made tick sequences.
3. Trigger / outcome engine with the fill model and cost model.
4. Tables, null model, in/out-of-sample.
5. One real dataset: ES RTH, last 12 months of Rithmic ticks via NinjaTrader.
6. Read the tables together and decide which states, if any, go to the chart.

## 12. Questions for discussion

- Is the state strictly the last bar, or last bar plus its relationship to the
  previous one?
- Is the trigger only valid on the very next bar?
- Follow, fade, or both, decided per state by the data? (Proposal: measure
  both always, act on whichever the table supports.)
- Reversal threshold `r` for swings: 2 ticks on ES 1-minute is a guess.
- Do we accept the ~1-year Rithmic tick history for phase 1, or buy deeper
  tick history up front?
- Time bars are clock-arbitrary. Once the pipeline exists, the same states on
  range bars or tick bars are a cheap experiment. Interest?

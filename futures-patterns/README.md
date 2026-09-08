# Trading Analytics

Research workspace for discretionary futures day trading. The goal is to find
**bar-to-bar relationships on intraday candlesticks (1-minute and 5-minute
OHLC) that have measurable predictive value for the very next bar**, then
surface those setups on the chart in NinjaTrader or TradeStation.

This is **not** an auto-trading system. Nothing here places orders. The project
is: define patterns precisely, measure them on real data, keep the ones that
survive honest testing, then build chart markers for them.

Instruments in scope (to be prioritised, see `docs/QUESTIONS.md`): E-mini /
Micro S&P (ES, MES), Nasdaq (NQ), Gold (GC), Crude (CL), Bitcoin futures
(BTC, MBT), Coffee (KC), and anything else that trades on a liquid exchange.

## Layout

| Path | What it is |
|---|---|
| `CLAUDE.md` | Project brief for Claude sessions: role, principles, definitions |
| `docs/QUESTIONS.md` | Open questions the owner needs to answer before phase 1 |
| `docs/BAR_TAXONOMY.md` | Precise, tick-aware definitions of every bar relationship we test |
| `docs/RESEARCH_PLAN.md` | Hypotheses, method, what counts as a "real" edge, phases |
| `docs/DATA_SOURCES.md` | Where to get historical and live futures data, with trade-offs |
| `docs/ARCHITECTURE.md` | The intrabar tick-path design: states, triggers, reactions, outcomes, costs. Discussion draft |
| `docs/EXPORT_GUIDE.md` | Step-by-step: export ES 1-minute history from NinjaTrader 8 (Rithmic) and TradeStation |
| `docs/FINDINGS.md` | Results log, starting with the random-walk null baseline |
| `platforms/` | Platform-side code: TradeStation export indicator now, NinjaScript markers later |
| `docs/DECISIONS.md` | Running log of decisions made, so nothing is re-argued |
| `analysis/` | Pure-Python library: CSV loading, bar classification, conditional tables, intrabar path stats |
| `scripts/` | Command-line entry points: synthetic data, contract merge, pattern tables, intrabar path, `run_es.sh` |
| `data/` | Local market data (git-ignored). `data/README.md` describes the CSV format |
| `results/` | Generated tables (git-ignored) |
| `tests/` | Unit tests for the classifier and the outcome logic |

## Quick start

No dependencies beyond Python 3.10+.

```bash
cd futures-patterns

# 1. Generate a synthetic random-walk dataset so the tooling can be exercised
#    before real data arrives. Random data is also our NULL MODEL: a pattern is
#    only interesting if it beats what a random walk produces.
python3 scripts/make_synthetic.py --days 60 --out data/synthetic_1m.csv

# 2. Conditional probability tables on 5-minute bars, keyed by the last 2 bars
python3 scripts/run_patterns.py data/synthetic_1m.csv --resample 5 --lookback 2 --tick 0.25

# 3. Intrabar path analysis: within each 5-minute bar, did price visit the high
#    or the low first, and what did that imply for the close?
python3 scripts/run_intrabar.py data/synthetic_1m.csv --minutes 5 --tick 0.25

# 4. Tests
python3 -m unittest discover -s tests -v
```

## Real data: ES from NinjaTrader 8 + Rithmic

Follow `docs/EXPORT_GUIDE.md`. In short:

```bash
# merge per-contract NinjaTrader exports into one Eastern-time, open-stamped series
python3 scripts/merge_contracts.py "data/nt/ES 12-25.Last.txt" "data/nt/ES 03-26.Last.txt" \
    --ts-is-close --tz-from UTC --drop-roll-days --out data/ES_1m.csv
# full ES regular-hours battery, saved under results/
bash scripts/run_es.sh data/ES_1m.csv
```

## Phases

1. **Definitions and tooling** (this commit): taxonomy, null model, analysis CLI.
2. **Data**: export ES 1-minute history from NinjaTrader 8 (Rithmic), cross-check with TradeStation. Tooling for this is in place; the export itself runs on the owner's Windows machine.
3. **Measurement**: run the tables per instrument, per session, per time-of-day.
   Keep candidates that beat the null with adequate sample size in-sample AND
   out-of-sample.
4. **Trigger economics**: for surviving setups, simulate the stop-entry trigger
   and the exit rules with realistic slippage and commissions.
5. **Chart markers**: port the winning definitions to NinjaScript (NinjaTrader 8)
   or EasyLanguage (TradeStation) so setups are painted on live candles.

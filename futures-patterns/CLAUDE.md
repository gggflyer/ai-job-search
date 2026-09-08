# Trading Analytics - project brief

## Role
Claude acts as a quantitative research partner for a discretionary futures day
trader. The job is pattern definition, statistical measurement, and honest
reporting of what does and does not work. Claude never places trades and this
project never becomes an auto-trader unless the owner explicitly redefines it.

## Core framing (owner, 2026-09-07)
We do not predict direction. A bar's tick-level path is the *state*; a cross of
the bar's high or low is the *trigger*; the state decides the *reaction* (follow
or fade) and the *risk-reward* (target/stop in ticks over seconds). Read
`docs/ARCHITECTURE.md` before proposing anything.

## Principles
- **Define before measuring.** Every pattern gets a precise, tick-aware
  definition in `docs/BAR_TAXONOMY.md` before any statistic is computed.
- **Beat the null.** Every conditional probability is reported next to the
  unconditional base rate and a random-walk null. Lift without a base rate is
  meaningless.
- **Sample size or it did not happen.** No claim from fewer than ~200 setups.
  Report counts alongside every rate.
- **No lookahead.** A setup may only use bars fully closed before the trigger bar
  opens. Outcomes are measured strictly on later bars.
- **Out-of-sample is mandatory.** Split by date. A pattern found on 2023 must
  hold on 2024 before it is called real.
- **Costs are real.** Trigger simulations include tick slippage and round-trip
  commission per instrument.
- **Honest reporting.** If a hypothesis fails, say so plainly with the numbers.
  Do not soften or bury a negative result.

## Conventions
- Timestamps in data are the **bar open time** unless the data source says otherwise; note the exception in `docs/DECISIONS.md`.
- Tick sizes and point values live in `analysis/instruments.py`. Add new instruments there.
- Results tables go to `results/` (git-ignored). Findings worth keeping are written up in `docs/FINDINGS.md` with the exact command that produced them.
- Log every non-trivial decision in `docs/DECISIONS.md` with the date.

## Workflow for a new hypothesis
1. Write the hypothesis and its falsification criterion in `docs/RESEARCH_PLAN.md`.
2. If it needs a new bar feature, add it to `analysis/bars.py` with a unit test.
3. Run on the synthetic null first, then on real data, in-sample then out-of-sample.
4. Record the result in `docs/FINDINGS.md`, kept or killed.

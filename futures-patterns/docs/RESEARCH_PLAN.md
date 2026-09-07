# Research plan

## Hypotheses (initial set, to be extended by the owner)

| ID | Hypothesis | Falsified if |
|---|---|---|
| H1 | After a 5-min bar goes high-first, P(close < open) exceeds the base rate | lift < 3 points or not significant out-of-sample |
| H2 | After two consecutive inside bars, P(next bar closes beyond the setup range) exceeds the base rate | same |
| H3 | A bar that closes on its own high raises P(next bar crosses that high) | same |
| H4 | A bar that closes on its own high raises P(next bar closes above that high) (cross AND hold) | same |
| H5 | Long trigger (stop one tick above high) after H3/H4 setups has positive expectancy after costs on a single-bar hold | mean pnl_ticks after costs <= 0 |
| H6 | Time of day changes all of the above materially (open, lunch, close) | no bucket differs by more than sampling noise |

The random-walk synthetic data is the null for every hypothesis. Several of
these outcomes have non-obvious base rates even on a random walk (for example,
the open being the bar's extreme is common, not rare, when a bar is built from
only five sub-bars). The synthetic run tells us what "nothing going on" looks
like before real data is read.

## Method

1. Load 1-minute bars. Resample to 5-minute. Drop bars outside the chosen
   session. Drop roll days.
2. Label every bar (taxonomy sections 1-3). Compute next-bar outcomes (section 4)
   and trigger results (section 5).
3. Build conditional tables keyed by the last k bars, k = 1..3, for each key
   type. Report count, rate per outcome, base rate, lift, and a z-score.
4. Split by date: first 70% in-sample, last 30% out-of-sample. A candidate
   must show the same sign of lift, with adequate count, in both.
5. Bucket by time of day (30-minute buckets) for surviving candidates.
6. Trigger economics for survivors: single-bar close exit, then a grid of
   target/stop pairs in ticks, with slippage and commission.
7. Write up kept and killed hypotheses in `docs/FINDINGS.md`.

## Statistical guardrails

- Minimum 200 setups per cell before a rate is quoted. Below that the row is
  printed with a `low-n` flag.
- z-score is a rough screen, not a verdict. With dozens of keys and outcomes,
  some will pass by chance. Out-of-sample confirmation is the real filter.
- Next-bar outcomes on consecutive bars are not independent when setups overlap
  (two inside bars is a subset of one inside bar). Compare like with like.
- Report everything in ticks so instruments are comparable.

## Phases and what each needs

| Phase | Deliverable | Needs from owner |
|---|---|---|
| 1 | Tooling and taxonomy (done in this commit) | answers to `QUESTIONS.md` B and C |
| 2 | Real 1-minute data for the first instrument | answers to D and E |
| 3 | Tables per instrument, per session, per time bucket | nothing new |
| 4 | Trigger economics on survivors | cost assumptions confirmed |
| 5 | NinjaScript or EasyLanguage marker indicator | answer to E.22 |

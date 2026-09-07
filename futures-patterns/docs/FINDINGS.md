# Findings

Each entry: date, instrument, session, date range, exact command, the rows that
matter, in-sample vs out-of-sample, verdict KEPT or KILLED.

## 2026-09-07 - Synthetic null baseline (random walk, 120 sessions, 5-min bars, tick 0.25)

Commands:
```
python3 scripts/make_synthetic.py --days 120 --out data/synthetic_1m.csv
python3 scripts/run_patterns.py data/synthetic_1m.csv --symbol ES --resample 5 --lookback 2 --oos 0.3
python3 scripts/run_patterns.py data/synthetic_1m.csv --symbol ES --resample 5 --lookback 1 --key closepos
python3 scripts/run_intrabar.py data/synthetic_1m.csv --symbol ES --minutes 5
```

Base rates on pure noise (ALL row, n = 9239):

| outcome on next bar | rate |
|---|---|
| crosses setup high | 47.7% |
| closes above setup high | 26.6% |
| crosses setup low | 46.0% |
| closes below setup low | 26.0% |
| inside | 13.8% |
| outside | 7.5% |

Intrabar: high-first 48.5%, low-first 49.6%, open is the bar's high 12.3%, open is
the bar's low 12.8%, close is the high 12.7%.

### Three lessons from the null, before touching real data

1. **Structural hit rates are not edge.** On random data, a bar that closes on
   its own high (`UH` key) is followed by a bar that crosses that high 88% of
   the time, z = +21. That is mechanics, not prediction: the next bar opens at
   the high, so any single uptick "crosses" it. The same row shows that
   *closing above* that high is only 52%, and the long trigger wins 52% of the
   time with a mean near zero after costs. Any real-data claim about "closes on
   the high" has to beat 88% / 52%, not 48% / 27%.
2. **Part of H1 is a tautology.** On noise, P(close < open | high first) is
   87%, and P(open is low | high first) is exactly 0% by definition (if the open
   were the low, the low was set first). The owner's intuition is correct as a
   description of a closed bar. The tradable question is different: *what is
   known while the bar is still forming?* First-minute direction predicts the
   5-minute close at 64% on noise (also structural: the first minute is part of
   the bar). Real data must beat that.
3. **The trigger simulation has a fill-price bias.** Long trigger means came out
   slightly positive on random data (+0.8 ticks on `UH`). Cause: the sim fills
   at exactly the stop price, but when a multi-tick move jumps through the stop
   the real fill is worse. That is slippage. `run_patterns.py` now adds
   `--slip` (default 1 tick) to costs; treat anything under ~1 tick of mean
   edge as zero until the 1-minute path sim can model the fill properly.

Two-bar keys (`I I`, `U U`, ...) show z-scores of 5-7 on noise for cross_high
after `U U` and cross_low after `D D`. That is not momentum; a bar whose high is
above the prior high has a higher open for the next bar to start from, and the
cross threshold is closer. Lift in *close_above_high* is the more honest column,
and it is +3 to +4 z on noise too, so the real-data threshold for a 2-bar
sequence is "materially above what the same key shows on the synthetic run",
not "above the ALL row".

Verdict: no hypothesis tested yet. Baseline recorded.

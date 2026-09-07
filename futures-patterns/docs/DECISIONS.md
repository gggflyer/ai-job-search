# Decision log

| Date | Decision | Why |
|---|---|---|
| 2026-09-07 | Analysis library in pure Python 3 standard library, no pandas | Runs on any machine including the owner's server with no installs. Pandas can be added later for speed if datasets get large. |
| 2026-09-07 | Ties count as inside, a cross requires at least one tick beyond | Matches how a stop order actually fills. Owner may override (Q7). |
| 2026-09-07 | Random-walk synthetic data is the standing null model | Several base rates are non-intuitive; measuring them on noise first prevents false discoveries. |
| 2026-09-07 | Project lives in a folder of `ai-job-search` on branch `claude/futures-pattern-recognition-500t74` until the owner names a dedicated repo | Session constraint; see Q21. |
| 2026-09-07 | Timestamps assumed to be bar open time | Common for NinjaTrader exports is bar CLOSE time; confirm with Q5 and flip `--ts-is-close` if so. |

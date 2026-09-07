# Decision log

| Date | Decision | Why |
|---|---|---|
| 2026-09-07 | Analysis library in pure Python 3 standard library, no pandas | Runs on any machine including the owner's server with no installs. Pandas can be added later for speed if datasets get large. |
| 2026-09-07 | Ties count as inside, a cross requires at least one tick beyond | Matches how a stop order actually fills. Owner may override (Q7). |
| 2026-09-07 | Random-walk synthetic data is the standing null model | Several base rates are non-intuitive; measuring them on noise first prevents false discoveries. |
| 2026-09-07 | Project lives in a folder of `ai-job-search` on branch `claude/futures-pattern-recognition-500t74` until the owner names a dedicated repo | Session constraint; see Q21. |
| 2026-09-07 | Timestamps assumed to be bar open time | Common for NinjaTrader exports is bar CLOSE time; confirm with Q5 and flip `--ts-is-close` if so. |
| 2026-09-07 | First instrument ES, regular hours 09:30-16:15 ET (CME RTH, matches both platforms' RTH templates) | Owner's choice. 16:00-16:15 can be excluded later with `--session 09:30-16:00`. |
| 2026-09-07 | Primary data source: NinjaTrader 8 + Rithmic export, per contract, merged by daily volume with roll days dropped. TradeStation export as a cross-check | Owner runs both. Rithmic serves minute bars to 2006 through NinjaTrader. |
| 2026-09-07 | NinjaTrader exports are UTC and bar-close stamped; loader converts with `--ts-is-close --tz-from UTC` | Per NinjaTrader import/export docs. Verify on first real file: the RTH open bar must land at 09:30. |
| 2026-09-07 | Internal timestamp convention: bar OPEN time, America/New_York, naive | Everything downstream assumes this. |
| 2026-09-07 | Continuous series is unadjusted, front contract by daily volume | Tick-level next-bar statistics do not need back-adjustment; roll days are removed instead. |

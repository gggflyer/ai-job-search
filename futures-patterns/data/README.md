# Data directory (git-ignored except this file and `samples/`)

Put one CSV per instrument and timeframe here, e.g. `ES_1m.csv`, `GC_1m.csv`.

## Accepted formats

**Preferred**, header row, comma separated, timestamp = bar OPEN time:

```
timestamp,open,high,low,close,volume
2026-01-05 09:30:00,5920.25,5922.00,5919.50,5921.75,3456
```

**Also accepted:**
- Separate `date` and `time` columns.
- NinjaTrader export, no header, semicolon separated: `20260105 093000;5920.25;5922;5919.5;5921.75;3456`.
  NinjaTrader stamps bars with their CLOSE time. Pass `--ts-is-close` to the
  scripts so the loader shifts them to open time before resampling.

## Naming

`<SYMBOL>_<tf>.csv` with `tf` in `1m`, `5m`. Continuous front-month,
unadjusted, roll days dropped.

## Timezone

Internal standard is **America/New_York, bar open time**. NinjaTrader exports are
UTC and close-stamped: convert with `--ts-is-close --tz-from UTC` (the merge
script and the analysis scripts both accept these). TradeStation exports are
exchange time, close-stamped: `--ts-is-close` only. On Windows, `pip install
tzdata` if Python cannot find the zone.

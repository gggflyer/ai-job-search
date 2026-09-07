# Getting ES 1-minute history out of your platforms

Owner setup: **NinjaTrader 8 + Rithmic** (primary) and **TradeStation**
(cross-check). Both are free. Do NinjaTrader first; Rithmic serves minute bars
back to 2006 through NinjaTrader, tick data only ~1 year.

## A. NinjaTrader 8 with Rithmic (primary)

NinjaTrader stores data per contract, so the export is one file per contract
and `scripts/merge_contracts.py` stitches them into a continuous series.

1. **Download the history.** Open a 1-minute chart of each ES contract you
   want (`ES 12-25`, `ES 03-26`, `ES 06-26`, `ES 09-26`, ...) with
   *Days to load* set large enough to cover the contract's active life (about
   120 days each; set 400 to be safe). Loading the chart pulls the minute
   bars from Rithmic into the local database. Repeat for every contract, going
   back as far as you want. Quarterly contracts, so 4 per year.
2. **Export.** Control Center > Tools > Historical Data. On the *Export* tab
   pick the instrument, Data type **Last**, Period **Minute**, the date range,
   and export. One `.txt` per contract, e.g. `ES 03-26.Last.txt`. Format is
   `yyyyMMdd HHmmss;open;high;low;close;volume`, **UTC**, **bar-close
   stamped**. Our loader reads this format as-is.
3. **Merge and convert** (run on the machine that has Python; the files are
   plain text so they can be copied anywhere):
   ```bash
   python3 scripts/merge_contracts.py "data/nt/ES 12-25.Last.txt" "data/nt/ES 03-26.Last.txt" "data/nt/ES 06-26.Last.txt" \
       --ts-is-close --tz-from UTC --tz-to America/New_York --drop-roll-days --out data/ES_1m.csv
   ```
   The merged file is open-time stamped, Eastern time, one contract per day
   chosen by volume, roll days removed.
4. **Sanity check** before trusting it:
   ```bash
   head -3 data/ES_1m.csv
   grep " 09:30:00" data/ES_1m.csv | head -3      # the RTH open bar should exist for every day
   grep " 16:15:00" data/ES_1m.csv | head -3      # and this should be the first bar AFTER RTH (i.e. not present when filtered)
   ```
   If the first RTH bar shows up at 08:30 or 10:30 the timezone flag is wrong;
   if it shows at 09:31 the close-stamp shift was not applied.
5. **Analyse:**
   ```bash
   bash scripts/run_es.sh data/ES_1m.csv
   ```

## B. TradeStation (cross-check and deeper continuous history)

1. Open `platforms/tradestation/ExportBars.txt`, create a new indicator in
   the EasyLanguage editor with that code, verify it.
2. Chart `@ES`, 1 minute, session *Regular*, Format Symbol > Range set to 10
   years. Apply the indicator. Wait; FileAppend writes one line at a time.
3. Analyse with `--ts-is-close` and no timezone flag (TradeStation stamps in
   exchange time):
   ```bash
   python3 scripts/run_patterns.py data/ES_1m_ts.csv --symbol ES --session 09:30-16:15 --ts-is-close --resample 5 --lookback 2 --oos 0.3
   ```
4. Compare the ALL row against the NinjaTrader run. Base rates should agree to
   within a point; if not, one export has a session or timestamp problem.

## Regular trading hours

CME's ES regular session is **09:30-16:15 ET**, which is what NinjaTrader's
"CME US Index Futures RTH" template and TradeStation's "Regular" session use.
The scripts default to that. The 16:00-16:15 stretch after the cash close
behaves differently and can be excluded with `--session 09:30-16:00` when we
get to time-of-day buckets.

Sources: [NinjaTrader export](https://ninjatrader.com/support/helpGuides/nt8/exporting.htm),
[NinjaTrader import formats and UTC note](https://ninjatrader.com/support/helpguides/nt8/importing.htm),
[Rithmic history depth in NinjaTrader](https://forum.ninjatrader.com/forum/ninjatrader-8/platform-technical-support-aa/1159630-rithmic-historical-data),
[TradeStation extended historical data](https://help.tradestation.com/10_00/eng/tradestationhelp/data_network/extended_historical_data.htm).

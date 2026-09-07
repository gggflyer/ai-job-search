# Data sources

Two separate needs: **historical 1-minute bars** for research (bulk, once) and a
**live feed** later for painting setups on the chart (the platform handles that).
Research needs only the first. Prices checked September 2026; re-verify before
buying.

## Tier 0: free, already paid for by an account you may hold

| Source | How | Depth | Notes |
|---|---|---|---|
| **TradeStation** | Platform stores futures history; export via an EasyLanguage print-to-file indicator or a helper script | Minute bars ~10 years for futures, tick ~6 months | Best free depth. Exports in exchange time. Set session to Regular when exporting. [Extended Historical Data](https://help.tradestation.com/10_00/eng/tradestationhelp/data_network/extended_historical_data.htm) |
| **NinjaTrader 8** | Control Center > Tools > Historical Data > Export, writes `.txt` in `yyyyMMdd HHmmss;O;H;L;C;V` format | Depends on the connected feed (Kinetick, Rithmic, CQG, NinjaTrader's own) | Our loader reads that format directly. Timestamps are the PC's local time and are bar-close stamped by default (use `--ts-is-close`). [Exporting](https://ninjatrader-live.ninjatrader.com/support/helpguides/nt8/exporting.htm) |
| **Interactive Brokers** | TWS API historical bar requests | Years of 1-min for liquid contracts, paced requests | Needs coding; futures data subscription required |

## Tier 1: buy history once

| Source | Coverage | Cost | Notes |
|---|---|---|---|
| **Databento** (`GLBX.MDP3`) | All CME/CBOT/NYMEX/COMEX, 1-min OHLCV, from 2010s | Usage-based, quote shown before any query; Standard plan $179/mo also exists | Cleanest, API-first, exact dollar cost known up front. [GLBX.MDP3](https://databento.com/datasets/GLBX.MDP3), [pricing](https://databento.com/pricing), [CME pricing plans](https://databento.com/blog/introducing-new-cme-pricing-plans) |
| **Databento** (`IFUS.IMPACT`) | ICE Futures US incl. Coffee KC, from Dec 2018 | From $10/GB usage-based | Coffee is ICE, not CME, so it needs this second dataset. [KC](https://databento.com/catalog/ifus/IFUS.IMPACT/futures/KC) |
| **FirstRate Data** | ~130 most active contracts, 1-min back to 2007-2008, continuous and individual contracts | Per-bundle one-off, updates ~$60-100/mo optional | Flat files, no API needed. [ES](https://firstratedata.com/i/futures/ES), [GC](https://firstratedata.com/i/futures/GC), [bundles](https://firstratedata.com/bundle/all) |
| Kibot, PortaraCQG, TickData | Similar flat-file vendors | Varies | Fallbacks if the above do not fit |

## Tier 2: free proxies for pipeline dry-runs

| Source | Why |
|---|---|
| **Crypto exchange public APIs** (Binance, Coinbase, Kraken, Bybit) | Free 1-minute klines back years, no account, 24/7. Not futures, but a perfect way to test the whole pipeline end to end before spending money. BTC spot behaviour is also directly relevant to CME BTC/MBT. |

## Recommendation

1. **Phase 2 first source (decided):** NinjaTrader 8 with the Rithmic feed,
   which serves minute bars back to 2006. Export per contract and merge with
   `scripts/merge_contracts.py`. TradeStation's `@ES` continuous export is the
   cross-check. Steps in `EXPORT_GUIDE.md`. Zero cost.
2. If depth or cleanliness is a problem, **Databento GLBX.MDP3** for CME
   products and **IFUS.IMPACT** for coffee. Ask for the quote before pulling.
3. Live feeds are the platform's job (NinjaTrader or TradeStation connect to
   their broker feed). The research code never needs a live feed.

## Format we standardise on

See `data/README.md`. One CSV per instrument per timeframe, open-time
stamped, exchange time, columns `timestamp,open,high,low,close,volume`.

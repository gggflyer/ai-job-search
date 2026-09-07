# Open questions for the owner

Answer these in any order. Each one changes what gets built next. Defaults in
*italics* are what Claude will assume if there is no answer.

## A. Instruments and timeframes
1. **Priority order of instruments.** Which one first? *Default: ES (or MES),
   then GC, CL, NQ, BTC, KC.* Each instrument gets its own tables; behaviour
   differs a lot between the index and the physicals.
2. **Full-size or micro?** Same price series, different tick value and
   commission. Only matters for the cost model. *Default: micro for cost, full
   size for tick size.*
3. **Primary timeframe.** 5-minute for setups with 1-minute underneath for
   intrabar path analysis? Or also 1-minute setups? *Default: 5-min setups,
   1-min for path.*
4. **Session.** Regular trading hours only (e.g. ES 09:30-16:00 ET), or the full
   Globex session? Overnight bars behave differently and will pollute daytime
   statistics if mixed. *Default: RTH only, with a separate overnight table.*
5. **Timezone of your platform exports.** NinjaTrader exports in the PC's local
   time by default; TradeStation exports in exchange time. Which is it on your
   machine?

## B. Pattern definitions (see `docs/BAR_TAXONOMY.md` for the proposed set)
6. **"Closes on the high"**: do you mean the bar closes at *its own* high, or
   at/through the *previous bar's* high? Both are defined and measured; which
   one is the trigger you have in mind?
7. **Ties.** If a bar's high exactly equals the prior high, is that "crossing"
   or "inside"? *Default: a tie is NOT a cross; a cross needs at least one tick
   beyond.*
8. **Tolerance.** "Closes on the high" within how many ticks? *Default: 0 ticks
   (exact), with a 1-tick variant reported alongside.*
9. **How far back does a setup look?** Two inside bars is a 2-bar setup. Do
   you want 3- and 4-bar sequences too? *Default: 1, 2 and 3.* Longer sequences
   fragment the sample fast.
10. **Direction of the setup bars.** Does it matter whether the inside bars
    closed up or down? *Default: measured both ways (range-only key and
    range-plus-direction key).*

## C. Trigger and exit mechanics
11. **Entry.** Buy-stop one tick above the setup bar's high, filled when the
    next bar trades through it? Any other entry (e.g. on close of the breakout
    bar)? *Default: stop one tick beyond, filled if next bar's high/low touches
    it.*
12. **Hold period.** You described "making that jump just for that single
    bar". Is the exit the close of the trigger bar, or do you want target /
    stop in ticks, or hold N bars? *Default: report single-bar close exit AND
    a fixed target/stop grid.*
13. **If the trigger does not fire on the next bar**, is the setup dead, or
    does the stop stay live for N more bars? *Default: dead after one bar.*
14. **Slippage and commission** per instrument, round trip. *Default: 1 tick
    slippage on entry, 0 on a close exit, commission from
    `analysis/instruments.py` which you should correct.*

## D. Data
15. **Which platforms/brokers do you already have accounts with?** NinjaTrader
    (with which data feed: Kinetick, Rithmic, CQG, Tradovate?), TradeStation,
    Interactive Brokers, something else? Every one of these can export
    historical 1-minute bars for free, which is the cheapest phase-2 source.
16. **History depth.** 1 year? 5 years? *Default: whatever the platform gives
    for free, then decide whether to buy more.*
17. **Budget for data**, if any. Databento is pay-as-you-go and would let us
    pull years of 1-minute CME data for tens of dollars per instrument. Ballpark
    only, to be verified.
18. **Do you already have any data files or spreadsheets** from your own
    looking at this? Drop them in `data/` and describe the columns.
19. **Contract roll.** For tick-level next-bar statistics, unadjusted
    front-month data with a roll on volume is fine. Do you care about
    back-adjustment? *Default: no adjustment, drop the roll-day bars.*

## E. Environment
20. **"This server"**: what is it? OS, whether Python is installed, whether it
    runs 24/7, whether NinjaTrader/TradeStation are installed on it (both are
    Windows-only). Claude sessions like this one run in a temporary cloud
    container, so the folder lives in git and you clone it onto the server.
21. **GitHub repo.** This folder currently lives inside the `ai-job-search`
    repo on a feature branch. Should Claude create a new dedicated repo (name?)
    under your account and move it there?
22. **Target platform for chart markers.** NinjaTrader 8 (C# NinjaScript) or
    TradeStation (EasyLanguage)? Which one do you actually chart on daily?

## F. What counts as success
23. **Threshold for "worth trading".** Hit rate alone is misleading. Propose:
    positive expectancy after costs, at least 300 out-of-sample setups, and a
    lift over the base rate that is statistically distinguishable. Agree, or
    do you have your own bar?
24. **Anything you already believe strongly** about these patterns? Those go
    in first as named hypotheses so they get tested rather than assumed.

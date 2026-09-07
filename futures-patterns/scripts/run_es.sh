#!/usr/bin/env bash
# Canonical ES regular-hours run. Usage: bash scripts/run_es.sh data/ES_1m.csv
# Expects an open-time-stamped, Eastern-time CSV (see docs/EXPORT_GUIDE.md).
set -euo pipefail
CSV="${1:-data/ES_1m.csv}"
COMMON=(--symbol ES --session 09:30-16:15 --resample 5)
mkdir -p results
{
  echo "##### 1-bar keys, range only"
  python3 scripts/run_patterns.py "$CSV" "${COMMON[@]}" --lookback 1 --key range --oos 0.3
  echo; echo "##### 1-bar keys, closes on own high/low"
  python3 scripts/run_patterns.py "$CSV" "${COMMON[@]}" --lookback 1 --key closepos --oos 0.3
  echo; echo "##### 2-bar keys, range only (two inside bars = 'I I')"
  python3 scripts/run_patterns.py "$CSV" "${COMMON[@]}" --lookback 2 --key range --oos 0.3
  echo; echo "##### 2-bar keys, range + direction"
  python3 scripts/run_patterns.py "$CSV" "${COMMON[@]}" --lookback 2 --key range_dir --oos 0.3
  echo; echo "##### 3-bar keys, range only"
  python3 scripts/run_patterns.py "$CSV" "${COMMON[@]}" --lookback 3 --key range --oos 0.3 --min-n 100
  echo; echo "##### base rates by 30-minute time of day"
  python3 scripts/run_patterns.py "$CSV" "${COMMON[@]}" --lookback 1 --key range --by-time 30 --min-n 100000
  echo; echo "##### intrabar path"
  python3 scripts/run_intrabar.py "$CSV" --symbol ES --session 09:30-16:15 --minutes 5
} | tee "results/ES_$(date +%Y%m%d_%H%M).txt"

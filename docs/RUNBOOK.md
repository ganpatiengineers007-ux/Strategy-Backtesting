# RUNBOOK

1. `python bootstrap.py --all` (poora repo + tests + BUILD_ORDER.md + WIRING_MAP.json)
2. `cd strategy-validation-lab && ./scripts/setup_truemax.sh`
3. `python bootstrap.py --verify` (blueprint ke hisaab se saari files maujood?)

Demo output: `runs/<run_id>/report.html|json`, `trades.csv`, `run.json`.

## Abhi asli (chalta hua) vs baaki
Asli: data engine (csv), registry, backtest engine, risk, fills, validation (leakage, OOS, walk-forward,
overfitting, confidence), metrics, reporting, job queue, CLI, contracts, parity tests.
Baaki: parquet/broker source, PostgreSQL, FastAPI routes (health ke alawa), cross-validation, robustness,
regime analysis, optimization, frontend pages, Go/Rust/C++ ko Python se asli call karna.
Strategy logic: gamma_blast/three_pm_momentum ka logic placeholder hai - asli niyam aapko dene honge.

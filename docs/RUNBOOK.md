# RUNBOOK

1. `python scripts/bootstrap.py --all --root .` (naye repo me); update ke liye `--force` (README kabhi overwrite nahi hota)
2. `python -m pytest -q`
3. `python scripts/bootstrap.py --verify --root .`

Demo: `python -m cli.main demo` -> `runs/<run_id>/report.html|json`, `trades.csv`, `run.json`
Optimize: `python -m cli.main optimize --strategy three_pm_momentum --data data/samples/sample_5m.csv --grid '{"stop_pct":[0.3,0.5],"target_pct":[0.8,1.0]}'`
Sample data: `python -m cli.main make-sample`

API: `pip install fastapi uvicorn` -> `uvicorn --factory backend.app:create_app`
Env: API_KEY (set ho to X-API-Key zaroori), RUNS_ROOT, DATA_DIR, DATABASE_URL=sqlite:///path,
BACKGROUND_WORKER=1 (job thread me), RUN_ISOLATED=1 (job alag process me, limits ke saath)

## Abhi asli vs baaki
Asli: data (csv, corporate actions, storage, options checks), registry (compatibility, permissions, lifecycle gates),
backtest (execution model), risk, 8 validation checks, optimization (holdout), metrics, reporting, jobs (inline/background/isolated),
CLI, API (saare blueprint routes, POST /strategies chhodkar), SQLite repo, proto messages, frontend pages.
Baaki: parquet/broker source ka asli connection, PostgreSQL adapter, option backtest (option-chain data + niyam chahiye),
strategy create API, full sandbox (network/filesystem isolation), Go/Rust/C++ ko Python se asli call karna.
Strategy logic: gamma_blast/three_pm_momentum placeholder; bahari strategies (archive/) abhi jodi nahi gayi.

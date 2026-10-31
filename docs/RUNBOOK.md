# RUNBOOK

1. `python bootstrap.py --all --root .` (naye repo me); update ke liye `--force` (README kabhi overwrite nahi hota)
2. `./scripts/setup_truemax.sh` ya `python -m pytest -q`
3. `python bootstrap.py --verify --root .`

Demo: `python -m cli.main demo` -> `runs/<run_id>/report.html|json`, `trades.csv`, `run.json`
Optimize: `python -m cli.main optimize --strategy three_pm_momentum --data data/samples/sample_5m.csv --grid '{"stop_pct":[0.3,0.5],"target_pct":[0.8,1.0]}'`
Sample data: `python -m cli.main make-sample`

API: `pip install fastapi uvicorn` -> `uvicorn --factory backend.app:create_app` (env: API_KEY, RUNS_ROOT, DATA_DIR, DATABASE_URL=sqlite:///path)
Frontend: `cd frontend && npm install && npm run dev` (API_BASE default http://localhost:8000; CORS abhi configure nahi)

## Abhi asli vs baaki
Asli: data (csv), registry, backtest, risk, saare 8 validation checks, optimization (holdout), metrics, reporting, jobs (inline), CLI, API handlers + FastAPI routes, SQLite repo, frontend pages.
Baaki: parquet/broker source, PostgreSQL adapter, background worker, CORS, strategy create API, auth > API key.
Strategy logic: gamma_blast/three_pm_momentum placeholder - asli niyam aapko dene honge.

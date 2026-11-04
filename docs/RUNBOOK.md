# RUNBOOK

1. `python scripts/bootstrap.py --all --root .` (naye repo me); update ke liye `--force` (README kabhi overwrite nahi hota)
2. `python -m pytest -q`
3. `python scripts/bootstrap.py --verify --root .`

Demo: `python -m cli.main demo` -> `runs/<run_id>/report.html|json`, `trades.csv`, `run.json`
Optimize: `python -m cli.main optimize --strategy three_pm_momentum --data data/samples/sample_5m.csv --grid '{"stop_pct":[0.3,0.5],"target_pct":[0.8,1.0]}'`
Sample data: `python -m cli.main make-sample` and `python -m cli.main make-options-sample` (option-chain CSV for gamma_blast)

API: `pip install fastapi uvicorn` -> `uvicorn --factory backend.app:create_app`
Env: API_KEY (set ho to X-API-Key zaroori, /health chhodkar), RUNS_ROOT, DATA_DIR, DATABASE_URL=sqlite:///path,
BACKGROUND_WORKER=1 (job thread me), RUN_ISOLATED=1 (job alag process me, limits ke saath),
JOB_STATE_DIR (job status JSON persistence), RATE_LIMIT_PER_MINUTE, HUB_DB_PATH.

## Production / operations

- Deployment, TLS, backups, migrations: `docs/DEPLOYMENT.md`.
- Health: `curl -fsS http://127.0.0.1:8080/api/health`; web `GET /healthz`.
- Rate limits: nginx `/api/` 10 r/s burst 20, backend sliding window (default 120/min).
- Logs: Docker json-file with 10 MB × 5 rotation; request logs include method, path, status, latency and `X-Request-ID`.
- Backups: `python scripts/backup.py` and verify with `--verify-restore`. Never delete old backups automatically.
- Migrations: `python scripts/migrate.py --sqlite runs/svl.sqlite3`.
- Sample data is synthetic. UI, JSON/HTML reports, datasets, runs, comparisons and validation pages label it `SYNTHETIC`.
- Blocked strategies return `status=BLOCKED` with `reason`; the UI shows readiness and reason, and never fabricates metrics.
- Live trading remains disabled; no broker/order code exists in this repo.

## Abhi asli vs baaki
Asli: data (csv, corporate actions, storage, options checks), registry (compatibility, permissions, lifecycle gates),
backtest (execution model), risk, 8 validation checks, optimization (holdout), metrics, reporting, jobs (inline/background/isolated),
CLI, API (saare blueprint routes, POST /strategies chhodkar), SQLite repo, proto messages, frontend pages.
Baaki (NEEDS ME): PostgreSQL adapter, strategy create API, full sandbox (network/filesystem isolation),
real Dhan/FYERS credentials and real market data.

Strategy status: 20 registry me wired hain. 11 synthetic sample data par backtest COMPLETED dete hain
(gamma_blast option-chain CSV ke saath). 8 book/tick strategies aur theta_straddle clear `blocked_reason`
ke saath BLOCKED hain; unhe fake OHLCV signal nahi diya jaata.

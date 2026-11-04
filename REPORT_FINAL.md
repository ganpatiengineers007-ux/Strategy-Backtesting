# Final completeness audit — Strategy-Backtesting

Date: 2026-11-04  
Scope: repository root cleanup, strategy wiring, tests/build, Docker stack, and live API backtests.

## Executive summary

- **20 strategies** are registered and visible through the API; **0 registry errors** and **0 broken symlinks**.
- Live API run on generated sample data: **11 COMPLETED**, **9 BLOCKED** with explicit reasons.
- Full Python suite: **270 passed** (includes repo, `fyers_hub`, and both vendored external suites).
- Frontend `typecheck` + production build: **passed**.
- Go tests/vet and C++ parity test: **passed**. Rust was not run because `cargo` is not installed.
- Docker stack rebuild: backend **healthy**, web on `http://localhost:8080`, `/api/health` **200**, 20 strategies.
- No repository files were deleted. Orphans/duplicates were moved into `archive/` or into their correct folders.

## Root cleanup

`archive/` now holds historical material; standard root files (`README.md`, `pyproject.toml`, `Makefile`, requirements, security/contributing docs) stay at the root.

| From | To | Reason |
|---|---|---|
| `bootstrap.py` (v6, newer) | `scripts/bootstrap.py` | Canonical scaffold generator; docs already invoke `scripts/bootstrap.py`. |
| `scripts/bootstrap.py` (v5) | `archive/bootstrap-v5.py` | Older duplicate, preserved not deleted. |
| `scripts/bootstrap-5.py` | `archive/bootstrap-5.py` | Superseded generator copy. |
| `build_production_fixes.py` | `scripts/build_production_fixes.py` | Historical generator tool; belongs with scripts. |
| `scan_project.py` | `scripts/scan_project.py` | Audit tool; belongs with scripts. |
| `quant_strategy_lab.py` | `scripts/quant_strategy_lab.py` | Standalone research tool; belongs with scripts. |
| `inspect_external.py` | `archive/inspect_external.root-duplicate.py` | Byte-identical duplicate of `scripts/inspect_external.py`. |
| `manifest.json`, `repo_inventory.csv` | `archive/audit/` | Generated audit artifacts from an older repo state. |
| `PRODUCTION_FIXES.md` | `docs/PRODUCTION_FIXES.md` | Historical build report; documentation belongs under `docs/`. |
| `frontend_live_bundle.zip`, `production_fixes_bundle.zip`, `str_wiring_bundle.zip` | `archive/bundles/` | Historical snapshot bundles, duplicated by live files. |
| empty `strategy-lab/` scaffold directories | `archive/legacy-strategy-lab/` | Orphan empty legacy scaffold; tracked with `.gitkeep`. |
| `all_strategies/greeks/test_adapters.py` | `tests/unit/strategies/test_greeks_adapters.py` | Test file was outside pytest; it also failed on the blocked theta adapter. Rewritten as a real pytest test. |

Reference updates: `docs/GENERATED_MAP.md` now points at `scripts/bootstrap.py`; cleanup script targets archived copies; deployment/runbook/strategy docs reflect the current paths and sample generators.

## Strategy wiring and catalog

- Registry discovery over `strategies/`, `all_strategies/`, `engines/`, and `external/`: **20** IDs, no duplicates/errors.
- All `all_strategies` symlinks resolve; `by_number/STR14_sweep.py`, `all_strategies/sweep/sweep_strategy.py`, and the generated links point to live files.
- The only non-pytest strategy test found in the catalog was fixed and moved into `tests/`.
- `gamma_blast` was already registered but blocked on normal OHLCV. The CSV normalizer now parses the `option_chain` JSON column, and `make-options-sample` generates a valid option-chain dataset, making gamma blast the 11th runnable strategy.
- External suites are now part of the default pytest run (`pyproject.toml`), with package markers added to avoid duplicate test-module names.

## Verification commands and results

| Check | Result |
|---|---|
| `.venv/bin/python -m pytest -q` | **270 passed**, 1 warning (Starlette/httpx deprecation) in 37.49s |
| `cd frontend && npm run typecheck && npm run build` | passed; 46 modules transformed |
| `cd engines/go && go vet ./... && go test ./...` | passed |
| C++ compile + rolling-stats test | passed |
| Rust (`cargo test`) | not run: `cargo` unavailable |
| `docker compose -f infra/docker-compose.yml up -d --build` | backend healthy; web up on 8080 |
| `GET /api/health` | `200 {"status":"ok"}` |
| `GET /api/strategies` | 20 strategies |
| `GET /api/datasets` | `sample_5m.csv` (9000 bars), `sample_options_5m.csv` (1500 bars, option chain) |
| Root broken symlinks | none |

Docker fixes made during the audit:

- `DATA_DIR` now points to `/app/data/samples` so the mounted sample datasets are actually discoverable by `/api/datasets`.
- Added a one-shot `runs-init` service that chowns the host `./runs` bind mount to UID/GID 10001 before the non-root backend starts. Without it, isolated API jobs failed with `PermissionError` on `/app/runs`.

## Live API backtests (sample data)

Sample data is gitignored and reproducible with `python -m cli.main make-sample` and `python -m cli.main make-options-sample`. The data is deterministic synthetic random-walk data; it proves execution/wiring, not production edge.

### COMPLETED — 11

| Strategy | Dataset | Status | Validation | Trades | Return % | Max DD % | Win rate % |
|---|---|---|---:|---:|---:|---:|---:|
| `delta_vwap` | `sample_5m.csv` | COMPLETED | FAIL | 237 | -19.10 | 19.14 | 35.86 |
| `fvg` | `sample_5m.csv` | COMPLETED | FAIL | 50 | -5.76 | 5.80 | 34.00 |
| `gamma_blast` | `sample_options_5m.csv` | COMPLETED | FAIL | 20 | 1.20 | 3.10 | 60.00 |
| `gamma_vwap` | `sample_5m.csv` | COMPLETED | INCOMPLETE | 0 | 0.00 | 0.00 | 0.00 |
| `greeks_confluence` | `sample_5m.csv` | COMPLETED | FAIL | 49 | -5.37 | 6.30 | 34.69 |
| `liquidity_sweep` | `sample_5m.csv` | COMPLETED | INCOMPLETE | 4 | -0.01 | 0.36 | 50.00 |
| `mean_reversion` | `sample_5m.csv` | COMPLETED | FAIL | 152 | -15.36 | 15.36 | 12.50 |
| `session_ignition` | `sample_5m.csv` | COMPLETED | FAIL | 56 | -6.69 | 6.69 | 21.43 |
| `sweep` | `sample_5m.csv` | COMPLETED | FAIL | 240 | -22.25 | 24.95 | 19.58 |
| `three_pm_momentum` | `sample_5m.csv` | COMPLETED | FAIL | 56 | -4.24 | 4.39 | 28.57 |
| `vega_iv` | `sample_5m.csv` | COMPLETED | FAIL | 49 | -5.37 | 6.30 | 34.69 |

Validation FAIL/INCOMPLETE results are expected to be treated as a warning: they reflect random-walk sample data (and, for `gamma_vwap`, zero trades), not a runtime failure. All runs produced reports/trades and are retrievable via `/api/backtests/{run_id}/results`.

### BLOCKED — 9

| Strategy | Status | Reason |
|---|---|---|
| `iceberg` | BLOCKED | `MISSING_DATA:l2_book,tick_trades` — needs best-level order-book refill events. |
| `latency_arb` | BLOCKED | `MISSING_DATA:second_venue_feed` — needs synchronized feeds from two venues. |
| `microstructure` | BLOCKED | `MISSING_DATA:l2_book,tick_trades` — needs L2 book + tick trades for VPIN/Kyle-lambda. |
| `obi_delta` | BLOCKED | `MISSING_DATA:l2_book` — needs L2 depth and trade tape for OBI/delta. |
| `reversal_ai` | BLOCKED | `MISSING_DATA:l2_book,tick_trades` — needs L2 imbalance, delta, spread, trade-count features. |
| `spoof_ml` | BLOCKED | `MISSING_DATA:l2_book,tick_trades` — needs L2 book and labelled spoofing episodes. |
| `stat_arb` | BLOCKED | `MISSING_DATA:multi_asset` — needs a synchronized multi-asset panel. |
| `theta_straddle` | BLOCKED | `UNSUPPORTED_STRATEGY` — short ATM call+put straddle cannot be modelled by the long-only Signal v0 engine. |
| `volume_profile` | BLOCKED | `MISSING_DATA:tick_trades` — needs a per-trade tape, not OHLCV bar volume. |

## Notes / remaining limitations

- Sample datasets are intentionally gitignored; generate them with the two CLI commands above before exercising the API.
- `infra/.env` contains the local API key and remains untracked.
- The repo root is reduced to standard project files plus `opencode.json`; historical scripts, generated inventories, and bundles are preserved under `archive/`.
- No production trading claims are made from synthetic-data backtests.

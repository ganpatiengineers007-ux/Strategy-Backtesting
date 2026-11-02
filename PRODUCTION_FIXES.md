# Production fixes - build report

Generated: 2026-11-02T01:25:24+00:00

## Patches aur files

| ID | File | Kya hua | Status | Kyon |
|---|---|---|---|---|
| P01 | `backend/app.py` | patch | applied | production me API_KEY zaroori; CORS helper |
| P02 | `backend/app.py` | patch | applied | startup par production check + CORS_ORIGINS se CORS |
| P03 | `fyers_hub/client/api.py` | patch | applied | auth error detection: 'token' substring hata kar specific phrases |
| P04 | `fyers_hub/ingest/ws.py` | patch | applied | except me 'log' shadowing hatao (callbacks TypeError se bachein) |
| P05 | `fyers_hub/ingest/ws.py` | patch | applied | P04 ke saath |
| P06 | `fyers_hub/ingest/live.py` | patch | applied | parse_tf import (safe_since ke liye) |
| P07 | `fyers_hub/ingest/live.py` | patch | applied | day_start_epoch import |
| P08 | `fyers_hub/ingest/live.py` | patch | applied | safe_since helper (candle corruption fix) |
| P09 | `fyers_hub/ingest/live.py` | patch | applied | 3-din window hata kar safe_since (volume/OHLC corruption fix) |
| P10 | `fyers_hub/cli.py` | patch | applied | datetime import |
| P11 | `fyers_hub/cli.py` | patch | applied | IST import |
| P12 | `fyers_hub/cli.py` | patch | applied | export helper (ISO IST timestamp) |
| P13 | `fyers_hub/cli.py` | patch | applied | export ab ISO timestamp likhta hai (backtest loader compatible) |
| P14 | `backtest/engine.py` | patch | applied | exit_pending flag init |
| P15 | `backtest/engine.py` | patch | applied | pending EXIT agle bar ke open par bharo |
| P16 | `backtest/engine.py` | patch | applied | signal EXIT ab same-bar close par nahi bharta (lookahead fix) |
| P17 | `scripts/sweep_strategy.py` | patch | applied | retry cooldown constant |
| P18 | `scripts/sweep_strategy.py` | patch | applied | retry state init |
| P19 | `scripts/sweep_strategy.py` | patch | applied | entry reject hone par position record na ho |
| P20 | `scripts/sweep_strategy.py` | patch | applied | _order failure ab None (empty string nahi) |
| P21 | `scripts/sweep_strategy.py` | patch | applied | exit reject hone par position khuli rakho |
| P22 | `scripts/sweep_strategy.py` | patch | applied | exit retry cooldown + EOD square-off retry |
| N01 | `registry/registry.py` | file | overwritten | bad manifest se poori registry na gire |
| N02 | `frontend/src/api/client.ts` | file | overwritten | API key header + 401 message + VITE_API_BASE |
| N03 | `tests/unit/fixes/__init__.py` | file | created | fix tests package |
| N04 | `tests/unit/fixes/test_derive_window.py` | file | created | derive window regression |
| N05 | `tests/unit/fixes/test_export_and_since.py` | file | created | export ISO regression |
| N06 | `tests/unit/fixes/test_sweep_order_state.py` | file | created | sweep order-state regression |
| N07 | `tests/unit/fixes/test_engine_exit_next_open.py` | file | created | engine exit regression |
| N08 | `tests/unit/fixes/test_registry_resilience.py` | file | created | registry regression |
| N09 | `tests/unit/fixes/test_app_production_guard.py` | file | created | production guard regression |
| N10 | `infra/Dockerfile` | file | overwritten | non-root backend image, uvicorn CMD |
| N11 | `infra/Dockerfile.frontend` | file | created | vite build + nginx static image |
| N12 | `infra/docker-compose.yml` | file | overwritten | backend + web, healthcheck, required API_KEY |
| N13 | `infra/nginx.conf` | file | overwritten | /api proxy + security headers |
| N14 | `infra/nginx.tls.conf.example` | file | created | host-level TLS example |
| N15 | `infra/.env.example` | file | created | compose env template |
| N16 | `.dockerignore` | file | created | secrets, runs, zips build context se bahar |
| N17 | `requirements-prod.txt` | file | created | runtime-only pinned ranges |
| N18 | `.github/workflows/ci.yml` | file | overwritten | pytest + frontend + docker build CI |
| N19 | `scripts/cleanup_unused.sh` | file | created | dry-run default cleanup |

## Verify

- Compile check: OK
- Fix tests: pytest install nahi - tests/unit/fixes server par chalao

## Lagu karne ka kram (server par)

1. `bundle.zip` ko repo me extract karo (ya `repo/` folder ko poori tarah use karo).
2. `python -m pytest -q` chalao (fixture tests sahit).
3. `infra/.env` banao: API_KEY aur CORS_ORIGINS bharo. Phir `docker compose -f infra/docker-compose.yml up -d --build`.
4. Host par TLS: `infra/nginx.tls.conf.example` ko certbot ke baad lagao.
5. Cleanup dekho: `./scripts/cleanup_unused.sh` (dry run). Theek lage to `--apply`.

## Zaroori chetavani

- Engine me EXIT ab agle bar ke open par bharta hai. Isse backtest ke numbers badlenge.
  `tests/regression/test_known_results.py` aur `tests/fixtures/expected_results.json` ko naye numbers se update karna hoga (naye nateeje ko review karke).
- Sweep trader ka `DRY_RUN = True` abhi bhi default hai. Live se pehle paper mode me chalao.
- Broker orderbook se position reconciliation ka step manual hai (code me automatic nahi).
- `_order` me agar broker orderId hi na de to use failure maana jata hai. Aise case me orderbook khud dekho.
- Derived timeframes ke liye daily-based tf (15D) ab har minute poori history se banta hai. Symbols zyada hon to CPU dekho.

## Rollback

Har badle hue file ka original `backup/` me hai. Repo me wapas copy karo.

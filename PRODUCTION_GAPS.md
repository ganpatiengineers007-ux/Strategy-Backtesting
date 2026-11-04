# Production gaps — Strategy-Backtesting

Date: 2026-11-04  
Scope: frontend pages/backend endpoints, production security/ops gaps, live API verification, fixes applied.

## Verified results (live stack)

| Check | Result |
|---|---|
| `.venv/bin/python -m pytest -q` | **280 passed** |
| `frontend npm run typecheck && npm run build` | passed; 46 modules |
| `go vet ./... && go test ./...` | passed |
| C++ CMake/ctest | passed |
| Rust | not run (`cargo` not installed) |
| Docker stack | backend healthy, web healthy, `http://127.0.0.1:8080` |
| Live API backtests on synthetic sample data | **11 COMPLETED, 9 BLOCKED** with explicit reasons |
| UI page flows against live API (JSDOM) | **16/16 pages OK** |
| Backup/restore test | passed (`scripts/backup.py --verify-restore`) |
| Rate limiting | backend and nginx return 429 beyond limit |

## Audit table — frontend pages

| Page | Route | Status | Notes |
|---|---|---|---|
| Dashboard | `#dashboard` | WORKING | Health, hub, latest runs, strategy readiness, synthetic-data notice |
| Live market data | `#live` | WORKING | Hub status/quotes/candles/chain; empty-state friendly when hub has no data |
| New backtest | `#new-run` | WORKING | Strategy/dataset pickers mark `[BLOCKED]` and `[SYNTHETIC]`, shows blocked reason, polls job |
| Settings | `#settings` | WORKING | API key set/clear in sessionStorage only |
| Strategies | `#strategies` | WORKING | 20 strategies with status/runnable/reason/required_data |
| Strategy detail | `#strategy/<id>` | WORKING | Status badge, blocked reason, live-trading disabled |
| Create strategy | `#create-strategy` | PLACEHOLDER | Intentionally disabled; strategy creation is repo review + commit |
| Backtest runs | `#runs` | WORKING | Runs table with status/reason/synthetic/detail links |
| Run detail | `#run/<id>` | WORKING | Run fields, reason, synthetic badge |
| Report | `#report/<id>` | WORKING | Metrics/charts/validation, synthetic badge, blocked notice |
| Validation results | `#validation/<id>` | WORKING | Overall/checks, synthetic badge |
| Compare runs | `#compare/<ids>` | WORKING | Run summary with synthetic labels + metric table |
| Datasets | `#datasets` | WORKING | Synthetic/real labels for every dataset |
| System health | `#health` | WORKING | API health, strategy counts, hub JSON |
| Audit log | `#audit` | WORKING | JSONL audit table |

## Audit table — backend API

| Endpoint | Method | Status | Notes |
|---|---|---|---|
| `/health` | GET | WORKING | Public, 200 |
| `/strategies` | GET | WORKING | 20 strategies, auth required, status/reason exposed |
| `/strategies/{id}` | GET | WORKING | Strategy detail, auth required |
| `/datasets` | GET | WORKING | `synthetic` and `data_label` on every file |
| `/backtests` | POST | WORKING | Starts backtest; returns job/run id, status, reason, synthetic |
| `/backtests` | GET | WORKING | List runs with status/reason/synthetic/data_label |
| `/backtests/{id}` | GET | WORKING | Run/job detail |
| `/backtests/{id}/results` | GET | WORKING | Results incl. dataset/synthetic/reason; API-only consumer |
| `/validations` | POST | WORKING | Starts backtest+validation; no separate UI form (reuse New run) |
| `/validations/{id}` | GET | WORKING | Validation checks |
| `/comparisons` | POST | WORKING | Compare runs, synthetic labels included |
| `/reports/{id}` | GET | WORKING | Report JSON |
| `/audit` | GET | WORKING | JSONL audit log |
| `/hub/*` | GET | WORKING | Status/quotes/coverage/candles/chain; returns empty when hub DB not initialized |
| Web static + `/healthz` | GET | WORKING | Frontend served by nginx; web healthcheck 200 |
| Path traversal | any | WORKING | `safe_id` blocks traversal; FastAPI path params reject slashes |
| Auth errors | all | WORKING | 401 for missing/wrong key; 400 bad input; 404 missing resources |
| Rate limit | all `/api` | WORKING | Backend sliding window + nginx `limit_req`; tested 429 |
| `POST /strategies` | POST | PLACEHOLDER | Intentionally not implemented (no strategy-creation API) |

## Production gap list

| # | Gap | Rank | Status | Notes |
|---|---|---|---|---|
| 1 | HTTPS/TLS for production | BLOCKER | FIXED (prepared, disabled) | `infra/docker-compose.tls.yml` + `infra/nginx.tls.conf.template`; enable only after domain + certs |
| 2 | API key exposed if used over plain HTTP | BLOCKER | FIXED (prepared) | Key kept only in browser `sessionStorage`, never bundled; stack bound to localhost by default |
| 3 | No rate limiting | IMPORTANT | FIXED | Backend `RATE_LIMIT_PER_MINUTE` sliding window; nginx `/api/` 10 r/s burst 20 |
| 4 | No request logging | IMPORTANT | FIXED | JSON request logs with method/path/status/latency/`X-Request-ID` |
| 5 | No log rotation | IMPORTANT | FIXED | Docker json-file max-size 10 MB, max-file 5 for backend/web/tls |
| 6 | Error handling/information leak | IMPORTANT | FIXED | JSON error responses; internals not leaked; auth enforced |
| 7 | SQLite durable records | IMPORTANT | FIXED | Backtest records mirrored to `DATABASE_URL` SQLite |
| 8 | DB migrations | IMPORTANT | FIXED basic | `scripts/migrate.py` + idempotent SQLite migration; PostgreSQL adapter is NEEDS ME |
| 9 | Backups/restore of runs + SQLite | BLOCKER | FIXED | `scripts/backup.py` archives `runs/` + SQLite, SHA manifest, `--verify-restore` test |
| 10 | Job queue/worker reliability | IMPORTANT | FIXED | UUID job IDs, optional `JOB_STATE_DIR` persistence, stale RUNNING -> FAILED on restart |
| 11 | Container restart/healthchecks | IMPORTANT | FIXED | Backend/web healthchecks, `restart: unless-stopped`, localhost-only web port |
| 12 | Secrets handling | IMPORTANT | FIXED | `.env` ignored; `.env.example` only; production API key min length; isolated subprocess excludes keys |
| 13 | CORS | IMPORTANT | FIXED | Same-origin default; `CORS_ORIGINS` opt-in, no credentials |
| 14 | CI pipeline | IMPORTANT | FIXED | Python, frontend, Go, C++, Docker build/config checked; Rust skipped when cargo absent |
| 15 | Monitoring/alerting | NICE-TO-HAVE | NEEDS ME | Health/logs exist; Prometheus target/alerts not added |
| 16 | Real market data / broker credentials | NEEDS ME | NEEDS ME | Sample data remains synthetic; no live trading or broker code |

## Only you can do (outside this commit)

1. Obtain and control a domain, point DNS at this host, and acquire TLS certificates (certbot or your CA).
2. Place `fullchain.pem` and `privkey.pem` under `infra/certs/` (ignored from git) and set `DOMAIN`/`TLS_CERT_PATH`/`TLS_KEY_PATH` in `infra/.env`.
3. Enable the TLS profile with `docker compose -f infra/docker-compose.yml -f infra/docker-compose.tls.yml --profile tls up -d --build`; firewall/block direct 8080 exposure if needed.
4. Rotate `API_KEY` in `infra/.env` and recreate containers; never commit the key.
5. Add real Dhan/Fyers credentials and real market data if required; run the Fyers hub ingest. Sample data stays synthetic.
6. Add a PostgreSQL adapter if production needs PostgreSQL beyond SQLite.
7. Decide production `CORS_ORIGINS`, rate limits, log retention, and monitoring stack if required.
8. Do not add broker connection/order-placement/live-execution code; live trading remains disabled by design.

# Wiring map

Machine-readable: `WIRING_MAP.json` (har file: phase, purpose, depends_on, test). Order: `BUILD_ORDER.md`.

Runtime flow:
```
frontend/src/pages -> frontend/src/api -> backend/api -> backend/services
  -> registry (manifest + compatibility) -> data/loaders (+ validators, quality)
  -> strategies/<id> -> backtest/engine (+ execution model, risk) -> validation/pipeline
  -> metrics -> reporting/generator -> persistence (runs/, audit.jsonl, optional SQLite)
```
Jobs: `POST /backtests` -> `backend/jobs/queue` -> inline ya `BackgroundWorker` (BACKGROUND_WORKER=1)
-> optional `RUN_ISOLATED=1` (alag process, CPU/memory/time limit, saaf env).
Contracts: `contracts/*.schema.json`, `contracts/proto/*.proto`, `openapi.yaml`; contract tests unhe consumers se milate hain.

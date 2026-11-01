# Wiring Report

## Wiring Chain (kiski call kiski)

```
Frontend (TypeScript/Vite)
  └─ frontend/src/api/strategies.ts
       ├─ listStrategies()      -> GET /strategies
       └─ getStrategy(id)       -> GET /strategies/{id}
            └─ fetch() call to BASE + path (http://localhost:8000)

Backend API (FastAPI)
  └─ backend/api/strategies.py
       ├─ GET /strategies          -> strategy_service.list_strategies()
       └─ GET /strategies/{strategy_id} -> strategy_service.get_strategy(id)
            └─ backend/app.py include_router() mounts all API routers

Backend Service
  └─ backend/services/strategy_service.py
       ├─ list_strategies()  -> Registry().discover() + Registry().manifest() + Registry().source_hash()
       └─ get_strategy(id)   -> Registry().manifest(id) + Registry().source_hash(id)

Registry
  └─ registry/registry.py
       ├─ discover()  -> scans strategies/*/ for manifest.yaml, validates, loads records
       ├─ manifest(sid)  -> returns manifest dict for strategy id
       ├─ load(sid, params)  -> imports entry_point module, instantiates class
       └─ source_hash(sid)  -> hash of strategy directory

Strategies (STR01..STR14)
  ├─ STR01..STR10  external/gts_quant_lab/... (quantlab, tests externally: 9 pass each)
  ├─ STR11         external/quant_stat_arb_framework/... (quantstrat, tests externally: 6 pass)
  ├─ STR12         strategies/gamma_blast/strategy.py  -> manifest.yaml present -> registered
  ├─ STR13         strategies/three_pm_momentum/strategy.py  -> manifest.yaml present -> registered
  └─ STR14         strategies/sweep/strategy.py  -> manifest.yaml present -> registered (this wiring)

Frontend pages consuming /strategies:
  ├─ frontend/src/pages/strategy-registry.ts   -> listStrategies() -> table of all strategies
  └─ frontend/src/pages/strategy-detail.ts     -> getStrategy(id) -> key/value detail view
```

## Done (complete)

| Item | Status | Details |
|------|--------|---------|
| Registry discovers STR12, STR13, STR14 | DONE | `strategies/gamma_blast/`, `strategies/three_pm_momentum/`, `strategies/sweep/` all have `manifest.yaml` |
| STR14 sweep wrapper | DONE | `strategies/sweep/strategy.py` — Strategy-compatible, no broker, no keys, no live orders |
| Import test for STR14 | DONE | `tests/unit/strategies/sweep/test_strategy.py` |
| API routes /strategies, /strategies/{id} | DONE | `backend/api/strategies.py` — already present, wired to service |
| Frontend API client | DONE | `frontend/src/api/strategies.ts` — calls `/strategies` and `/strategies/{id}` |
| Frontend pages | DONE | `strategy-registry.ts` lists strategies; `strategy-detail.ts` shows detail |
| Service layer | DONE | `backend/services/strategy_service.py` — calls Registry |
| App router mounting | DONE | `backend/app.py` mounts strategies router |
| Tests green | DONE | 150 passed (`python3 -m pytest tests/unit -q`) |
| Commit | DONE | `30b69f9` — STR14 sweep + audit scripts |

## Pending

| Item | Reason |
|------|--------|
| STR01..STR11 in local Registry | These are external strategies (quantlab/quantstrat). Their code and tests live in `external/` directories, not under local `strategies/`. To add them to the local registry, copy or symlink them into `strategies/` with `manifest.yaml`. |
| STR01..STR10 local import tests | External quantlab tests already pass (9 each). No local test files needed unless strategies are copied into `strategies/`. |
| STR11 local import test | External quantstrat tests already pass (6). Same as above. |
| STUB folders with >5 lines | `tests/unit/strategies/examples/`, `tests/unit/strategies/gamma_blast/`, `tests/unit/strategies/three_pm_momentum/`, `tests/unit/backend/adapters/`, `tests/unit/contracts/`, `tests/unit/engines/bindings/`, `tests/unit/engines/reference/` already have minimal import tests (≤5 lines, marked STUB by audit). They pass. |
| Empty KHALI folders | Skipped per rules: docs/, data/, config/, logs/, engines/cpp/, engines/go/, engines/rust/, artifacts/, output/, .github/, .pytest_cache/, etc. |

## Rules respected

- No live orders or broker connections (STR14 wrapper uses pure price-action logic, no dhanhq import)
- No API keys or credentials
- No existing files modified — only new files created
- All 150 tests pass

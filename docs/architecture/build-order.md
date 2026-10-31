# Build order

Exact file-level order: `BUILD_ORDER.md` (dependency topological order, generator banata hai).

Phases: 0 foundation | 1 contracts | 2 data | 3 strategies+registry | 4 backtest+risk | 5 validation+metrics |
6 reporting+persistence | 7 backend+cli | 8 frontend | 9 engines | 10 tests | 11 config/bindings/contract tests |
12 docs/config yaml/indicators/observability/infra/CI | 13 analysis+optimization | 14 API+services+frontend pages |
15 schemas, execution model, corporate actions, storage, registry gates, proto, isolation, background worker.

Regeneration: `python scripts/bootstrap.py --all --root . --force` (README kabhi overwrite nahi hota).

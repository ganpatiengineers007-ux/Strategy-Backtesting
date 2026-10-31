# BUILD ORDER (dependency topological order)

| # | File | Phase | Pehle chahiye | Test |
|---|---|---|---|---|
| 1 | `README.md` | 0 | - | `see tests/` |
| 2 | `pyproject.toml` | 0 | - | `see tests/` |
| 3 | `.gitignore` | 0 | - | `see tests/` |
| 4 | `docs/architecture/ADR-0001-language-ownership.md` | 0 | - | `see tests/` |
| 5 | `docs/architecture/wiring-map.md` | 0 | - | `see tests/` |
| 6 | `docs/architecture/build-order.md` | 0 | - | `see tests/` |
| 7 | `contracts/strategy.schema.json` | 1 | - | `see tests/` |
| 8 | `contracts/data.schema.json` | 1 | - | `see tests/` |
| 9 | `contracts/signal.schema.json` | 1 | - | `see tests/` |
| 10 | `contracts/trade.schema.json` | 1 | - | `see tests/` |
| 11 | `contracts/report.schema.json` | 1 | - | `see tests/` |
| 12 | `contracts/run.schema.json` | 1 | - | `see tests/` |
| 13 | `contracts/openapi.yaml` | 1 | - | `see tests/` |
| 14 | `contracts/proto/common.proto` | 1 | - | `see tests/` |
| 15 | `contracts/proto/market_data.proto` | 1 | - | `see tests/` |
| 16 | `contracts/proto/strategy.proto` | 1 | - | `see tests/` |
| 17 | `contracts/proto/signal.proto` | 1 | - | `see tests/` |
| 18 | `contracts/proto/backtest.proto` | 1 | - | `see tests/` |
| 19 | `contracts/proto/metrics.proto` | 1 | - | `see tests/` |
| 20 | `contracts/proto/report.proto` | 1 | - | `see tests/` |
| 21 | `strategies/gamma_blast/manifest.yaml` | 3 | - | `see tests/` |
| 22 | `strategies/three_pm_momentum/manifest.yaml` | 3 | - | `see tests/` |
| 23 | `risk/limits.py` | 4 | - | `tests/unit/risk/test_limits.py` |
| 24 | `risk/exposure.py` | 4 | - | `tests/unit/risk/test_exposure.py` |
| 25 | `risk/drawdown.py` | 4 | - | `tests/unit/risk/test_drawdown.py` |
| 26 | `risk/kill_switch.py` | 4 | - | `tests/unit/risk/test_kill_switch.py` |
| 27 | `risk/manager.py` | 4 | - | `tests/unit/risk/test_manager.py` |
| 28 | `persistence/database.py` | 6 | - | `tests/unit/persistence/test_database.py` |
| 29 | `persistence/models.py` | 6 | - | `tests/unit/persistence/test_models.py` |
| 30 | `persistence/repositories.py` | 6 | - | `tests/unit/persistence/test_repositories.py` |
| 31 | `persistence/audit.py` | 6 | - | `tests/unit/persistence/test_audit.py` |
| 32 | `reporting/templates/report.html` | 6 | - | `see tests/` |
| 33 | `backend/middleware/request_id.py` | 7 | - | `tests/unit/backend/middleware/test_request_id.py` |
| 34 | `backend/middleware/error_handler.py` | 7 | - | `tests/unit/backend/middleware/test_error_handler.py` |
| 35 | `backend/middleware/authentication.py` | 7 | - | `tests/unit/backend/middleware/test_authentication.py` |
| 36 | `backend/api/health.py` | 7 | - | `tests/unit/backend/api/test_health.py` |
| 37 | `backend/api/strategies.py` | 7 | - | `tests/unit/backend/api/test_strategies.py` |
| 38 | `backend/api/datasets.py` | 7 | - | `tests/unit/backend/api/test_datasets.py` |
| 39 | `backend/api/backtests.py` | 7 | - | `tests/unit/backend/api/test_backtests.py` |
| 40 | `backend/api/validation.py` | 7 | - | `tests/unit/backend/api/test_validation.py` |
| 41 | `backend/api/comparisons.py` | 7 | - | `tests/unit/backend/api/test_comparisons.py` |
| 42 | `backend/api/reports.py` | 7 | - | `tests/unit/backend/api/test_reports.py` |
| 43 | `backend/schemas/backtest.py` | 7 | - | `tests/unit/backend/schemas/test_backtest.py` |
| 44 | `backend/schemas/strategy.py` | 7 | - | `tests/unit/backend/schemas/test_strategy.py` |
| 45 | `backend/schemas/report.py` | 7 | - | `tests/unit/backend/schemas/test_report.py` |
| 46 | `cli/main.py` | 7 | - | `tests/unit/cli/test_main.py` |
| 47 | `cli/commands.py` | 7 | - | `tests/unit/cli/test_commands.py` |
| 48 | `frontend/package.json` | 8 | - | `see tests/` |
| 49 | `frontend/tsconfig.json` | 8 | - | `see tests/` |
| 50 | `frontend/src/components/navigation.ts` | 8 | - | `see tests/` |
| 51 | `frontend/src/components/data-table.ts` | 8 | - | `see tests/` |
| 52 | `frontend/src/components/metric-card.ts` | 8 | - | `see tests/` |
| 53 | `frontend/src/components/chart-panel.ts` | 8 | - | `see tests/` |
| 54 | `frontend/src/components/status-badge.ts` | 8 | - | `see tests/` |
| 55 | `frontend/src/components/error-panel.ts` | 8 | - | `see tests/` |
| 56 | `frontend/src/components/charts/equity-curve.ts` | 8 | - | `see tests/` |
| 57 | `frontend/src/components/charts/drawdown-chart.ts` | 8 | - | `see tests/` |
| 58 | `frontend/src/components/charts/monthly-returns.ts` | 8 | - | `see tests/` |
| 59 | `frontend/src/components/charts/trade-distribution.ts` | 8 | - | `see tests/` |
| 60 | `engines/go/go.mod` | 9 | - | `see tests/` |
| 61 | `engines/go/internal/contracts/contracts.go` | 9 | - | `see tests/` |
| 62 | `engines/go/internal/jobs/jobs.go` | 9 | - | `see tests/` |
| 63 | `engines/go/internal/observability/observability.go` | 9 | - | `see tests/` |
| 64 | `engines/cpp/include/svl/rolling_stats.hpp` | 9 | - | `see tests/` |
| 65 | `engines/cpp/CMakeLists.txt` | 9 | - | `see tests/` |
| 66 | `engines/rust/Cargo.toml` | 9 | - | `see tests/` |
| 67 | `engines/rust/src/lib.rs` | 9 | - | `see tests/` |
| 68 | `config/risk_policy.json` | 11 | - | `see tests/` |
| 69 | `config/execution_defaults.json` | 11 | - | `see tests/` |
| 70 | `contracts/schema_check.py` | 11 | - | `tests/unit/contracts/test_schema_check.py` |
| 71 | `engines/reference/rolling_stats.py` | 11 | - | `tests/unit/engines/reference/test_rolling_stats.py` |
| 72 | `frontend/vite.config.ts` | 11 | - | `see tests/` |
| 73 | `docs/RUNBOOK.md` | 11 | - | `see tests/` |
| 74 | `LICENSE` | 12 | - | `see tests/` |
| 75 | `CHANGELOG.md` | 12 | - | `see tests/` |
| 76 | `CONTRIBUTING.md` | 12 | - | `see tests/` |
| 77 | `SECURITY.md` | 12 | - | `see tests/` |
| 78 | `requirements.lock` | 12 | - | `see tests/` |
| 79 | `.env.example` | 12 | - | `see tests/` |
| 80 | `.editorconfig` | 12 | - | `see tests/` |
| 81 | `.pre-commit-config.yaml` | 12 | - | `see tests/` |
| 82 | `.github/workflows/ci.yml` | 12 | - | `see tests/` |
| 83 | `artifacts/.gitkeep` | 12 | - | `see tests/` |
| 84 | `output/.gitkeep` | 12 | - | `see tests/` |
| 85 | `config/backtest.yaml` | 12 | - | `see tests/` |
| 86 | `config/costs.yaml` | 12 | - | `see tests/` |
| 87 | `config/risk.yaml` | 12 | - | `see tests/` |
| 88 | `config/system.yaml` | 12 | - | `see tests/` |
| 89 | `config/data.yaml` | 12 | - | `see tests/` |
| 90 | `config/validation.yaml` | 12 | - | `see tests/` |
| 91 | `config/reporting.yaml` | 12 | - | `see tests/` |
| 92 | `config/logging.yaml` | 12 | - | `see tests/` |
| 93 | `docs/ARCHITECTURE.md` | 12 | - | `see tests/` |
| 94 | `docs/REPOSITORY_MAP.md` | 12 | - | `see tests/` |
| 95 | `docs/STRATEGY_CONTRACT.md` | 12 | - | `see tests/` |
| 96 | `docs/DATA_CONTRACT.md` | 12 | - | `see tests/` |
| 97 | `docs/BACKTEST_ENGINE.md` | 12 | - | `see tests/` |
| 98 | `docs/VALIDATION_POLICY.md` | 12 | - | `see tests/` |
| 99 | `docs/METRICS_DICTIONARY.md` | 12 | - | `see tests/` |
| 100 | `docs/SECURITY_POLICY.md` | 12 | - | `see tests/` |
| 101 | `docs/TESTING_POLICY.md` | 12 | - | `see tests/` |
| 102 | `docs/DEPLOYMENT.md` | 12 | - | `see tests/` |
| 103 | `docs/DECISION_GATES.md` | 12 | - | `see tests/` |
| 104 | `docs/adr/ADR-001-LANGUAGE-BOUNDARIES.md` | 12 | - | `see tests/` |
| 105 | `docs/adr/ADR-002-DATA-CONTRACTS.md` | 12 | - | `see tests/` |
| 106 | `docs/adr/ADR-003-EXECUTION-MODEL.md` | 12 | - | `see tests/` |
| 107 | `frontend/public/favicon.svg` | 12 | - | `see tests/` |
| 108 | `frontend/public/logo.svg` | 12 | - | `see tests/` |
| 109 | `frontend/src/styles/base.css` | 12 | - | `see tests/` |
| 110 | `frontend/src/styles/layout.css` | 12 | - | `see tests/` |
| 111 | `frontend/src/styles/components.css` | 12 | - | `see tests/` |
| 112 | `frontend/src/styles/dashboard.css` | 12 | - | `see tests/` |
| 113 | `strategies/examples/example_strategy.yaml` | 12 | - | `see tests/` |
| 114 | `strategies/gamma_blast/config.yaml` | 12 | - | `see tests/` |
| 115 | `strategies/three_pm_momentum/config.yaml` | 12 | - | `see tests/` |
| 116 | `indicators/trend.py` | 12 | - | `tests/unit/indicators/test_trend.py` |
| 117 | `indicators/momentum.py` | 12 | - | `tests/unit/indicators/test_momentum.py` |
| 118 | `indicators/volatility.py` | 12 | - | `tests/unit/indicators/test_volatility.py` |
| 119 | `indicators/volume.py` | 12 | - | `tests/unit/indicators/test_volume.py` |
| 120 | `indicators/market_structure.py` | 12 | - | `tests/unit/indicators/test_market_structure.py` |
| 121 | `indicators/options_greeks.py` | 12 | - | `tests/unit/indicators/test_options_greeks.py` |
| 122 | `observability/logging.py` | 12 | - | `tests/unit/observability/test_logging.py` |
| 123 | `observability/metrics.py` | 12 | - | `tests/unit/observability/test_metrics.py` |
| 124 | `observability/tracing.py` | 12 | - | `tests/unit/observability/test_tracing.py` |
| 125 | `observability/health.py` | 12 | - | `tests/unit/observability/test_health.py` |
| 126 | `backend/schemas/validation.py` | 12 | - | `tests/unit/backend/schemas/test_validation.py` |
| 127 | `cli/formatting.py` | 12 | - | `tests/unit/cli/test_formatting.py` |
| 128 | `persistence/migrations/001_initial.sql` | 12 | - | `see tests/` |
| 129 | `engines/go/README.md` | 12 | - | `see tests/` |
| 130 | `engines/cpp/README.md` | 12 | - | `see tests/` |
| 131 | `engines/rust/README.md` | 12 | - | `see tests/` |
| 132 | `scripts/run_tests.sh` | 12 | - | `see tests/` |
| 133 | `scripts/run_backtest.sh` | 12 | - | `see tests/` |
| 134 | `scripts/build_frontend.sh` | 12 | - | `see tests/` |
| 135 | `scripts/generate_report.sh` | 12 | - | `see tests/` |
| 136 | `infra/Dockerfile` | 12 | - | `see tests/` |
| 137 | `infra/docker-compose.yml` | 12 | - | `see tests/` |
| 138 | `infra/nginx.conf` | 12 | - | `see tests/` |
| 139 | `infra/ci/pipeline.yml` | 12 | - | `see tests/` |
| 140 | `tests/fixtures/sample_ohlcv.csv` | 12 | - | `see tests/` |
| 141 | `tests/fixtures/expected_results.json` | 12 | - | `see tests/` |
| 142 | `docs/OPTIMIZATION.md` | 13 | - | `see tests/` |
| 143 | `backend/api/common.py` | 14 | - | `tests/unit/backend/api/test_common.py` |
| 144 | `frontend/src/components/page.ts` | 14 | - | `see tests/` |
| 145 | `frontend/src/env.d.ts` | 14 | - | `see tests/` |
| 146 | `scripts/validate_repo.sh` | 0 | `pyproject.toml` | `see tests/` |
| 147 | `tests/contract/test_strategy_contract.py` | 11 | `contracts/strategy.schema.json` | `see tests/` |
| 148 | `data/models.py` | 2 | `contracts/data.schema.json` | `tests/unit/data/test_models.py` |
| 149 | `data/timestamps.py` | 2 | `contracts/data.schema.json` | `tests/unit/data/test_timestamps.py` |
| 150 | `data/normalizer.py` | 2 | `contracts/data.schema.json` | `tests/unit/data/test_normalizer.py` |
| 151 | `data/validators.py` | 2 | `contracts/data.schema.json` | `tests/unit/data/test_validators.py` |
| 152 | `data/corporate_actions.py` | 2 | `contracts/data.schema.json` | `tests/unit/data/test_corporate_actions.py` |
| 153 | `data/survivorship.py` | 2 | `contracts/data.schema.json` | `tests/unit/data/test_survivorship.py` |
| 154 | `data/quality_report.py` | 2 | `contracts/data.schema.json` | `tests/unit/data/test_quality_report.py` |
| 155 | `data/storage.py` | 2 | `contracts/data.schema.json` | `tests/unit/data/test_storage.py` |
| 156 | `data/loaders.py` | 2 | `contracts/data.schema.json` | `tests/unit/data/test_loaders.py` |
| 157 | `data/sources/csv_source.py` | 2 | `contracts/data.schema.json` | `tests/unit/data/sources/test_csv_source.py` |
| 158 | `data/sources/parquet_source.py` | 2 | `contracts/data.schema.json` | `tests/unit/data/sources/test_parquet_source.py` |
| 159 | `data/sources/broker_source.py` | 2 | `contracts/data.schema.json` | `tests/unit/data/sources/test_broker_source.py` |
| 160 | `tests/contract/test_data_contract.py` | 11 | `contracts/data.schema.json` | `see tests/` |
| 161 | `strategies/base.py` | 3 | `contracts/signal.schema.json`, `contracts/strategy.schema.json` | `tests/unit/strategies/test_base.py` |
| 162 | `strategies/context.py` | 3 | `contracts/signal.schema.json`, `contracts/strategy.schema.json` | `tests/unit/strategies/test_context.py` |
| 163 | `strategies/models.py` | 3 | `contracts/signal.schema.json`, `contracts/strategy.schema.json` | `tests/unit/strategies/test_models.py` |
| 164 | `strategies/validation.py` | 3 | `contracts/signal.schema.json`, `contracts/strategy.schema.json` | `tests/unit/strategies/test_validation.py` |
| 165 | `tests/contract/test_signal_contract.py` | 10 | `contracts/signal.schema.json` | `see tests/` |
| 166 | `tests/contract/test_trade_contract.py` | 11 | `contracts/trade.schema.json` | `see tests/` |
| 167 | `tests/contract/test_report_contract.py` | 11 | `contracts/report.schema.json` | `see tests/` |
| 168 | `tests/contract/test_run_contract.py` | 11 | `contracts/run.schema.json` | `see tests/` |
| 169 | `backend/app.py` | 7 | `contracts/openapi.yaml` | `tests/unit/backend/test_app.py` |
| 170 | `frontend/src/types/strategy.ts` | 8 | `contracts/openapi.yaml` | `see tests/` |
| 171 | `frontend/src/types/backtest.ts` | 8 | `contracts/openapi.yaml` | `see tests/` |
| 172 | `frontend/src/types/metrics.ts` | 8 | `contracts/openapi.yaml` | `see tests/` |
| 173 | `frontend/src/types/report.ts` | 8 | `contracts/openapi.yaml` | `see tests/` |
| 174 | `frontend/src/api/client.ts` | 8 | `contracts/openapi.yaml` | `see tests/` |
| 175 | `frontend/src/api/strategies.ts` | 8 | `contracts/openapi.yaml` | `see tests/` |
| 176 | `frontend/src/api/backtests.ts` | 8 | `contracts/openapi.yaml` | `see tests/` |
| 177 | `frontend/src/api/reports.ts` | 8 | `contracts/openapi.yaml` | `see tests/` |
| 178 | `frontend/src/api/health.ts` | 8 | `contracts/openapi.yaml` | `see tests/` |
| 179 | `frontend/src/api/validation.ts` | 8 | `contracts/openapi.yaml` | `see tests/` |
| 180 | `frontend/src/api/datasets.ts` | 8 | `contracts/openapi.yaml` | `see tests/` |
| 181 | `frontend/src/api/comparisons.ts` | 8 | `contracts/openapi.yaml` | `see tests/` |
| 182 | `frontend/src/api/audit.ts` | 8 | `contracts/openapi.yaml` | `see tests/` |
| 183 | `tests/contract/test_openapi_contract.py` | 10 | `contracts/openapi.yaml` | `see tests/` |
| 184 | `backend/adapters/go_adapter.py` | 11 | `contracts/openapi.yaml` | `tests/unit/backend/adapters/test_go_adapter.py` |
| 185 | `tests/unit/test_risk.py` | 12 | `risk/manager.py` | `see tests/` |
| 186 | `backend/api/audit.py` | 11 | `persistence/audit.py` | `tests/unit/backend/api/test_audit.py` |
| 187 | `tests/integration/test_api_handlers.py` | 14 | `backend/api/backtests.py` | `see tests/` |
| 188 | `engines/go/internal/validation/validation.go` | 9 | `engines/go/internal/contracts/contracts.go` | `see tests/` |
| 189 | `engines/cpp/src/rolling_stats.cpp` | 9 | `engines/cpp/include/svl/rolling_stats.hpp` | `see tests/` |
| 190 | `engines/rust/tests/rolling_test.rs` | 11 | `engines/rust/src/lib.rs` | `see tests/` |
| 191 | `engines/rust/tests/contract_tests.rs` | 12 | `engines/rust/src/lib.rs` | `see tests/` |
| 192 | `engines/bindings/native.py` | 11 | `engines/reference/rolling_stats.py` | `tests/unit/engines/bindings/test_native.py` |
| 193 | `tests/regression/test_known_results.py` | 12 | `tests/fixtures/expected_results.json` | `see tests/` |
| 194 | `Makefile` | 0 | `scripts/validate_repo.sh` | `see tests/` |
| 195 | `scripts/setup_truemax.sh` | 11 | `scripts/validate_repo.sh` | `see tests/` |
| 196 | `tests/integration/test_blocked_missing_data.py` | 10 | `data/validators.py` | `see tests/` |
| 197 | `tests/unit/test_data.py` | 12 | `data/loaders.py` | `see tests/` |
| 198 | `registry/registry.py` | 3 | `strategies/base.py` | `tests/unit/registry/test_registry.py` |
| 199 | `registry/metadata.py` | 3 | `strategies/base.py` | `tests/unit/registry/test_metadata.py` |
| 200 | `registry/versioning.py` | 3 | `strategies/base.py` | `tests/unit/registry/test_versioning.py` |
| 201 | `registry/compatibility.py` | 3 | `strategies/base.py` | `tests/unit/registry/test_compatibility.py` |
| 202 | `registry/permissions.py` | 3 | `strategies/base.py` | `tests/unit/registry/test_permissions.py` |
| 203 | `registry/lifecycle.py` | 3 | `strategies/base.py` | `tests/unit/registry/test_lifecycle.py` |
| 204 | `registry/storage.py` | 3 | `strategies/base.py` | `tests/unit/registry/test_storage.py` |
| 205 | `strategies/gamma_blast/strategy.py` | 3 | `strategies/base.py`, `strategies/gamma_blast/manifest.yaml` | `tests/unit/strategies/gamma_blast/test_strategy.py` |
| 206 | `strategies/three_pm_momentum/strategy.py` | 3 | `strategies/base.py`, `strategies/three_pm_momentum/manifest.yaml` | `tests/unit/strategies/three_pm_momentum/test_strategy.py` |
| 207 | `backtest/clock.py` | 4 | `data/loaders.py`, `risk/manager.py`, `strategies/base.py` | `tests/unit/backtest/test_clock.py` |
| 208 | `backtest/event_queue.py` | 4 | `data/loaders.py`, `risk/manager.py`, `strategies/base.py` | `tests/unit/backtest/test_event_queue.py` |
| 209 | `backtest/orders.py` | 4 | `data/loaders.py`, `risk/manager.py`, `strategies/base.py` | `tests/unit/backtest/test_orders.py` |
| 210 | `backtest/slippage.py` | 4 | `data/loaders.py`, `risk/manager.py`, `strategies/base.py` | `tests/unit/backtest/test_slippage.py` |
| 211 | `backtest/fees.py` | 4 | `data/loaders.py`, `risk/manager.py`, `strategies/base.py` | `tests/unit/backtest/test_fees.py` |
| 212 | `backtest/fills.py` | 4 | `data/loaders.py`, `risk/manager.py`, `strategies/base.py` | `tests/unit/backtest/test_fills.py` |
| 213 | `backtest/execution.py` | 4 | `data/loaders.py`, `risk/manager.py`, `strategies/base.py` | `tests/unit/backtest/test_execution.py` |
| 214 | `backtest/position_sizing.py` | 4 | `data/loaders.py`, `risk/manager.py`, `strategies/base.py` | `tests/unit/backtest/test_position_sizing.py` |
| 215 | `backtest/stop_manager.py` | 4 | `data/loaders.py`, `risk/manager.py`, `strategies/base.py` | `tests/unit/backtest/test_stop_manager.py` |
| 216 | `backtest/portfolio.py` | 4 | `data/loaders.py`, `risk/manager.py`, `strategies/base.py` | `tests/unit/backtest/test_portfolio.py` |
| 217 | `backtest/accounting.py` | 4 | `data/loaders.py`, `risk/manager.py`, `strategies/base.py` | `tests/unit/backtest/test_accounting.py` |
| 218 | `backtest/results.py` | 4 | `data/loaders.py`, `risk/manager.py`, `strategies/base.py` | `tests/unit/backtest/test_results.py` |
| 219 | `backtest/engine.py` | 4 | `data/loaders.py`, `risk/manager.py`, `strategies/base.py` | `tests/unit/backtest/test_engine.py` |
| 220 | `tests/_helpers.py` | 11 | `data/models.py`, `strategies/base.py` | `see tests/` |
| 221 | `strategies/examples/example_strategy.py` | 12 | `strategies/base.py` | `tests/unit/strategies/examples/test_example_strategy.py` |
| 222 | `tests/integration/test_api.py` | 12 | `backend/app.py` | `see tests/` |
| 223 | `tests/integration/test_api_routes.py` | 14 | `backend/app.py` | `see tests/` |
| 224 | `tests/contract/test_types_vs_contracts.py` | 11 | `frontend/src/types/backtest.ts` | `see tests/` |
| 225 | `frontend/src/pages/dashboard.ts` | 8 | `frontend/src/api/client.ts` | `see tests/` |
| 226 | `frontend/src/pages/strategy-registry.ts` | 8 | `frontend/src/api/client.ts` | `see tests/` |
| 227 | `frontend/src/pages/strategy-detail.ts` | 8 | `frontend/src/api/client.ts` | `see tests/` |
| 228 | `frontend/src/pages/create-strategy.ts` | 8 | `frontend/src/api/client.ts` | `see tests/` |
| 229 | `frontend/src/pages/backtest-runs.ts` | 8 | `frontend/src/api/client.ts` | `see tests/` |
| 230 | `frontend/src/pages/backtest-detail.ts` | 8 | `frontend/src/api/client.ts` | `see tests/` |
| 231 | `frontend/src/pages/validation-results.ts` | 8 | `frontend/src/api/client.ts` | `see tests/` |
| 232 | `frontend/src/pages/comparison.ts` | 8 | `frontend/src/api/client.ts` | `see tests/` |
| 233 | `frontend/src/pages/reports.ts` | 8 | `frontend/src/api/client.ts` | `see tests/` |
| 234 | `frontend/src/pages/datasets.ts` | 8 | `frontend/src/api/client.ts` | `see tests/` |
| 235 | `frontend/src/pages/system-health.ts` | 8 | `frontend/src/api/client.ts` | `see tests/` |
| 236 | `frontend/src/pages/audit-log.ts` | 8 | `frontend/src/api/client.ts` | `see tests/` |
| 237 | `frontend/tests/api.test.ts` | 11 | `frontend/src/api/client.ts` | `see tests/` |
| 238 | `engines/go/cmd/validator/main.go` | 9 | `engines/go/internal/validation/validation.go` | `see tests/` |
| 239 | `engines/go/internal/validation/validation_test.go` | 11 | `engines/go/internal/validation/validation.go` | `see tests/` |
| 240 | `engines/cpp/tests/test_rolling_stats.cpp` | 11 | `engines/cpp/src/rolling_stats.cpp` | `see tests/` |
| 241 | `tests/contract/test_rolling_stats_parity.py` | 11 | `engines/bindings/native.py` | `see tests/` |
| 242 | `backend/services/strategy_service.py` | 7 | `data/loaders.py`, `registry/registry.py` | `tests/unit/backend/services/test_strategy_service.py` |
| 243 | `backend/services/dataset_service.py` | 7 | `data/loaders.py`, `registry/registry.py` | `tests/unit/backend/services/test_dataset_service.py` |
| 244 | `backend/services/backtest_service.py` | 7 | `data/loaders.py`, `registry/registry.py` | `tests/unit/backend/services/test_backtest_service.py` |
| 245 | `backend/services/validation_service.py` | 7 | `data/loaders.py`, `registry/registry.py` | `tests/unit/backend/services/test_validation_service.py` |
| 246 | `backend/services/report_service.py` | 7 | `data/loaders.py`, `registry/registry.py` | `tests/unit/backend/services/test_report_service.py` |
| 247 | `backend/dependencies.py` | 11 | `persistence/repositories.py`, `registry/registry.py` | `tests/unit/backend/test_dependencies.py` |
| 248 | `tests/unit/test_registry.py` | 12 | `registry/registry.py` | `see tests/` |
| 249 | `validation/leakage_checks.py` | 5 | `backtest/results.py` | `tests/unit/validation/test_leakage_checks.py` |
| 250 | `validation/out_of_sample.py` | 5 | `backtest/results.py` | `tests/unit/validation/test_out_of_sample.py` |
| 251 | `validation/walk_forward.py` | 5 | `backtest/results.py` | `tests/unit/validation/test_walk_forward.py` |
| 252 | `validation/cross_validation.py` | 5 | `backtest/results.py` | `tests/unit/validation/test_cross_validation.py` |
| 253 | `validation/overfitting.py` | 5 | `backtest/results.py` | `tests/unit/validation/test_overfitting.py` |
| 254 | `validation/robustness.py` | 5 | `backtest/results.py` | `tests/unit/validation/test_robustness.py` |
| 255 | `validation/regime_analysis.py` | 5 | `backtest/results.py` | `tests/unit/validation/test_regime_analysis.py` |
| 256 | `validation/statistical_confidence.py` | 5 | `backtest/results.py` | `tests/unit/validation/test_statistical_confidence.py` |
| 257 | `validation/pipeline.py` | 5 | `backtest/results.py` | `tests/unit/validation/test_pipeline.py` |
| 258 | `metrics/accuracy.py` | 5 | `backtest/results.py` | `tests/unit/metrics/test_accuracy.py` |
| 259 | `metrics/expectancy.py` | 5 | `backtest/results.py` | `tests/unit/metrics/test_expectancy.py` |
| 260 | `metrics/trade_metrics.py` | 5 | `backtest/results.py` | `tests/unit/metrics/test_trade_metrics.py` |
| 261 | `metrics/risk_metrics.py` | 5 | `backtest/results.py` | `tests/unit/metrics/test_risk_metrics.py` |
| 262 | `metrics/return_metrics.py` | 5 | `backtest/results.py` | `tests/unit/metrics/test_return_metrics.py` |
| 263 | `metrics/benchmarks.py` | 5 | `backtest/results.py` | `tests/unit/metrics/test_benchmarks.py` |
| 264 | `metrics/confidence_intervals.py` | 5 | `backtest/results.py` | `tests/unit/metrics/test_confidence_intervals.py` |
| 265 | `backend/jobs/queue.py` | 7 | `backtest/engine.py` | `tests/unit/backend/jobs/test_queue.py` |
| 266 | `backend/jobs/worker.py` | 7 | `backtest/engine.py` | `tests/unit/backend/jobs/test_worker.py` |
| 267 | `backend/jobs/job_status.py` | 7 | `backtest/engine.py` | `tests/unit/backend/jobs/test_job_status.py` |
| 268 | `tests/integration/test_end_to_end_backtest.py` | 10 | `backtest/engine.py` | `see tests/` |
| 269 | `tests/unit/test_backtest.py` | 12 | `backtest/engine.py` | `see tests/` |
| 270 | `tests/integration/test_strategy_pipeline.py` | 12 | `backtest/engine.py` | `see tests/` |
| 271 | `tests/property/test_accounting_invariants.py` | 12 | `backtest/engine.py` | `see tests/` |
| 272 | `tests/performance/test_benchmark.py` | 12 | `backtest/engine.py` | `see tests/` |
| 273 | `tests/test_no_lookahead.py` | 12 | `backtest/engine.py` | `see tests/` |
| 274 | `tests/test_reproducibility.py` | 12 | `backtest/engine.py` | `see tests/` |
| 275 | `tests/test_execution_costs.py` | 12 | `backtest/engine.py` | `see tests/` |
| 276 | `frontend/src/main.ts` | 8 | `frontend/src/pages/dashboard.ts` | `see tests/` |
| 277 | `frontend/src/app.ts` | 8 | `frontend/src/pages/dashboard.ts` | `see tests/` |
| 278 | `tests/unit/test_config.py` | 12 | `backend/services/backtest_service.py` | `see tests/` |
| 279 | `backend/services/comparison_service.py` | 14 | `backend/services/report_service.py` | `tests/unit/backend/services/test_comparison_service.py` |
| 280 | `optimization/parameter_search.py` | 5 | `validation/pipeline.py` | `tests/unit/optimization/test_parameter_search.py` |
| 281 | `optimization/constraints.py` | 5 | `validation/pipeline.py` | `tests/unit/optimization/test_constraints.py` |
| 282 | `optimization/experiment_tracking.py` | 5 | `validation/pipeline.py` | `tests/unit/optimization/test_experiment_tracking.py` |
| 283 | `reporting/html_report.py` | 6 | `contracts/report.schema.json`, `metrics/return_metrics.py` | `tests/unit/reporting/test_html_report.py` |
| 284 | `reporting/json_report.py` | 6 | `contracts/report.schema.json`, `metrics/return_metrics.py` | `tests/unit/reporting/test_json_report.py` |
| 285 | `reporting/csv_export.py` | 6 | `contracts/report.schema.json`, `metrics/return_metrics.py` | `tests/unit/reporting/test_csv_export.py` |
| 286 | `reporting/charts.py` | 6 | `contracts/report.schema.json`, `metrics/return_metrics.py` | `tests/unit/reporting/test_charts.py` |
| 287 | `reporting/generator.py` | 6 | `contracts/report.schema.json`, `metrics/return_metrics.py` | `tests/unit/reporting/test_generator.py` |
| 288 | `tests/unit/test_metrics.py` | 12 | `metrics/return_metrics.py` | `see tests/` |
| 289 | `frontend/index.html` | 8 | `frontend/src/main.ts` | `see tests/` |
| 290 | `tests/integration/test_optimization_flow.py` | 13 | `optimization/parameter_search.py` | `see tests/` |
| 291 | `tests/integration/test_report_pipeline.py` | 12 | `reporting/generator.py` | `see tests/` |

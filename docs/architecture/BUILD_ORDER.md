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
| 74 | `scripts/validate_repo.sh` | 0 | `pyproject.toml` | `see tests/` |
| 75 | `tests/contract/test_strategy_contract.py` | 11 | `contracts/strategy.schema.json` | `see tests/` |
| 76 | `data/models.py` | 2 | `contracts/data.schema.json` | `tests/unit/data/test_models.py` |
| 77 | `data/timestamps.py` | 2 | `contracts/data.schema.json` | `tests/unit/data/test_timestamps.py` |
| 78 | `data/normalizer.py` | 2 | `contracts/data.schema.json` | `tests/unit/data/test_normalizer.py` |
| 79 | `data/validators.py` | 2 | `contracts/data.schema.json` | `tests/unit/data/test_validators.py` |
| 80 | `data/corporate_actions.py` | 2 | `contracts/data.schema.json` | `tests/unit/data/test_corporate_actions.py` |
| 81 | `data/survivorship.py` | 2 | `contracts/data.schema.json` | `tests/unit/data/test_survivorship.py` |
| 82 | `data/quality_report.py` | 2 | `contracts/data.schema.json` | `tests/unit/data/test_quality_report.py` |
| 83 | `data/storage.py` | 2 | `contracts/data.schema.json` | `tests/unit/data/test_storage.py` |
| 84 | `data/loaders.py` | 2 | `contracts/data.schema.json` | `tests/unit/data/test_loaders.py` |
| 85 | `data/sources/csv_source.py` | 2 | `contracts/data.schema.json` | `tests/unit/data/sources/test_csv_source.py` |
| 86 | `data/sources/parquet_source.py` | 2 | `contracts/data.schema.json` | `tests/unit/data/sources/test_parquet_source.py` |
| 87 | `data/sources/broker_source.py` | 2 | `contracts/data.schema.json` | `tests/unit/data/sources/test_broker_source.py` |
| 88 | `tests/contract/test_data_contract.py` | 11 | `contracts/data.schema.json` | `see tests/` |
| 89 | `strategies/base.py` | 3 | `contracts/signal.schema.json`, `contracts/strategy.schema.json` | `tests/unit/strategies/test_base.py` |
| 90 | `strategies/context.py` | 3 | `contracts/signal.schema.json`, `contracts/strategy.schema.json` | `tests/unit/strategies/test_context.py` |
| 91 | `strategies/models.py` | 3 | `contracts/signal.schema.json`, `contracts/strategy.schema.json` | `tests/unit/strategies/test_models.py` |
| 92 | `strategies/validation.py` | 3 | `contracts/signal.schema.json`, `contracts/strategy.schema.json` | `tests/unit/strategies/test_validation.py` |
| 93 | `tests/contract/test_signal_contract.py` | 10 | `contracts/signal.schema.json` | `see tests/` |
| 94 | `tests/contract/test_trade_contract.py` | 11 | `contracts/trade.schema.json` | `see tests/` |
| 95 | `tests/contract/test_report_contract.py` | 11 | `contracts/report.schema.json` | `see tests/` |
| 96 | `tests/contract/test_run_contract.py` | 11 | `contracts/run.schema.json` | `see tests/` |
| 97 | `backend/app.py` | 7 | `contracts/openapi.yaml` | `tests/unit/backend/test_app.py` |
| 98 | `frontend/src/types/strategy.ts` | 8 | `contracts/openapi.yaml` | `see tests/` |
| 99 | `frontend/src/types/backtest.ts` | 8 | `contracts/openapi.yaml` | `see tests/` |
| 100 | `frontend/src/types/metrics.ts` | 8 | `contracts/openapi.yaml` | `see tests/` |
| 101 | `frontend/src/types/report.ts` | 8 | `contracts/openapi.yaml` | `see tests/` |
| 102 | `frontend/src/api/client.ts` | 8 | `contracts/openapi.yaml` | `see tests/` |
| 103 | `frontend/src/api/strategies.ts` | 8 | `contracts/openapi.yaml` | `see tests/` |
| 104 | `frontend/src/api/backtests.ts` | 8 | `contracts/openapi.yaml` | `see tests/` |
| 105 | `frontend/src/api/reports.ts` | 8 | `contracts/openapi.yaml` | `see tests/` |
| 106 | `frontend/src/api/health.ts` | 8 | `contracts/openapi.yaml` | `see tests/` |
| 107 | `frontend/src/api/validation.ts` | 8 | `contracts/openapi.yaml` | `see tests/` |
| 108 | `frontend/src/api/datasets.ts` | 8 | `contracts/openapi.yaml` | `see tests/` |
| 109 | `frontend/src/api/comparisons.ts` | 8 | `contracts/openapi.yaml` | `see tests/` |
| 110 | `frontend/src/api/audit.ts` | 8 | `contracts/openapi.yaml` | `see tests/` |
| 111 | `tests/contract/test_openapi_contract.py` | 10 | `contracts/openapi.yaml` | `see tests/` |
| 112 | `backend/adapters/go_adapter.py` | 11 | `contracts/openapi.yaml` | `tests/unit/backend/adapters/test_go_adapter.py` |
| 113 | `backend/api/audit.py` | 11 | `persistence/audit.py` | `tests/unit/backend/api/test_audit.py` |
| 114 | `engines/go/internal/validation/validation.go` | 9 | `engines/go/internal/contracts/contracts.go` | `see tests/` |
| 115 | `engines/cpp/src/rolling_stats.cpp` | 9 | `engines/cpp/include/svl/rolling_stats.hpp` | `see tests/` |
| 116 | `engines/rust/tests/rolling_test.rs` | 11 | `engines/rust/src/lib.rs` | `see tests/` |
| 117 | `engines/bindings/native.py` | 11 | `engines/reference/rolling_stats.py` | `tests/unit/engines/bindings/test_native.py` |
| 118 | `Makefile` | 0 | `scripts/validate_repo.sh` | `see tests/` |
| 119 | `scripts/setup_truemax.sh` | 11 | `scripts/validate_repo.sh` | `see tests/` |
| 120 | `tests/integration/test_blocked_missing_data.py` | 10 | `data/validators.py` | `see tests/` |
| 121 | `registry/registry.py` | 3 | `strategies/base.py` | `tests/unit/registry/test_registry.py` |
| 122 | `registry/metadata.py` | 3 | `strategies/base.py` | `tests/unit/registry/test_metadata.py` |
| 123 | `registry/versioning.py` | 3 | `strategies/base.py` | `tests/unit/registry/test_versioning.py` |
| 124 | `registry/compatibility.py` | 3 | `strategies/base.py` | `tests/unit/registry/test_compatibility.py` |
| 125 | `registry/permissions.py` | 3 | `strategies/base.py` | `tests/unit/registry/test_permissions.py` |
| 126 | `registry/lifecycle.py` | 3 | `strategies/base.py` | `tests/unit/registry/test_lifecycle.py` |
| 127 | `registry/storage.py` | 3 | `strategies/base.py` | `tests/unit/registry/test_storage.py` |
| 128 | `strategies/gamma_blast/strategy.py` | 3 | `strategies/base.py`, `strategies/gamma_blast/manifest.yaml` | `tests/unit/strategies/gamma_blast/test_strategy.py` |
| 129 | `strategies/three_pm_momentum/strategy.py` | 3 | `strategies/base.py`, `strategies/three_pm_momentum/manifest.yaml` | `tests/unit/strategies/three_pm_momentum/test_strategy.py` |
| 130 | `backtest/clock.py` | 4 | `data/loaders.py`, `risk/manager.py`, `strategies/base.py` | `tests/unit/backtest/test_clock.py` |
| 131 | `backtest/event_queue.py` | 4 | `data/loaders.py`, `risk/manager.py`, `strategies/base.py` | `tests/unit/backtest/test_event_queue.py` |
| 132 | `backtest/orders.py` | 4 | `data/loaders.py`, `risk/manager.py`, `strategies/base.py` | `tests/unit/backtest/test_orders.py` |
| 133 | `backtest/slippage.py` | 4 | `data/loaders.py`, `risk/manager.py`, `strategies/base.py` | `tests/unit/backtest/test_slippage.py` |
| 134 | `backtest/fees.py` | 4 | `data/loaders.py`, `risk/manager.py`, `strategies/base.py` | `tests/unit/backtest/test_fees.py` |
| 135 | `backtest/fills.py` | 4 | `data/loaders.py`, `risk/manager.py`, `strategies/base.py` | `tests/unit/backtest/test_fills.py` |
| 136 | `backtest/execution.py` | 4 | `data/loaders.py`, `risk/manager.py`, `strategies/base.py` | `tests/unit/backtest/test_execution.py` |
| 137 | `backtest/position_sizing.py` | 4 | `data/loaders.py`, `risk/manager.py`, `strategies/base.py` | `tests/unit/backtest/test_position_sizing.py` |
| 138 | `backtest/stop_manager.py` | 4 | `data/loaders.py`, `risk/manager.py`, `strategies/base.py` | `tests/unit/backtest/test_stop_manager.py` |
| 139 | `backtest/portfolio.py` | 4 | `data/loaders.py`, `risk/manager.py`, `strategies/base.py` | `tests/unit/backtest/test_portfolio.py` |
| 140 | `backtest/accounting.py` | 4 | `data/loaders.py`, `risk/manager.py`, `strategies/base.py` | `tests/unit/backtest/test_accounting.py` |
| 141 | `backtest/results.py` | 4 | `data/loaders.py`, `risk/manager.py`, `strategies/base.py` | `tests/unit/backtest/test_results.py` |
| 142 | `backtest/engine.py` | 4 | `data/loaders.py`, `risk/manager.py`, `strategies/base.py` | `tests/unit/backtest/test_engine.py` |
| 143 | `tests/_helpers.py` | 11 | `data/models.py`, `strategies/base.py` | `see tests/` |
| 144 | `tests/contract/test_types_vs_contracts.py` | 11 | `frontend/src/types/backtest.ts` | `see tests/` |
| 145 | `frontend/src/pages/dashboard.ts` | 8 | `frontend/src/api/client.ts` | `see tests/` |
| 146 | `frontend/src/pages/strategy-registry.ts` | 8 | `frontend/src/api/client.ts` | `see tests/` |
| 147 | `frontend/src/pages/strategy-detail.ts` | 8 | `frontend/src/api/client.ts` | `see tests/` |
| 148 | `frontend/src/pages/create-strategy.ts` | 8 | `frontend/src/api/client.ts` | `see tests/` |
| 149 | `frontend/src/pages/backtest-runs.ts` | 8 | `frontend/src/api/client.ts` | `see tests/` |
| 150 | `frontend/src/pages/backtest-detail.ts` | 8 | `frontend/src/api/client.ts` | `see tests/` |
| 151 | `frontend/src/pages/validation-results.ts` | 8 | `frontend/src/api/client.ts` | `see tests/` |
| 152 | `frontend/src/pages/comparison.ts` | 8 | `frontend/src/api/client.ts` | `see tests/` |
| 153 | `frontend/src/pages/reports.ts` | 8 | `frontend/src/api/client.ts` | `see tests/` |
| 154 | `frontend/src/pages/datasets.ts` | 8 | `frontend/src/api/client.ts` | `see tests/` |
| 155 | `frontend/src/pages/system-health.ts` | 8 | `frontend/src/api/client.ts` | `see tests/` |
| 156 | `frontend/src/pages/audit-log.ts` | 8 | `frontend/src/api/client.ts` | `see tests/` |
| 157 | `frontend/tests/api.test.ts` | 11 | `frontend/src/api/client.ts` | `see tests/` |
| 158 | `engines/go/cmd/validator/main.go` | 9 | `engines/go/internal/validation/validation.go` | `see tests/` |
| 159 | `engines/go/internal/validation/validation_test.go` | 11 | `engines/go/internal/validation/validation.go` | `see tests/` |
| 160 | `engines/cpp/tests/test_rolling_stats.cpp` | 11 | `engines/cpp/src/rolling_stats.cpp` | `see tests/` |
| 161 | `tests/contract/test_rolling_stats_parity.py` | 11 | `engines/bindings/native.py` | `see tests/` |
| 162 | `backend/services/strategy_service.py` | 7 | `data/loaders.py`, `registry/registry.py` | `tests/unit/backend/services/test_strategy_service.py` |
| 163 | `backend/services/dataset_service.py` | 7 | `data/loaders.py`, `registry/registry.py` | `tests/unit/backend/services/test_dataset_service.py` |
| 164 | `backend/services/backtest_service.py` | 7 | `data/loaders.py`, `registry/registry.py` | `tests/unit/backend/services/test_backtest_service.py` |
| 165 | `backend/services/validation_service.py` | 7 | `data/loaders.py`, `registry/registry.py` | `tests/unit/backend/services/test_validation_service.py` |
| 166 | `backend/services/report_service.py` | 7 | `data/loaders.py`, `registry/registry.py` | `tests/unit/backend/services/test_report_service.py` |
| 167 | `backend/dependencies.py` | 11 | `persistence/repositories.py`, `registry/registry.py` | `tests/unit/backend/test_dependencies.py` |
| 168 | `validation/leakage_checks.py` | 5 | `backtest/results.py` | `tests/unit/validation/test_leakage_checks.py` |
| 169 | `validation/out_of_sample.py` | 5 | `backtest/results.py` | `tests/unit/validation/test_out_of_sample.py` |
| 170 | `validation/walk_forward.py` | 5 | `backtest/results.py` | `tests/unit/validation/test_walk_forward.py` |
| 171 | `validation/cross_validation.py` | 5 | `backtest/results.py` | `tests/unit/validation/test_cross_validation.py` |
| 172 | `validation/overfitting.py` | 5 | `backtest/results.py` | `tests/unit/validation/test_overfitting.py` |
| 173 | `validation/robustness.py` | 5 | `backtest/results.py` | `tests/unit/validation/test_robustness.py` |
| 174 | `validation/regime_analysis.py` | 5 | `backtest/results.py` | `tests/unit/validation/test_regime_analysis.py` |
| 175 | `validation/statistical_confidence.py` | 5 | `backtest/results.py` | `tests/unit/validation/test_statistical_confidence.py` |
| 176 | `validation/pipeline.py` | 5 | `backtest/results.py` | `tests/unit/validation/test_pipeline.py` |
| 177 | `metrics/accuracy.py` | 5 | `backtest/results.py` | `tests/unit/metrics/test_accuracy.py` |
| 178 | `metrics/expectancy.py` | 5 | `backtest/results.py` | `tests/unit/metrics/test_expectancy.py` |
| 179 | `metrics/trade_metrics.py` | 5 | `backtest/results.py` | `tests/unit/metrics/test_trade_metrics.py` |
| 180 | `metrics/risk_metrics.py` | 5 | `backtest/results.py` | `tests/unit/metrics/test_risk_metrics.py` |
| 181 | `metrics/return_metrics.py` | 5 | `backtest/results.py` | `tests/unit/metrics/test_return_metrics.py` |
| 182 | `metrics/benchmarks.py` | 5 | `backtest/results.py` | `tests/unit/metrics/test_benchmarks.py` |
| 183 | `metrics/confidence_intervals.py` | 5 | `backtest/results.py` | `tests/unit/metrics/test_confidence_intervals.py` |
| 184 | `backend/jobs/queue.py` | 7 | `backtest/engine.py` | `tests/unit/backend/jobs/test_queue.py` |
| 185 | `backend/jobs/worker.py` | 7 | `backtest/engine.py` | `tests/unit/backend/jobs/test_worker.py` |
| 186 | `backend/jobs/job_status.py` | 7 | `backtest/engine.py` | `tests/unit/backend/jobs/test_job_status.py` |
| 187 | `tests/integration/test_end_to_end_backtest.py` | 10 | `backtest/engine.py` | `see tests/` |
| 188 | `frontend/src/main.ts` | 8 | `frontend/src/pages/dashboard.ts` | `see tests/` |
| 189 | `frontend/src/app.ts` | 8 | `frontend/src/pages/dashboard.ts` | `see tests/` |
| 190 | `optimization/parameter_search.py` | 5 | `validation/pipeline.py` | `tests/unit/optimization/test_parameter_search.py` |
| 191 | `optimization/constraints.py` | 5 | `validation/pipeline.py` | `tests/unit/optimization/test_constraints.py` |
| 192 | `optimization/experiment_tracking.py` | 5 | `validation/pipeline.py` | `tests/unit/optimization/test_experiment_tracking.py` |
| 193 | `reporting/html_report.py` | 6 | `contracts/report.schema.json`, `metrics/return_metrics.py` | `tests/unit/reporting/test_html_report.py` |
| 194 | `reporting/json_report.py` | 6 | `contracts/report.schema.json`, `metrics/return_metrics.py` | `tests/unit/reporting/test_json_report.py` |
| 195 | `reporting/csv_export.py` | 6 | `contracts/report.schema.json`, `metrics/return_metrics.py` | `tests/unit/reporting/test_csv_export.py` |
| 196 | `reporting/charts.py` | 6 | `contracts/report.schema.json`, `metrics/return_metrics.py` | `tests/unit/reporting/test_charts.py` |
| 197 | `reporting/generator.py` | 6 | `contracts/report.schema.json`, `metrics/return_metrics.py` | `tests/unit/reporting/test_generator.py` |
| 198 | `frontend/index.html` | 8 | `frontend/src/main.ts` | `see tests/` |

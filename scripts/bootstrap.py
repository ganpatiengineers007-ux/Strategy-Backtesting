#!/usr/bin/env python3
"""
strategy-validation-lab : Wiring Map Scaffold Generator (v2.1)

Usage:
  python bootstrap.py --plan               # phases ki list + file counts
  python bootstrap.py --all                # saari files ek saath
  python bootstrap.py --phase 4            # sirf ek phase
  python bootstrap.py --phase 2 --phase 3  # kai phases
  python bootstrap.py --all --dry-run      # kuch likhe bina dikhao
  python bootstrap.py --all --force        # existing files overwrite
  python bootstrap.py --verify             # wiring check: files + dependencies
  python bootstrap.py --test               # generated repo ke tests chalao (pytest chahiye)

v6: Phase 15 (baaki 22 stubs me asli code, isolation, background worker, proto, registry gates, options checks).
v5.1: test_api route check openapi()-based (naye FastAPI ke liye).
v5: Phase 13 (analysis+optimization) + Phase 14 (API, services, SQLite, frontend pages).
v4: Phase 12 (docs, config yaml, indicators, observability, infra, CI) bhi shamil.
v3: Phase 11 (missing files) + asli chalne wala code (data, backtest, risk, validation,
metrics, reporting, jobs, CLI, contracts) ek hi run me. Sirf Python stdlib.
  python bootstrap.py --root my-dir        # output folder (default: strategy-validation-lab)

Har file me header hota hai: PURPOSE, DEPENDS_ON, TEST. Python module ke liye
tests/unit/... me import-test auto banta hai. Isse BUILD_ORDER.md aur
WIRING_MAP.json bhi generate hote hain (dependency topological order me).
"""
import argparse, json, sys
from graphlib import TopologicalSorter
from pathlib import Path

# ----------------------------------------------------------------- helpers
def many(prefix, spec, deps=()):
    """'a:purpose;b:purpose' -> [(prefix/a.ext, purpose, deps)]"""
    out = []
    for item in spec.split(";"):
        name, purpose = (x.strip() for x in item.split(":", 1))
        out.append((f"{prefix}{name}", purpose, list(deps)))
    return out

def _ext(p, spec, d, ext):
    return many(p, ";".join(f"{i.split(':',1)[0].strip()}.{ext}:{i.split(':',1)[1].strip()}" for i in spec.split(";")), d)

PY = lambda p, s, d=(): _ext(p, s, d, "py")
TS = lambda p, s, d=(): _ext(p, s, d, "ts")

# ----------------------------------------------------------------- PHASES
PHASES = []

# Phase 0 -------------------------------------------------------------
PHASES.append((0, "Foundation: repo root, scripts, docs", [
    ("README.md", "Project overview aur quick start", []),
    ("pyproject.toml", "Python build, lint, type-check, pytest config", []),
    (".gitignore", "Ignore rules", []),
    ("Makefile", "make validate / make test shortcuts", ["scripts/validate_repo.sh"]),
    ("scripts/validate_repo.sh", "Format, lint, type check, build, test ek jagah", ["pyproject.toml"]),
    ("docs/architecture/ADR-0001-language-ownership.md", "Kaun-sa module kis bhasha me (Python/Go/C++/Rust)", []),
    ("docs/architecture/wiring-map.md", "Is blueprint ki copy", []),
    ("docs/architecture/build-order.md", "Build & Dependency Map", []),
]))

# Phase 1 -------------------------------------------------------------
PHASES.append((1, "Contracts: schemas, OpenAPI, proto", (
    many("contracts/", "strategy.schema.json:Strategy manifest contract;data.schema.json:Dataset metadata contract;"
         "signal.schema.json:Signal contract;trade.schema.json:Trade record contract;"
         "report.schema.json:Report contract;run.schema.json:Backtest run contract;"
         "openapi.yaml:Frontend-Backend HTTP contract")
    + many("contracts/proto/", "common.proto:Shared types;market_data.proto:Market data messages;"
           "strategy.proto:Strategy messages;signal.proto:Signal messages;backtest.proto:Backtest messages;"
           "metrics.proto:Metrics messages;report.proto:Report messages")
)))

# Phase 2 -------------------------------------------------------------
_c = ["contracts/data.schema.json"]
PHASES.append((2, "Data Engine", (
    PY("data/", "models:Dataset aur bar/tick data models;timestamps:Timezone aur timestamp normalisation;"
       "normalizer:Source data ko common schema me lana;validators:Schema, gap, duplicate, OHLC checks;"
       "corporate_actions:Split/dividend adjustments;survivorship:Survivorship bias checks;"
       "quality_report:Quality status (PASS/WARN/BLOCKED);storage:Parquet + repository storage;"
       "loaders:Entry point: source chuno, load, normalize, validate", _c)
    + PY("data/sources/", "csv_source:CSV reader;parquet_source:Parquet reader;broker_source:Broker API reader", _c)
)))

# Phase 3 -------------------------------------------------------------
PHASES.append((3, "Strategy Interface + Registry", (
    PY("strategies/", "base:Strategy abstract interface;context:Strategy ko milne wala market context;"
       "models:Signal/Decision models;validation:Manifest + data requirement check",
       ["contracts/strategy.schema.json", "contracts/signal.schema.json"])
    + PY("registry/", "registry:Strategy registry entry point;metadata:Strategy metadata;"
         "versioning:Version + source hash;compatibility:Engine/contract compatibility;"
         "permissions:Kaun kya chala sakta hai;lifecycle:DRAFT->VALIDATED->APPROVED states;"
         "storage:Registry persistence", ["strategies/base.py"])
    + [("strategies/gamma_blast/manifest.yaml", "GammaBlast ID, version, params, data needs", []),
       ("strategies/gamma_blast/strategy.py", "GammaBlastStrategy", ["strategies/base.py", "strategies/gamma_blast/manifest.yaml"]),
       ("strategies/three_pm_momentum/manifest.yaml", "ThreePMMomentum manifest", []),
       ("strategies/three_pm_momentum/strategy.py", "ThreePMMomentumStrategy", ["strategies/base.py", "strategies/three_pm_momentum/manifest.yaml"])]
)))

# Phase 4 -------------------------------------------------------------
_b = ["strategies/base.py", "data/loaders.py"]
PHASES.append((4, "Backtest Engine + Risk", (
    PY("risk/", "limits:Position/loss limits;exposure:Exposure calc;drawdown:Drawdown tracking;"
       "kill_switch:Emergency stop;manager:Risk entry point (engine ke liye interface)")
    + PY("backtest/", "clock:Simulated time;event_queue:Market event queue;orders:Order models;"
         "slippage:Slippage models;fees:Fee models;fills:Fill rules (SL+Target same candle = conservative);"
         "execution:Slippage+fees+fills combine;position_sizing:Size calc;stop_manager:Stop/target handling;"
         "portfolio:Positions/cash;accounting:Equity, PnL;results:Trades+equity output;"
         "engine:Backtest entry point", _b + ["risk/manager.py"])
)))

# Phase 5 -------------------------------------------------------------
_r = ["backtest/results.py"]
PHASES.append((5, "Validation, Metrics, Optimization", (
    PY("validation/", "leakage_checks:Look-ahead leakage;out_of_sample:OOS test;walk_forward:Walk-forward;"
       "cross_validation:Time-series CV;overfitting:Overfit detection;robustness:Param sensitivity;"
       "regime_analysis:Regime-wise performance;statistical_confidence:Significance tests;"
       "pipeline:Saare checks ka order, PASS/FAIL/UNAVAILABLE", _r)
    + PY("metrics/", "accuracy:Win rate etc.;expectancy:Expectancy;trade_metrics:Trade stats;"
         "risk_metrics:Sharpe, DD;return_metrics:Returns;benchmarks:Benchmark compare;"
         "confidence_intervals:Bootstrap CI", _r)
    + PY("optimization/", "parameter_search:Param search;constraints:Search constraints;"
         "experiment_tracking:Experiment log", ["validation/pipeline.py"])
)))

# Phase 6 -------------------------------------------------------------
PHASES.append((6, "Reporting + Persistence", (
    PY("persistence/", "database:PostgreSQL connection;models:ORM models;repositories:Data access;audit:Audit log")
    + PY("reporting/", "html_report:HTML report;json_report:JSON report;csv_export:CSV export;charts:Chart images/data;"
         "generator:Reporting entry point", ["metrics/return_metrics.py", "contracts/report.schema.json"])
    + [("reporting/templates/report.html", "Report HTML template", [])]
)))

# Phase 7 -------------------------------------------------------------
PHASES.append((7, "Backend API, Services, Jobs, CLI", (
    [("backend/app.py", "Backend entry point", ["contracts/openapi.yaml"])]
    + PY("backend/middleware/", "request_id:Request ID;error_handler:Common errors;authentication:Auth")
    + PY("backend/api/", "health:/health;strategies:/strategies;datasets:/datasets;backtests:/backtests;"
         "validation:/validations;comparisons:/comparisons;reports:/reports")
    + PY("backend/services/", "strategy_service:Registry se;dataset_service:Data engine se;"
         "backtest_service:Engine + job queue;validation_service:Validation pipeline;"
         "report_service:Reporting generator", ["registry/registry.py", "data/loaders.py"])
    + PY("backend/schemas/", "backtest:Request/response models;strategy:Strategy schemas;report:Report schemas")
    + PY("backend/jobs/", "queue:Job queue;worker:Worker;job_status:QUEUED/RUNNING/SUCCEEDED/FAILED", ["backtest/engine.py"])
    + PY("cli/", "main:CLI entry;commands:Commands")
)))

# Phase 8 -------------------------------------------------------------
_t = ["contracts/openapi.yaml"]
PHASES.append((8, "Frontend", (
    [("frontend/index.html", "Web page entry", ["frontend/src/main.ts"]),
     ("frontend/package.json", "Frontend deps", []),
     ("frontend/tsconfig.json", "TS config", [])]
    + TS("frontend/src/", "main:Frontend start;app:Routing aur page assembly", ["frontend/src/pages/dashboard.ts"])
    + TS("frontend/src/types/", "strategy:Strategy types;backtest:Backtest types;metrics:Metrics types;report:Report types", _t)
    + TS("frontend/src/api/", "client:HTTP client;strategies:/strategies;backtests:/backtests;reports:/reports;"
         "health:/health;validation:/validations;datasets:/datasets;comparisons:/comparisons;audit:Audit", _t)
    + TS("frontend/src/components/", "navigation:Nav;data-table:Tables;metric-card:Metric card;chart-panel:Charts;"
         "status-badge:Status;error-panel:Errors")
    + TS("frontend/src/components/charts/", "equity-curve:Equity;drawdown-chart:Drawdown;"
         "monthly-returns:Monthly;trade-distribution:Trades")
    + TS("frontend/src/pages/", "dashboard:Dashboard;strategy-registry:Registry;strategy-detail:Detail;"
         "create-strategy:Create;backtest-runs:Runs;backtest-detail:Run detail;validation-results:Validation;"
         "comparison:Compare;reports:Reports;datasets:Datasets;system-health:Health;audit-log:Audit",
         ["frontend/src/api/client.ts"])
)))

# Phase 9 -------------------------------------------------------------
PHASES.append((9, "Go / C++ / Rust engines", [
    ("engines/go/go.mod", "Go module", []),
    ("engines/go/cmd/validator/main.go", "Go service entry", ["engines/go/internal/validation/validation.go"]),
    ("engines/go/internal/contracts/contracts.go", "Contract types", []),
    ("engines/go/internal/validation/validation.go", "Validation logic", ["engines/go/internal/contracts/contracts.go"]),
    ("engines/go/internal/jobs/jobs.go", "Jobs", []),
    ("engines/go/internal/observability/observability.go", "Logging/metrics", []),
    ("engines/cpp/include/svl/rolling_stats.hpp", "C++ public interface", []),
    ("engines/cpp/src/rolling_stats.cpp", "Rolling stats", ["engines/cpp/include/svl/rolling_stats.hpp"]),
    ("engines/cpp/CMakeLists.txt", "C++ build", []),
    ("engines/rust/Cargo.toml", "Rust crate", []),
    ("engines/rust/src/lib.rs", "Rust library interface", []),
]))

# Phase 10 ------------------------------------------------------------
PHASES.append((10, "Tests (contract + integration)", [
    ("tests/contract/test_signal_contract.py", "signal.schema <-> models/orders/types", ["contracts/signal.schema.json"]),
    ("tests/contract/test_openapi_contract.py", "openapi <-> backend schemas", ["contracts/openapi.yaml"]),
    ("tests/integration/test_end_to_end_backtest.py", "Data -> engine -> validation -> report", ["backtest/engine.py"]),
    ("tests/integration/test_blocked_missing_data.py", "Missing option chain => BLOCKED", ["data/validators.py"]),
]))

# ================================================================= PHASE 11 + REAL CODE
# OVERRIDES: stub ki jagah asli, chalne wala code. Sirf stdlib (koi pip dependency nahi).
OVERRIDES = {}

def O(path, text):
    OVERRIDES[path] = text.lstrip("\n")

def _schema(title, props, required=None):
    return json.dumps({
        "$schema": "https://json-schema.org/draft/2020-12/schema", "title": title, "type": "object",
        "properties": {k: {"type": v} for k, v in props.items()},
        "required": list(props) if required is None else required}, indent=2) + "\n"

PHASES.append((11, "Missing files: config, bindings, adapters, engine tests, contract tests, runbook", [
    ("config/risk_policy.json", "Risk limits + on_violation policy", []),
    ("config/execution_defaults.json", "Capital, slippage, fees, ambiguous-candle rule", []),
    ("contracts/schema_check.py", "Chhota JSON-schema checker (required + types) contract tests ke liye", []),
    ("backend/dependencies.py", "Shared registry/repository providers", ["registry/registry.py", "persistence/repositories.py"]),
    ("backend/api/audit.py", "Audit log read API", ["persistence/audit.py"]),
    ("backend/adapters/go_adapter.py", "Python -> Go validator service client", ["contracts/openapi.yaml"]),
    ("engines/reference/rolling_stats.py", "Python reference rolling mean (native parity ka standard)", []),
    ("engines/bindings/native.py", "Native (C++/Rust) ya Python fallback ka single interface", ["engines/reference/rolling_stats.py"]),
    ("engines/go/internal/validation/validation_test.go", "Go unit test", ["engines/go/internal/validation/validation.go"]),
    ("engines/cpp/tests/test_rolling_stats.cpp", "C++ test (Python reference se parity values)", ["engines/cpp/src/rolling_stats.cpp"]),
    ("engines/rust/tests/rolling_test.rs", "Rust test (same parity values)", ["engines/rust/src/lib.rs"]),
    ("tests/_helpers.py", "Test helpers: bars, dataset, dummy strategy", ["data/models.py", "strategies/base.py"]),
    ("tests/contract/test_strategy_contract.py", "manifest <-> strategy.schema", ["contracts/strategy.schema.json"]),
    ("tests/contract/test_data_contract.py", "Dataset.meta <-> data.schema", ["contracts/data.schema.json"]),
    ("tests/contract/test_trade_contract.py", "Engine trades <-> trade.schema", ["contracts/trade.schema.json"]),
    ("tests/contract/test_run_contract.py", "Run record <-> run.schema", ["contracts/run.schema.json"]),
    ("tests/contract/test_report_contract.py", "Report <-> report.schema", ["contracts/report.schema.json"]),
    ("tests/contract/test_types_vs_contracts.py", "frontend types <-> schemas", ["frontend/src/types/backtest.ts"]),
    ("tests/contract/test_rolling_stats_parity.py", "native vs reference parity", ["engines/bindings/native.py"]),
    ("frontend/vite.config.ts", "Frontend bundler config", []),
    ("frontend/tests/api.test.ts", "Frontend API client test placeholder", ["frontend/src/api/client.ts"]),
    ("scripts/setup_truemax.sh", "Naye machine par ek command me poora setup + verify", ["scripts/validate_repo.sh"]),
    ("docs/RUNBOOK.md", "Setup, run, verify steps", []),
]))

# ---------------------------------------------------------------- Phase 0
O("README.md", r'''
# strategy-validation-lab

Backtest + validation system. Blueprint: `docs/architecture/BUILD_ORDER.md`, `WIRING_MAP.json`.

```
./scripts/setup_truemax.sh        # venv + tests + demo
python -m cli.main demo           # sample data -> backtest -> validation -> report
python -m cli.main list           # registered strategies
python -m pytest -q               # tests
```
Rule: koi strategy tab tak "approved" nahi jab tak validation pipeline PASS na de.
Missing required data => backtest BLOCKED (data ka andaza nahi lagaya jaata).
''')
O("pyproject.toml", r'''
[project]
name = "strategy-validation-lab"
version = "0.1.0"
requires-python = ">=3.10"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
''')
O(".gitignore", "__pycache__/\n*.pyc\n.venv/\nruns/\ndata/samples/\nnode_modules/\ntarget/\nbuild/\ndist/\n.pytest_cache/\n")
O("Makefile", "validate:\n\t./scripts/validate_repo.sh\n\ntest:\n\tpython -m pytest -q\n\ndemo:\n\tpython -m cli.main demo\n")
O("scripts/validate_repo.sh", r'''
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "== python compile"
python -m compileall -q backend backtest cli contracts data engines metrics optimization persistence registry reporting risk strategies validation
echo "== python tests"
python -m pytest -q
if command -v go >/dev/null; then echo "== go"; (cd engines/go && go vet ./... && go test ./...); else echo "skip go (not installed)"; fi
if command -v cargo >/dev/null; then echo "== rust"; (cd engines/rust && cargo test -q); else echo "skip rust (not installed)"; fi
if command -v cmake >/dev/null; then echo "== c++"; (cd engines/cpp && cmake -S . -B build >/dev/null && cmake --build build >/dev/null && ctest --test-dir build --output-on-failure);
elif command -v g++ >/dev/null; then echo "== c++ (g++)"; g++ -std=c++17 -Iengines/cpp/include engines/cpp/src/rolling_stats.cpp engines/cpp/tests/test_rolling_stats.cpp -o /tmp/svl_cpp_test && /tmp/svl_cpp_test;
else echo "skip c++ (not installed)"; fi
if command -v npm >/dev/null && [ -d frontend/node_modules ]; then echo "== frontend"; (cd frontend && npx tsc --noEmit); else echo "skip frontend (npm install nahi hua)"; fi
echo "ALL CHECKS OK"
''')
O("scripts/setup_truemax.sh", r'''
#!/usr/bin/env bash
# Naye machine par: ./scripts/setup_truemax.sh
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv
. .venv/bin/activate
pip install -q -U pip pytest
./scripts/validate_repo.sh
python -m cli.main demo
''')
O("docs/RUNBOOK.md", r'''
# RUNBOOK

1. `python bootstrap.py --all` (poora repo + tests + BUILD_ORDER.md + WIRING_MAP.json)
2. `cd strategy-validation-lab && ./scripts/setup_truemax.sh`
3. `python bootstrap.py --verify` (blueprint ke hisaab se saari files maujood?)

Demo output: `runs/<run_id>/report.html|json`, `trades.csv`, `run.json`.

## Abhi asli (chalta hua) vs baaki
Asli: data engine (csv), registry, backtest engine, risk, fills, validation (leakage, OOS, walk-forward,
overfitting, confidence), metrics, reporting, job queue, CLI, contracts, parity tests.
Baaki: parquet/broker source, PostgreSQL, FastAPI routes (health ke alawa), cross-validation, robustness,
regime analysis, optimization, frontend pages, Go/Rust/C++ ko Python se asli call karna.
Strategy logic: gamma_blast/three_pm_momentum ka logic placeholder hai - asli niyam aapko dene honge.
''')
O("docs/architecture/ADR-0001-language-ownership.md", r'''
# ADR-0001: Language ownership
- Python: orchestration, backtest, validation, metrics, reporting (single owner).
- Go: validator service, sirf contracts ke zariye.
- C++: rolling stats, tab tak Python fallback jab tak benchmark gain na dikhaye.
- Rust: safe numeric module, same calculation ka dohra ownership nahi.
- Parity: `tests/contract/test_rolling_stats_parity.py` + har engine ka apna test.
''')

# ---------------------------------------------------------------- Phase 1: contracts
O("contracts/signal.schema.json", _schema("signal", {"side": "string", "stop_loss": ["number", "null"],
  "target": ["number", "null"], "size_hint": ["number", "null"], "reason": "string"}, ["side"]))
O("contracts/trade.schema.json", _schema("trade", {"entry_ts": "string", "exit_ts": "string",
  "entry_price": "number", "exit_price": "number", "qty": "integer", "pnl": "number", "fees": "number", "reason": "string"}))
O("contracts/data.schema.json", _schema("data", {"dataset_id": "string", "symbol": "string", "timeframe": "string",
  "start_time": "string", "end_time": "string", "timezone": "string", "source": "string", "schema_version": "string",
  "content_hash": "string", "quality_status": "string"}))
O("contracts/strategy.schema.json", _schema("strategy", {"id": "string", "version": "string", "entry_point": "string",
  "required_data": "array", "parameters": "object", "execution_modes": "array"}))
O("contracts/run.schema.json", _schema("run", {"run_id": "string", "strategy_id": "string", "strategy_version": "string",
  "source_hash": "string", "dataset_id": "string", "dataset_hash": "string", "status": "string", "parameters": "object",
  "config": "object", "engine_version": "string", "created_at": "string"}))
O("contracts/report.schema.json", _schema("report", {"run_id": "string", "status": "string", "metrics": "object",
  "validation": "object", "generated_at": "string"}))
O("contracts/openapi.yaml", r'''
openapi: 3.1.0
info: {title: strategy-validation-lab, version: 0.1.0}
paths:
  /health: {get: {summary: Health}}
  /strategies: {get: {summary: List}, post: {summary: Create}}
  /strategies/{id}: {get: {summary: Detail}}
  /datasets: {get: {summary: List datasets}}
  /backtests: {get: {summary: List runs}, post: {summary: Start run}}
  /backtests/{id}: {get: {summary: Run detail + job status}}
  /validations/{id}: {get: {summary: Validation result}}
  /comparisons: {post: {summary: Compare runs}}
  /reports/{id}: {get: {summary: Report}}
  /audit: {get: {summary: Audit log}}
''')
O("contracts/schema_check.py", r'''
"""Minimal schema check: required keys + basic types (no external dependency)."""
import json
from pathlib import Path

_T = {"string": str, "number": (int, float), "integer": int, "array": list,
      "object": dict, "boolean": bool, "null": type(None)}


def load(name):
    return json.loads((Path(__file__).parent / name).read_text(encoding="utf-8"))


def check(obj, schema):
    errs = [f"missing: {k}" for k in schema.get("required", []) if k not in obj]
    for k, spec in schema.get("properties", {}).items():
        if k not in obj:
            continue
        types = spec["type"] if isinstance(spec["type"], list) else [spec["type"]]
        v = obj[k]
        ok = any(isinstance(v, _T[t]) and not (t in ("number", "integer") and isinstance(v, bool)) for t in types)
        if not ok:
            errs.append(f"bad type: {k}={v!r} expected {types}")
    return errs
''')

# ---------------------------------------------------------------- Phase 2: data
O("data/models.py", r'''
"""Bar + Dataset models (Data Contract: dataset_id, symbol, timeframe, time range, timezone, source, hash, quality)."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Bar:
    ts: str
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    extras: dict = field(default_factory=dict)


@dataclass
class Dataset:
    dataset_id: str
    symbol: str
    timeframe: str
    bars: list
    timezone: str = "UTC"
    source: str = "csv"
    schema_version: str = "1.0"
    content_hash: str = ""
    fields: set = field(default_factory=set)
    quality_status: str = "UNKNOWN"
    quality: dict = field(default_factory=dict)

    def meta(self):
        return {"dataset_id": self.dataset_id, "symbol": self.symbol, "timeframe": self.timeframe,
                "start_time": self.bars[0].ts if self.bars else "", "end_time": self.bars[-1].ts if self.bars else "",
                "timezone": self.timezone, "source": self.source, "schema_version": self.schema_version,
                "content_hash": self.content_hash, "quality_status": self.quality_status}

    def slice(self, start, end, suffix):
        return Dataset(f"{self.dataset_id}:{suffix}", self.symbol, self.timeframe, self.bars[start:end],
                       self.timezone, self.source, self.schema_version, self.content_hash,
                       set(self.fields), self.quality_status, dict(self.quality))
''')
O("data/timestamps.py", r'''
"""Timestamp parsing (ISO-8601)."""
from datetime import datetime


def parse_ts(s):
    return datetime.fromisoformat(s.strip().replace("Z", "+00:00"))
''')
O("data/sources/csv_source.py", r'''
"""CSV reader -> list of dict rows."""
import csv


def read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
''')
O("data/sources/parquet_source.py", r'''
"""Parquet reader (pyarrow optional)."""


def read_rows(path):
    try:
        import pyarrow.parquet as pq
    except ImportError as e:
        raise RuntimeError("Parquet ke liye `pip install pyarrow` chahiye") from e
    return pq.read_table(path).to_pylist()
''')
O("data/sources/broker_source.py", r'''
"""Broker API source: abhi configured nahi (credentials + adapter aapko dena hoga)."""


def read_rows(*_args, **_kwargs):
    raise NotImplementedError("Broker source configured nahi hai")
''')
O("data/normalizer.py", r'''
"""Raw rows -> Bar list (common schema). Extra numeric columns (oi, option_chain...) extras me jaate hain."""
from data.models import Bar

BASE = ("ts", "timestamp", "datetime", "open", "high", "low", "close", "volume")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return v


def normalize(rows):
    bars = []
    for raw in rows:
        r = {str(k).strip().lower(): v for k, v in raw.items()}
        ts = r.get("ts") or r.get("timestamp") or r.get("datetime")
        if not ts:
            raise ValueError("timestamp column missing (ts/timestamp/datetime)")
        for col in ("open", "high", "low", "close"):
            if col not in r:
                raise ValueError(f"column missing: {col}")
        extras = {k: _num(v) for k, v in r.items() if k not in BASE and v not in ("", None)}
        bars.append(Bar(str(ts).strip(), float(r["open"]), float(r["high"]), float(r["low"]),
                        float(r["close"]), float(r.get("volume") or 0), extras))
    return bars
''')
O("data/validators.py", r'''
"""Data checks: duplicate / out-of-order / bad timestamp / non-positive / inconsistent OHLC."""
from data.timestamps import parse_ts


def _issue(level, code, msg):
    return {"level": level, "code": code, "msg": msg}


def validate(bars):
    issues, seen, prev = [], set(), None
    if not bars:
        return [_issue("ERROR", "EMPTY", "no bars")]
    for b in bars:
        if b.ts in seen:
            issues.append(_issue("ERROR", "DUPLICATE_TS", b.ts))
        seen.add(b.ts)
        try:
            t = parse_ts(b.ts)
        except ValueError:
            issues.append(_issue("ERROR", "BAD_TS", b.ts))
            continue
        if prev is not None and t < prev:
            issues.append(_issue("ERROR", "OUT_OF_ORDER", b.ts))
        prev = t
        if min(b.open, b.high, b.low, b.close) <= 0:
            issues.append(_issue("ERROR", "NON_POSITIVE_PRICE", b.ts))
        if b.high < max(b.open, b.close, b.low) or b.low > min(b.open, b.close, b.high):
            issues.append(_issue("ERROR", "OHLC_INCONSISTENT", b.ts))
    return issues
''')
O("data/quality_report.py", r'''
"""Quality status: ERROR => BLOCKED, warning => WARN, else PASS."""


def build_report(issues):
    errors = [i for i in issues if i["level"] == "ERROR"]
    warns = [i for i in issues if i["level"] == "WARN"]
    status = "BLOCKED" if errors else ("WARN" if warns else "PASS")
    codes = {}
    for i in issues:
        codes[i["code"]] = codes.get(i["code"], 0) + 1
    return {"status": status, "errors": len(errors), "warnings": len(warns), "codes": codes, "sample": issues[:20]}
''')
O("data/loaders.py", r'''
"""Entry point: source choose -> load -> normalize -> validate -> Dataset (hash + quality)."""
import hashlib
from pathlib import Path

from data.models import Dataset
from data.normalizer import normalize, BASE
from data.quality_report import build_report
from data.sources import csv_source, parquet_source
from data.validators import validate

BASE_FIELDS = {"open", "high", "low", "close", "volume"}


def load_dataset(path, dataset_id=None, symbol="UNKNOWN", timeframe="UNKNOWN", timezone="UTC"):
    p = Path(path)
    ext = p.suffix.lower()
    if ext == ".csv":
        rows = csv_source.read_rows(p)
    elif ext == ".parquet":
        rows = parquet_source.read_rows(p)
    else:
        raise ValueError(f"unsupported source: {ext}")
    content_hash = hashlib.sha256(p.read_bytes()).hexdigest()
    try:
        bars = normalize(rows)
        issues = validate(bars)
    except (KeyError, ValueError) as e:
        bars, issues = [], [{"level": "ERROR", "code": "SCHEMA", "msg": str(e)}]
    fields = set(BASE_FIELDS)
    for b in bars:
        fields.update(b.extras)
    q = build_report(issues)
    return Dataset(dataset_id or p.stem, symbol, timeframe, bars, timezone, ext.lstrip("."), "1.0",
                   content_hash, fields, q["status"], q)
''')

# ---------------------------------------------------------------- Phase 3: strategies + registry
O("strategies/base.py", r'''
"""Strategy interface. Har strategy isi se guzregi; alag engine nahi banta."""
from abc import ABC, abstractmethod


class Strategy(ABC):
    strategy_id = "base"
    required_data = ()

    def __init__(self, params=None):
        self.params = dict(params or {})

    @abstractmethod
    def on_bar(self, ctx):
        """Return strategies.models.Signal ya None."""
''')
O("strategies/context.py", r'''
"""Context: strategy sirf current bar aur pichhli bars dekh sakti hai (prev)."""


class Context:
    def __init__(self, bars, index, position):
        self._bars, self.index, self.position = bars, index, position

    @property
    def bar(self):
        return self._bars[self.index]

    def prev(self, n=1):
        j = self.index - n
        return self._bars[j] if j >= 0 else None
''')
O("strategies/models.py", r'''
"""Signal model (contracts/signal.schema.json). v0: long-only (BUY / EXIT)."""
from dataclasses import dataclass, asdict

VALID_SIDES = ("BUY", "EXIT")


@dataclass
class Signal:
    side: str
    stop_loss: float = None
    target: float = None
    size_hint: float = None
    reason: str = ""

    def to_dict(self):
        return asdict(self)

    def validate(self):
        if self.side not in VALID_SIDES:
            raise ValueError(f"UNSUPPORTED_SIDE:{self.side}")
        for name in ("stop_loss", "target"):
            v = getattr(self, name)
            if v is not None and v <= 0:
                raise ValueError(f"INVALID_{name.upper()}")
        if self.stop_loss and self.target and self.stop_loss >= self.target:
            raise ValueError("STOP_NOT_BELOW_TARGET")
''')
O("strategies/validation.py", r'''
"""Manifest + data requirement checks."""
REQUIRED_KEYS = ("id", "version", "entry_point", "required_data", "parameters", "execution_modes")


def validate_manifest(m):
    return [f"missing: {k}" for k in REQUIRED_KEYS if k not in m]


def check_data_requirements(required, dataset):
    missing = [f for f in required if f not in dataset.fields]
    return (not missing, missing)
''')
O("strategies/gamma_blast/manifest.yaml", r'''
id: gamma_blast
version: 0.1.0
entry_point: strategies.gamma_blast.strategy:GammaBlastStrategy
required_data: [option_chain, oi]
parameters: {}
execution_modes: [backtest]
''')
O("strategies/gamma_blast/strategy.py", r'''
"""GammaBlastStrategy: PLACEHOLDER. Asli niyam yahan daalne hain.
Option chain + OI chahiye; na ho to engine backtest ko BLOCKED karta hai."""
from strategies.base import Strategy


class GammaBlastStrategy(Strategy):
    strategy_id = "gamma_blast"
    required_data = ("option_chain", "oi")

    def on_bar(self, ctx):
        return None  # TODO: real entry/exit rules
''')
O("strategies/three_pm_momentum/manifest.yaml", r'''
id: three_pm_momentum
version: 0.1.0
entry_point: strategies.three_pm_momentum.strategy:ThreePMMomentumStrategy
required_data: []
parameters: {stop_pct: 0.5, target_pct: 1.0, entry_hour: 15, entry_minute: 0, exit_hour: 15, exit_minute: 25}
execution_modes: [backtest]
''')
O("strategies/three_pm_momentum/strategy.py", r'''
"""ThreePMMomentumStrategy: PLACEHOLDER logic (interface demo). Asli niyam aapko replace karne hain.
Rule (demo): entry time par close > pichhla close => BUY; stop/target %; exit time par EXIT."""
from strategies.base import Strategy
from strategies.models import Signal


class ThreePMMomentumStrategy(Strategy):
    strategy_id = "three_pm_momentum"
    required_data = ()

    def on_bar(self, ctx):
        p, bar = self.params, ctx.bar
        t = int(bar.ts[11:13]) * 60 + int(bar.ts[14:16])
        if ctx.position is not None:
            if t >= p["exit_hour"] * 60 + p["exit_minute"]:
                return Signal("EXIT", reason="EOD_EXIT")
            return None
        if t == p["entry_hour"] * 60 + p["entry_minute"]:
            prev = ctx.prev(1)
            if prev is not None and bar.close > prev.close:
                return Signal("BUY", stop_loss=round(bar.close * (1 - p["stop_pct"] / 100), 2),
                              target=round(bar.close * (1 + p["target_pct"] / 100), 2), reason="momentum")
        return None
''')
O("registry/metadata.py", r'''
"""Minimal manifest parser (flat `key: value`, [list], {k: v}). Koi yaml dependency nahi."""
from pathlib import Path


def _scalar(s):
    s = s.strip()
    if s in ("true", "True"):
        return True
    if s in ("false", "False"):
        return False
    for cast in (int, float):
        try:
            return cast(s)
        except ValueError:
            pass
    return s.strip("'\"")


def _value(s):
    s = s.strip()
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        return [_scalar(x) for x in inner.split(",")] if inner else []
    if s.startswith("{") and s.endswith("}"):
        inner, d = s[1:-1].strip(), {}
        for part in (inner.split(",") if inner else []):
            k, _, v = part.partition(":")
            d[k.strip()] = _scalar(v)
        return d
    return _scalar(s)


def parse_manifest_text(text):
    out = {}
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        k, _, v = line.partition(":")
        out[k.strip()] = _value(v)
    return out


def load_manifest(path):
    return parse_manifest_text(Path(path).read_text(encoding="utf-8"))
''')
O("registry/versioning.py", r'''
"""Source hash = strategy.py + manifest.yaml ka sha256 (run ke saath save hota hai)."""
import hashlib
from pathlib import Path


def source_hash(strategy_dir):
    h = hashlib.sha256()
    for name in ("manifest.yaml", "strategy.py"):
        f = Path(strategy_dir) / name
        if f.exists():
            h.update(f.read_bytes())
    return h.hexdigest()
''')
O("registry/lifecycle.py", r'''
"""Strategy lifecycle states."""
ALLOWED = {"DRAFT": {"VALIDATED", "RETIRED"}, "VALIDATED": {"APPROVED", "DRAFT", "RETIRED"},
           "APPROVED": {"RETIRED", "DRAFT"}, "RETIRED": set()}


def can_transition(a, b):
    return b in ALLOWED.get(a, set())
''')
O("registry/registry.py", r'''
"""Registry entry point: manifests discover, validate, strategy load."""
import importlib
from pathlib import Path

from registry.metadata import load_manifest
from registry.versioning import source_hash as _hash
from strategies.validation import validate_manifest


class Registry:
    def __init__(self, strategies_dir=None):
        self.dir = Path(strategies_dir) if strategies_dir else Path(__file__).resolve().parent.parent / "strategies"
        self.records = {}

    def discover(self):
        self.records.clear()
        for d in sorted(self.dir.iterdir()):
            mf = d / "manifest.yaml"
            if d.is_dir() and mf.exists():
                m = load_manifest(mf)
                errs = validate_manifest(m)
                if errs:
                    raise ValueError(f"{d.name}: invalid manifest {errs}")
                self.records[m["id"]] = {"manifest": m, "dir": d}
        return sorted(self.records)

    def _rec(self, sid):
        if sid not in self.records:
            self.discover()
        if sid not in self.records:
            raise KeyError(f"unknown strategy: {sid}")
        return self.records[sid]

    def manifest(self, sid):
        return self._rec(sid)["manifest"]

    def load(self, sid, params=None):
        m = self._rec(sid)["manifest"]
        mod, cls = m["entry_point"].split(":")
        merged = dict(m.get("parameters") or {})
        merged.update(params or {})
        return getattr(importlib.import_module(mod), cls)(merged)

    def source_hash(self, sid):
        return _hash(self._rec(sid)["dir"])
''')

# ---------------------------------------------------------------- Phase 4: backtest + risk
O("risk/limits.py", r'''
"""Risk limits (config/risk_policy.json se aate hain)."""
from dataclasses import dataclass


@dataclass
class RiskLimits:
    max_position_pct: float = 100.0
    max_drawdown_pct: float = 30.0
    on_violation: str = "halt"
''')
O("risk/exposure.py", r'''
def position_value(position, price):
    return 0.0 if position is None else position.qty * price
''')
O("risk/drawdown.py", r'''
class DrawdownTracker:
    def __init__(self):
        self.peak = None

    def update(self, equity):
        self.peak = equity if self.peak is None else max(self.peak, equity)
        return 0.0 if not self.peak else (self.peak - equity) / self.peak * 100.0
''')
O("risk/kill_switch.py", r'''
class KillSwitch:
    def __init__(self):
        self.tripped, self.reason = False, ""

    def trip(self, reason):
        if not self.tripped:
            self.tripped, self.reason = True, reason
''')
O("risk/manager.py", r'''
"""Risk entry point: order allow/reject + drawdown kill switch."""
from risk.drawdown import DrawdownTracker
from risk.kill_switch import KillSwitch
from risk.limits import RiskLimits


class RiskManager:
    def __init__(self, limits=None):
        self.limits = limits or RiskLimits()
        self.dd, self.kill = DrawdownTracker(), KillSwitch()

    def check_order(self, qty, price, equity):
        if self.kill.tripped:
            return False, "KILL_SWITCH"
        if qty <= 0:
            return False, "ZERO_SIZE"
        if qty * price > equity * self.limits.max_position_pct / 100.0:
            return False, "MAX_POSITION"
        return True, ""

    def after_bar(self, equity):
        dd = self.dd.update(equity)
        if dd >= self.limits.max_drawdown_pct:
            self.kill.trip(f"MAX_DRAWDOWN:{dd:.2f}%")
        return self.kill.tripped
''')
O("backtest/clock.py", r'''
class SimClock:
    def __init__(self):
        self.now = None

    def set(self, ts):
        self.now = ts
''')
O("backtest/event_queue.py", r'''
class EventQueue:
    """Market events ko time-order me deta hai: (index, bar)."""

    def __init__(self, bars):
        self.bars = bars

    def __iter__(self):
        return iter(enumerate(self.bars))
''')
O("backtest/orders.py", r'''
from dataclasses import dataclass


@dataclass
class Order:
    side: str
    qty: int
    stop_loss: float = None
    target: float = None
    reason: str = ""
''')
O("backtest/fees.py", r'''
def fee(notional, fee_pct):
    return abs(notional) * fee_pct
''')
O("backtest/slippage.py", r'''
def apply(price, side, bps):
    """BUY ka price upar, SELL ka neeche."""
    k = bps / 10000.0
    return price * (1 + k) if side == "BUY" else price * (1 - k)
''')
O("backtest/fills.py", r'''
"""Exit fill rules (long). Ek candle me Stop + Target dono => conservative: stop pehle."""


def resolve_exit(bar, stop, target, policy="stop_first"):
    if policy != "stop_first":
        raise ValueError(f"unsupported ambiguous_candle_policy: {policy}")
    stop_hit = stop is not None and bar.low <= stop
    target_hit = target is not None and bar.high >= target
    if stop_hit and target_hit:
        return min(stop, bar.open), "STOP_AMBIGUOUS_CONSERVATIVE"
    if stop_hit:
        return min(stop, bar.open), "STOP"  # gap-down: open par fill
    if target_hit:
        return target, "TARGET"
    return None
''')
O("backtest/stop_manager.py", r'''
from backtest.fills import resolve_exit


def check(position, bar, policy="stop_first"):
    if position is None:
        return None
    return resolve_exit(bar, position.stop, position.target, policy)
''')
O("backtest/position_sizing.py", r'''
def size(equity, price, stop=None, risk_pct=1.0, max_pct=100.0):
    cap = int(equity * max_pct / 100.0 / price)
    if stop is not None and stop < price:
        return max(0, min(int(equity * risk_pct / 100.0 / (price - stop)), cap))
    return max(0, min(int(equity * 0.10 / price), cap))  # stop nahi: equity ka 10%
''')
O("backtest/portfolio.py", r'''
"""Single-instrument long-only portfolio."""
from dataclasses import dataclass


@dataclass
class Position:
    qty: int
    entry_price: float
    entry_ts: str
    stop: float
    target: float
    entry_fee: float


class Portfolio:
    def __init__(self, cash):
        self.cash, self.position, self.trades = cash, None, []

    def open(self, qty, price, ts, stop, target, fee):
        self.cash -= qty * price + fee
        self.position = Position(qty, price, ts, stop, target, fee)

    def close(self, price, ts, fee, reason):
        p = self.position
        self.cash += p.qty * price - fee
        self.trades.append({"entry_ts": p.entry_ts, "exit_ts": ts, "entry_price": p.entry_price,
                            "exit_price": price, "qty": p.qty,
                            "pnl": (price - p.entry_price) * p.qty - p.entry_fee - fee,
                            "fees": p.entry_fee + fee, "reason": reason})
        self.position = None

    def equity(self, price):
        return self.cash + (self.position.qty * price if self.position else 0.0)
''')
O("backtest/accounting.py", r'''
class EquityCurve:
    def __init__(self):
        self.points = []

    def record(self, ts, equity):
        self.points.append([ts, equity])
''')
O("backtest/results.py", r'''
from dataclasses import dataclass, field, asdict


@dataclass
class BacktestResult:
    status: str                       # COMPLETED | BLOCKED | HALTED
    reason: str = ""
    trades: list = field(default_factory=list)
    equity: list = field(default_factory=list)
    rejections: list = field(default_factory=list)
    config: dict = field(default_factory=dict)
    meta: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)
''')
O("backtest/engine.py", r'''
"""Backtest engine entry point.
Flow: event -> strategy -> signal validation -> sizing -> risk -> next-bar-open fill (no look-ahead)
      -> stops -> portfolio/accounting -> risk recheck."""
from backtest import fees, slippage, stop_manager, position_sizing
from backtest.accounting import EquityCurve
from backtest.clock import SimClock
from backtest.event_queue import EventQueue
from backtest.portfolio import Portfolio
from backtest.results import BacktestResult
from risk.limits import RiskLimits
from risk.manager import RiskManager
from strategies.context import Context
from strategies.validation import check_data_requirements

ENGINE_VERSION = "0.1.0"
DEFAULT_CONFIG = {"initial_capital": 1_000_000.0, "slippage_bps": 2.0, "fee_pct": 0.0003,
                  "risk_per_trade_pct": 1.0, "ambiguous_candle_policy": "stop_first",
                  "max_position_pct": 100.0, "max_drawdown_pct": 30.0}


def run_backtest(dataset, strategy, config=None):
    cfg = dict(DEFAULT_CONFIG)
    cfg.update(config or {})
    meta = dict(dataset.meta())
    meta["engine_version"] = ENGINE_VERSION
    if dataset.quality_status == "BLOCKED":
        return BacktestResult("BLOCKED", "DATA_QUALITY_BLOCKED", config=cfg, meta=meta)
    ok, missing = check_data_requirements(strategy.required_data, dataset)
    if not ok:
        return BacktestResult("BLOCKED", "MISSING_DATA:" + ",".join(missing), config=cfg, meta=meta)

    pf, curve, clock = Portfolio(cfg["initial_capital"]), EquityCurve(), SimClock()
    risk = RiskManager(RiskLimits(cfg["max_position_pct"], cfg["max_drawdown_pct"]))
    bps, fee_pct, policy = cfg["slippage_bps"], cfg["fee_pct"], cfg["ambiguous_candle_policy"]
    bars, pending, rejections, status, reason = dataset.bars, None, [], "COMPLETED", ""

    def close(raw_price, bar, why):
        px = slippage.apply(raw_price, "SELL", bps)
        pf.close(px, bar.ts, fees.fee(pf.position.qty * px, fee_pct), why)

    for i, bar in EventQueue(bars):
        clock.set(bar.ts)
        if pending and pf.position is None:
            px = slippage.apply(bar.open, "BUY", bps)
            pf.open(pending["qty"], px, bar.ts, pending["stop"], pending["target"],
                    fees.fee(pending["qty"] * px, fee_pct))
        pending = None
        ex = stop_manager.check(pf.position, bar, policy)
        if ex:
            close(ex[0], bar, ex[1])
        eq = pf.equity(bar.close)
        curve.record(bar.ts, eq)
        if risk.after_bar(eq):
            if pf.position:
                close(bar.close, bar, "KILL_SWITCH")
            status, reason = "HALTED", risk.kill.reason
            break
        sig = strategy.on_bar(Context(bars, i, pf.position))
        if sig is None:
            continue
        try:
            sig.validate()
        except ValueError as e:
            rejections.append({"ts": bar.ts, "reason": f"INVALID_SIGNAL:{e}"})
            continue
        if sig.side == "BUY" and pf.position is None:
            qty = position_sizing.size(eq, bar.close, sig.stop_loss, cfg["risk_per_trade_pct"], cfg["max_position_pct"])
            allowed, why = risk.check_order(qty, bar.close, eq)
            if allowed:
                pending = {"qty": qty, "stop": sig.stop_loss, "target": sig.target}
            else:
                rejections.append({"ts": bar.ts, "reason": why})
        elif sig.side == "EXIT" and pf.position:
            close(bar.close, bar, "SIGNAL_EXIT")
    if pf.position and bars:
        close(bars[-1].close, bars[-1], "END_OF_DATA")
    return BacktestResult(status, reason, pf.trades, curve.points, rejections, cfg, meta)
''')

# ---------------------------------------------------------------- Phase 5: metrics + validation
O("metrics/return_metrics.py", r'''
def compute(equity, initial):
    final = equity[-1][1] if equity else initial
    return {"final_equity": final, "total_return_pct": (final / initial - 1) * 100.0}
''')
O("metrics/risk_metrics.py", r'''
import math
import statistics


def max_drawdown_pct(equity):
    peak, worst = None, 0.0
    for _, e in equity:
        peak = e if peak is None else max(peak, e)
        worst = max(worst, (peak - e) / peak * 100.0 if peak else 0.0)
    return worst


def sharpe_daily(equity):
    daily = {}
    for ts, e in equity:
        daily[ts[:10]] = e
    v = list(daily.values())
    rets = [v[i] / v[i - 1] - 1 for i in range(1, len(v)) if v[i - 1]]
    if len(rets) < 2:
        return None
    sd = statistics.pstdev(rets)
    return None if sd == 0 else statistics.mean(rets) / sd * math.sqrt(252)


def compute(equity):
    return {"max_drawdown_pct": max_drawdown_pct(equity), "sharpe_daily": sharpe_daily(equity)}
''')
O("metrics/trade_metrics.py", r'''
def compute(trades):
    pnl = [t["pnl"] for t in trades]
    wins, losses = [x for x in pnl if x > 0], [x for x in pnl if x <= 0]
    gl = abs(sum(losses))
    return {"n_trades": len(pnl), "total_pnl": sum(pnl), "fees_total": sum(t["fees"] for t in trades),
            "avg_win": sum(wins) / len(wins) if wins else 0.0,
            "avg_loss": sum(losses) / len(losses) if losses else 0.0,
            "profit_factor": (sum(wins) / gl) if gl else None}
''')
O("metrics/accuracy.py", r'''
def win_rate(trades):
    return 100.0 * sum(1 for t in trades if t["pnl"] > 0) / len(trades) if trades else 0.0
''')
O("metrics/expectancy.py", r'''
def expectancy(trades):
    return sum(t["pnl"] for t in trades) / len(trades) if trades else 0.0
''')
O("metrics/benchmarks.py", r'''
def buy_and_hold_return_pct(bars):
    return (bars[-1].close / bars[0].open - 1) * 100.0 if bars else 0.0
''')
O("metrics/confidence_intervals.py", r'''
import random


def bootstrap_mean_ci(values, n=1000, alpha=0.05, seed=7):
    if len(values) < 5:
        return None
    rng, k = random.Random(seed), len(values)
    means = sorted(sum(rng.choice(values) for _ in range(k)) / k for _ in range(n))
    return means[int(n * alpha / 2)], means[int(n * (1 - alpha / 2)) - 1]
''')
O("metrics/__init__.py", r'''
"""Unified metrics. Yeh sirf ginti karta hai; approval validation pipeline deta hai."""
from . import accuracy, benchmarks, confidence_intervals, expectancy, return_metrics, risk_metrics, trade_metrics


def compute_all(result, dataset=None):
    out = {}
    out.update(return_metrics.compute(result.equity, result.config["initial_capital"]))
    out.update(risk_metrics.compute(result.equity))
    out.update(trade_metrics.compute(result.trades))
    out["win_rate_pct"] = accuracy.win_rate(result.trades)
    out["expectancy"] = expectancy.expectancy(result.trades)
    ci = confidence_intervals.bootstrap_mean_ci([t["pnl"] for t in result.trades])
    out["expectancy_ci95"] = list(ci) if ci else None
    if dataset is not None:
        out["buy_and_hold_return_pct"] = benchmarks.buy_and_hold_return_pct(dataset.bars)
    return out
''')
O("validation/leakage_checks.py", r'''
"""Structural checks only. Strategy-level look-ahead ka poora saboot nahi (engine next-bar-open fill karta hai)."""


def run(result, dataset):
    ts = {b.ts for b in dataset.bars}
    problems = []
    for t in result.trades:
        if t["entry_ts"] > t["exit_ts"]:
            problems.append(f"exit before entry: {t['entry_ts']}")
        if t["entry_ts"] not in ts or t["exit_ts"] not in ts:
            problems.append("trade timestamp dataset me nahi")
    times = [p[0] for p in result.equity]
    if any(times[i] >= times[i + 1] for i in range(len(times) - 1)):
        problems.append("equity timestamps strictly increasing nahi")
    return {"status": "FAIL" if problems else "PASS", "problems": problems[:10],
            "note": "structural checks only"}
''')
O("validation/out_of_sample.py", r'''
from backtest.engine import run_backtest
from metrics import expectancy

MIN_TRADES = 5


def run(dataset, factory, config=None, split=0.7):
    k = int(len(dataset.bars) * split)
    ins = run_backtest(dataset.slice(0, k, "IS"), factory(), config)
    oos = run_backtest(dataset.slice(k, len(dataset.bars), "OOS"), factory(), config)
    out = {"is_trades": len(ins.trades), "oos_trades": len(oos.trades),
           "is_expectancy": expectancy.expectancy(ins.trades), "oos_expectancy": expectancy.expectancy(oos.trades)}
    if len(oos.trades) < MIN_TRADES:
        return {"status": "UNAVAILABLE", "reason": "TOO_FEW_OOS_TRADES", **out}
    return {"status": "PASS" if out["oos_expectancy"] > 0 else "FAIL", **out}
''')
O("validation/walk_forward.py", r'''
from backtest.engine import run_backtest
from metrics import expectancy


def run(dataset, factory, config=None, windows=4):
    n, rows = len(dataset.bars), []
    for w in range(windows):
        a, b = n * w // windows, n * (w + 1) // windows
        res = run_backtest(dataset.slice(a, b, f"WF{w}"), factory(), config)
        rows.append({"window": w, "trades": len(res.trades), "expectancy": expectancy.expectancy(res.trades)})
    total = sum(r["trades"] for r in rows)
    if total < 5:
        return {"status": "UNAVAILABLE", "reason": "TOO_FEW_TRADES", "windows": rows}
    active = [r for r in rows if r["trades"]]
    good = sum(1 for r in active if r["expectancy"] > 0)
    ok = len(active) >= windows // 2 and good * 2 >= len(active)
    return {"status": "PASS" if ok else "FAIL", "profitable_windows": good, "active_windows": len(active), "windows": rows}
''')
O("validation/overfitting.py", r'''
def run(oos):
    if oos.get("status") == "UNAVAILABLE" or oos.get("is_expectancy", 0) <= 0:
        return {"status": "UNAVAILABLE", "reason": "NEEDS_PROFITABLE_IN_SAMPLE_AND_ENOUGH_OOS_TRADES"}
    drop = (oos["is_expectancy"] - oos["oos_expectancy"]) / oos["is_expectancy"]
    return {"status": "FAIL" if drop > 0.5 else "PASS", "degradation": drop}
''')
O("validation/statistical_confidence.py", r'''
from metrics.confidence_intervals import bootstrap_mean_ci

MIN_TRADES = 30


def run(result):
    pnl = [t["pnl"] for t in result.trades]
    if len(pnl) < MIN_TRADES:
        return {"status": "UNAVAILABLE", "reason": f"NEED_{MIN_TRADES}_TRADES", "n_trades": len(pnl)}
    lo, hi = bootstrap_mean_ci(pnl)
    return {"status": "PASS" if lo > 0 else "FAIL", "ci95": [lo, hi], "n_trades": len(pnl)}
''')
for _name in ("cross_validation", "robustness", "regime_analysis"):
    O(f"validation/{_name}.py", '"""Abhi implement nahi: honest UNAVAILABLE (PASS nahi)."""\n\n\n'
      'def run(*_args, **_kwargs):\n    return {"status": "UNAVAILABLE", "reason": "NOT_IMPLEMENTED_YET"}\n')
O("validation/pipeline.py", r'''
"""Validation order + overall status. Koi FAIL => FAIL; koi UNAVAILABLE => INCOMPLETE; tabhi PASS jab sab PASS."""
from backtest.engine import run_backtest
from validation import (cross_validation, leakage_checks, out_of_sample, overfitting, regime_analysis,
                        robustness, statistical_confidence, walk_forward)


def overall_status(checks):
    st = [c["status"] for c in checks.values()]
    if "FAIL" in st:
        return "FAIL"
    if "UNAVAILABLE" in st:
        return "INCOMPLETE"
    return "PASS"


def run_validation(dataset, factory, config=None, split=0.7, windows=4):
    base = run_backtest(dataset, factory(), config)
    if base.status == "BLOCKED":
        return {"status": "BLOCKED", "reason": base.reason, "checks": {}}
    oos = out_of_sample.run(dataset, factory, config, split)
    checks = {"leakage": leakage_checks.run(base, dataset), "out_of_sample": oos,
              "walk_forward": walk_forward.run(dataset, factory, config, windows),
              "cross_validation": cross_validation.run(), "overfitting": overfitting.run(oos),
              "robustness": robustness.run(), "regime_analysis": regime_analysis.run(),
              "statistical_confidence": statistical_confidence.run(base)}
    return {"status": overall_status(checks), "checks": checks}
''')

# ---------------------------------------------------------------- Phase 6: reporting + persistence
O("reporting/charts.py", r'''
def equity_svg(equity, w=720, h=200):
    if len(equity) < 2:
        return ""
    step = max(1, len(equity) // 300)
    ys = [e for _, e in equity[::step]]
    lo, hi = min(ys), max(ys)
    span = (hi - lo) or 1.0
    pts = " ".join(f"{i * w / (len(ys) - 1):.1f},{h - (y - lo) / span * (h - 10) - 5:.1f}" for i, y in enumerate(ys))
    return f'<svg viewBox="0 0 {w} {h}" width="100%"><polyline fill="none" stroke="#2563eb" stroke-width="1.5" points="{pts}"/></svg>'
''')
O("reporting/json_report.py", r'''
import json


def write(report, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    return str(path)
''')
O("reporting/csv_export.py", r'''
import csv

FIELDS = ["entry_ts", "exit_ts", "entry_price", "exit_price", "qty", "pnl", "fees", "reason"]


def write_trades(trades, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(trades)
    return str(path)
''')
O("reporting/html_report.py", r'''
import html
from pathlib import Path
from string import Template

from reporting.charts import equity_svg

TEMPLATE = Path(__file__).parent / "templates" / "report.html"


def _rows(d):
    return "".join(f"<tr><td>{html.escape(str(k))}</td><td>{html.escape(str(v))}</td></tr>" for k, v in d.items())


def write(report, equity, path):
    checks = {k: f"{v.get('status')} {v.get('reason', '')}".strip()
              for k, v in report["validation"].get("checks", {}).items()}
    text = Template(TEMPLATE.read_text(encoding="utf-8")).safe_substitute(
        title=html.escape(report["run_id"]), status=html.escape(f"{report['status']} {report.get('reason', '')}"),
        validation=html.escape(str(report["validation"].get("status"))), metrics_rows=_rows(report["metrics"]),
        validation_rows=_rows(checks), chart=equity_svg(equity))
    Path(path).write_text(text, encoding="utf-8")
    return str(path)
''')
O("reporting/templates/report.html", r'''
<!doctype html>
<html><head><meta charset="utf-8"><title>${title}</title>
<style>body{font-family:sans-serif;max-width:820px;margin:2rem auto}td{padding:2px 12px;border-bottom:1px solid #ddd}</style></head>
<body><h1>${title}</h1>
<p>Backtest status: <b>${status}</b> | Validation: <b>${validation}</b></p>
${chart}<h2>Metrics</h2><table>${metrics_rows}</table>
<h2>Validation checks</h2><table>${validation_rows}</table></body></html>
''')
O("reporting/generator.py", r'''
"""Reporting entry point: metrics + validation -> json/csv/html artifacts."""
from datetime import datetime, timezone
from pathlib import Path

from reporting import csv_export, html_report, json_report


def generate_report(run_id, result, metrics, validation, out_dir):
    out = Path(out_dir) / run_id
    out.mkdir(parents=True, exist_ok=True)
    report = {"run_id": run_id, "status": result.status, "reason": result.reason, "metrics": metrics,
              "validation": validation, "generated_at": datetime.now(timezone.utc).isoformat()}
    paths = {"json": json_report.write(report, out / "report.json"),
             "csv": csv_export.write_trades(result.trades, out / "trades.csv"),
             "html": html_report.write(report, result.equity, out / "report.html")}
    return report, paths
''')
O("persistence/models.py", r'''
from dataclasses import dataclass, field


@dataclass
class RunRecord:
    run_id: str
    strategy_id: str
    status: str
    data: dict = field(default_factory=dict)
''')
O("persistence/audit.py", r'''
"""Append-only audit log (JSONL)."""
import json
from datetime import datetime, timezone
from pathlib import Path


def log(root, event, **data):
    Path(root).mkdir(parents=True, exist_ok=True)
    row = {"ts": datetime.now(timezone.utc).isoformat(), "event": event, **data}
    with open(Path(root) / "audit.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(row, default=str) + "\n")


def read(root, limit=100):
    f = Path(root) / "audit.jsonl"
    if not f.exists():
        return []
    return [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines()][-limit:]
''')
O("persistence/repositories.py", r'''
"""File-backed run repository (runs/<run_id>/run.json). PostgreSQL adapter baad me, isi interface par."""
import json
from pathlib import Path


class RunRepository:
    def __init__(self, root="runs"):
        self.root = Path(root)

    def save(self, run_id, record):
        d = self.root / run_id
        d.mkdir(parents=True, exist_ok=True)
        (d / "run.json").write_text(json.dumps(record, indent=2, default=str), encoding="utf-8")

    def get(self, run_id):
        return json.loads((self.root / run_id / "run.json").read_text(encoding="utf-8"))

    def list_ids(self):
        return sorted(p.parent.name for p in self.root.glob("*/run.json")) if self.root.exists() else []
''')

# ---------------------------------------------------------------- Phase 7: backend + cli
O("backend/jobs/job_status.py", r'''
from dataclasses import dataclass
from enum import Enum


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


@dataclass
class Job:
    job_id: str
    payload: dict
    status: JobStatus = JobStatus.QUEUED
    result: dict = None
    error: str = None
''')
O("backend/jobs/queue.py", r'''
import itertools

from backend.jobs.job_status import Job, JobStatus


class JobQueue:
    def __init__(self):
        self.jobs, self._ids = {}, itertools.count(1)

    def submit(self, payload):
        job = Job(f"job-{next(self._ids)}", payload)
        self.jobs[job.job_id] = job
        return job

    def get(self, job_id):
        return self.jobs[job_id]

    def next_queued(self):
        return next((j for j in self.jobs.values() if j.status == JobStatus.QUEUED), None)
''')
O("backend/jobs/worker.py", r'''
"""Worker: job RUNNING -> SUCCEEDED/FAILED. Failure ka karan save rehta hai."""
from backend.jobs.job_status import JobStatus


def run_next(queue, handler):
    job = queue.next_queued()
    if job is None:
        return None
    job.status = JobStatus.RUNNING
    try:
        job.result = handler(job.payload)
        job.status = JobStatus.SUCCEEDED
    except Exception as e:  # noqa: BLE001 - failure reason save karna hai
        job.status, job.error = JobStatus.FAILED, f"{type(e).__name__}: {e}"
    return job
''')
O("backend/services/backtest_service.py", r'''
"""Poora flow: registry -> data -> engine -> validation -> metrics -> report -> persistence -> audit."""
import json
from datetime import datetime, timezone
from pathlib import Path

from backtest.engine import ENGINE_VERSION, run_backtest
from data.loaders import load_dataset
from metrics import compute_all
from persistence import audit
from persistence.repositories import RunRepository
from registry.registry import Registry
from reporting.generator import generate_report
from validation.pipeline import run_validation

ROOT = Path(__file__).resolve().parents[2]


def load_config():
    cfg = {}
    for name in ("execution_defaults.json", "risk_policy.json"):
        f = ROOT / "config" / name
        if f.exists():
            cfg.update(json.loads(f.read_text(encoding="utf-8")))
    cfg.pop("on_violation", None)
    return cfg


def run_full(strategy_id, data_path, params=None, config=None, out_root="runs", symbol="UNKNOWN",
             timeframe="UNKNOWN", run_id=None):
    reg = Registry()
    manifest = reg.manifest(strategy_id)
    cfg = load_config()
    cfg.update(config or {})
    ds = load_dataset(data_path, symbol=symbol, timeframe=timeframe)
    factory = lambda: reg.load(strategy_id, params)  # noqa: E731
    result = run_backtest(ds, factory(), cfg)
    if result.status == "BLOCKED":
        metrics, validation = {}, {"status": "BLOCKED", "reason": result.reason, "checks": {}}
    else:
        metrics, validation = compute_all(result, ds), run_validation(ds, factory, cfg)
    now = datetime.now(timezone.utc)
    run_id = run_id or f"run-{now.strftime('%Y%m%d%H%M%S')}-{strategy_id}"
    report, paths = generate_report(run_id, result, metrics, validation, out_root)
    record = {"run_id": run_id, "strategy_id": strategy_id, "strategy_version": str(manifest["version"]),
              "source_hash": reg.source_hash(strategy_id), "dataset_id": ds.dataset_id,
              "dataset_hash": ds.content_hash, "status": result.status, "reason": result.reason,
              "validation_status": validation["status"], "parameters": {**manifest.get("parameters", {}), **(params or {})},
              "config": result.config, "engine_version": ENGINE_VERSION, "created_at": now.isoformat(),
              "report": paths}
    RunRepository(out_root).save(run_id, record)
    audit.log(out_root, "run_completed", run_id=run_id, status=result.status, validation=validation["status"])
    return record, paths
''')
O("backend/api/health.py", r'''
"""/health route (FastAPI ho to router, warna plain function)."""


def health_payload():
    return {"status": "ok"}


try:
    from fastapi import APIRouter
    router = APIRouter()

    @router.get("/health")
    def health():
        return health_payload()
except ImportError:  # fastapi optional
    router = None
''')
O("backend/api/audit.py", r'''
"""/audit route."""
from persistence import audit


def read_audit(root="runs", limit=100):
    return audit.read(root, limit)


try:
    from fastapi import APIRouter
    router = APIRouter()

    @router.get("/audit")
    def get_audit(limit: int = 100):
        return read_audit(limit=limit)
except ImportError:
    router = None
''')
O("backend/dependencies.py", r'''
from persistence.repositories import RunRepository
from registry.registry import Registry


def get_registry():
    return Registry()


def get_repository(root="runs"):
    return RunRepository(root)
''')
O("backend/adapters/go_adapter.py", r'''
"""Go validator service client (HTTP/JSON, contracts/openapi.yaml ke mutabik). URL na ho to saaf error."""
import json
import urllib.request


class GoValidatorClient:
    def __init__(self, base_url=None, timeout=10):
        self.base_url, self.timeout = base_url, timeout

    def validate(self, payload):
        if not self.base_url:
            raise RuntimeError("Go validator URL configure nahi hai")
        req = urllib.request.Request(self.base_url.rstrip("/") + "/validate", json.dumps(payload).encode(),
                                     {"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            return json.loads(r.read())
''')
O("backend/app.py", r'''
"""Backend entry point. Abhi sirf /health + /audit (FastAPI ho to). Baaki routes service layer par banenge."""


def create_app():
    try:
        from fastapi import FastAPI
    except ImportError as e:
        raise RuntimeError("`pip install fastapi uvicorn` chahiye") from e
    from backend.api import audit, health
    app = FastAPI(title="strategy-validation-lab")
    app.include_router(health.router)
    app.include_router(audit.router)
    return app
''')
O("cli/commands.py", r'''
import csv
import random
from datetime import date, timedelta
from pathlib import Path

from backend.services.backtest_service import run_full
from registry.registry import Registry


def make_sample_csv(path, days=120, seed=42):
    """Deterministic random-walk 5-min bars (sirf demo, asli data nahi)."""
    rng, price, d, rows = random.Random(seed), 1000.0, date(2024, 1, 1), []
    while len(rows) < days * 75:
        if d.weekday() < 5:
            for i in range(75):
                mins = 9 * 60 + 15 + i * 5
                o = price
                c = max(1.0, o * (1 + rng.gauss(0, 0.0008)))
                rows.append([f"{d.isoformat()}T{mins // 60:02d}:{mins % 60:02d}:00", round(o, 2),
                             round(max(o, c) * (1 + abs(rng.gauss(0, 0.0004))), 2),
                             round(min(o, c) * (1 - abs(rng.gauss(0, 0.0004))), 2), round(c, 2), rng.randint(100, 5000)])
                price = c
        d += timedelta(days=1)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ts", "open", "high", "low", "close", "volume"])
        w.writerows(rows)
    return str(path)


def cmd_list(_args):
    for sid in Registry().discover():
        print(sid)


def cmd_run(args):
    record, paths = run_full(args.strategy, args.data, out_root=args.out)
    print(f"status={record['status']} validation={record['validation_status']} reason={record['reason']}")
    print("report:", paths["html"])


def cmd_demo(args):
    csv_path = make_sample_csv(Path(args.out) / "sample_5m.csv")
    for sid in ("three_pm_momentum", "gamma_blast"):
        record, paths = run_full(sid, csv_path, out_root=args.out, symbol="DEMO", timeframe="5m")
        print(f"[{sid}] status={record['status']} validation={record['validation_status']} {record['reason']}")
        print("   report:", paths["html"])
''')
O("cli/main.py", r'''
"""CLI: python -m cli.main {demo|list|run}"""
import argparse
import sys

from cli import commands


def main(argv=None):
    ap = argparse.ArgumentParser(prog="svl")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").set_defaults(fn=commands.cmd_list)
    d = sub.add_parser("demo")
    d.add_argument("--out", default="runs")
    d.set_defaults(fn=commands.cmd_demo)
    r = sub.add_parser("run")
    r.add_argument("--strategy", required=True)
    r.add_argument("--data", required=True)
    r.add_argument("--out", default="runs")
    r.set_defaults(fn=commands.cmd_run)
    args = ap.parse_args(argv)
    args.fn(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
''')

# ---------------------------------------------------------------- config
O("config/risk_policy.json", json.dumps({"max_position_pct": 100.0, "max_drawdown_pct": 30.0, "on_violation": "halt"}, indent=2) + "\n")
O("config/execution_defaults.json", json.dumps({"initial_capital": 1000000.0, "slippage_bps": 2.0, "fee_pct": 0.0003,
  "risk_per_trade_pct": 1.0, "ambiguous_candle_policy": "stop_first"}, indent=2) + "\n")

# ---------------------------------------------------------------- Phase 8: frontend (typed client + types)
O("frontend/src/api/client.ts", r'''
const BASE: string = (globalThis as any).API_BASE ?? "http://localhost:8000";

export async function getJson<T>(path: string): Promise<T> {
  const r = await fetch(BASE + path);
  if (!r.ok) throw new Error(`GET ${path} failed: ${r.status}`);
  return (await r.json()) as T;
}

export async function postJson<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(BASE + path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  if (!r.ok) throw new Error(`POST ${path} failed: ${r.status}`);
  return (await r.json()) as T;
}
''')
O("frontend/src/types/strategy.ts", "export interface Strategy {\n  id: string;\n  version: string;\n  entry_point: string;\n  required_data: string[];\n  parameters: Record<string, unknown>;\n  execution_modes: string[];\n}\n")
O("frontend/src/types/backtest.ts", r'''
export interface Trade {
  entry_ts: string;
  exit_ts: string;
  entry_price: number;
  exit_price: number;
  qty: number;
  pnl: number;
  fees: number;
  reason: string;
}

export interface Run {
  run_id: string;
  strategy_id: string;
  strategy_version: string;
  source_hash: string;
  dataset_id: string;
  dataset_hash: string;
  status: string;
  parameters: Record<string, unknown>;
  config: Record<string, unknown>;
  engine_version: string;
  created_at: string;
}
''')
O("frontend/src/types/report.ts", "export interface Report {\n  run_id: string;\n  status: string;\n  metrics: Record<string, unknown>;\n  validation: Record<string, unknown>;\n  generated_at: string;\n}\n")
O("frontend/src/api/health.ts", 'import { getJson } from "./client";\nexport const getHealth = () => getJson<{ status: string }>("/health");\n')
O("frontend/src/api/strategies.ts", 'import { getJson } from "./client";\nimport { Strategy } from "../types/strategy";\nexport const listStrategies = () => getJson<Strategy[]>("/strategies");\nexport const getStrategy = (id: string) => getJson<Strategy>(`/strategies/${id}`);\n')
O("frontend/src/api/backtests.ts", 'import { getJson, postJson } from "./client";\nimport { Run } from "../types/backtest";\nexport const listRuns = () => getJson<Run[]>("/backtests");\nexport const getRun = (id: string) => getJson<Run>(`/backtests/${id}`);\nexport const startRun = (body: unknown) => postJson<Run>("/backtests", body);\n')
O("frontend/src/api/reports.ts", 'import { getJson } from "./client";\nimport { Report } from "../types/report";\nexport const getReport = (id: string) => getJson<Report>(`/reports/${id}`);\n')
O("frontend/vite.config.ts", 'import { defineConfig } from "vite";\nexport default defineConfig({ server: { port: 5173 } });\n')
O("frontend/tests/api.test.ts", "// TODO: vitest se client.ts ka test (fetch mock). Abhi placeholder.\nexport {};\n")

# ---------------------------------------------------------------- Phase 9: engines
O("engines/go/internal/contracts/contracts.go", r'''
package contracts

type JobStatus string

const (
	Queued    JobStatus = "QUEUED"
	Running   JobStatus = "RUNNING"
	Succeeded JobStatus = "SUCCEEDED"
	Failed    JobStatus = "FAILED"
)
''')
O("engines/go/internal/validation/validation.go", r'''
package validation

import "svl/validator/internal/contracts"

// IsTerminal: job ki antim avastha hai ya nahi.
func IsTerminal(s contracts.JobStatus) bool {
	return s == contracts.Succeeded || s == contracts.Failed
}
''')
O("engines/go/internal/validation/validation_test.go", r'''
package validation

import (
	"testing"

	"svl/validator/internal/contracts"
)

func TestIsTerminal(t *testing.T) {
	if !IsTerminal(contracts.Succeeded) || !IsTerminal(contracts.Failed) {
		t.Fatal("SUCCEEDED/FAILED terminal hone chahiye")
	}
	if IsTerminal(contracts.Queued) || IsTerminal(contracts.Running) {
		t.Fatal("QUEUED/RUNNING terminal nahi")
	}
}
''')
O("engines/go/cmd/validator/main.go", r'''
package main

import (
	"fmt"

	"svl/validator/internal/contracts"
	"svl/validator/internal/validation"
)

func main() {
	fmt.Println("validator ready; SUCCEEDED terminal =", validation.IsTerminal(contracts.Succeeded))
}
''')
O("engines/cpp/include/svl/rolling_stats.hpp", r'''
#pragma once
#include <cstddef>
#include <vector>

namespace svl {
// Pehle (window-1) entries NaN; baaki rolling mean.
std::vector<double> rolling_mean(const std::vector<double>& values, std::size_t window);
}
''')
O("engines/cpp/src/rolling_stats.cpp", r'''
#include "svl/rolling_stats.hpp"
#include <limits>

namespace svl {
std::vector<double> rolling_mean(const std::vector<double>& v, std::size_t window) {
    std::vector<double> out(v.size(), std::numeric_limits<double>::quiet_NaN());
    if (window == 0) return out;
    double sum = 0.0;
    for (std::size_t i = 0; i < v.size(); ++i) {
        sum += v[i];
        if (i >= window) sum -= v[i - window];
        if (i + 1 >= window) out[i] = sum / static_cast<double>(window);
    }
    return out;
}
}
''')
O("engines/cpp/tests/test_rolling_stats.cpp", r'''
#include "svl/rolling_stats.hpp"
#include <cassert>
#include <cmath>

int main() {
    auto r = svl::rolling_mean({1, 2, 3, 4, 5}, 3);  // parity: Python reference ke saath same
    assert(std::isnan(r[0]) && std::isnan(r[1]));
    assert(std::fabs(r[2] - 2.0) < 1e-12 && std::fabs(r[3] - 3.0) < 1e-12 && std::fabs(r[4] - 4.0) < 1e-12);
    return 0;
}
''')
O("engines/cpp/CMakeLists.txt", r'''
cmake_minimum_required(VERSION 3.16)
project(svl_engine CXX)
set(CMAKE_CXX_STANDARD 17)
add_library(svl_rolling src/rolling_stats.cpp)
target_include_directories(svl_rolling PUBLIC include)
enable_testing()
add_executable(test_rolling tests/test_rolling_stats.cpp)
target_link_libraries(test_rolling svl_rolling)
add_test(NAME rolling COMMAND test_rolling)
''')
O("engines/rust/Cargo.toml", '[package]\nname = "svl_engine"\nversion = "0.1.0"\nedition = "2021"\n')
O("engines/rust/src/lib.rs", r'''
/// Pehle (window-1) entries NaN; baaki rolling mean (Python reference ke saath parity).
pub fn rolling_mean(values: &[f64], window: usize) -> Vec<f64> {
    let mut out = vec![f64::NAN; values.len()];
    if window == 0 {
        return out;
    }
    let mut sum = 0.0;
    for i in 0..values.len() {
        sum += values[i];
        if i >= window {
            sum -= values[i - window];
        }
        if i + 1 >= window {
            out[i] = sum / window as f64;
        }
    }
    out
}
''')
O("engines/rust/tests/rolling_test.rs", r'''
use svl_engine::rolling_mean;

#[test]
fn parity_with_python_reference() {
    let r = rolling_mean(&[1.0, 2.0, 3.0, 4.0, 5.0], 3);
    assert!(r[0].is_nan() && r[1].is_nan());
    assert!((r[2] - 2.0).abs() < 1e-12 && (r[3] - 3.0).abs() < 1e-12 && (r[4] - 4.0).abs() < 1e-12);
}
''')
O("engines/reference/rolling_stats.py", r'''
"""Python reference: native (C++/Rust) result isi se match hona chahiye."""
import math


def rolling_mean(values, window):
    out, s = [math.nan] * len(values), 0.0
    if window <= 0:
        return out
    for i, v in enumerate(values):
        s += v
        if i >= window:
            s -= values[i - window]
        if i + 1 >= window:
            out[i] = s / window
    return out
''')
O("engines/bindings/native.py", r'''
"""Single interface. Native extension (`svl_native`) ho to wahi, warna Python reference.
Rule: C++ ko main calculation se tabhi jodo jab benchmark meaningful gain dikhaye."""
from engines.reference.rolling_stats import rolling_mean as _ref

try:
    import svl_native as _native  # optional compiled module
    rolling_mean = _native.rolling_mean
    BACKEND = "native"
except ImportError:
    rolling_mean = _ref
    BACKEND = "python-reference"
''')

# ---------------------------------------------------------------- tests
O("tests/_helpers.py", r'''
from data.models import Bar, Dataset
from strategies.base import Strategy
from strategies.models import Signal


def make_bars(n=20, start=100.0, step=1.0):
    bars, p = [], start
    for i in range(n):
        o = p + 0.3
        c = o + (step if i % 2 == 0 else -step / 2)
        bars.append(Bar(f"2024-01-01T{9 + i // 12:02d}:{(i % 12) * 5:02d}:00", o, max(o, c) + 0.1, min(o, c) - 0.1, c, 100.0))
        p = c
    return bars


def make_dataset(bars, fields=None):
    return Dataset("t", "T", "5m", bars, fields=fields or {"open", "high", "low", "close", "volume"}, quality_status="PASS")


class BuyAtIndex(Strategy):
    strategy_id = "buy_at_index"

    def on_bar(self, ctx):
        if ctx.index == self.params.get("at", 1) and ctx.position is None:
            return Signal("BUY", reason="test")
        return None
''')
O("tests/unit/backtest/test_fills.py", r'''
from backtest.fills import resolve_exit
from data.models import Bar


def test_ambiguous_candle_is_conservative():
    assert resolve_exit(Bar("t", 100, 110, 90, 105), 95, 108) == (95, "STOP_AMBIGUOUS_CONSERVATIVE")


def test_gap_down_fills_at_open():
    assert resolve_exit(Bar("t", 90, 92, 88, 91), 95, 108) == (90, "STOP")


def test_target_only_and_none():
    assert resolve_exit(Bar("t", 100, 110, 99, 105), 95, 108) == (108, "TARGET")
    assert resolve_exit(Bar("t", 100, 101, 99, 100), 95, 108) is None
''')
O("tests/unit/backtest/test_engine.py", r'''
from backtest.engine import run_backtest
from tests._helpers import BuyAtIndex, make_bars, make_dataset

NO_COST = {"slippage_bps": 0.0, "fee_pct": 0.0}


def test_entry_is_next_bar_open_not_signal_close():
    bars = make_bars(20)
    res = run_backtest(make_dataset(bars), BuyAtIndex({"at": 1}), NO_COST)
    t = res.trades[0]
    assert t["entry_ts"] == bars[2].ts
    assert t["entry_price"] == bars[2].open and t["entry_price"] != bars[1].close


def test_missing_required_data_is_blocked():
    class Needs(BuyAtIndex):
        required_data = ("option_chain",)
    res = run_backtest(make_dataset(make_bars(10)), Needs(), NO_COST)
    assert res.status == "BLOCKED" and res.reason == "MISSING_DATA:option_chain"


def test_bad_quality_is_blocked():
    ds = make_dataset(make_bars(10))
    ds.quality_status = "BLOCKED"
    assert run_backtest(ds, BuyAtIndex(), NO_COST).status == "BLOCKED"
''')
O("tests/unit/data/test_validators.py", r'''
from data.models import Bar
from data.validators import validate


def codes(bars):
    return {i["code"] for i in validate(bars)}


def test_inconsistent_ohlc_and_duplicates():
    assert "OHLC_INCONSISTENT" in codes([Bar("2024-01-01T09:15:00", 100, 90, 95, 99)])
    ok = Bar("2024-01-01T09:15:00", 100, 101, 99, 100)
    assert "DUPLICATE_TS" in codes([ok, ok])


def test_clean_data_has_no_issues():
    assert validate([Bar("2024-01-01T09:15:00", 100, 101, 99, 100), Bar("2024-01-01T09:20:00", 100, 102, 99, 101)]) == []
''')
O("tests/unit/risk/test_manager.py", r'''
from risk.limits import RiskLimits
from risk.manager import RiskManager


def test_position_limit_and_drawdown_kill():
    rm = RiskManager(RiskLimits(max_position_pct=50, max_drawdown_pct=10))
    assert rm.check_order(100, 100, 10000) == (False, "MAX_POSITION")
    assert rm.check_order(40, 100, 10000) == (True, "")
    assert rm.after_bar(10000) is False
    assert rm.after_bar(8900) is True and rm.kill.reason.startswith("MAX_DRAWDOWN")
    assert rm.check_order(1, 1, 10000) == (False, "KILL_SWITCH")
''')
O("tests/unit/metrics/test_trade_metrics.py", r'''
from metrics import trade_metrics


def test_trade_metrics():
    m = trade_metrics.compute([{"pnl": 10, "fees": 1}, {"pnl": -5, "fees": 1}, {"pnl": 5, "fees": 1}])
    assert m["n_trades"] == 3 and m["profit_factor"] == 3.0 and m["fees_total"] == 3
''')
O("tests/unit/backend/jobs/test_worker.py", r'''
from backend.jobs.job_status import JobStatus
from backend.jobs.queue import JobQueue
from backend.jobs.worker import run_next


def test_success_and_failure_reason_kept():
    q = JobQueue()
    a, b = q.submit({"x": 1}), q.submit({"x": 2})
    run_next(q, lambda p: {"ok": p["x"]})
    assert a.status == JobStatus.SUCCEEDED and a.result == {"ok": 1}

    def boom(_):
        raise RuntimeError("data missing")
    run_next(q, boom)
    assert b.status == JobStatus.FAILED and "data missing" in b.error
''')
O("tests/unit/registry/test_registry.py", r'''
from registry.lifecycle import can_transition
from registry.registry import Registry


def test_discover_and_load():
    reg = Registry()
    assert {"gamma_blast", "three_pm_momentum"} <= set(reg.discover())
    s = reg.load("three_pm_momentum", {"stop_pct": 0.7})
    assert s.params["stop_pct"] == 0.7 and s.params["target_pct"] == 1.0
    assert len(reg.source_hash("gamma_blast")) == 64


def test_lifecycle():
    assert can_transition("DRAFT", "VALIDATED") and not can_transition("DRAFT", "APPROVED")
''')
O("tests/unit/validation/test_pipeline.py", r'''
from tests._helpers import BuyAtIndex, make_bars, make_dataset
from validation.pipeline import overall_status, run_validation


def test_overall_status_rules():
    assert overall_status({"a": {"status": "PASS"}, "b": {"status": "UNAVAILABLE"}}) == "INCOMPLETE"
    assert overall_status({"a": {"status": "FAIL"}, "b": {"status": "UNAVAILABLE"}}) == "FAIL"
    assert overall_status({"a": {"status": "PASS"}}) == "PASS"


def test_pipeline_never_passes_unimplemented_checks():
    res = run_validation(make_dataset(make_bars(200)), lambda: BuyAtIndex({"at": 1}))
    assert "leakage" in res["checks"] and res["status"] != "PASS"
    assert res["checks"]["cross_validation"]["status"] == "UNAVAILABLE"
''')
O("tests/integration/test_end_to_end_backtest.py", r'''
from pathlib import Path

from backend.services.backtest_service import run_full
from cli.commands import make_sample_csv
from contracts import schema_check


def test_full_flow_creates_verified_artifacts(tmp_path):
    csv = make_sample_csv(tmp_path / "s.csv", days=40)
    record, paths = run_full("three_pm_momentum", csv, out_root=str(tmp_path / "runs"))
    assert record["status"] in ("COMPLETED", "HALTED")
    assert not schema_check.check(record, schema_check.load("run.schema.json"))
    for k in ("json", "html", "csv"):
        assert Path(paths[k]).exists()
    assert (tmp_path / "runs" / "audit.jsonl").exists()
''')
O("tests/integration/test_blocked_missing_data.py", r'''
from backend.services.backtest_service import run_full
from cli.commands import make_sample_csv


def test_option_strategy_blocked_without_option_chain(tmp_path):
    csv = make_sample_csv(tmp_path / "s.csv", days=10)
    record, _ = run_full("gamma_blast", csv, out_root=str(tmp_path / "runs"))
    assert record["status"] == "BLOCKED" and record["reason"].startswith("MISSING_DATA")
    assert record["validation_status"] == "BLOCKED"
''')
O("tests/contract/test_signal_contract.py", r'''
from contracts import schema_check
from strategies.models import Signal


def test_signal_matches_contract():
    assert not schema_check.check(Signal("BUY", stop_loss=1.0, target=2.0).to_dict(), schema_check.load("signal.schema.json"))
''')
O("tests/contract/test_openapi_contract.py", r'''
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATHS = ["/health", "/strategies", "/backtests", "/validations/{id}", "/comparisons", "/reports/{id}", "/audit"]


def test_openapi_lists_all_routes_and_client_uses_them():
    spec = (ROOT / "contracts/openapi.yaml").read_text(encoding="utf-8")
    assert all(p in spec for p in PATHS)
    client = "".join(f.read_text(encoding="utf-8") for f in (ROOT / "frontend/src/api").glob("*.ts"))
    for p in ("/health", "/strategies", "/backtests", "/reports/"):
        assert p in client
''')
O("tests/contract/test_strategy_contract.py", r'''
from contracts import schema_check
from registry.registry import Registry


def test_all_manifests_match_contract():
    reg = Registry()
    for sid in reg.discover():
        assert not schema_check.check(reg.manifest(sid), schema_check.load("strategy.schema.json")), sid
''')
O("tests/contract/test_data_contract.py", r'''
from cli.commands import make_sample_csv
from contracts import schema_check
from data.loaders import load_dataset


def test_dataset_meta_matches_contract(tmp_path):
    ds = load_dataset(make_sample_csv(tmp_path / "s.csv", days=5), symbol="X", timeframe="5m")
    assert ds.quality_status == "PASS"
    assert not schema_check.check(ds.meta(), schema_check.load("data.schema.json"))
''')
O("tests/contract/test_trade_contract.py", r'''
from backtest.engine import run_backtest
from contracts import schema_check
from tests._helpers import BuyAtIndex, make_bars, make_dataset


def test_trades_match_contract():
    res = run_backtest(make_dataset(make_bars(20)), BuyAtIndex({"at": 1}))
    assert res.trades
    for t in res.trades:
        assert not schema_check.check(t, schema_check.load("trade.schema.json"))
''')
O("tests/contract/test_run_contract.py", r'''
from backend.services.backtest_service import run_full
from cli.commands import make_sample_csv
from contracts import schema_check


def test_run_record_matches_contract(tmp_path):
    rec, _ = run_full("three_pm_momentum", make_sample_csv(tmp_path / "s.csv", days=10), out_root=str(tmp_path / "r"))
    assert not schema_check.check(rec, schema_check.load("run.schema.json"))
''')
O("tests/contract/test_report_contract.py", r'''
from backend.services.backtest_service import run_full
from cli.commands import make_sample_csv
from contracts import schema_check
import json


def test_report_matches_contract(tmp_path):
    _, paths = run_full("three_pm_momentum", make_sample_csv(tmp_path / "s.csv", days=10), out_root=str(tmp_path / "r"))
    report = json.loads(open(paths["json"], encoding="utf-8").read())
    assert not schema_check.check(report, schema_check.load("report.schema.json"))
''')
O("tests/contract/test_types_vs_contracts.py", r'''
from pathlib import Path

from contracts import schema_check

TS = Path(__file__).resolve().parents[2] / "frontend/src/types"


def _fields(schema_name, ts_file):
    text = (TS / ts_file).read_text(encoding="utf-8")
    return [k for k in schema_check.load(schema_name)["required"] if f"{k}:" not in text]


def test_ts_types_cover_schema_fields():
    assert _fields("trade.schema.json", "backtest.ts") == []
    assert _fields("run.schema.json", "backtest.ts") == []
    assert _fields("report.schema.json", "report.ts") == []
    assert _fields("strategy.schema.json", "strategy.ts") == []
''')
O("tests/contract/test_rolling_stats_parity.py", r'''
import math

from engines.bindings import native
from engines.reference.rolling_stats import rolling_mean as ref


def test_native_matches_reference():
    vals = [1.0, 2.0, 3.0, 4.0, 5.0, 9.0, 2.5]
    a, b = native.rolling_mean(vals, 3), ref(vals, 3)
    assert len(a) == len(b)
    for x, y in zip(a, b):
        assert (math.isnan(x) and math.isnan(y)) or abs(x - y) < 1e-9


def test_known_values():  # C++ aur Rust tests me bhi yahi values hain
    r = ref([1, 2, 3, 4, 5], 3)
    assert math.isnan(r[0]) and math.isnan(r[1]) and r[2:] == [2.0, 3.0, 4.0]
''')


# ================================================================= PHASE 12 (README v1.0 ke baaki hisse)
_P12 = []

def F(path, purpose, text, deps=()):
    _P12.append((path, purpose, list(deps)))
    O(path, text)

# ---- root files
F("LICENSE", "License placeholder (license aap chunenge)", "All rights reserved.\n\nPLACEHOLDER: apni pasand ka license (MIT/Apache-2.0/proprietary) yahan lagayein.\n")
F("CHANGELOG.md", "Version history", "# Changelog\n\n## 0.1.0\n- Scaffold + data, backtest, risk, validation, metrics, reporting, CLI (placeholder strategies).\n")
F("CONTRIBUTING.md", "Contribution rules", "# Contributing\n\n1. `python -m pytest -q` pass hona chahiye.\n2. Naya module = uska test + `docs/` me jikr.\n3. Contract (`contracts/`) badle to saare consumers + contract tests update.\n4. Koi strategy PASS validation ke bina `APPROVED` nahi.\n")
F("SECURITY.md", "Security reporting", "# Security\n\nVulnerability public issue me mat daalo; repo owner ko private roop se batao.\nSecrets (`.env`, tokens, broker keys) kabhi commit nahi.\n")
F("requirements.lock", "Pinned deps (core abhi stdlib-only)", "# Core system sirf Python stdlib use karta hai.\npytest>=7\n# Optional: fastapi, uvicorn, pyarrow\n")
F(".env.example", "Env variables ka namuna", "DATABASE_URL=\nAPI_BASE=http://localhost:8000\nLOG_LEVEL=INFO\n# Broker keys yahan nahi, secret manager me rakho\n")
F(".editorconfig", "Editor settings", "root = true\n\n[*]\nindent_style = space\nindent_size = 4\nend_of_line = lf\ninsert_final_newline = true\ncharset = utf-8\n\n[*.{ts,json,yaml,yml,css,html}]\nindent_size = 2\n")
F(".pre-commit-config.yaml", "Commit se pehle tests", "repos:\n  - repo: local\n    hooks:\n      - id: pytest\n        name: pytest\n        entry: python -m pytest -q\n        language: system\n        pass_filenames: false\n")
F(".github/workflows/ci.yml", "GitHub Actions: har push par tests", r'''
name: ci
on: [push, pull_request]
jobs:
  python-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install pytest
      - run: python -m pytest -q
''')
F("artifacts/.gitkeep", "Artifacts folder (content git me nahi)", "")
F("output/.gitkeep", "Output folder (content git me nahi)", "")
O(".gitignore", "__pycache__/\n*.pyc\n.venv/\nruns/\ndata/samples/\nnode_modules/\ntarget/\nbuild/\ndist/\n.pytest_cache/\n.env\nartifacts/*\n!artifacts/.gitkeep\noutput/*\n!output/.gitkeep\n")

# ---- config yaml (backtest/costs/risk asli me load hote hain; baaki planned)
_pl = "# NOTE: abhi code me wired nahi (planned). Asli load: backtest.yaml, costs.yaml, risk.yaml.\n"
F("config/backtest.yaml", "Capital + sizing + ambiguous candle rule (LOADED)", "initial_capital: 1000000\nrisk_per_trade_pct: 1.0\nambiguous_candle_policy: stop_first\n")
F("config/costs.yaml", "Slippage + fees (LOADED)", "slippage_bps: 2.0\nfee_pct: 0.0003\n")
F("config/risk.yaml", "Risk limits (LOADED)", "max_position_pct: 100.0\nmax_drawdown_pct: 30.0\non_violation: halt\n")
F("config/system.yaml", "System settings", _pl + "env: dev\nlive_trading_enabled: false\n")
F("config/data.yaml", "Data settings", _pl + "default_timezone: UTC\nmax_gap_bars: 3\n")
F("config/validation.yaml", "Validation thresholds", _pl + "oos_split: 0.7\nwalk_forward_windows: 4\nmin_trades: 30\n")
F("config/reporting.yaml", "Reporting settings", _pl + "formats: [json, csv, html]\n")
F("config/logging.yaml", "Logging settings", _pl + "level: INFO\njson: true\n")

# ---- docs
def _doc(name, title, body):
    F(f"docs/{name}", title, f"# {title}\n\n{body.strip()}\n")
_doc("ARCHITECTURE.md", "Architecture", "Flow: frontend -> backend API -> services -> registry -> data -> strategy -> backtest(+risk) -> validation -> metrics -> reporting -> persistence.\nDetail: `architecture/BUILD_ORDER.md`, `architecture/WIRING_MAP.json`.\nRule: koi file apni zimmedari ke bahar kaam nahi karti.")
_doc("REPOSITORY_MAP.md", "Repository map", "Har folder ki zimmedari: data (load+validate), strategies+registry, backtest+risk, validation, metrics, reporting, persistence, backend, cli, engines (Go/C++/Rust), contracts, frontend, indicators, observability.\nFile-level map: `architecture/WIRING_MAP.json`.")
_doc("STRATEGY_CONTRACT.md", "Strategy contract", "Manifest keys: id, version, entry_point, required_data, parameters, execution_modes (`contracts/strategy.schema.json`).\nSignal: side (BUY/EXIT), stop_loss, target, size_hint, reason (`contracts/signal.schema.json`).\nv0: long-only. Required data na mile => backtest BLOCKED.")
_doc("DATA_CONTRACT.md", "Data contract", "Dataset metadata: dataset_id, symbol, timeframe, start/end time, timezone, source, schema_version, content_hash, quality_status.\nChecks: duplicate/out-of-order timestamp, non-positive price, inconsistent OHLC. Koi ERROR => BLOCKED.")
_doc("BACKTEST_ENGINE.md", "Backtest engine", "Signal bar ke close par; fill agli bar ke open par (no look-ahead). Slippage + fees lagte hain.\nEk candle me stop aur target dono => stop pehle (conservative). Gap-down => open par fill.\nRisk: max position, max drawdown => kill switch (HALTED).")
_doc("VALIDATION_POLICY.md", "Validation policy", "Checks: leakage, out-of-sample, walk-forward, overfitting, statistical confidence (asli); cross-validation, robustness, regime (abhi UNAVAILABLE).\nOverall: koi FAIL => FAIL; koi UNAVAILABLE => INCOMPLETE; sab PASS => PASS. UNAVAILABLE kabhi PASS nahi.")
_doc("METRICS_DICTIONARY.md", "Metrics dictionary", "final_equity, total_return_pct, max_drawdown_pct, sharpe_daily, n_trades, total_pnl, fees_total, avg_win, avg_loss, profit_factor, win_rate_pct, expectancy, expectancy_ci95, buy_and_hold_return_pct.\nMetrics sirf ginti karte hain; approval validation pipeline se.")
_doc("SECURITY_POLICY.md", "Security policy", "WARNING: registry strategy code ko isi process me import karta hai. Untrusted code ke liye alag process + limited permissions + resource limits zaroori (abhi nahi bana).\nSecrets git me nahi. Live trading default disabled.")
_doc("TESTING_POLICY.md", "Testing policy", "unit (har module), integration (end-to-end), contract (schemas), regression (known result), property (accounting invariants), performance (loose benchmark), no-lookahead, reproducibility, execution-cost tests.")
_doc("DEPLOYMENT.md", "Deployment", "Local: `./scripts/setup_truemax.sh`. Docker: `docker compose -f infra/docker-compose.yml up --build`. CI: `.github/workflows/ci.yml`.")
_doc("DECISION_GATES.md", "Decision gates", "Gate 1: data quality PASS. Gate 2: backtest COMPLETED. Gate 3: validation PASS (koi UNAVAILABLE nahi). Gate 4: manual approval. Live trading in sab ke bina nahi, aur abhi system me live execution hai hi nahi.")
_doc("adr/ADR-001-LANGUAGE-BOUNDARIES.md", "ADR-001 Language boundaries", "Python = orchestration/backtest/validation. Go = validator service. C++/Rust = benchmark-proven numeric kernels, parity tests ke saath. Ek calculation ka ek owner.")
_doc("adr/ADR-002-DATA-CONTRACTS.md", "ADR-002 Data contracts", "Contracts `contracts/` me; consumers (Python/TS/Go) unse bandhe; contract tests mismatch pakadte hain.")
_doc("adr/ADR-003-EXECUTION-MODEL.md", "ADR-003 Execution model", "Next-bar-open fill, conservative stop-first, slippage bps + fee pct, long-only v0.")

# ---- frontend styles + public
F("frontend/public/favicon.svg", "Favicon", '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="6" fill="#2563eb"/><path d="M5 22l7-8 5 4 10-12" stroke="#fff" stroke-width="3" fill="none"/></svg>\n')
F("frontend/public/logo.svg", "Logo", '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 32"><text x="0" y="23" font-family="sans-serif" font-size="20" fill="#2563eb">Strategy Lab</text></svg>\n')
F("frontend/src/styles/base.css", "Base styles", ":root{--bg:#fff;--fg:#111;--accent:#2563eb}\n@media (prefers-color-scheme:dark){:root{--bg:#111;--fg:#eee}}\nbody{margin:0;font-family:system-ui,sans-serif;background:var(--bg);color:var(--fg)}\n")
F("frontend/src/styles/layout.css", "Layout", ".layout{display:grid;grid-template-columns:200px 1fr;min-height:100vh}\n@media(max-width:700px){.layout{grid-template-columns:1fr}}\n")
F("frontend/src/styles/components.css", "Components", ".card{border:1px solid #8884;border-radius:8px;padding:12px}\n.badge{padding:2px 8px;border-radius:10px;font-size:12px}\n.badge.pass{background:#16a34a;color:#fff}.badge.fail{background:#dc2626;color:#fff}.badge.blocked{background:#f59e0b}\n")
F("frontend/src/styles/dashboard.css", "Dashboard", ".grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px}\n")

# ---- strategies extras
F("strategies/examples/example_strategy.py", "Example strategy (template)", r'''
"""Example: naya strategy banane ka template. index 1 par BUY, stop/target % se."""
from strategies.base import Strategy
from strategies.models import Signal


class ExampleStrategy(Strategy):
    strategy_id = "example"
    required_data = ()

    def on_bar(self, ctx):
        if ctx.index == 1 and ctx.position is None:
            c = ctx.bar.close
            return Signal("BUY", stop_loss=round(c * 0.99, 2), target=round(c * 1.02, 2), reason="example")
        return None
''', ["strategies/base.py"])
F("strategies/examples/example_strategy.yaml", "Example manifest (discover nahi hota)", "id: example\nversion: 0.1.0\nentry_point: strategies.examples.example_strategy:ExampleStrategy\nrequired_data: []\nparameters: {}\nexecution_modes: [backtest]\n")
F("strategies/gamma_blast/config.yaml", "GammaBlast tunable params (placeholder)", "# Asli parameters yahan aayenge\nparameters: {}\n")
F("strategies/three_pm_momentum/config.yaml", "ThreePM tunable params", "stop_pct: 0.5\ntarget_pct: 1.0\nentry_hour: 15\nentry_minute: 0\nexit_hour: 15\nexit_minute: 25\n")

# ---- indicators (real, stdlib)
F("indicators/trend.py", "SMA / EMA", r'''
def sma(values, n):
    out, s = [None] * len(values), 0.0
    for i, v in enumerate(values):
        s += v
        if i >= n:
            s -= values[i - n]
        if i >= n - 1:
            out[i] = s / n
    return out


def ema(values, n):
    out, k, prev = [None] * len(values), 2.0 / (n + 1), None
    for i, v in enumerate(values):
        if i == n - 1:
            prev = sum(values[:n]) / n
            out[i] = prev
        elif i >= n:
            prev = v * k + prev * (1 - k)
            out[i] = prev
    return out
''')
F("indicators/momentum.py", "RSI (Wilder) / ROC", r'''
def _rsi(ag, al):
    return 100.0 if al == 0 else 100.0 - 100.0 / (1 + ag / al)


def rsi(closes, n=14):
    out = [None] * len(closes)
    if len(closes) <= n:
        return out
    gains = losses = 0.0
    for i in range(1, n + 1):
        d = closes[i] - closes[i - 1]
        gains, losses = gains + max(d, 0), losses + max(-d, 0)
    ag, al = gains / n, losses / n
    out[n] = _rsi(ag, al)
    for i in range(n + 1, len(closes)):
        d = closes[i] - closes[i - 1]
        ag, al = (ag * (n - 1) + max(d, 0)) / n, (al * (n - 1) + max(-d, 0)) / n
        out[i] = _rsi(ag, al)
    return out


def roc(values, n):
    return [None if i < n else (v / values[i - n] - 1) * 100.0 for i, v in enumerate(values)]
''')
F("indicators/volatility.py", "True range / ATR (Wilder)", r'''
def true_range(bars):
    out = []
    for i, b in enumerate(bars):
        if i == 0:
            out.append(b.high - b.low)
        else:
            pc = bars[i - 1].close
            out.append(max(b.high - b.low, abs(b.high - pc), abs(b.low - pc)))
    return out


def atr(bars, n=14):
    tr, out = true_range(bars), [None] * len(bars)
    if len(bars) < n:
        return out
    prev = sum(tr[:n]) / n
    out[n - 1] = prev
    for i in range(n, len(bars)):
        prev = (prev * (n - 1) + tr[i]) / n
        out[i] = prev
    return out
''')
F("indicators/volume.py", "VWAP (daily reset) / OBV", r'''
def vwap(bars):
    out, day, pv, vol = [], None, 0.0, 0.0
    for b in bars:
        if b.ts[:10] != day:
            day, pv, vol = b.ts[:10], 0.0, 0.0
        pv += (b.high + b.low + b.close) / 3.0 * b.volume
        vol += b.volume
        out.append(pv / vol if vol else None)
    return out


def obv(bars):
    out, total = [0.0], 0.0
    for i in range(1, len(bars)):
        total += bars[i].volume if bars[i].close > bars[i - 1].close else -bars[i].volume if bars[i].close < bars[i - 1].close else 0.0
        out.append(total)
    return out[: len(bars)]
''')
F("indicators/market_structure.py", "Swing pivots (confirmed, no look-ahead)", r'''
"""Pivot sirf `right` bars baad confirm hota hai: result me confirm_index se pehle use mat karo."""


def _pivots(vals, left, right, better):
    out = []
    for i in range(left, len(vals) - right):
        if all(better(vals[i], vals[j]) for j in range(i - left, i)) and \
           all(not better(vals[j], vals[i]) for j in range(i + 1, i + right + 1)):
            out.append({"index": i, "confirm_index": i + right, "price": vals[i]})
    return out


def pivot_highs(bars, left=2, right=2):
    return _pivots([b.high for b in bars], left, right, lambda a, b: a > b)


def pivot_lows(bars, left=2, right=2):
    return _pivots([b.low for b in bars], left, right, lambda a, b: a < b)
''')
F("indicators/options_greeks.py", "Black-Scholes price + Greeks (European, no dividends)", r'''
import math


def _cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _pdf(x):
    return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)


def _d(S, K, T, r, sigma):
    if S <= 0 or K <= 0 or T <= 0 or sigma <= 0:
        raise ValueError("S, K, T, sigma > 0 hone chahiye")
    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
    return d1, d1 - sigma * math.sqrt(T)


def price(S, K, T, r, sigma, kind="call"):
    d1, d2 = _d(S, K, T, r, sigma)
    if kind == "call":
        return S * _cdf(d1) - K * math.exp(-r * T) * _cdf(d2)
    return K * math.exp(-r * T) * _cdf(-d2) - S * _cdf(-d1)


def delta(S, K, T, r, sigma, kind="call"):
    d1, _ = _d(S, K, T, r, sigma)
    return _cdf(d1) if kind == "call" else _cdf(d1) - 1


def gamma(S, K, T, r, sigma):
    d1, _ = _d(S, K, T, r, sigma)
    return _pdf(d1) / (S * sigma * math.sqrt(T))


def vega(S, K, T, r, sigma):
    d1, _ = _d(S, K, T, r, sigma)
    return S * _pdf(d1) * math.sqrt(T)
''')
O("tests/unit/indicators/test_trend.py", r'''
from indicators.trend import ema, sma


def test_sma_and_ema():
    assert sma([1, 2, 3, 4, 5], 3) == [None, None, 2.0, 3.0, 4.0]
    e = ema([1, 2, 3, 4, 5], 3)
    assert e[:2] == [None, None] and e[2] == 2.0 and abs(e[3] - 3.0) < 1e-12
''')
O("tests/unit/indicators/test_momentum.py", r'''
from indicators.momentum import roc, rsi


def test_rsi_bounds_and_roc():
    up = rsi([float(i) for i in range(1, 30)], 14)
    assert up[14] == 100.0 and up[0] is None
    mixed = [x for x in rsi([10, 11, 10.5, 12, 11, 13, 12, 14, 13, 15, 14, 16, 15, 17, 16, 18], 14) if x is not None]
    assert all(0 <= x <= 100 for x in mixed)
    assert roc([100, 110], 1) == [None, 10.000000000000009] or abs(roc([100, 110], 1)[1] - 10) < 1e-9
''')
O("tests/unit/indicators/test_volatility.py", r'''
from indicators.volatility import atr, true_range
from tests._helpers import make_bars


def test_atr_positive_and_warmup():
    bars = make_bars(30)
    a = atr(bars, 14)
    assert a[12] is None and a[13] > 0
    assert all(t >= 0 for t in true_range(bars))
''')
O("tests/unit/indicators/test_volume.py", r'''
from data.models import Bar
from indicators.volume import obv, vwap


def test_vwap_first_bar_and_daily_reset():
    bars = [Bar("2024-01-01T09:15:00", 10, 12, 8, 10, 100), Bar("2024-01-02T09:15:00", 20, 22, 18, 20, 50)]
    v = vwap(bars)
    assert abs(v[0] - 10.0) < 1e-9 and abs(v[1] - 20.0) < 1e-9
    assert obv(bars) == [0.0, 50.0]
''')
O("tests/unit/indicators/test_market_structure.py", r'''
from data.models import Bar
from indicators.market_structure import pivot_highs


def test_pivot_is_confirmed_after_right_bars():
    highs = [1, 2, 5, 2, 1, 2, 3]
    bars = [Bar(f"2024-01-01T09:{i:02d}:00", h, h, h, h) for i, h in enumerate(highs)]
    p = pivot_highs(bars, 2, 2)
    assert p == [{"index": 2, "confirm_index": 4, "price": 5}]
''')
O("tests/unit/indicators/test_options_greeks.py", r'''
import math

from indicators import options_greeks as g


def test_put_call_parity_and_greek_signs():
    S, K, T, r, s = 100.0, 100.0, 0.5, 0.05, 0.2
    c, p = g.price(S, K, T, r, s, "call"), g.price(S, K, T, r, s, "put")
    assert abs((c - p) - (S - K * math.exp(-r * T))) < 1e-9
    assert 0 < g.delta(S, K, T, r, s) < 1 and -1 < g.delta(S, K, T, r, s, "put") < 0
    assert g.gamma(S, K, T, r, s) > 0 and g.vega(S, K, T, r, s) > 0
''')

# ---- observability
F("observability/logging.py", "JSON logging setup", r'''
import json
import logging as _logging


class _Json(_logging.Formatter):
    def format(self, record):
        return json.dumps({"level": record.levelname, "name": record.name, "msg": record.getMessage()})


def setup_logging(level="INFO", as_json=True):
    h = _logging.StreamHandler()
    h.setFormatter(_Json() if as_json else _logging.Formatter("%(levelname)s %(name)s %(message)s"))
    root = _logging.getLogger()
    root.handlers[:] = [h]
    root.setLevel(level)
    return root
''')
F("observability/metrics.py", "In-process counters", r'''
_counters = {}


def inc(name, n=1):
    _counters[name] = _counters.get(name, 0) + n


def snapshot():
    return dict(_counters)


def reset():
    _counters.clear()
''')
F("observability/tracing.py", "Simple timing spans", r'''
import time
from contextlib import contextmanager

SPANS = []


@contextmanager
def span(name):
    t = time.perf_counter()
    try:
        yield
    finally:
        SPANS.append({"name": name, "seconds": time.perf_counter() - t})
''')
F("observability/health.py", "Health report", r'''
import sys

from registry.registry import Registry


def check_health():
    try:
        n = len(Registry().discover())
        return {"status": "ok", "python": sys.version.split()[0], "strategies": n}
    except Exception as e:  # noqa: BLE001
        return {"status": "degraded", "error": f"{type(e).__name__}: {e}"}
''')
O("tests/unit/observability/test_metrics.py", r'''
from observability import metrics, tracing


def test_counters_and_spans():
    metrics.reset()
    metrics.inc("runs")
    metrics.inc("runs", 2)
    assert metrics.snapshot() == {"runs": 3}
    with tracing.span("x"):
        pass
    assert tracing.SPANS[-1]["name"] == "x"
''')
O("tests/unit/observability/test_health.py", r'''
from observability.health import check_health


def test_health_ok():
    h = check_health()
    assert h["status"] == "ok" and h["strategies"] >= 2
''')
O("tests/unit/observability/test_logging.py", r'''
import json
import logging

from observability.logging import setup_logging


def test_json_log_format(capsys):
    setup_logging("INFO")
    logging.getLogger("t").info("hello")
    line = capsys.readouterr().err.strip().splitlines()[-1]
    assert json.loads(line)["msg"] == "hello"
''')

# ---- backend schema + cli formatting
F("backend/schemas/validation.py", "Validation request/response models", r'''
from dataclasses import dataclass, field


@dataclass
class ValidationRequest:
    strategy_id: str
    dataset_path: str
    params: dict = field(default_factory=dict)


@dataclass
class ValidationResponse:
    run_id: str
    status: str
    checks: dict = field(default_factory=dict)
''')
F("cli/formatting.py", "Metrics ko text table banana", r'''
def format_metrics(metrics):
    width = max((len(k) for k in metrics), default=0)
    return "\n".join(f"{k:<{width}}  {v}" for k, v in metrics.items())
''')
O("tests/unit/cli/test_formatting.py", r'''
from cli.formatting import format_metrics


def test_format_metrics():
    out = format_metrics({"a": 1, "long_name": 2})
    assert out.splitlines()[0].startswith("a         ") and "long_name  2" in out
''')

# ---- persistence migration
F("persistence/migrations/001_initial.sql", "Initial PostgreSQL schema", r'''
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    strategy_id TEXT NOT NULL,
    strategy_version TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    dataset_id TEXT NOT NULL,
    dataset_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    validation_status TEXT,
    parameters JSONB NOT NULL,
    config JSONB NOT NULL,
    engine_version TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    ts TIMESTAMPTZ NOT NULL,
    event TEXT NOT NULL,
    data JSONB
);
''')

# ---- engine READMEs + rust contract test
F("engines/go/README.md", "Go engine", "# Go validator\n\n`go test ./...` (engines/go). Python se sambandh sirf `contracts/` ke zariye.\n")
F("engines/cpp/README.md", "C++ engine", "# C++ rolling stats\n\nBuild: `cmake -S . -B build && cmake --build build && ctest --test-dir build`.\nParity: Python reference (`engines/reference`).\n")
F("engines/rust/README.md", "Rust engine", "# Rust numeric library\n\n`cargo test` (engines/rust). Parity: Python reference.\n")
F("engines/rust/tests/contract_tests.rs", "Rust contract test", r'''
use svl_engine::rolling_mean;

#[test]
fn window_zero_gives_all_nan() {
    assert!(rolling_mean(&[1.0, 2.0], 0).iter().all(|x| x.is_nan()));
}

#[test]
fn output_length_matches_input() {
    assert_eq!(rolling_mean(&[1.0, 2.0, 3.0], 2).len(), 3);
}
''', ["engines/rust/src/lib.rs"])

# ---- scripts
F("scripts/run_tests.sh", "Python tests", "#!/usr/bin/env bash\nset -euo pipefail\ncd \"$(dirname \"$0\")/..\"\npython -m pytest -q \"$@\"\n")
F("scripts/run_backtest.sh", "Ek strategy ka backtest", "#!/usr/bin/env bash\n# Usage: scripts/run_backtest.sh <strategy_id> <data.csv>\nset -euo pipefail\ncd \"$(dirname \"$0\")/..\"\npython -m cli.main run --strategy \"$1\" --data \"$2\"\n")
F("scripts/build_frontend.sh", "Frontend build", "#!/usr/bin/env bash\nset -euo pipefail\ncd \"$(dirname \"$0\")/../frontend\"\nnpm install\nnpx tsc --noEmit\n")
F("scripts/generate_report.sh", "Demo report", "#!/usr/bin/env bash\nset -euo pipefail\ncd \"$(dirname \"$0\")/..\"\npython -m cli.main demo --out output\n")

# ---- infra
F("infra/Dockerfile", "Container image", "FROM python:3.12-slim\nWORKDIR /app\nCOPY . .\nRUN pip install --no-cache-dir pytest\nCMD [\"python\", \"-m\", \"cli.main\", \"demo\"]\n")
F("infra/docker-compose.yml", "Compose", "services:\n  lab:\n    build:\n      context: ..\n      dockerfile: infra/Dockerfile\n    volumes:\n      - ../output:/app/runs\n")
F("infra/nginx.conf", "Reverse proxy (frontend + API)", "server {\n  listen 80;\n  location /api/ { proxy_pass http://backend:8000/; }\n  location / { root /usr/share/nginx/html; try_files $uri /index.html; }\n}\n")
F("infra/ci/pipeline.yml", "CI pipeline (generic copy)", "# Primary CI: .github/workflows/ci.yml\nsteps:\n  - pip install pytest\n  - python -m pytest -q\n")

# ---- tests (README ke naam)
F("tests/fixtures/sample_ohlcv.csv", "Chhota OHLCV fixture (oi column ke saath)", "ts,open,high,low,close,volume,oi\n2024-01-01T09:15:00,100,101,99,100.5,1000,5000\n2024-01-01T09:20:00,100.5,102,100,101.5,1200,5100\n2024-01-01T09:25:00,101.5,103,101,102,900,5200\n2024-01-01T09:30:00,102,102.5,100.5,101,1100,5150\n2024-01-01T09:35:00,101,101.5,99.5,100,800,5300\n2024-01-01T09:40:00,100,101,99,100.8,950,5350\n")
F("tests/fixtures/expected_results.json", "Known result (regression)", json.dumps({"days": 20, "seed": 42, "strategy": "three_pm_momentum", "n_trades": 10, "total_pnl": -10324.498}, indent=2) + "\n")
F("tests/unit/test_data.py", "Fixture CSV load", r'''
from pathlib import Path

from data.loaders import load_dataset

FIX = Path(__file__).resolve().parents[1] / "fixtures"


def test_fixture_loads_with_extra_fields():
    ds = load_dataset(FIX / "sample_ohlcv.csv", symbol="X", timeframe="5m")
    assert ds.quality_status == "PASS" and "oi" in ds.fields and len(ds.bars) == 6
    assert len(ds.content_hash) == 64
''', ["data/loaders.py"])
F("tests/unit/test_registry.py", "Registry smoke", "from registry.registry import Registry\n\n\ndef test_two_strategies_registered():\n    assert {'gamma_blast', 'three_pm_momentum'} <= set(Registry().discover())\n", ["registry/registry.py"])
F("tests/unit/test_backtest.py", "Backtest smoke", r'''
from backtest.engine import run_backtest
from tests._helpers import BuyAtIndex, make_bars, make_dataset


def test_runs_and_closes_position():
    res = run_backtest(make_dataset(make_bars(30)), BuyAtIndex({"at": 2}))
    assert res.status == "COMPLETED" and len(res.trades) == 1
''', ["backtest/engine.py"])
F("tests/unit/test_metrics.py", "Metrics smoke", r'''
from backtest.engine import run_backtest
from metrics import compute_all
from tests._helpers import BuyAtIndex, make_bars, make_dataset


def test_compute_all_keys():
    ds = make_dataset(make_bars(30))
    m = compute_all(run_backtest(ds, BuyAtIndex({"at": 2})), ds)
    assert {"total_return_pct", "max_drawdown_pct", "n_trades", "win_rate_pct", "expectancy"} <= set(m)
''', ["metrics/return_metrics.py"])
F("tests/unit/test_risk.py", "Risk smoke", "from risk.manager import RiskManager\n\n\ndef test_default_allows_small_order():\n    assert RiskManager().check_order(1, 100, 10000) == (True, '')\n", ["risk/manager.py"])
F("tests/unit/test_config.py", "Config files actually load", r'''
from backend.services.backtest_service import load_config


def test_yaml_config_loaded_and_policy_key_removed():
    cfg = load_config()
    assert cfg["slippage_bps"] == 2.0 and cfg["fee_pct"] == 0.0003
    assert cfg["max_drawdown_pct"] == 30.0 and "on_violation" not in cfg
''', ["backend/services/backtest_service.py"])
F("tests/integration/test_strategy_pipeline.py", "registry -> data -> engine -> metrics", r'''
from backtest.engine import run_backtest
from cli.commands import make_sample_csv
from data.loaders import load_dataset
from metrics import compute_all
from registry.registry import Registry


def test_pipeline(tmp_path):
    ds = load_dataset(make_sample_csv(tmp_path / "s.csv", days=15))
    res = run_backtest(ds, Registry().load("three_pm_momentum"))
    assert res.status == "COMPLETED" and "n_trades" in compute_all(res, ds)
''', ["backtest/engine.py"])
F("tests/integration/test_api.py", "Health/audit payloads (+FastAPI ho to routes)", r'''
import pytest

from backend.api.audit import read_audit
from backend.api.health import health_payload


def test_payloads(tmp_path):
    assert health_payload() == {"status": "ok"}
    assert read_audit(str(tmp_path)) == []


def test_fastapi_app_routes():
    try:
        import fastapi  # noqa: F401
    except ImportError:
        pytest.skip("fastapi not installed")
    from backend.app import create_app
    paths = set(create_app().openapi()["paths"])
    assert "/health" in paths and "/audit" in paths
''', ["backend/app.py"])
F("tests/integration/test_report_pipeline.py", "Report artifacts content", r'''
import json
from pathlib import Path

from backend.services.backtest_service import run_full
from cli.commands import make_sample_csv


def test_report_files_have_content(tmp_path):
    _, paths = run_full("three_pm_momentum", make_sample_csv(tmp_path / "s.csv", days=15), out_root=str(tmp_path / "r"))
    assert "<table>" in Path(paths["html"]).read_text(encoding="utf-8")
    assert "metrics" in json.loads(Path(paths["json"]).read_text(encoding="utf-8"))
    assert Path(paths["csv"]).read_text(encoding="utf-8").startswith("entry_ts,exit_ts")
''', ["reporting/generator.py"])
F("tests/regression/test_known_results.py", "Fixed seed => fixed result", r'''
import json
from pathlib import Path

from backtest.engine import run_backtest
from cli.commands import make_sample_csv
from data.loaders import load_dataset
from registry.registry import Registry

FIX = Path(__file__).resolve().parents[1] / "fixtures"


def test_known_result(tmp_path):
    exp = json.loads((FIX / "expected_results.json").read_text(encoding="utf-8"))
    ds = load_dataset(make_sample_csv(tmp_path / "s.csv", days=exp["days"], seed=exp["seed"]))
    res = run_backtest(ds, Registry().load(exp["strategy"]))
    assert len(res.trades) == exp["n_trades"]
    assert abs(sum(t["pnl"] for t in res.trades) - exp["total_pnl"]) < 0.01
''', ["tests/fixtures/expected_results.json"])
F("tests/property/test_accounting_invariants.py", "Random runs me accounting invariants", r'''
import random

from backtest.engine import run_backtest
from data.models import Bar
from strategies.base import Strategy
from strategies.models import Signal
from tests._helpers import make_dataset

NO_COST = {"slippage_bps": 0.0, "fee_pct": 0.0}


class RandomStrategy(Strategy):
    def __init__(self, params=None):
        super().__init__(params)
        self.rng = random.Random(self.params["seed"])

    def on_bar(self, ctx):
        if ctx.position is None and self.rng.random() < 0.1:
            c = ctx.bar.close
            return Signal("BUY", stop_loss=c * 0.98, target=c * 1.03)
        if ctx.position is not None and self.rng.random() < 0.1:
            return Signal("EXIT")
        return None


def _bars(seed, n=300):
    rng, p, out = random.Random(seed), 100.0, []
    for i in range(n):
        o = p
        c = max(1.0, o * (1 + rng.gauss(0, 0.01)))
        j = i % 75
        out.append(Bar(f"2024-01-{1 + i // 75:02d}T{9 + j // 12:02d}:{(j % 12) * 5:02d}:00", o,
                       max(o, c) * 1.002, min(o, c) * 0.998, c, 100.0))
        p = c
    return out


def test_equity_equals_initial_plus_pnl_when_no_costs():
    for seed in range(25):
        res = run_backtest(make_dataset(_bars(seed)), RandomStrategy({"seed": seed}), NO_COST)
        assert res.status in ("COMPLETED", "HALTED")
        initial = res.config["initial_capital"]
        if res.status == "COMPLETED":
            assert abs(res.equity[-1][1] - (initial + sum(t["pnl"] for t in res.trades))) < 1e-6, seed
        for t in res.trades:
            assert t["qty"] > 0 and t["exit_ts"] >= t["entry_ts"]
''', ["backtest/engine.py"])
F("tests/performance/test_benchmark.py", "Loose speed guard", r'''
import time

from backtest.engine import run_backtest
from cli.commands import make_sample_csv
from data.loaders import load_dataset
from registry.registry import Registry


def test_5000_bars_under_20_seconds(tmp_path):
    ds = load_dataset(make_sample_csv(tmp_path / "s.csv", days=70))
    assert len(ds.bars) >= 5000
    t = time.perf_counter()
    run_backtest(ds, Registry().load("three_pm_momentum"))
    assert time.perf_counter() - t < 20
''', ["backtest/engine.py"])
F("tests/test_no_lookahead.py", "Future bars past results ko nahi badalte", r'''
from backtest.engine import run_backtest
from data.models import Bar
from tests._helpers import BuyAtIndex, make_bars, make_dataset

NO_COST = {"slippage_bps": 0.0, "fee_pct": 0.0}


def test_changing_future_does_not_change_past_equity():
    bars = make_bars(60)
    tampered = bars[:31] + [Bar(b.ts, b.open * 3, b.high * 3, b.low * 3, b.close * 3, b.volume) for b in bars[31:]]
    a = run_backtest(make_dataset(bars), BuyAtIndex({"at": 1}), NO_COST)
    b = run_backtest(make_dataset(tampered), BuyAtIndex({"at": 1}), NO_COST)
    assert a.equity[:31] == b.equity[:31]
    assert a.trades[0]["entry_ts"] == b.trades[0]["entry_ts"]
''', ["backtest/engine.py"])
F("tests/test_reproducibility.py", "Same input => same output", r'''
from backtest.engine import run_backtest
from cli.commands import make_sample_csv
from data.loaders import load_dataset
from metrics import compute_all
from registry.registry import Registry


def test_two_runs_identical(tmp_path):
    ds = load_dataset(make_sample_csv(tmp_path / "s.csv", days=15))
    a = run_backtest(ds, Registry().load("three_pm_momentum"))
    b = run_backtest(ds, Registry().load("three_pm_momentum"))
    assert a.to_dict() == b.to_dict() and compute_all(a, ds) == compute_all(b, ds)
    assert Registry().source_hash("three_pm_momentum") == Registry().source_hash("three_pm_momentum")
''', ["backtest/engine.py"])
F("tests/test_execution_costs.py", "Zyada cost => kam PnL", r'''
from backtest.engine import run_backtest
from tests._helpers import BuyAtIndex, make_bars, make_dataset


def test_costs_reduce_pnl():
    ds = make_dataset(make_bars(30))
    free = run_backtest(ds, BuyAtIndex({"at": 1}), {"slippage_bps": 0.0, "fee_pct": 0.0})
    costly = run_backtest(ds, BuyAtIndex({"at": 1}), {"slippage_bps": 20.0, "fee_pct": 0.002})
    assert costly.trades[0]["pnl"] < free.trades[0]["pnl"] and costly.trades[0]["fees"] > 0
''', ["backtest/engine.py"])

PHASES.append((12, "README v1.0 ke baaki hisse: docs, config yaml, indicators, observability, infra, CI, extra tests", _P12))

# config yaml ab asli me load hote hain (json ke baad, yaml jeetta hai)
_old = '''            cfg.update(json.loads(f.read_text(encoding="utf-8")))
    cfg.pop("on_violation", None)'''
_new = '''            cfg.update(json.loads(f.read_text(encoding="utf-8")))
    for name in ("backtest.yaml", "costs.yaml", "risk.yaml"):  # yaml authoritative
        f = ROOT / "config" / name
        if f.exists():
            cfg.update(parse_manifest_text(f.read_text(encoding="utf-8")))
    cfg.pop("on_violation", None)'''
assert _old in OVERRIDES["backend/services/backtest_service.py"]
OVERRIDES["backend/services/backtest_service.py"] = OVERRIDES["backend/services/backtest_service.py"].replace(_old, _new).replace(
    "from registry.registry import Registry\n", "from registry.metadata import parse_manifest_text\nfrom registry.registry import Registry\n", 1)


# ================================================================= PHASE 13 + 14
_P13, _P14 = [], []

def F13(path, purpose, text, deps=()):
    _P13.append((path, purpose, list(deps)))
    O(path, text)

def F14(path, purpose, text, deps=()):
    _P14.append((path, purpose, list(deps)))
    O(path, text)

# ---------------------------------------------------------------- test helper: multi-day data + trading strategy
OVERRIDES["tests/_helpers.py"] += r'''

from datetime import date, timedelta
import random as _random


def make_days(days=20, per_day=20, seed=1, drift=0.0004):
    """Multi-day random-walk bars (valid dates), per_day bars/din."""
    rng, p, d, out = _random.Random(seed), 100.0, date(2024, 1, 1), []
    while len(out) < days * per_day:
        if d.weekday() < 5:
            for i in range(per_day):
                o = p
                c = max(1.0, o * (1 + rng.gauss(drift, 0.004)))
                out.append(Bar(f"{d.isoformat()}T{9 + i // 12:02d}:{(i % 12) * 5:02d}:00", o,
                               max(o, c) * 1.001, min(o, c) * 0.999, c, 100.0))
                p = c
        d += timedelta(days=1)
    return out


class BuyEvery(Strategy):
    """Har n bars par BUY, n//2 par EXIT. params: n (int), stop_pct/target_pct (float)."""
    strategy_id = "buy_every"

    def on_bar(self, ctx):
        n = self.params.get("n", 6)
        if ctx.position is None and ctx.index % n == 0:
            c = ctx.bar.close
            return Signal("BUY", stop_loss=c * (1 - self.params.get("stop_pct", 1.0) / 100),
                          target=c * (1 + self.params.get("target_pct", 2.0) / 100))
        if ctx.position is not None and ctx.index % n == n // 2:
            return Signal("EXIT")
        return None
'''

# ================================================================ PHASE 13: analysis + optimization
O("validation/cross_validation.py", r'''
"""Anchored out-of-sample folds (koi parameter fitting nahi => time-series CV ka test hissa)."""
from backtest.engine import run_backtest
from metrics import expectancy

MIN_TRADES = 5


def decide(folds):
    active = [f for f in folds if f["trades"] > 0]
    if sum(f["trades"] for f in folds) < MIN_TRADES or len(active) < 2:
        return "UNAVAILABLE", "TOO_FEW_TRADES"
    good = sum(1 for f in active if f["expectancy"] > 0)
    return ("PASS" if good / len(active) >= 0.6 else "FAIL"), ""


def run(dataset, factory, config=None, folds=4):
    n = len(dataset.bars)
    size = n // (folds + 1)
    rows = []
    for k in range(1, folds + 1):
        res = run_backtest(dataset.slice(k * size, (k + 1) * size, f"CV{k}"), factory(), config)
        rows.append({"fold": k, "trades": len(res.trades), "expectancy": expectancy.expectancy(res.trades)})
    status, reason = decide(rows)
    return {"status": status, "reason": reason, "folds": rows}
''')
O("validation/robustness.py", r'''
"""Parameter sensitivity: har float parameter +-20%. Neighbourhood me edge bana rehna chahiye."""
from backtest.engine import run_backtest
from metrics import expectancy

MIN_TRADES = 5
FACTORS = (0.8, 1.2)


def variants(params):
    return [{**params, k: round(v * f, 6)} for k, v in params.items()
            if isinstance(v, float) and v > 0 for f in FACTORS]


def decide(base_exp, var_exps):
    if base_exp <= 0:
        return "UNAVAILABLE", "BASE_NOT_PROFITABLE"
    if not var_exps:
        return "UNAVAILABLE", "NO_FLOAT_PARAMS"
    share = sum(1 for e in var_exps if e > 0) / len(var_exps)
    return ("PASS" if share >= 0.75 else "FAIL"), ""


def run(dataset, factory, config=None):
    base = factory()
    res = run_backtest(dataset, base, config)
    if len(res.trades) < MIN_TRADES:
        return {"status": "UNAVAILABLE", "reason": "TOO_FEW_TRADES"}
    exps = [expectancy.expectancy(run_backtest(dataset, type(base)(p), config).trades) for p in variants(base.params)]
    status, reason = decide(expectancy.expectancy(res.trades), exps)
    return {"status": status, "reason": reason, "variant_expectancies": exps}
''')
O("validation/regime_analysis.py", r'''
"""Regime = din ki range (high/low volatility). Dono regime me edge chahiye."""
from metrics import expectancy

MIN_TRADES = 5


def decide(groups):
    if sum(len(g) for g in groups.values()) < MIN_TRADES or any(len(g) < 2 for g in groups.values()):
        return "UNAVAILABLE", "TOO_FEW_TRADES_PER_REGIME"
    return ("PASS" if all(expectancy.expectancy(g) > 0 for g in groups.values()) else "FAIL"), ""


def run(dataset, result):
    rng = {}
    for b in dataset.bars:
        r = rng.setdefault(b.ts[:10], [b.high, b.low, b.open])
        r[0], r[1] = max(r[0], b.high), min(r[1], b.low)
    vol = {d: (h - l) / o for d, (h, l, o) in rng.items()}
    if not vol:
        return {"status": "UNAVAILABLE", "reason": "NO_DATA"}
    med = sorted(vol.values())[len(vol) // 2]
    groups = {"high_vol": [], "low_vol": []}
    for t in result.trades:
        groups["high_vol" if vol.get(t["entry_ts"][:10], 0) >= med else "low_vol"].append(t)
    status, reason = decide(groups)
    return {"status": status, "reason": reason,
            "regimes": {k: {"trades": len(g), "expectancy": expectancy.expectancy(g)} for k, g in groups.items()}}
''')
OVERRIDES["validation/pipeline.py"] = OVERRIDES["validation/pipeline.py"].replace(
    '"cross_validation": cross_validation.run(),', '"cross_validation": cross_validation.run(dataset, factory, config),').replace(
    '"robustness": robustness.run(), "regime_analysis": regime_analysis.run(),',
    '"robustness": robustness.run(dataset, factory, config), "regime_analysis": regime_analysis.run(dataset, base),')
assert "robustness.run(dataset, factory, config)" in OVERRIDES["validation/pipeline.py"]

O("optimization/constraints.py", r'''
"""Parameter constraints. rule = (op, left_param, right_param); abhi op: lt, le."""
DEFAULT_RULES = [("lt", "stop_pct", "target_pct")]


def satisfies(params, rules):
    for op, a, b in rules:
        if a in params and b in params:
            if op == "lt" and not params[a] < params[b]:
                return False
            if op == "le" and not params[a] <= params[b]:
                return False
    return True
''')
O("optimization/experiment_tracking.py", r'''
"""Har trial ka record (JSONL): kitni cheezein try hui, yeh multiple-testing ke liye zaroori hai."""
import json
from datetime import datetime, timezone
from pathlib import Path


def log_trial(root, experiment_id, params, metrics):
    Path(root).mkdir(parents=True, exist_ok=True)
    row = {"ts": datetime.now(timezone.utc).isoformat(), "experiment": experiment_id, "params": params, **metrics}
    with open(Path(root) / "experiments.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def read(root):
    f = Path(root) / "experiments.jsonl"
    return [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines()] if f.exists() else []
''')
O("optimization/parameter_search.py", r'''
"""Grid search sirf pehle hisse (SEARCH) par; chuna hua param pichhle HOLDOUT par alag se parkha jaata hai.
Holdout PASS saboot nahi: jitne zyada trials, utna chance-luck. n_trials result me hai."""
import itertools

from backtest.engine import run_backtest
from metrics import expectancy
from optimization.constraints import satisfies
from optimization.experiment_tracking import log_trial

MIN_TRADES = 5


def grid(space):
    keys = list(space)
    return [dict(zip(keys, vals)) for vals in itertools.product(*(space[k] for k in keys))]


def search(dataset, make, space, config=None, is_ratio=0.6, min_trades=MIN_TRADES, rules=None,
           track_root=None, experiment_id="exp"):
    n = len(dataset.bars)
    k = int(n * is_ratio)
    search_ds, hold_ds = dataset.slice(0, k, "SEARCH"), dataset.slice(k, n, "HOLDOUT")
    trials = []
    for p in grid(space):
        if rules and not satisfies(p, rules):
            continue
        res = run_backtest(search_ds, make(p), config)
        t = {"params": p, "trades": len(res.trades), "expectancy": expectancy.expectancy(res.trades)}
        trials.append(t)
        if track_root:
            log_trial(track_root, experiment_id, p, {"trades": t["trades"], "expectancy": t["expectancy"], "phase": "search"})
    eligible = [t for t in trials if t["trades"] >= min_trades]
    if not eligible:
        return {"status": "UNAVAILABLE", "reason": "NO_ELIGIBLE_TRIALS", "n_trials": len(trials), "trials": trials}
    best = max(eligible, key=lambda t: t["expectancy"])
    hold = run_backtest(hold_ds, make(best["params"]), config)
    he = expectancy.expectancy(hold.trades)
    if track_root:
        log_trial(track_root, experiment_id, best["params"], {"trades": len(hold.trades), "expectancy": he, "phase": "holdout"})
    status = "UNAVAILABLE" if len(hold.trades) < min_trades else ("PASS" if he > 0 else "FAIL")
    return {"status": status, "best_params": best["params"], "in_sample_expectancy": best["expectancy"],
            "holdout_trades": len(hold.trades), "holdout_expectancy": he, "n_trials": len(trials), "trials": trials,
            "warning": "Holdout PASS != proof; n_trials ginti dekho"}
''')

# CLI: optimize + make-sample
OVERRIDES["cli/commands.py"] = OVERRIDES["cli/commands.py"].replace(
    "import csv\nimport random", "import csv\nimport json\nimport random").replace(
    "from backend.services.backtest_service import run_full",
    "from backend.services.backtest_service import load_config, run_full\nfrom data.loaders import load_dataset\nfrom optimization import parameter_search\nfrom optimization.constraints import DEFAULT_RULES") + r'''

def cmd_optimize(args):
    reg = Registry()
    ds = load_dataset(args.data)
    out = parameter_search.search(ds, lambda p: reg.load(args.strategy, p), json.loads(args.grid), load_config(),
                                  rules=DEFAULT_RULES, track_root=args.out, experiment_id=args.strategy)
    print(f"status={out['status']} trials={out['n_trials']} {out.get('reason', '')}")
    if "best_params" in out:
        print("best:", out["best_params"], "holdout_trades:", out["holdout_trades"],
              "holdout_expectancy:", round(out["holdout_expectancy"], 2))
    print(out.get("warning", ""))


def cmd_sample(args):
    print("written:", make_sample_csv(args.out, days=args.days))
'''
OVERRIDES["cli/main.py"] = OVERRIDES["cli/main.py"].replace(
    "    args = ap.parse_args(argv)",
    '''    o = sub.add_parser("optimize")
    o.add_argument("--strategy", required=True)
    o.add_argument("--data", required=True)
    o.add_argument("--grid", required=True, help='JSON: {"stop_pct":[0.3,0.5],"target_pct":[0.8,1.0]}')
    o.add_argument("--out", default="runs")
    o.set_defaults(fn=commands.cmd_optimize)
    s = sub.add_parser("make-sample")
    s.add_argument("--out", default="data/samples/sample_5m.csv")
    s.add_argument("--days", type=int, default=120)
    s.set_defaults(fn=commands.cmd_sample)
    args = ap.parse_args(argv)''')
assert "cmd_optimize" in OVERRIDES["cli/main.py"] and "cmd_optimize" in OVERRIDES["cli/commands.py"]

F13("docs/OPTIMIZATION.md", "Optimization rules", "# Optimization\n\nSearch sirf pehle 60% data par; chuna param baaki 40% HOLDOUT par parkha jaata hai.\nHar trial `experiments.jsonl` me. Zyada trials = chance-luck ka khatra; `n_trials` hamesha dikhao.\nCLI: `python -m cli.main optimize --strategy three_pm_momentum --data data/samples/sample_5m.csv --grid '{\"stop_pct\":[0.3,0.5],\"target_pct\":[0.8,1.0]}'`\n")
O("docs/VALIDATION_POLICY.md", "# Validation policy\n\nAsli checks: leakage, out-of-sample, walk-forward, cross-validation (anchored folds), overfitting, robustness (+-20% float params), regime analysis (high/low vol days), statistical confidence.\nOverall: koi FAIL => FAIL; koi UNAVAILABLE => INCOMPLETE; sab PASS => PASS. UNAVAILABLE kabhi PASS nahi.\n")

# tests phase 13
O("tests/unit/validation/test_cross_validation.py", r'''
from tests._helpers import BuyEvery, make_dataset, make_days
from validation import cross_validation as cv


def test_decide_rules():
    f = lambda t, e: {"trades": t, "expectancy": e}  # noqa: E731
    assert cv.decide([f(1, 1), f(1, 1)])[0] == "UNAVAILABLE"
    assert cv.decide([f(5, 1), f(5, 2), f(5, -1)])[0] == "PASS"
    assert cv.decide([f(5, 1), f(5, -2), f(5, -1)])[0] == "FAIL"


def test_run_returns_folds():
    ds = make_dataset(make_days(30, 20))
    out = cv.run(ds, lambda: BuyEvery({"n": 6}), folds=4)
    assert len(out["folds"]) == 4 and out["status"] in ("PASS", "FAIL")
''')
O("tests/unit/validation/test_robustness.py", r'''
from tests._helpers import BuyEvery, make_dataset, make_days
from validation import robustness as rb


def test_variants_only_float_params():
    v = rb.variants({"stop_pct": 1.0, "n": 6})
    assert len(v) == 2 and all(x["n"] == 6 for x in v)


def test_decide():
    assert rb.decide(-1, [1])[0] == "UNAVAILABLE"
    assert rb.decide(1, [])[1] == "NO_FLOAT_PARAMS"
    assert rb.decide(1, [1, 1, 1, -1])[0] == "PASS"
    assert rb.decide(1, [1, -1, -1, -1])[0] == "FAIL"


def test_run_smoke():
    ds = make_dataset(make_days(30, 20))
    out = rb.run(ds, lambda: BuyEvery({"n": 6, "stop_pct": 1.0, "target_pct": 2.0}))
    assert out["status"] in ("PASS", "FAIL", "UNAVAILABLE")
''')
O("tests/unit/validation/test_regime_analysis.py", r'''
from backtest.engine import run_backtest
from tests._helpers import BuyEvery, make_dataset, make_days
from validation import regime_analysis as ra


def test_decide():
    pos, neg = [{"pnl": 5}] * 3, [{"pnl": -5}] * 3
    assert ra.decide({"high_vol": pos, "low_vol": pos})[0] == "PASS"
    assert ra.decide({"high_vol": pos, "low_vol": neg})[0] == "FAIL"
    assert ra.decide({"high_vol": pos[:1], "low_vol": pos[:1]})[0] == "UNAVAILABLE"


def test_run_splits_trades_into_two_regimes():
    ds = make_dataset(make_days(30, 20))
    res = run_backtest(ds, BuyEvery({"n": 6}))
    out = ra.run(ds, res)
    assert set(out["regimes"]) == {"high_vol", "low_vol"}
    assert sum(r["trades"] for r in out["regimes"].values()) == len(res.trades)
''')
O("tests/unit/optimization/test_constraints.py", r'''
from optimization.constraints import DEFAULT_RULES, satisfies


def test_stop_must_be_below_target():
    assert satisfies({"stop_pct": 0.5, "target_pct": 1.0}, DEFAULT_RULES)
    assert not satisfies({"stop_pct": 2.0, "target_pct": 1.0}, DEFAULT_RULES)
    assert satisfies({"x": 1}, DEFAULT_RULES)
''')
O("tests/unit/optimization/test_experiment_tracking.py", r'''
from optimization import experiment_tracking as et


def test_log_and_read(tmp_path):
    et.log_trial(tmp_path, "e1", {"a": 1}, {"trades": 3})
    et.log_trial(tmp_path, "e1", {"a": 2}, {"trades": 4})
    rows = et.read(tmp_path)
    assert [r["params"]["a"] for r in rows] == [1, 2] and rows[0]["experiment"] == "e1"
''')
O("tests/unit/optimization/test_parameter_search.py", r'''
from optimization import parameter_search as ps
from optimization.constraints import DEFAULT_RULES
from tests._helpers import BuyEvery, make_dataset, make_days


def test_grid():
    assert len(ps.grid({"a": [1, 2], "b": [3, 4, 5]})) == 6


def test_search_uses_holdout_and_counts_trials(tmp_path):
    ds = make_dataset(make_days(40, 20))
    space = {"n": [6, 8], "stop_pct": [0.5, 1.0], "target_pct": [0.4, 2.0]}
    out = ps.search(ds, lambda p: BuyEvery(p), space, rules=DEFAULT_RULES, track_root=str(tmp_path))
    assert out["n_trials"] == 4  # stop<target rule: 2 valid stop/target combos x 2 n
    assert out["status"] in ("PASS", "FAIL", "UNAVAILABLE") and "warning" in out
    from optimization.experiment_tracking import read
    assert len(read(tmp_path)) >= out["n_trials"]


def test_no_eligible_trials_is_unavailable():
    ds = make_dataset(make_days(5, 20))
    out = ps.search(ds, lambda p: BuyEvery(p), {"n": [50]}, min_trades=999)
    assert out["status"] == "UNAVAILABLE"
''')
F13("tests/integration/test_optimization_flow.py", "CLI optimize end-to-end", r'''
import json

from cli import main
from cli.commands import make_sample_csv


def test_cli_optimize_runs(tmp_path, capsys):
    csv = make_sample_csv(tmp_path / "s.csv", days=40)
    grid = json.dumps({"stop_pct": [0.3, 0.5], "target_pct": [0.8, 1.0]})
    assert main.main(["optimize", "--strategy", "three_pm_momentum", "--data", csv, "--grid", grid,
                      "--out", str(tmp_path / "o")]) == 0
    out = capsys.readouterr().out
    assert "trials=4" in out and (tmp_path / "o" / "experiments.jsonl").exists()
''', ["optimization/parameter_search.py"])

PHASES.append((13, "Analysis + optimization: cross-validation, robustness, regime, parameter search, tracking", _P13))

# ================================================================ PHASE 14: backend + persistence + frontend
O("persistence/database.py", r'''
"""SQLite run repository (stdlib). PostgreSQL adapter isi interface par baad me (migrations/001_initial.sql)."""
import json
import sqlite3
from contextlib import closing
from pathlib import Path

SCHEMA = ("CREATE TABLE IF NOT EXISTS runs (run_id TEXT PRIMARY KEY, strategy_id TEXT NOT NULL, "
          "status TEXT NOT NULL, created_at TEXT NOT NULL, record TEXT NOT NULL)")


class SqliteRunRepository:
    def __init__(self, path="runs/svl.sqlite3"):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path)) as c, c:
            c.execute(SCHEMA)

    def save(self, run_id, record):
        with closing(sqlite3.connect(self.path)) as c, c:
            c.execute("INSERT OR REPLACE INTO runs VALUES (?,?,?,?,?)",
                      (run_id, record["strategy_id"], record["status"], record["created_at"], json.dumps(record, default=str)))

    def get(self, run_id):
        with closing(sqlite3.connect(self.path)) as c:
            row = c.execute("SELECT record FROM runs WHERE run_id=?", (run_id,)).fetchone()
        if row is None:
            raise KeyError(run_id)
        return json.loads(row[0])

    def list_ids(self):
        with closing(sqlite3.connect(self.path)) as c:
            return [r[0] for r in c.execute("SELECT run_id FROM runs ORDER BY created_at")]
''')
O("tests/unit/persistence/test_database.py", r'''
import pytest  # noqa: F401

from persistence.database import SqliteRunRepository


def test_save_get_list(tmp_path):
    repo = SqliteRunRepository(tmp_path / "t.db")
    rec = {"run_id": "r1", "strategy_id": "s", "status": "COMPLETED", "created_at": "2024-01-01T00:00:00"}
    repo.save("r1", rec)
    assert repo.get("r1") == rec and repo.list_ids() == ["r1"]
    try:
        repo.get("nope")
        raise AssertionError("KeyError expected")
    except KeyError:
        pass
''')
OVERRIDES["backend/services/backtest_service.py"] = OVERRIDES["backend/services/backtest_service.py"].replace(
    "timeframe=\"UNKNOWN\", run_id=None):", "timeframe=\"UNKNOWN\", run_id=None, repo=None):").replace(
    "RunRepository(out_root).save(run_id, record)", "(repo or RunRepository(out_root)).save(run_id, record)")
assert "repo=None" in OVERRIDES["backend/services/backtest_service.py"]
OVERRIDES["reporting/generator.py"] = OVERRIDES["reporting/generator.py"].replace(
    '    paths = {"json"', '    report["equity"] = result.equity[:: max(1, len(result.equity) // 500)]\n    report["trades"] = result.trades[:1000]\n    paths = {"json"')
assert 'report["equity"]' in OVERRIDES["reporting/generator.py"]

# ---- middleware
O("backend/middleware/request_id.py", "import uuid\n\n\ndef new_request_id():\n    return uuid.uuid4().hex\n")
O("backend/middleware/error_handler.py", r'''
def to_error(exc):
    """Exception -> (http_status, body). Andar ki detail bahar nahi jaati."""
    if isinstance(exc, (KeyError, FileNotFoundError)):
        return 404, {"error": "not_found"}
    if isinstance(exc, ValueError):
        return 400, {"error": "bad_request", "detail": str(exc)}
    return 500, {"error": "internal_error"}
''')
O("backend/middleware/authentication.py", r'''
import hmac


def is_authorized(headers, expected_key):
    """expected_key khaali => dev mode (sab allowed). Warna X-API-Key match chahiye."""
    if not expected_key:
        return True
    return hmac.compare_digest(str(headers.get("x-api-key", "")), expected_key)
''')
O("tests/unit/backend/middleware/test_request_id.py", "from backend.middleware.request_id import new_request_id\n\n\ndef test_unique_ids():\n    assert new_request_id() != new_request_id() and len(new_request_id()) == 32\n")
O("tests/unit/backend/middleware/test_error_handler.py", r'''
from backend.middleware.error_handler import to_error


def test_mapping():
    assert to_error(KeyError("x"))[0] == 404 and to_error(ValueError("bad"))[0] == 400
    assert to_error(RuntimeError("secret"))[1] == {"error": "internal_error"}
''')
O("tests/unit/backend/middleware/test_authentication.py", r'''
from backend.middleware.authentication import is_authorized


def test_dev_mode_and_key():
    assert is_authorized({}, "") is True
    assert is_authorized({"x-api-key": "k"}, "k") is True
    assert is_authorized({"x-api-key": "bad"}, "k") is False and is_authorized({}, "k") is False
''')

# ---- services
O("backend/services/report_service.py", r'''
"""Reports/runs read-only. run_id strict (path traversal band)."""
import json
import re
from pathlib import Path

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


def safe_id(run_id):
    if not isinstance(run_id, str) or not _ID.match(run_id):
        raise ValueError("invalid run_id")
    return run_id


def get_report(run_id, root="runs"):
    f = Path(root) / safe_id(run_id) / "report.json"
    if not f.exists():
        raise KeyError(run_id)
    return json.loads(f.read_text(encoding="utf-8"))


def get_run(run_id, root="runs"):
    f = Path(root) / safe_id(run_id) / "run.json"
    if not f.exists():
        raise KeyError(run_id)
    return json.loads(f.read_text(encoding="utf-8"))


def list_runs(root="runs"):
    ids = sorted(p.parent.name for p in Path(root).glob("*/run.json")) if Path(root).exists() else []
    return [{k: r.get(k) for k in ("run_id", "strategy_id", "status", "validation_status", "created_at")}
            for r in (get_run(i, root) for i in ids)]
''')
O("backend/services/validation_service.py", r'''
from backend.services.report_service import get_report


def get_validation(run_id, root="runs"):
    return {"run_id": run_id, **get_report(run_id, root)["validation"]}
''')
F14("backend/services/comparison_service.py", "Runs ki metrics side-by-side", r'''
from backend.services.report_service import get_report


def compare(run_ids, root="runs"):
    if not isinstance(run_ids, list) or not 2 <= len(run_ids) <= 10:
        raise ValueError("2 se 10 run_ids chahiye")
    rows = []
    for rid in run_ids:
        r = get_report(rid, root)
        rows.append({"run_id": rid, "status": r["status"], "validation": r["validation"].get("status"), "metrics": r["metrics"]})
    return {"runs": rows, "metric_names": sorted({k for r in rows for k in r["metrics"]})}
''', ["backend/services/report_service.py"])
O("backend/services/strategy_service.py", r'''
from registry.registry import Registry


def list_strategies():
    reg = Registry()
    return [{**reg.manifest(s), "source_hash": reg.source_hash(s)} for s in reg.discover()]


def get_strategy(strategy_id):
    reg = Registry()
    m = reg.manifest(strategy_id)  # KeyError agar unknown
    return {**m, "source_hash": reg.source_hash(strategy_id)}
''')
O("backend/services/dataset_service.py", r'''
"""Datasets DATA_DIR ke andar hi (client path nahi deta, sirf file ka naam)."""
import os
import re
from pathlib import Path

from data.loaders import load_dataset

_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*\.csv$")


def data_dir():
    return Path(os.environ.get("DATA_DIR", "data/samples"))


def resolve(name):
    if not isinstance(name, str) or not _NAME.match(name):
        raise ValueError("invalid dataset name (sirf *.csv file ka naam)")
    p = data_dir() / name
    if not p.exists():
        raise KeyError(name)
    return str(p)


def list_datasets():
    d = data_dir()
    out = []
    for f in sorted(d.glob("*.csv")) if d.exists() else []:
        ds = load_dataset(f)
        out.append({"file": f.name, **ds.meta(), "bars": len(ds.bars)})
    return out
''')

# ---- api layer (handlers framework-free + FastAPI routers if installed)
F14("backend/api/common.py", "Shared helpers: router factory, error mapping, env roots", r'''
import functools
import os


def runs_root():
    return os.environ.get("RUNS_ROOT", "runs")


def make_router():
    try:
        from fastapi import APIRouter
    except ImportError:
        return None
    return APIRouter()


def guarded(fn):
    """Handler errors -> HTTP errors (FastAPI ho to)."""
    try:
        from fastapi import HTTPException
    except ImportError:
        return fn
    from backend.middleware.error_handler import to_error

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except HTTPException:
            raise
        except Exception as e:  # noqa: BLE001
            status, body = to_error(e)
            raise HTTPException(status_code=status, detail=body) from e
    return wrapper
''')
O("backend/api/strategies.py", r'''
from backend.api.common import guarded, make_router
from backend.services import strategy_service


def list_all():
    return strategy_service.list_strategies()


def get_one(strategy_id: str):
    return strategy_service.get_strategy(strategy_id)


router = make_router()
if router is not None:
    router.get("/strategies")(guarded(list_all))
    router.get("/strategies/{strategy_id}")(guarded(get_one))
''')
O("backend/api/datasets.py", r'''
from backend.api.common import guarded, make_router
from backend.services import dataset_service


def list_all():
    return dataset_service.list_datasets()


router = make_router()
if router is not None:
    router.get("/datasets")(guarded(list_all))
''')
O("backend/api/backtests.py", r'''
from backend.api.common import guarded, make_router, runs_root
from backend.dependencies import get_queue
from backend.jobs.worker import run_next
from backend.services import dataset_service, report_service
from backend.services.backtest_service import run_full


def _handler(p):
    record, _ = run_full(p["strategy_id"], dataset_service.resolve(p["dataset"]), p.get("params"), p.get("config"),
                         out_root=runs_root(), symbol=p.get("symbol", "UNKNOWN"), timeframe=p.get("timeframe", "UNKNOWN"))
    return {"run_id": record["run_id"], "status": record["status"], "validation_status": record["validation_status"],
            "reason": record["reason"]}


def _job_view(job):
    return {"job_id": job.job_id, "status": job.status.value, "result": job.result, "error": job.error}


def start(payload: dict):
    if not isinstance(payload, dict) or "strategy_id" not in payload or "dataset" not in payload:
        raise ValueError("strategy_id aur dataset chahiye")
    q = get_queue()
    job = q.submit(payload)
    run_next(q, _handler)  # abhi inline; background worker baad me
    return _job_view(job)


def list_runs():
    return report_service.list_runs(runs_root())


def get_one(item_id: str):
    if item_id.startswith("job-"):
        return _job_view(get_queue().get(item_id))
    return report_service.get_run(item_id, runs_root())


router = make_router()
if router is not None:
    router.post("/backtests")(guarded(start))
    router.get("/backtests")(guarded(list_runs))
    router.get("/backtests/{item_id}")(guarded(get_one))
''')
O("backend/api/validation.py", r'''
from backend.api.common import guarded, make_router, runs_root
from backend.services import validation_service


def get_one(run_id: str):
    return validation_service.get_validation(run_id, runs_root())


router = make_router()
if router is not None:
    router.get("/validations/{run_id}")(guarded(get_one))
''')
O("backend/api/comparisons.py", r'''
from backend.api.common import guarded, make_router, runs_root
from backend.services import comparison_service


def create(payload: dict):
    return comparison_service.compare(payload.get("run_ids") if isinstance(payload, dict) else None, runs_root())


router = make_router()
if router is not None:
    router.post("/comparisons")(guarded(create))
''')
O("backend/api/reports.py", r'''
from backend.api.common import guarded, make_router, runs_root
from backend.services import report_service


def get_one(run_id: str):
    return report_service.get_report(run_id, runs_root())


router = make_router()
if router is not None:
    router.get("/reports/{run_id}")(guarded(get_one))
''')
O("backend/api/audit.py", r'''
"""/audit route."""
from backend.api.common import guarded, make_router, runs_root
from persistence import audit


def read_audit(root=None, limit=100):
    return audit.read(root or runs_root(), limit)


def get_audit(limit: int = 100):
    return read_audit(limit=limit)


router = make_router()
if router is not None:
    router.get("/audit")(guarded(get_audit))
''')
O("backend/dependencies.py", r'''
import os

from backend.jobs.queue import JobQueue
from persistence.repositories import RunRepository
from registry.registry import Registry

_QUEUE = JobQueue()


def get_registry():
    return Registry()


def get_queue():
    return _QUEUE


def get_repository(root=None):
    url = os.environ.get("DATABASE_URL", "")
    if url.startswith("sqlite:///"):
        from persistence.database import SqliteRunRepository
        return SqliteRunRepository(url[len("sqlite:///"):])
    return RunRepository(root or os.environ.get("RUNS_ROOT", "runs"))
''')
O("backend/app.py", r'''
"""Backend entry point (FastAPI). Chalane ke liye: pip install fastapi uvicorn; uvicorn --factory backend.app:create_app
Env: API_KEY (set ho to X-API-Key zaroori, /health chhodkar), RUNS_ROOT, DATA_DIR, DATABASE_URL."""
import os


def create_app():
    try:
        from fastapi import FastAPI, Request
        from fastapi.responses import JSONResponse
    except ImportError as e:
        raise RuntimeError("`pip install fastapi uvicorn` chahiye") from e
    from backend.api import audit, backtests, comparisons, datasets, health, reports, strategies, validation
    from backend.middleware.authentication import is_authorized
    from backend.middleware.request_id import new_request_id

    app = FastAPI(title="strategy-validation-lab")

    @app.middleware("http")
    async def guard(request: Request, call_next):
        rid = new_request_id()
        if request.url.path != "/health" and not is_authorized(request.headers, os.environ.get("API_KEY", "")):
            return JSONResponse({"error": "unauthorized", "request_id": rid}, status_code=401)
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response

    for module in (health, strategies, datasets, backtests, validation, comparisons, reports, audit):
        app.include_router(module.router)
    return app
''')
OVERRIDES["tests/integration/test_api.py"] = r'''
import pytest

from backend.api.audit import read_audit
from backend.api.health import health_payload


def test_payloads(tmp_path):
    assert health_payload() == {"status": "ok"}
    assert read_audit(str(tmp_path)) == []


def test_fastapi_app_routes():
    try:
        import fastapi  # noqa: F401
    except ImportError:
        pytest.skip("fastapi not installed")
    from backend.app import create_app
    paths = set(create_app().openapi()["paths"])
    assert {"/health", "/audit", "/strategies", "/backtests", "/reports/{run_id}", "/validations/{run_id}",
            "/comparisons", "/datasets"} <= paths
'''
F14("tests/integration/test_api_handlers.py", "API handlers (framework ke bina) end-to-end", r'''
import os

from backend.api import backtests, comparisons, datasets, reports, strategies, validation
from cli.commands import make_sample_csv


def _env(tmp_path):
    make_sample_csv(tmp_path / "data" / "s.csv", days=30)
    os.environ["DATA_DIR"], os.environ["RUNS_ROOT"] = str(tmp_path / "data"), str(tmp_path / "runs")


def _raises(exc, fn, *a):
    try:
        fn(*a)
    except exc:
        return True
    return False


def test_full_api_flow(tmp_path):
    _env(tmp_path)
    assert {s["id"] for s in strategies.list_all()} >= {"gamma_blast", "three_pm_momentum"}
    assert strategies.get_one("gamma_blast")["required_data"] == ["option_chain", "oi"]
    assert datasets.list_all()[0]["file"] == "s.csv"
    job = backtests.start({"strategy_id": "three_pm_momentum", "dataset": "s.csv"})
    assert job["status"] == "SUCCEEDED"
    rid = job["result"]["run_id"]
    assert backtests.get_one(job["job_id"])["status"] == "SUCCEEDED"
    assert backtests.get_one(rid)["run_id"] == rid and rid in [r["run_id"] for r in backtests.list_runs()]
    assert validation.get_one(rid)["status"] in ("PASS", "FAIL", "INCOMPLETE")
    rep = reports.get_one(rid)
    assert "metrics" in rep and len(rep["equity"]) > 10
    assert len(comparisons.create({"run_ids": [rid, rid]})["runs"]) == 2


def test_blocked_strategy_job_succeeds_but_run_blocked(tmp_path):
    _env(tmp_path)
    job = backtests.start({"strategy_id": "gamma_blast", "dataset": "s.csv"})
    assert job["status"] == "SUCCEEDED" and job["result"]["status"] == "BLOCKED"


def test_bad_inputs_rejected(tmp_path):
    _env(tmp_path)
    assert _raises(ValueError, reports.get_one, "../etc")
    assert _raises(ValueError, reports.get_one, "..")
    assert _raises(KeyError, reports.get_one, "run-does-not-exist")
    assert _raises(ValueError, backtests.start, {"strategy_id": "x"})
    assert _raises(ValueError, comparisons.create, {"run_ids": ["only-one"]})
    job = backtests.start({"strategy_id": "three_pm_momentum", "dataset": "../../etc/passwd"})
    assert job["status"] == "FAILED" and "invalid dataset" in job["error"]
    job = backtests.start({"strategy_id": "nope", "dataset": "s.csv"})
    assert job["status"] == "FAILED"
''', ["backend/api/backtests.py"])
F14("tests/integration/test_api_routes.py", "FastAPI routes (CI me chalta hai; fastapi na ho to skip)", r'''
import os

import pytest

from cli.commands import make_sample_csv


def _client(tmp_path):
    try:
        from fastapi.testclient import TestClient
    except ImportError:
        pytest.skip("fastapi/httpx not installed")
    from backend.app import create_app
    make_sample_csv(tmp_path / "data" / "s.csv", days=20)
    os.environ["DATA_DIR"], os.environ["RUNS_ROOT"] = str(tmp_path / "data"), str(tmp_path / "runs")
    os.environ.pop("API_KEY", None)
    return TestClient(create_app())


def test_routes_and_errors(tmp_path):
    c = _client(tmp_path)
    assert c.get("/health").json() == {"status": "ok"}
    assert len(c.get("/strategies").json()) >= 2
    assert c.get("/strategies/unknown").status_code == 404
    assert c.get("/reports/run-nope").status_code == 404
    r = c.post("/backtests", json={"strategy_id": "three_pm_momentum", "dataset": "s.csv"})
    assert r.status_code == 200 and r.json()["status"] == "SUCCEEDED" and "x-request-id" in r.headers
    rid = r.json()["result"]["run_id"]
    assert c.get(f"/reports/{rid}").status_code == 200
    assert c.post("/comparisons", json={"run_ids": [rid]}).status_code == 400


def test_api_key_enforced(tmp_path):
    c = _client(tmp_path)
    os.environ["API_KEY"] = "secret"
    try:
        assert c.get("/health").status_code == 200
        assert c.get("/strategies").status_code == 401
        assert c.get("/strategies", headers={"x-api-key": "secret"}).status_code == 200
    finally:
        os.environ.pop("API_KEY", None)
''', ["backend/app.py"])

# ---- frontend (typed, XSS-safe: sab values escape hote hain)
O("frontend/tsconfig.json", json.dumps({"compilerOptions": {"target": "ES2022", "module": "ESNext", "moduleResolution": "Bundler",
  "lib": ["ES2022", "DOM"], "strict": True, "noEmit": True, "skipLibCheck": True}, "include": ["src"]}, indent=2) + "\n")
O("frontend/package.json", json.dumps({"name": "svl-frontend", "private": True, "version": "0.1.0", "type": "module",
  "scripts": {"dev": "vite", "build": "tsc --noEmit && vite build", "typecheck": "tsc --noEmit"},
  "devDependencies": {"typescript": "^5.4.0", "vite": "^5.2.0"}}, indent=2) + "\n")
O("frontend/index.html", '<!doctype html>\n<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">\n<title>Strategy Lab</title><link rel="icon" href="/favicon.svg"></head>\n<body><nav id="nav"></nav><main id="app"></main><script type="module" src="/src/main.ts"></script></body></html>\n')
O("frontend/src/main.ts", 'import "./styles/base.css";\nimport "./styles/layout.css";\nimport "./styles/components.css";\nimport "./styles/dashboard.css";\nimport { start } from "./app";\n\nstart(document.getElementById("app") as HTMLElement, document.getElementById("nav") as HTMLElement);\n')
O("frontend/src/components/data-table.ts", r'''
export function esc(v: unknown): string {
  const map: Record<string, string> = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
  return String(v).replace(/[&<>"']/g, (c) => map[c]);
}

export function renderTable(rows: Record<string, unknown>[]): string {
  if (!rows.length) return "<p>No data</p>";
  const cols = Object.keys(rows[0]);
  const head = cols.map((c) => `<th>${esc(c)}</th>`).join("");
  const body = rows.map((r) => `<tr>${cols.map((c) => `<td>${esc(r[c] ?? "")}</td>`).join("")}</tr>`).join("");
  return `<table><tr>${head}</tr>${body}</table>`;
}

export function renderKeyValues(obj: Record<string, unknown>): string {
  return renderTable(Object.entries(obj).map(([key, value]) => ({ key, value: typeof value === "object" ? JSON.stringify(value) : value })));
}
''')
O("frontend/src/components/metric-card.ts", 'import { esc } from "./data-table";\n\nexport function metricCard(label: string, value: unknown): string {\n  const v = typeof value === "number" ? value.toFixed(2) : String(value ?? "-");\n  return `<div class="card"><small>${esc(label)}</small><div><b>${esc(v)}</b></div></div>`;\n}\n')
O("frontend/src/components/status-badge.ts", 'import { esc } from "./data-table";\n\nexport function statusBadge(status: string): string {\n  const cls = String(status).toLowerCase();\n  return `<span class="badge ${esc(cls)}">${esc(status)}</span>`;\n}\n')
O("frontend/src/components/error-panel.ts", 'import { esc } from "./data-table";\n\nexport function errorPanel(message: string): string {\n  return `<div class="card badge fail">${esc(message)}</div>`;\n}\n')
F14("frontend/src/components/page.ts", "Common page mount (loading + error handling)", r'''
import { errorPanel } from "./error-panel";
import { esc } from "./data-table";

export async function mountPage(el: HTMLElement, title: string, loader: () => Promise<string>): Promise<void> {
  const h = `<h2>${esc(title)}</h2>`;
  el.innerHTML = h + "<p>Loading...</p>";
  try {
    el.innerHTML = h + (await loader());
  } catch (e) {
    el.innerHTML = h + errorPanel(String(e));
  }
}
''')
O("frontend/src/components/chart-panel.ts", r'''
export function lineChartSvg(values: number[], w = 600, h = 160, color = "#2563eb"): string {
  if (values.length < 2) return "<p>Not enough data</p>";
  const lo = Math.min(...values);
  const span = Math.max(...values) - lo || 1;
  const pts = values.map((v, i) => `${((i * w) / (values.length - 1)).toFixed(1)},${(h - ((v - lo) / span) * (h - 10) - 5).toFixed(1)}`).join(" ");
  return `<svg viewBox="0 0 ${w} ${h}" width="100%"><polyline fill="none" stroke="${color}" stroke-width="1.5" points="${pts}"/></svg>`;
}
''')
O("frontend/src/components/charts/equity-curve.ts", 'import { lineChartSvg } from "../chart-panel";\n\nexport function equityCurve(points: [string, number][]): string {\n  return lineChartSvg(points.map((p) => p[1]));\n}\n')
O("frontend/src/components/charts/drawdown-chart.ts", r'''
import { lineChartSvg } from "../chart-panel";

export function drawdownChart(points: [string, number][]): string {
  let peak = -Infinity;
  const dd = points.map(([, e]) => {
    peak = Math.max(peak, e);
    return -((peak - e) / peak) * 100;
  });
  return lineChartSvg(dd, 600, 120, "#dc2626");
}
''')
O("frontend/src/components/charts/monthly-returns.ts", r'''
import { renderTable } from "../data-table";

export function monthlyReturns(points: [string, number][]): string {
  const last: Record<string, number> = {};
  for (const [ts, e] of points) last[ts.slice(0, 7)] = e;
  const months = Object.keys(last).sort();
  const rows = months.map((m, i) => ({ month: m, return_pct: i === 0 ? "-" : ((last[m] / last[months[i - 1]] - 1) * 100).toFixed(2) }));
  return renderTable(rows);
}
''')
O("frontend/src/components/charts/trade-distribution.ts", r'''
import { esc } from "../data-table";

export function tradeDistribution(pnls: number[], bins = 10): string {
  if (!pnls.length) return "<p>No trades</p>";
  const lo = Math.min(...pnls);
  const width = (Math.max(...pnls) - lo || 1) / bins;
  const counts = new Array<number>(bins).fill(0);
  for (const p of pnls) counts[Math.min(bins - 1, Math.floor((p - lo) / width))]++;
  const top = Math.max(...counts);
  return counts.map((c, i) => `<div>${esc((lo + i * width).toFixed(0))} <span style="display:inline-block;background:#2563eb;height:8px;width:${(c / top) * 200}px"></span> ${c}</div>`).join("");
}
''')
O("frontend/src/components/navigation.ts", r'''
const LINKS: [string, string][] = [["dashboard", "Dashboard"], ["strategies", "Strategies"], ["datasets", "Datasets"], ["runs", "Runs"],
  ["compare", "Compare"], ["health", "Health"], ["audit", "Audit"]];

export function navigation(): string {
  return LINKS.map(([h, l]) => `<a href="#${h}">${l}</a>`).join(" | ");
}
''')
O("frontend/src/api/validation.ts", 'import { getJson } from "./client";\nexport const getValidation = (id: string) => getJson<Record<string, any>>(`/validations/${id}`);\n')
O("frontend/src/api/datasets.ts", 'import { getJson } from "./client";\nexport const listDatasets = () => getJson<Record<string, unknown>[]>("/datasets");\n')
O("frontend/src/api/comparisons.ts", 'import { postJson } from "./client";\nexport const compareRuns = (runIds: string[]) => postJson<Record<string, any>>("/comparisons", { run_ids: runIds });\n')
O("frontend/src/api/audit.ts", 'import { getJson } from "./client";\nexport const getAudit = () => getJson<Record<string, unknown>[]>("/audit");\n')
O("frontend/src/api/reports.ts", 'import { getJson } from "./client";\nimport { Report } from "../types/report";\nexport const getReport = (id: string) => getJson<Report & Record<string, any>>(`/reports/${id}`);\n')
O("frontend/src/api/backtests.ts", 'import { getJson, postJson } from "./client";\nexport const listRuns = () => getJson<Record<string, any>[]>("/backtests");\nexport const getRun = (id: string) => getJson<Record<string, any>>(`/backtests/${id}`);\nexport const startRun = (body: unknown) => postJson<Record<string, any>>("/backtests", body);\n')
O("frontend/src/api/strategies.ts", 'import { getJson } from "./client";\nimport { Strategy } from "../types/strategy";\nexport const listStrategies = () => getJson<Strategy[]>("/strategies");\nexport const getStrategy = (id: string) => getJson<Strategy>(`/strategies/${id}`);\n')
O("frontend/src/types/metrics.ts", "export type Metrics = Record<string, number | null | number[]>;\n")

_link = lambda h, t: f'<a href="#{h}">{t}</a>'  # noqa: E731
O("frontend/src/pages/dashboard.ts", r'''
import { getHealth } from "../api/health";
import { listRuns } from "../api/backtests";
import { mountPage } from "../components/page";
import { renderTable } from "../components/data-table";
import { statusBadge } from "../components/status-badge";

export function render(el: HTMLElement): Promise<void> {
  return mountPage(el, "Dashboard", async () => {
    const [health, runs] = await Promise.all([getHealth(), listRuns()]);
    return `<p>API: ${statusBadge(health.status)}</p>` + renderTable(runs.slice(-10).reverse());
  });
}
''')
O("frontend/src/pages/strategy-registry.ts", r'''
import { listStrategies } from "../api/strategies";
import { mountPage } from "../components/page";
import { esc, renderTable } from "../components/data-table";

export function render(el: HTMLElement): Promise<void> {
  return mountPage(el, "Strategies", async () => {
    const rows = (await listStrategies()).map((s) => ({ id: s.id, version: s.version, required_data: s.required_data.join(", ") || "-", detail: `<a href="#strategy/${esc(s.id)}">open</a>` }));
    return renderTable(rows).replace(/&lt;a href=&quot;#strategy\/([\w.-]+)&quot;&gt;open&lt;\/a&gt;/g, '<a href="#strategy/$1">open</a>');
  });
}
''')
O("frontend/src/pages/strategy-detail.ts", r'''
import { getStrategy } from "../api/strategies";
import { mountPage } from "../components/page";
import { renderKeyValues } from "../components/data-table";

export function render(el: HTMLElement, id = ""): Promise<void> {
  return mountPage(el, `Strategy: ${id}`, async () => renderKeyValues(await getStrategy(id) as unknown as Record<string, unknown>));
}
''')
O("frontend/src/pages/create-strategy.ts", r'''
import { mountPage } from "../components/page";

export function render(el: HTMLElement): Promise<void> {
  return mountPage(el, "Create strategy", async () =>
    "<p>API se strategy banana abhi band hai (security: code isi process me chalta hai). Repo me <code>strategies/&lt;id&gt;/</code> banao: manifest.yaml + strategy.py, phir review karke commit.</p>");
}
''')
O("frontend/src/pages/backtest-runs.ts", r'''
import { listRuns } from "../api/backtests";
import { mountPage } from "../components/page";
import { renderTable } from "../components/data-table";

export function render(el: HTMLElement): Promise<void> {
  return mountPage(el, "Backtest runs", async () => renderTable((await listRuns()).reverse()) + "<p>Detail: <code>#run/&lt;run_id&gt;</code></p>");
}
''')
O("frontend/src/pages/backtest-detail.ts", r'''
import { getRun } from "../api/backtests";
import { mountPage } from "../components/page";
import { renderKeyValues, esc } from "../components/data-table";

export function render(el: HTMLElement, id = ""): Promise<void> {
  return mountPage(el, `Run: ${id}`, async () =>
    renderKeyValues(await getRun(id)) + `<p><a href="#report/${esc(id)}">report</a> | <a href="#validation/${esc(id)}">validation</a></p>`);
}
''')
O("frontend/src/pages/validation-results.ts", r'''
import { getValidation } from "../api/validation";
import { mountPage } from "../components/page";
import { renderTable } from "../components/data-table";
import { statusBadge } from "../components/status-badge";

export function render(el: HTMLElement, id = ""): Promise<void> {
  return mountPage(el, `Validation: ${id}`, async () => {
    const v = await getValidation(id);
    const rows = Object.entries(v.checks ?? {}).map(([check, r]: [string, any]) => ({ check, status: r.status, reason: r.reason ?? "" }));
    return `<p>Overall: ${statusBadge(v.status)} ${v.reason ?? ""}</p>` + renderTable(rows);
  });
}
''')
O("frontend/src/pages/comparison.ts", r'''
import { compareRuns } from "../api/comparisons";
import { mountPage } from "../components/page";
import { renderTable } from "../components/data-table";

export function render(el: HTMLElement, ids = ""): Promise<void> {
  return mountPage(el, "Compare runs", async () => {
    const runIds = ids.split(",").map((s) => s.trim()).filter(Boolean);
    if (runIds.length < 2) return "<p>URL: <code>#compare/runid1,runid2</code></p>";
    const c = await compareRuns(runIds);
    const rows = (c.metric_names as string[]).map((m) => ({ metric: m, ...Object.fromEntries(c.runs.map((r: any) => [r.run_id, r.metrics[m]])) }));
    return renderTable(rows);
  });
}
''')
O("frontend/src/pages/reports.ts", r'''
import { getReport } from "../api/reports";
import { mountPage } from "../components/page";
import { renderTable } from "../components/data-table";
import { metricCard } from "../components/metric-card";
import { statusBadge } from "../components/status-badge";
import { equityCurve } from "../components/charts/equity-curve";
import { drawdownChart } from "../components/charts/drawdown-chart";
import { monthlyReturns } from "../components/charts/monthly-returns";
import { tradeDistribution } from "../components/charts/trade-distribution";

export function render(el: HTMLElement, id = ""): Promise<void> {
  return mountPage(el, `Report: ${id}`, async () => {
    const r = await getReport(id);
    const m = r.metrics as Record<string, unknown>;
    const cards = ["total_return_pct", "max_drawdown_pct", "n_trades", "win_rate_pct", "expectancy"].map((k) => metricCard(k, m[k])).join("");
    const eq = (r.equity ?? []) as [string, number][];
    const pnls = ((r.trades ?? []) as { pnl: number }[]).map((t) => t.pnl);
    return `<p>${statusBadge(r.status)} validation: ${statusBadge(String((r.validation as any).status))}</p><div class="grid">${cards}</div>` +
      `<h3>Equity</h3>${equityCurve(eq)}<h3>Drawdown %</h3>${drawdownChart(eq)}<h3>Monthly</h3>${monthlyReturns(eq)}` +
      `<h3>Trade PnL</h3>${tradeDistribution(pnls)}<h3>All metrics</h3>` + renderTable(Object.entries(m).map(([metric, value]) => ({ metric, value: JSON.stringify(value) })));
  });
}
''')
O("frontend/src/pages/datasets.ts", 'import { listDatasets } from "../api/datasets";\nimport { mountPage } from "../components/page";\nimport { renderTable } from "../components/data-table";\n\nexport function render(el: HTMLElement): Promise<void> {\n  return mountPage(el, "Datasets", async () => renderTable(await listDatasets()));\n}\n')
O("frontend/src/pages/system-health.ts", 'import { getHealth } from "../api/health";\nimport { mountPage } from "../components/page";\nimport { renderKeyValues } from "../components/data-table";\n\nexport function render(el: HTMLElement): Promise<void> {\n  return mountPage(el, "System health", async () => renderKeyValues(await getHealth()));\n}\n')
O("frontend/src/pages/audit-log.ts", 'import { getAudit } from "../api/audit";\nimport { mountPage } from "../components/page";\nimport { renderTable } from "../components/data-table";\n\nexport function render(el: HTMLElement): Promise<void> {\n  return mountPage(el, "Audit log", async () => renderTable((await getAudit()).reverse()));\n}\n')
O("frontend/src/app.ts", r'''
import { navigation } from "./components/navigation";
import * as dashboard from "./pages/dashboard";
import * as registry from "./pages/strategy-registry";
import * as strategyDetail from "./pages/strategy-detail";
import * as createStrategy from "./pages/create-strategy";
import * as runs from "./pages/backtest-runs";
import * as runDetail from "./pages/backtest-detail";
import * as validation from "./pages/validation-results";
import * as comparison from "./pages/comparison";
import * as reports from "./pages/reports";
import * as datasets from "./pages/datasets";
import * as health from "./pages/system-health";
import * as audit from "./pages/audit-log";

type Page = { render: (el: HTMLElement, arg?: string) => Promise<void> };

const ROUTES: Record<string, Page> = {
  dashboard, strategies: registry, strategy: strategyDetail, "create-strategy": createStrategy, runs, run: runDetail,
  validation, compare: comparison, report: reports, datasets, health, audit,
};

export function start(el: HTMLElement, nav: HTMLElement): void {
  nav.innerHTML = navigation();
  const go = (): void => {
    const [name, ...rest] = (location.hash.slice(1) || "dashboard").split("/");
    void (ROUTES[name] ?? dashboard).render(el, decodeURIComponent(rest.join("/")));
  };
  window.addEventListener("hashchange", go);
  go();
}
''')

F14("frontend/src/env.d.ts", "CSS import declarations", 'declare module "*.css";\n')

PHASES.append((14, "Backend API + services + SQLite + middleware + frontend pages", _P14))

# CI: fastapi/httpx + frontend typecheck
O(".github/workflows/ci.yml", r'''
name: ci
on: [push, pull_request]
jobs:
  python-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install pytest fastapi httpx
      - run: python -m pytest -q
  frontend-typecheck:
    runs-on: ubuntu-latest
    continue-on-error: true
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: cd frontend && npm install && npx tsc --noEmit
''')
O("requirements.lock", "# Core system sirf Python stdlib use karta hai.\npytest>=7\n# API chalane ke liye (optional): fastapi, uvicorn; API tests ke liye: httpx\n# Parquet (optional): pyarrow\n")
O("docs/RUNBOOK.md", r'''
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
''')

# ================================================================= PHASE 15: baaki stubs me asli code + blueprint ke gaps
_P15 = []

def F15(path, purpose, text, deps=()):
    _P15.append((path, purpose, list(deps)))
    O(path, text)

def _patch(path, old, new, count=1):
    assert OVERRIDES[path].count(old) >= 1, (path, old[:60])
    OVERRIDES[path] = OVERRIDES[path].replace(old, new) if count == 0 else OVERRIDES[path].replace(old, new, count)

# ---------------------------------------------------------------- backend/schemas
O("backend/schemas/backtest.py", r'''
"""Backtest request/response models + strict validation (API ke andar aane wala data yahin parkha jaata hai)."""
from dataclasses import dataclass, field

ALLOWED_KEYS = {"strategy_id", "dataset", "params", "config", "symbol", "timeframe", "validation"}


@dataclass
class BacktestRequest:
    strategy_id: str
    dataset: str
    params: dict = field(default_factory=dict)
    config: dict = field(default_factory=dict)
    symbol: str = "UNKNOWN"
    timeframe: str = "UNKNOWN"
    validation: dict = field(default_factory=dict)  # optional: {"split": 0.7, "windows": 4}

    @classmethod
    def from_dict(cls, d):
        if not isinstance(d, dict):
            raise ValueError("JSON object chahiye")
        unknown = set(d) - ALLOWED_KEYS
        if unknown:
            raise ValueError("unknown keys: " + ", ".join(sorted(unknown)))
        for k in ("strategy_id", "dataset"):
            if not isinstance(d.get(k), str) or not d[k].strip():
                raise ValueError(f"{k} chahiye")
        for k in ("params", "config", "validation"):
            if d.get(k) is not None and not isinstance(d[k], dict):
                raise ValueError(f"{k} object hona chahiye")
        v = d.get("validation") or {}
        if set(v) - {"split", "windows"}:
            raise ValueError("validation me sirf split, windows allowed")
        if "split" in v and not (isinstance(v["split"], (int, float)) and 0.1 <= v["split"] <= 0.9):
            raise ValueError("split 0.1 se 0.9 ke beech")
        if "windows" in v and not (isinstance(v["windows"], int) and not isinstance(v["windows"], bool) and 2 <= v["windows"] <= 12):
            raise ValueError("windows 2 se 12 ke beech (int)")
        return cls(d["strategy_id"].strip(), d["dataset"].strip(), dict(d.get("params") or {}), dict(d.get("config") or {}),
                   str(d.get("symbol", "UNKNOWN")), str(d.get("timeframe", "UNKNOWN")), dict(v))


@dataclass
class BacktestResponse:
    job_id: str
    status: str
    result: dict = None
    error: str = None
''')
O("backend/schemas/strategy.py", r'''
from dataclasses import dataclass, field


@dataclass
class StrategySummary:
    id: str
    version: str
    required_data: list = field(default_factory=list)
    execution_modes: list = field(default_factory=list)
    live_trading_enabled: bool = False

    @classmethod
    def from_manifest(cls, m):
        lt = m.get("live_trading")
        return cls(str(m["id"]), str(m["version"]), list(m.get("required_data") or []),
                   list(m.get("execution_modes") or []), bool(lt.get("enabled")) if isinstance(lt, dict) else bool(lt))
''')
O("backend/schemas/report.py", r'''
from dataclasses import dataclass


@dataclass
class ReportSummary:
    run_id: str
    status: str
    validation_status: str
    n_trades: int
    total_return_pct: float

    @classmethod
    def from_report(cls, r):
        m = r.get("metrics") or {}
        return cls(r["run_id"], r["status"], (r.get("validation") or {}).get("status", "UNKNOWN"),
                   int(m.get("n_trades", 0)), float(m.get("total_return_pct", 0.0)))
''')
O("tests/unit/backend/schemas/test_backtest.py", r'''
from backend.schemas.backtest import BacktestRequest


def _bad(d):
    try:
        BacktestRequest.from_dict(d)
    except ValueError:
        return True
    return False


def test_valid_and_defaults():
    r = BacktestRequest.from_dict({"strategy_id": " s ", "dataset": "a.csv", "validation": {"split": 0.8, "windows": 5}})
    assert r.strategy_id == "s" and r.params == {} and r.validation["windows"] == 5


def test_rejects_bad_input():
    assert _bad("x") and _bad({"strategy_id": "s"}) and _bad({"strategy_id": "s", "dataset": ""})
    assert _bad({"strategy_id": "s", "dataset": "a.csv", "typo_key": 1})
    assert _bad({"strategy_id": "s", "dataset": "a.csv", "params": [1]})
    assert _bad({"strategy_id": "s", "dataset": "a.csv", "validation": {"split": 2}})
    assert _bad({"strategy_id": "s", "dataset": "a.csv", "validation": {"windows": True}})
''')
O("tests/unit/backend/schemas/test_strategy.py", r'''
from backend.schemas.strategy import StrategySummary


def test_summary_and_live_flag():
    m = {"id": "x", "version": "0.1.0", "required_data": ["oi"], "execution_modes": ["backtest"], "live_trading": {"enabled": False}}
    s = StrategySummary.from_manifest(m)
    assert s.id == "x" and s.live_trading_enabled is False and s.required_data == ["oi"]
    m["live_trading"] = {"enabled": True}
    assert StrategySummary.from_manifest(m).live_trading_enabled is True
''')
O("tests/unit/backend/schemas/test_report.py", r'''
from backend.schemas.report import ReportSummary


def test_summary():
    r = ReportSummary.from_report({"run_id": "r", "status": "COMPLETED", "validation": {"status": "FAIL"},
                                   "metrics": {"n_trades": 4, "total_return_pct": -1.5}})
    assert r.validation_status == "FAIL" and r.n_trades == 4 and r.total_return_pct == -1.5
''')

# ---------------------------------------------------------------- backtest/execution.py + engine refactor
O("backtest/execution.py", r'''
"""ExecutionModel: slippage + fees + fill rules ek jagah (engine seedha slippage/fees nahi bulata)."""
from backtest import fees, slippage, stop_manager


class ExecutionModel:
    def __init__(self, slippage_bps=2.0, fee_pct=0.0003, ambiguous_candle_policy="stop_first"):
        if slippage_bps < 0 or fee_pct < 0:
            raise ValueError("slippage_bps aur fee_pct negative nahi ho sakte")
        self.slippage_bps, self.fee_pct, self.policy = slippage_bps, fee_pct, ambiguous_candle_policy

    def fill_entry(self, ref_price, qty):
        px = slippage.apply(ref_price, "BUY", self.slippage_bps)
        return px, fees.fee(qty * px, self.fee_pct)

    def fill_exit(self, raw_price, qty):
        px = slippage.apply(raw_price, "SELL", self.slippage_bps)
        return px, fees.fee(qty * px, self.fee_pct)

    def check_exit(self, position, bar):
        return stop_manager.check(position, bar, self.policy)
''')
O("tests/unit/backtest/test_execution.py", r'''
from backtest.execution import ExecutionModel
from data.models import Bar
from backtest.portfolio import Position


def test_costs_direction_and_amounts():
    m = ExecutionModel(slippage_bps=10, fee_pct=0.001)
    px, fee = m.fill_entry(100.0, 10)
    assert abs(px - 100.1) < 1e-9 and abs(fee - 1.001) < 1e-9
    px, fee = m.fill_exit(100.0, 10)
    assert abs(px - 99.9) < 1e-9 and abs(fee - 0.999) < 1e-9


def test_negative_costs_rejected_and_exit_rule():
    try:
        ExecutionModel(-1, 0)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    pos = Position(1, 100.0, "t", 95.0, 108.0, 0.0)
    assert ExecutionModel().check_exit(pos, Bar("t", 100, 110, 90, 105)) == (95.0, "STOP_AMBIGUOUS_CONSERVATIVE")
''')
_patch("backtest/engine.py", "from backtest import fees, slippage, stop_manager, position_sizing\n",
       "from backtest import position_sizing\nfrom backtest.execution import ExecutionModel\n")
_patch("backtest/engine.py", '''    def close(raw_price, bar, why):
        px = slippage.apply(raw_price, "SELL", bps)
        pf.close(px, bar.ts, fees.fee(pf.position.qty * px, fee_pct), why)
''', '''    model = ExecutionModel(bps, fee_pct, policy)

    def close(raw_price, bar, why):
        px, fee = model.fill_exit(raw_price, pf.position.qty)
        pf.close(px, bar.ts, fee, why)
''')
_patch("backtest/engine.py", '''            px = slippage.apply(bar.open, "BUY", bps)
            pf.open(pending["qty"], px, bar.ts, pending["stop"], pending["target"],
                    fees.fee(pending["qty"] * px, fee_pct))''', '''            px, fee = model.fill_entry(bar.open, pending["qty"])
            pf.open(pending["qty"], px, bar.ts, pending["stop"], pending["target"], fee)''')
_patch("backtest/engine.py", "ex = stop_manager.check(pf.position, bar, policy)", "ex = model.check_exit(pf.position, bar)")

# ---------------------------------------------------------------- data/corporate_actions, survivorship, storage, options
O("data/corporate_actions.py", r'''
"""Corporate actions: pichhli bars ko back-adjust (split, dividend). Naya Bar list lautata hai, original nahi badalta."""
from data.models import Bar


def _scale(bar, price_factor, volume_factor=1.0):
    return Bar(bar.ts, bar.open * price_factor, bar.high * price_factor, bar.low * price_factor,
               bar.close * price_factor, bar.volume * volume_factor, dict(bar.extras))


def apply_splits(bars, splits):
    """splits: [{"date": "YYYY-MM-DD", "ratio": 2.0}]  (2-for-1 => ratio 2.0). date se pehle ki bars adjust."""
    for s in splits:
        if s["ratio"] <= 0:
            raise ValueError("split ratio > 0 hona chahiye")
    out = []
    for b in bars:
        f = 1.0
        for s in splits:
            if b.ts[:10] < s["date"]:
                f *= s["ratio"]
        out.append(_scale(b, 1.0 / f, f))
    return out


def apply_dividends(bars, dividends):
    """dividends: [{"date": "YYYY-MM-DD", "amount": 5.0}]. Factor = 1 - amount / (ex-date se pehle ka last close)."""
    factors = []
    for d in dividends:
        prev = [b for b in bars if b.ts[:10] < d["date"]]
        if not prev:
            continue
        if d["amount"] < 0 or d["amount"] >= prev[-1].close:
            raise ValueError("dividend amount 0 se close ke beech hona chahiye")
        factors.append((d["date"], 1.0 - d["amount"] / prev[-1].close))
    out = []
    for b in bars:
        f = 1.0
        for date, k in factors:
            if b.ts[:10] < date:
                f *= k
        out.append(_scale(b, f))
    return out
''')
O("tests/unit/data/test_corporate_actions.py", r'''
from data.corporate_actions import apply_dividends, apply_splits
from data.models import Bar


def _bars():
    return [Bar("2024-01-01T09:15:00", 100, 102, 98, 100, 10), Bar("2024-01-02T09:15:00", 50, 51, 49, 50, 20)]


def test_split_adjusts_only_before_date_and_original_untouched():
    orig = _bars()
    out = apply_splits(orig, [{"date": "2024-01-02", "ratio": 2.0}])
    assert out[0].close == 50.0 and out[0].volume == 20.0 and out[1].close == 50.0 and out[1].volume == 20
    assert orig[0].close == 100  # original nahi badla


def test_dividend_factor():
    out = apply_dividends(_bars(), [{"date": "2024-01-02", "amount": 10.0}])
    assert abs(out[0].close - 90.0) < 1e-9 and out[1].close == 50


def test_bad_inputs():
    for fn, arg in ((apply_splits, [{"date": "2024-01-02", "ratio": 0}]), (apply_dividends, [{"date": "2024-01-02", "amount": 100.0}])):
        try:
            fn(_bars(), arg)
            raise AssertionError("expected ValueError")
        except ValueError:
            pass
''')
O("data/survivorship.py", r'''
"""Survivorship-bias check: universe snapshots (date -> symbols) me churn dikhna chahiye."""


def check(snapshots):
    dates = sorted(snapshots)
    if len(dates) < 2:
        return {"status": "UNAVAILABLE", "reason": "NEED_MULTIPLE_UNIVERSE_SNAPSHOTS"}
    first, last = set(snapshots[dates[0]]), set(snapshots[dates[-1]])
    dropped, added = sorted(first - last), sorted(last - first)
    if not dropped and not added:
        return {"status": "WARN", "reason": "NO_CHURN: sirf aaj ke constituents hone ka khatra (survivorship bias)",
                "dropped": [], "added": []}
    return {"status": "PASS", "dropped": dropped, "added": added,
            "churn_pct": 100.0 * len(dropped) / len(first) if first else 0.0}
''')
O("tests/unit/data/test_survivorship.py", r'''
from data.survivorship import check


def test_statuses():
    assert check({"2020-01-01": ["A"]})["status"] == "UNAVAILABLE"
    assert check({"2020-01-01": ["A", "B"], "2024-01-01": ["A", "B"]})["status"] == "WARN"
    r = check({"2020-01-01": ["A", "B"], "2024-01-01": ["A", "C"]})
    assert r["status"] == "PASS" and r["dropped"] == ["B"] and r["added"] == ["C"] and r["churn_pct"] == 50.0
''')
O("data/storage.py", r'''
"""DatasetStore: Dataset ko disk par (meta.json + bars.jsonl) checksum ke saath rakhna. Parquet baad me (pyarrow optional)."""
import hashlib
import json
import re
from pathlib import Path

from data.models import Bar, Dataset


def _safe(name):
    s = re.sub(r"[^A-Za-z0-9_.-]", "_", name)
    if not s or s.startswith("."):
        raise ValueError("invalid dataset id")
    return s


class DatasetStore:
    def __init__(self, root="data/store"):
        self.root = Path(root)

    def save(self, ds):
        d = self.root / _safe(ds.dataset_id)
        d.mkdir(parents=True, exist_ok=True)
        lines = [json.dumps([b.ts, b.open, b.high, b.low, b.close, b.volume, b.extras]) for b in ds.bars]
        body = "\n".join(lines) + ("\n" if lines else "")
        (d / "bars.jsonl").write_text(body, encoding="utf-8")
        meta = {**ds.meta(), "fields": sorted(ds.fields), "quality": ds.quality, "bars": len(ds.bars),
                "bars_sha256": hashlib.sha256(body.encode()).hexdigest()}
        (d / "meta.json").write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")
        return str(d)

    def load(self, dataset_id):
        d = self.root / _safe(dataset_id)
        if not (d / "meta.json").exists():
            raise KeyError(dataset_id)
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        body = (d / "bars.jsonl").read_text(encoding="utf-8")
        if hashlib.sha256(body.encode()).hexdigest() != meta["bars_sha256"]:
            raise ValueError("checksum mismatch: dataset badla gaya hai")
        bars = [Bar(*json.loads(x)) for x in body.splitlines()]
        return Dataset(meta["dataset_id"], meta["symbol"], meta["timeframe"], bars, meta["timezone"], meta["source"],
                       meta["schema_version"], meta["content_hash"], set(meta["fields"]), meta["quality_status"], meta["quality"])

    def list_ids(self):
        return sorted(p.parent.name for p in self.root.glob("*/meta.json")) if self.root.exists() else []
''')
O("tests/unit/data/test_storage.py", r'''
from data.storage import DatasetStore
from tests._helpers import make_bars, make_dataset


def test_round_trip_and_tamper_detection(tmp_path):
    store = DatasetStore(tmp_path)
    ds = make_dataset(make_bars(15))
    store.save(ds)
    back = store.load("t")
    assert back.bars == ds.bars and back.fields == ds.fields and back.meta() == ds.meta()
    assert store.list_ids() == ["t"]
    f = tmp_path / "t" / "bars.jsonl"
    f.write_text(f.read_text().replace("100.", "999.", 1))
    try:
        store.load("t")
        raise AssertionError("expected ValueError")
    except ValueError as e:
        assert "checksum" in str(e)


def test_unsafe_id_and_unknown(tmp_path):
    store = DatasetStore(tmp_path)
    for fn in (store.load,):
        try:
            fn("..")
            raise AssertionError("expected ValueError")
        except ValueError:
            pass
    try:
        store.load("nope")
        raise AssertionError("expected KeyError")
    except KeyError:
        pass
''')
F15("data/options.py", "Option contract + chain validation (expiry, strike, lot size, bid/ask)", r'''
"""Option data checks. Poora option backtest tab banega jab option-chain data + strategy ke niyam milenge."""
from dataclasses import dataclass
from datetime import date

REQUIRED = ("ts", "underlying", "expiry", "strike", "option_type", "lot_size")


@dataclass(frozen=True)
class OptionContract:
    underlying: str
    expiry: str
    strike: float
    kind: str
    lot_size: int


def days_to_expiry(ts, expiry):
    return (date.fromisoformat(expiry) - date.fromisoformat(ts[:10])).days


def validate_chain(rows):
    issues = []
    for i, r in enumerate(rows):
        missing = [k for k in REQUIRED if r.get(k) in (None, "")]
        if missing:
            issues.append({"row": i, "code": "MISSING_FIELDS", "msg": ",".join(missing)})
            continue
        try:
            if float(r["strike"]) <= 0:
                issues.append({"row": i, "code": "BAD_STRIKE", "msg": str(r["strike"])})
            if int(r["lot_size"]) <= 0:
                issues.append({"row": i, "code": "BAD_LOT_SIZE", "msg": str(r["lot_size"])})
            if str(r["option_type"]).upper() not in ("CE", "PE", "CALL", "PUT"):
                issues.append({"row": i, "code": "BAD_OPTION_TYPE", "msg": str(r["option_type"])})
            if days_to_expiry(r["ts"], r["expiry"]) < 0:
                issues.append({"row": i, "code": "EXPIRED_CONTRACT", "msg": r["expiry"]})
        except (ValueError, TypeError) as e:
            issues.append({"row": i, "code": "BAD_VALUE", "msg": str(e)})
            continue
        bid, ask = r.get("bid"), r.get("ask")
        if bid is not None and ask is not None and (float(bid) < 0 or float(bid) > float(ask)):
            issues.append({"row": i, "code": "BAD_BID_ASK", "msg": f"{bid}>{ask}"})
    return issues


def quality_status(issues):
    return "BLOCKED" if issues else "PASS"
''')
O("tests/unit/data/test_options.py", r'''
from data.options import days_to_expiry, quality_status, validate_chain

GOOD = {"ts": "2024-01-01T09:15:00", "underlying": "NIFTY", "expiry": "2024-01-04", "strike": 21000, "option_type": "CE",
        "lot_size": 25, "bid": 100.0, "ask": 101.0}


def test_good_row_and_days():
    assert validate_chain([GOOD]) == [] and quality_status([]) == "PASS"
    assert days_to_expiry("2024-01-01T09:15:00", "2024-01-04") == 3


def test_bad_rows_flagged():
    bad = [dict(GOOD, strike=0), dict(GOOD, lot_size=0), dict(GOOD, option_type="XX"), dict(GOOD, expiry="2023-12-01"),
           dict(GOOD, bid=5, ask=1), dict(GOOD, expiry=""), dict(GOOD, expiry="not-a-date")]
    codes = [i["code"] for i in validate_chain(bad)]
    assert codes == ["BAD_STRIKE", "BAD_LOT_SIZE", "BAD_OPTION_TYPE", "EXPIRED_CONTRACT", "BAD_BID_ASK", "MISSING_FIELDS", "BAD_VALUE"]
    assert quality_status(validate_chain(bad)) == "BLOCKED"
''')

# ---------------------------------------------------------------- registry: lifecycle, compatibility, permissions, storage
O("registry/lifecycle.py", r'''
"""Strategy lifecycle states (blueprint: Draft, Validated, Rejected + Approved, Retired)."""
ALLOWED = {"DRAFT": {"VALIDATED", "REJECTED", "RETIRED"},
           "VALIDATED": {"APPROVED", "DRAFT", "REJECTED", "RETIRED"},
           "APPROVED": {"RETIRED", "DRAFT"},
           "REJECTED": {"DRAFT"},
           "RETIRED": set()}


def can_transition(a, b):
    return b in ALLOWED.get(a, set())
''')
O("registry/permissions.py", r'''
"""Role-based permissions. viewer < analyst < admin."""
_VIEWER = {"list", "view", "view_report"}
_ANALYST = _VIEWER | {"run_backtest", "run_validation", "compare"}
ROLES = {"viewer": _VIEWER, "analyst": _ANALYST, "admin": _ANALYST | {"register", "approve", "reject", "retire"}}


def can(role, action):
    return action in ROLES.get(role, set())


def require(role, action):
    if not can(role, action):
        raise PermissionError(f"role '{role}' ko '{action}' ki ijazat nahi")
''')
O("registry/compatibility.py", r'''
"""Manifest compatibility: backtest mode, live-trading band, min engine version."""


def _ver(s):
    parts = [int(x) for x in str(s).split(".")[:3]]
    return tuple(parts + [0] * (3 - len(parts)))


def check(manifest, engine_version=None):
    if engine_version is None:
        from backtest.engine import ENGINE_VERSION as engine_version
    errs = []
    if "backtest" not in (manifest.get("execution_modes") or []):
        errs.append("EXECUTION_MODE_BACKTEST_MISSING")
    lt = manifest.get("live_trading")
    if lt is True or (isinstance(lt, dict) and lt.get("enabled") is True):
        errs.append("LIVE_TRADING_NOT_ALLOWED")
    mv = manifest.get("min_engine_version")
    if mv is not None:
        try:
            if _ver(mv) > _ver(engine_version):
                errs.append(f"ENGINE_TOO_OLD:needs {mv}")
        except ValueError:
            errs.append("BAD_MIN_ENGINE_VERSION")
    return errs
''')
O("registry/storage.py", r'''
"""RegistryStore: strategy status + history (JSON). Gates: VALIDATED ke liye validation PASS, APPROVED ke liye admin + pichhli PASS."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from registry import lifecycle, permissions

_ACTION = {"DRAFT": "register", "VALIDATED": "run_validation", "APPROVED": "approve", "REJECTED": "reject", "RETIRED": "retire"}


class RegistryStore:
    def __init__(self, root="registry_state"):
        self.file = Path(root) / "state.json"

    def _load(self):
        return json.loads(self.file.read_text(encoding="utf-8")) if self.file.exists() else {}

    def _save(self, state):
        self.file.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.file.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
        os.replace(tmp, self.file)

    def get(self, sid):
        return self._load().get(sid, {"status": "DRAFT", "validation_status": None, "validation_run_id": None, "history": []})

    def promote(self, sid, to, role, validation_status=None, validation_run_id=None, note=""):
        if to not in _ACTION:
            raise ValueError(f"unknown status {to}")
        permissions.require(role, _ACTION[to])
        entry = self.get(sid)
        cur = entry["status"]
        if not lifecycle.can_transition(cur, to):
            raise ValueError(f"transition {cur} -> {to} allowed nahi")
        if to == "VALIDATED":
            if validation_status != "PASS":
                raise ValueError("VALIDATED ke liye validation status PASS chahiye")
            entry["validation_status"], entry["validation_run_id"] = validation_status, validation_run_id
        if to == "APPROVED" and entry.get("validation_status") != "PASS":
            raise ValueError("APPROVED ke liye pichhli validation PASS honi chahiye")
        entry["status"] = to
        entry["history"].append({"ts": datetime.now(timezone.utc).isoformat(), "from": cur, "to": to, "role": role, "note": note})
        state = self._load()
        state[sid] = entry
        self._save(state)
        return entry
''')
O("tests/unit/registry/test_permissions.py", r'''
from registry.permissions import can, require


def test_roles():
    assert can("viewer", "list") and not can("viewer", "run_backtest")
    assert can("analyst", "run_backtest") and not can("analyst", "approve")
    assert can("admin", "approve") and not can("nobody", "list")
    try:
        require("analyst", "approve")
        raise AssertionError("expected PermissionError")
    except PermissionError:
        pass
''')
O("tests/unit/registry/test_compatibility.py", r'''
from registry import compatibility as c

OK = {"execution_modes": ["backtest"], "live_trading": {"enabled": False}}


def test_checks():
    assert c.check(OK, "0.1.0") == []
    assert "EXECUTION_MODE_BACKTEST_MISSING" in c.check({"execution_modes": ["paper"]}, "0.1.0")
    assert "LIVE_TRADING_NOT_ALLOWED" in c.check({**OK, "live_trading": {"enabled": True}}, "0.1.0")
    assert "LIVE_TRADING_NOT_ALLOWED" in c.check({**OK, "live_trading": True}, "0.1.0")
    assert c.check({**OK, "min_engine_version": "0.2"}, "0.1.0")[0].startswith("ENGINE_TOO_OLD")
    assert c.check({**OK, "min_engine_version": "0.1.0"}, "0.1.0") == []
    assert c.check({**OK, "min_engine_version": "x.y"}, "0.1.0") == ["BAD_MIN_ENGINE_VERSION"]


def test_real_manifests_are_compatible():
    from registry.registry import Registry
    reg = Registry()
    for sid in reg.discover():
        assert c.check(reg.manifest(sid)) == [], sid
''')
O("tests/unit/registry/test_storage.py", r'''
from registry.storage import RegistryStore


def _fails(fn, exc, *a, **k):
    try:
        fn(*a, **k)
    except exc:
        return True
    return False


def test_gates_and_history(tmp_path):
    s = RegistryStore(tmp_path)
    assert s.get("x")["status"] == "DRAFT"
    assert _fails(s.promote, ValueError, "x", "VALIDATED", "analyst", validation_status="FAIL")
    assert _fails(s.promote, PermissionError, "x", "REJECTED", "analyst")
    assert _fails(s.promote, ValueError, "x", "APPROVED", "admin")  # DRAFT -> APPROVED allowed nahi
    s.promote("x", "VALIDATED", "analyst", validation_status="PASS", validation_run_id="run-1")
    assert _fails(s.promote, PermissionError, "x", "APPROVED", "analyst")
    e = s.promote("x", "APPROVED", "admin", note="manual review")
    assert e["status"] == "APPROVED" and e["validation_run_id"] == "run-1" and len(e["history"]) == 2
    assert RegistryStore(tmp_path).get("x")["status"] == "APPROVED"  # disk par bacha


def test_reject_then_back_to_draft(tmp_path):
    s = RegistryStore(tmp_path)
    s.promote("y", "REJECTED", "admin")
    assert s.promote("y", "DRAFT", "admin")["status"] == "DRAFT"
''')
_patch("registry/registry.py", "from registry.metadata import load_manifest\n", "from registry import compatibility\nfrom registry.metadata import load_manifest\n")
_patch("registry/registry.py", "errs = validate_manifest(m)", "errs = validate_manifest(m) + compatibility.check(m)")
for _sid in ("strategies/gamma_blast/manifest.yaml", "strategies/three_pm_momentum/manifest.yaml"):
    OVERRIDES[_sid] = OVERRIDES[_sid].rstrip("\n") + "\nlive_trading: {enabled: false}\n"

# ---------------------------------------------------------------- contracts/proto (real messages; protoc ke bina bhi structure test hota hai)
O("contracts/proto/common.proto", r'''
syntax = "proto3";
package svl;

enum Side {
  SIDE_UNSPECIFIED = 0;
  BUY = 1;
  SELL = 2;
  EXIT = 3;
}

enum QualityStatus {
  QUALITY_UNSPECIFIED = 0;
  PASS = 1;
  WARN = 2;
  BLOCKED = 3;
}

message Error {
  string code = 1;
  string message = 2;
}
''')
O("contracts/proto/market_data.proto", r'''
syntax = "proto3";
package svl;

import "common.proto";

message Bar {
  string ts = 1;
  double open = 2;
  double high = 3;
  double low = 4;
  double close = 5;
  double volume = 6;
  map<string, double> extras = 7;
}

message Dataset {
  string dataset_id = 1;
  string symbol = 2;
  string timeframe = 3;
  string start_time = 4;
  string end_time = 5;
  string timezone = 6;
  string source = 7;
  string schema_version = 8;
  string content_hash = 9;
  QualityStatus quality_status = 10;
  repeated Bar bars = 11;
}
''')
O("contracts/proto/strategy.proto", r'''
syntax = "proto3";
package svl;

message StrategyManifest {
  string id = 1;
  string version = 2;
  string entry_point = 3;
  repeated string required_data = 4;
  map<string, string> parameters = 5;
  repeated string execution_modes = 6;
  bool live_trading_enabled = 7;
}
''')
O("contracts/proto/signal.proto", r'''
syntax = "proto3";
package svl;

import "common.proto";

message Signal {
  Side side = 1;
  optional double stop_loss = 2;
  optional double target = 3;
  optional double size_hint = 4;
  string reason = 5;
}
''')
O("contracts/proto/backtest.proto", r'''
syntax = "proto3";
package svl;

message Trade {
  string entry_ts = 1;
  string exit_ts = 2;
  double entry_price = 3;
  double exit_price = 4;
  int64 qty = 5;
  double pnl = 6;
  double fees = 7;
  string reason = 8;
}

message EquityPoint {
  string ts = 1;
  double equity = 2;
}

message BacktestRequest {
  string strategy_id = 1;
  string dataset = 2;
  map<string, string> params = 3;
  string symbol = 4;
  string timeframe = 5;
}

message BacktestResult {
  string run_id = 1;
  string status = 2;
  string reason = 3;
  repeated Trade trades = 4;
  repeated EquityPoint equity = 5;
}
''')
O("contracts/proto/metrics.proto", r'''
syntax = "proto3";
package svl;

message Metrics {
  map<string, double> values = 1;
}

message CheckResult {
  string status = 1;
  string reason = 2;
}

message ValidationResult {
  string status = 1;
  map<string, CheckResult> checks = 2;
}
''')
O("contracts/proto/report.proto", r'''
syntax = "proto3";
package svl;

import "metrics.proto";

message Report {
  string run_id = 1;
  string status = 2;
  Metrics metrics = 3;
  ValidationResult validation = 4;
  string generated_at = 5;
}
''')
F15("tests/contract/test_proto_files.py", "Proto files ka structure (protoc ke bina)", r'''
import re
from pathlib import Path

PROTO = Path(__file__).resolve().parents[2] / "contracts" / "proto"
BLOCK = re.compile(r"(message|enum)\s+(\w+)\s*\{([^{}]*)\}")
FIELD = re.compile(r"^\s*(?:repeated\s+|optional\s+)?(?:map<\s*\w+\s*,\s*[\w.]+\s*>|[\w.]+)\s+(\w+)\s*=\s*(\d+)\s*;", re.M)
ENUM_VAL = re.compile(r"^\s*(\w+)\s*=\s*(-?\d+)\s*;", re.M)


def _clean(text):
    return re.sub(r"//.*", "", text)


def test_every_proto_is_well_formed():
    files = sorted(PROTO.glob("*.proto"))
    assert len(files) == 7
    names_seen = {}
    for f in files:
        t = _clean(f.read_text(encoding="utf-8"))
        assert 'syntax = "proto3";' in t and "package svl;" in t, f.name
        assert t.count("{") == t.count("}"), f.name
        for imp in re.findall(r'import\s+"([^"]+)";', t):
            assert (PROTO / imp).exists(), f"{f.name}: missing import {imp}"
        blocks = BLOCK.findall(t)
        assert blocks, f.name
        for kind, name, body in blocks:
            assert name not in names_seen, f"duplicate type {name}"
            names_seen[name] = f.name
            if kind == "message":
                nums = [int(n) for _, n in FIELD.findall(body)]
                fields = [n for n, _ in FIELD.findall(body)]
                assert len(nums) == len(set(nums)) and len(fields) == len(set(fields)), f"{f.name}:{name}"
                assert all(n >= 1 for n in nums)
            else:
                vals = ENUM_VAL.findall(body)
                assert vals and vals[0][1] == "0", f"{f.name}:{name} pehla enum value 0 hona chahiye"
    assert {"Bar", "Dataset", "Signal", "Trade", "BacktestResult", "Metrics", "Report"} <= set(names_seen)


def test_proto_fields_cover_json_schema_trade_fields():
    from contracts import schema_check
    trade_fields = set(schema_check.load("trade.schema.json")["required"])
    body = re.search(r"message Trade\s*\{([^{}]*)\}", _clean((PROTO / "backtest.proto").read_text(encoding="utf-8"))).group(1)
    assert trade_fields <= {n for n, _ in FIELD.findall(body)}
''', ["contracts/proto/backtest.proto"])

# ---------------------------------------------------------------- isolated run + background worker
F15("backend/jobs/run_job.py", "Subprocess entry: limits lagakar run_full chalata hai (stdin JSON -> stdout JSON)", r'''
"""Alag process me chalne wala entry. Pehle resource limits, phir hi koi strategy code import hota hai.
Sandbox nahi: sirf CPU/memory/time limit + saaf env. Network/filesystem isolation ke liye container/OS user chahiye."""
import json
import os
import sys


def _apply_limits():
    try:
        import resource
    except ImportError:  # non-posix
        return
    cpu = int(os.environ.get("SVL_CPU_SECONDS", "0"))
    mem = int(os.environ.get("SVL_MEM_MB", "0"))
    if cpu:
        resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))
    if mem:
        resource.setrlimit(resource.RLIMIT_AS, (mem * 1024 * 1024, mem * 1024 * 1024))


def main():
    _apply_limits()
    req = json.load(sys.stdin)
    from backend.services.backtest_service import run_full
    record, paths = run_full(req["strategy_id"], req["data_path"], req.get("params"), req.get("config"),
                             out_root=req["out_root"], symbol=req.get("symbol", "UNKNOWN"),
                             timeframe=req.get("timeframe", "UNKNOWN"), validation_opts=req.get("validation_opts"))
    print(json.dumps({"record": record, "paths": paths}, default=str))


if __name__ == "__main__":
    main()
''', ["backend/services/backtest_service.py"])
F15("backend/jobs/isolated.py", "Run ko alag process me limits ke saath chalana", r'''
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def child_env(cpu_seconds, mem_mb):
    """Sirf zaroori env (koi API key/token child ko nahi jaata)."""
    return {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "PYTHONPATH": str(ROOT), "LANG": "C.UTF-8",
            "SVL_CPU_SECONDS": str(cpu_seconds), "SVL_MEM_MB": str(mem_mb)}


def run_isolated(request, timeout=300, mem_mb=2048):
    p = subprocess.run([sys.executable, "-m", "backend.jobs.run_job"], input=json.dumps(request), capture_output=True,
                       text=True, timeout=timeout, cwd=str(ROOT), env=child_env(timeout, mem_mb))
    if p.returncode != 0:
        tail = (p.stderr.strip().splitlines() or ["no stderr"])[-1][:300]
        raise RuntimeError(f"isolated run failed (exit {p.returncode}): {tail}")
    return json.loads(p.stdout.strip().splitlines()[-1])
''', ["backend/jobs/run_job.py"])
O("backend/jobs/queue.py", r'''
import itertools
import threading

from backend.jobs.job_status import Job, JobStatus


class JobQueue:
    def __init__(self):
        self.jobs, self._ids, self._lock = {}, itertools.count(1), threading.Lock()

    def submit(self, payload):
        with self._lock:
            job = Job(f"job-{next(self._ids)}", payload)
            self.jobs[job.job_id] = job
            return job

    def get(self, job_id):
        return self.jobs[job_id]

    def next_queued(self):
        return next((j for j in self.jobs.values() if j.status == JobStatus.QUEUED), None)

    def claim_next(self):
        """Atomically pehla QUEUED job RUNNING bana kar deta hai."""
        with self._lock:
            job = self.next_queued()
            if job is not None:
                job.status = JobStatus.RUNNING
            return job
''')
O("backend/jobs/worker.py", r'''
"""Worker: job RUNNING -> SUCCEEDED/FAILED (failure ka karan save). BackgroundWorker = daemon thread."""
import threading

from backend.jobs.job_status import JobStatus


def run_next(queue, handler):
    job = queue.claim_next()
    if job is None:
        return None
    try:
        job.result = handler(job.payload)
        job.status = JobStatus.SUCCEEDED
    except Exception as e:  # noqa: BLE001 - failure reason save karna hai
        job.status, job.error = JobStatus.FAILED, f"{type(e).__name__}: {e}"
    return job


class BackgroundWorker:
    def __init__(self, queue, handler, interval=0.2):
        self.queue, self.handler, self.interval = queue, handler, interval
        self._stop, self._thread = threading.Event(), None

    def start(self):
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="svl-worker")
        self._thread.start()

    def _loop(self):
        while not self._stop.is_set():
            if run_next(self.queue, self.handler) is None:
                self._stop.wait(self.interval)

    def stop(self, timeout=5):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout)
''')
_patch("backend/services/backtest_service.py", 'timeframe="UNKNOWN", run_id=None, repo=None):', 'timeframe="UNKNOWN", run_id=None, repo=None, validation_opts=None):')
_patch("backend/services/backtest_service.py", "run_validation(ds, factory, cfg)", "run_validation(ds, factory, cfg, **(validation_opts or {}))")
O("backend/api/backtests.py", r'''
"""/backtests. Default: job inline chalta hai. Env: BACKGROUND_WORKER=1 (thread), RUN_ISOLATED=1 (alag process + limits)."""
import os
from pathlib import Path

from backend.api.common import guarded, make_router, runs_root
from backend.dependencies import get_queue
from backend.jobs.worker import BackgroundWorker, run_next
from backend.schemas.backtest import BacktestRequest
from backend.services import dataset_service, report_service
from backend.services.backtest_service import run_full

_worker = None


def _handler(payload):
    req = BacktestRequest.from_dict(payload)
    data_path = str(Path(dataset_service.resolve(req.dataset)).resolve())
    out_root = str(Path(runs_root()).resolve())
    if os.environ.get("RUN_ISOLATED") == "1":
        from backend.jobs.isolated import run_isolated
        record = run_isolated({"strategy_id": req.strategy_id, "data_path": data_path, "params": req.params,
                               "config": req.config, "out_root": out_root, "symbol": req.symbol,
                               "timeframe": req.timeframe, "validation_opts": req.validation})["record"]
    else:
        record, _ = run_full(req.strategy_id, data_path, req.params, req.config, out_root=out_root, symbol=req.symbol,
                             timeframe=req.timeframe, validation_opts=req.validation)
    return {"run_id": record["run_id"], "status": record["status"], "validation_status": record["validation_status"],
            "reason": record["reason"]}


def _job_view(job):
    return {"job_id": job.job_id, "status": job.status.value, "result": job.result, "error": job.error}


def _ensure_worker():
    global _worker
    if _worker is None:
        _worker = BackgroundWorker(get_queue(), _handler)
    _worker.start()
    return _worker


def start(payload: dict):
    BacktestRequest.from_dict(payload)  # galat input turant ValueError
    q = get_queue()
    job = q.submit(payload)
    if os.environ.get("BACKGROUND_WORKER") == "1":
        _ensure_worker()
    else:
        run_next(q, _handler)
    return _job_view(job)


def list_runs():
    return report_service.list_runs(runs_root())


def get_one(item_id: str):
    if item_id.startswith("job-"):
        return _job_view(get_queue().get(item_id))
    return report_service.get_run(item_id, runs_root())


def get_results(item_id: str):
    r = report_service.get_report(item_id, runs_root())
    return {k: r.get(k) for k in ("run_id", "status", "reason", "metrics", "trades", "equity")}


router = make_router()
if router is not None:
    router.post("/backtests")(guarded(start))
    router.get("/backtests")(guarded(list_runs))
    router.get("/backtests/{item_id}")(guarded(get_one))
    router.get("/backtests/{item_id}/results")(guarded(get_results))
''')
O("backend/api/validation.py", r'''
from backend.api import backtests
from backend.api.common import guarded, make_router, runs_root
from backend.services import validation_service


def start(payload: dict):
    """POST /validations: pura pipeline chalta hai; payload me optional validation={'split':..,'windows':..}."""
    return backtests.start(payload)


def get_one(run_id: str):
    return validation_service.get_validation(run_id, runs_root())


router = make_router()
if router is not None:
    router.post("/validations")(guarded(start))
    router.get("/validations/{run_id}")(guarded(get_one))
''')
O("contracts/openapi.yaml", r'''
openapi: 3.1.0
info: {title: strategy-validation-lab, version: 0.1.0}
paths:
  /health: {get: {summary: Health}}
  /strategies: {get: {summary: List}, post: {summary: Create (abhi band)}}
  /strategies/{id}: {get: {summary: Detail}}
  /datasets: {get: {summary: List datasets}}
  /backtests: {get: {summary: List runs}, post: {summary: Start run}}
  /backtests/{id}: {get: {summary: Run detail + job status}}
  /backtests/{id}/results: {get: {summary: Run results (metrics, trades, equity)}}
  /validations: {post: {summary: Start validation run}}
  /validations/{id}: {get: {summary: Validation result}}
  /comparisons: {post: {summary: Compare runs}}
  /reports/{id}: {get: {summary: Report}}
  /audit: {get: {summary: Audit log}}
''')
F15("tests/unit/backend/jobs/test_isolated.py", "Isolated run: env saaf + result inline ke barabar", r'''
import os

from backend.jobs.isolated import child_env, run_isolated
from backend.services.backtest_service import run_full
from cli.commands import make_sample_csv


def test_child_env_has_no_secrets():
    os.environ["SVL_SECRET_TEST"] = "x"
    try:
        env = child_env(60, 512)
        assert "SVL_SECRET_TEST" not in env and env["SVL_MEM_MB"] == "512" and "PYTHONPATH" in env
    finally:
        os.environ.pop("SVL_SECRET_TEST", None)


def test_isolated_matches_inline(tmp_path):
    csv = make_sample_csv(tmp_path / "s.csv", days=15)
    req = {"strategy_id": "three_pm_momentum", "data_path": str(csv), "out_root": str(tmp_path / "iso"), "params": None, "config": None}
    iso = run_isolated(req, timeout=120, mem_mb=2048)["record"]
    inline, _ = run_full("three_pm_momentum", str(csv), out_root=str(tmp_path / "inl"))
    assert iso["status"] == inline["status"] and iso["dataset_hash"] == inline["dataset_hash"]
    assert iso["validation_status"] == inline["validation_status"]


def test_isolated_failure_is_reported(tmp_path):
    csv = make_sample_csv(tmp_path / "s.csv", days=5)
    try:
        run_isolated({"strategy_id": "no_such_strategy", "data_path": str(csv), "out_root": str(tmp_path / "o")}, timeout=60)
        raise AssertionError("expected RuntimeError")
    except RuntimeError as e:
        assert "isolated run failed" in str(e)
''', ["backend/jobs/isolated.py"])
F15("tests/integration/test_background_worker.py", "BACKGROUND_WORKER=1: job turant QUEUED/RUNNING, phir SUCCEEDED", r'''
import os
import time

from backend.api import backtests
from cli.commands import make_sample_csv


def test_background_job_completes(tmp_path):
    make_sample_csv(tmp_path / "data" / "s.csv", days=15)
    os.environ.update({"DATA_DIR": str(tmp_path / "data"), "RUNS_ROOT": str(tmp_path / "runs"), "BACKGROUND_WORKER": "1"})
    try:
        job = backtests.start({"strategy_id": "three_pm_momentum", "dataset": "s.csv"})
        deadline = time.time() + 90
        while time.time() < deadline:
            view = backtests.get_one(job["job_id"])
            if view["status"] in ("SUCCEEDED", "FAILED"):
                break
            time.sleep(0.2)
        assert view["status"] == "SUCCEEDED", view
        run_id = view["result"]["run_id"]
        res = backtests.get_results(run_id)
        assert res["run_id"] == run_id and "metrics" in res and len(res["equity"]) > 10
    finally:
        os.environ.pop("BACKGROUND_WORKER", None)
        if backtests._worker is not None:
            backtests._worker.stop()
''', ["backend/jobs/worker.py"])
F15("tests/integration/test_api_validation_endpoint.py", "POST /validations options + results endpoint", r'''
import os

from backend.api import backtests, validation
from cli.commands import make_sample_csv


def test_validation_start_with_options(tmp_path):
    make_sample_csv(tmp_path / "data" / "s.csv", days=30)
    os.environ.update({"DATA_DIR": str(tmp_path / "data"), "RUNS_ROOT": str(tmp_path / "runs")})
    os.environ.pop("BACKGROUND_WORKER", None)
    job = validation.start({"strategy_id": "three_pm_momentum", "dataset": "s.csv", "validation": {"split": 0.6, "windows": 3}})
    assert job["status"] == "SUCCEEDED"
    rid = job["result"]["run_id"]
    v = validation.get_one(rid)
    assert len(v["checks"]["walk_forward"].get("windows", [])) in (0, 3)
    assert set(backtests.get_results(rid)) == {"run_id", "status", "reason", "metrics", "trades", "equity"}


def test_bad_validation_options_rejected(tmp_path):
    try:
        validation.start({"strategy_id": "x", "dataset": "s.csv", "validation": {"windows": 99}})
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
''', ["backend/api/validation.py"])

# ---------------------------------------------------------------- Go jobs + observability (+ tests)
O("engines/go/internal/jobs/jobs.go", r'''
package jobs

import "svl/validator/internal/contracts"

var allowed = map[contracts.JobStatus][]contracts.JobStatus{
	contracts.Queued:  {contracts.Running, contracts.Failed},
	contracts.Running: {contracts.Succeeded, contracts.Failed},
}

// CanTransition: job ki avastha ka sahi badlaav hai ya nahi (Python ke JobStatus ke saath same).
func CanTransition(from, to contracts.JobStatus) bool {
	for _, t := range allowed[from] {
		if t == to {
			return true
		}
	}
	return false
}
''')
O("engines/go/internal/observability/observability.go", r'''
package observability

import "sync"

// Counters: thread-safe naam-wale counter.
type Counters struct {
	mu sync.Mutex
	m  map[string]int
}

func NewCounters() *Counters { return &Counters{m: map[string]int{}} }

func (c *Counters) Inc(name string) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.m[name]++
}

func (c *Counters) Get(name string) int {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.m[name]
}
''')
F15("engines/go/internal/jobs/jobs_test.go", "Go test: job transitions", r'''
package jobs

import (
	"testing"

	"svl/validator/internal/contracts"
)

func TestCanTransition(t *testing.T) {
	if !CanTransition(contracts.Queued, contracts.Running) || !CanTransition(contracts.Running, contracts.Succeeded) {
		t.Fatal("QUEUED->RUNNING aur RUNNING->SUCCEEDED allowed hone chahiye")
	}
	if CanTransition(contracts.Succeeded, contracts.Running) || CanTransition(contracts.Queued, contracts.Succeeded) {
		t.Fatal("ye transitions allowed nahi")
	}
}
''', ["engines/go/internal/jobs/jobs.go"])
F15("engines/go/internal/observability/observability_test.go", "Go test: counters", r'''
package observability

import "testing"

func TestCounters(t *testing.T) {
	c := NewCounters()
	c.Inc("runs")
	c.Inc("runs")
	if c.Get("runs") != 2 || c.Get("none") != 0 {
		t.Fatal("counter galat")
	}
}
''', ["engines/go/internal/observability/observability.go"])

# ---------------------------------------------------------------- docs
O("docs/architecture/wiring-map.md", r'''
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
''')
O("docs/architecture/build-order.md", r'''
# Build order

Exact file-level order: `BUILD_ORDER.md` (dependency topological order, generator banata hai).

Phases: 0 foundation | 1 contracts | 2 data | 3 strategies+registry | 4 backtest+risk | 5 validation+metrics |
6 reporting+persistence | 7 backend+cli | 8 frontend | 9 engines | 10 tests | 11 config/bindings/contract tests |
12 docs/config yaml/indicators/observability/infra/CI | 13 analysis+optimization | 14 API+services+frontend pages |
15 schemas, execution model, corporate actions, storage, registry gates, proto, isolation, background worker.

Regeneration: `python scripts/bootstrap.py --all --root . --force` (README kabhi overwrite nahi hota).
''')
O("docs/RUNBOOK.md", r'''
# RUNBOOK

1. `python scripts/bootstrap.py --all --root .` (naye repo me); update ke liye `--force` (README kabhi overwrite nahi hota)
2. `python -m pytest -q`
3. `python scripts/bootstrap.py --verify --root .`

Demo: `python -m cli.main demo` -> `runs/<run_id>/report.html|json`, `trades.csv`, `run.json`
Optimize: `python -m cli.main optimize --strategy three_pm_momentum --data data/samples/sample_5m.csv --grid '{"stop_pct":[0.3,0.5],"target_pct":[0.8,1.0]}'`
Sample data: `python -m cli.main make-sample`

API: `pip install fastapi uvicorn` -> `uvicorn --factory backend.app:create_app`
Env: API_KEY (set ho to X-API-Key zaroori), RUNS_ROOT, DATA_DIR, DATABASE_URL=sqlite:///path,
BACKGROUND_WORKER=1 (job thread me), RUN_ISOLATED=1 (job alag process me, limits ke saath)

## Abhi asli vs baaki
Asli: data (csv, corporate actions, storage, options checks), registry (compatibility, permissions, lifecycle gates),
backtest (execution model), risk, 8 validation checks, optimization (holdout), metrics, reporting, jobs (inline/background/isolated),
CLI, API (saare blueprint routes, POST /strategies chhodkar), SQLite repo, proto messages, frontend pages.
Baaki: parquet/broker source ka asli connection, PostgreSQL adapter, option backtest (option-chain data + niyam chahiye),
strategy create API, full sandbox (network/filesystem isolation), Go/Rust/C++ ko Python se asli call karna.
Strategy logic: gamma_blast/three_pm_momentum placeholder; bahari strategies (archive/) abhi jodi nahi gayi.
''')

PHASES.append((15, "Baaki stubs me asli code + isolation, background worker, proto, registry gates, options checks", _P15))

# ----------------------------------------------------------------- content
def header(path, purpose, deps, test, c):
    d = ", ".join(deps) or "none"
    return (f"{c} FILE: {path}\n{c} PURPOSE: {purpose}\n{c} DEPENDS_ON: {d}\n{c} TEST: {test}\n")

def test_path(path):
    p = Path(path)
    if p.suffix == ".py" and p.parts[0] not in ("tests", "scripts") and p.name != "__init__.py":
        return f"tests/unit/{'/'.join(p.parts[:-1])}/test_{p.stem}.py"
    return "see tests/"

def render(path, purpose, deps):
    p, ext, t = Path(path), Path(path).suffix, test_path(path)
    h = lambda c: header(path, purpose, deps, t, c)
    if ext == ".py":
        if path.startswith("tests/"):
            return h("#") + "\n\ndef test_placeholder():\n    import pytest\n    pytest.skip('TODO: implement')\n"
        return f'"""{purpose}\n\nDEPENDS_ON: {", ".join(deps) or "none"}\nTEST: {t}\n"""\n\n__all__: list[str] = []\n'
    if ext == ".ts":
        return h("//") + "\nexport {};\n"
    if ext == ".go":
        pkg = "main" if p.name == "main.go" else p.parent.name
        body = "\nfunc main() {}\n" if pkg == "main" else ""
        return h("//") + f"\npackage {pkg}\n{body}"
    if ext in (".cpp", ".hpp"):
        return h("//") + ("\n#pragma once\n" if ext == ".hpp" else "\n")
    if ext == ".rs":
        return h("//") + "\n"
    if ext == ".proto":
        return h("//") + '\nsyntax = "proto3";\npackage svl;\n'
    if ext == ".json":
        return json.dumps({"$schema": "https://json-schema.org/draft/2020-12/schema",
                           "title": p.stem, "description": purpose, "type": "object",
                           "properties": {}, "x-depends-on": deps}, indent=2, ensure_ascii=False) + "\n"
    if ext == ".yaml":
        return h("#") + ("openapi: 3.1.0\ninfo:\n  title: strategy-validation-lab\n  version: 0.1.0\npaths: {}\n"
                         if "openapi" in p.name else "id: TODO\nversion: 0.1.0\nentry_point: TODO\nrequired_data: []\nparameters: {}\nexecution_modes: []\n")
    if ext == ".html":
        return f"<!doctype html>\n<!-- {path}: {purpose} -->\n<html><body><div id=\"app\"></div></body></html>\n"
    if ext == ".sh":
        return "#!/usr/bin/env bash\nset -euo pipefail\n" + h("#") + "# TODO: ruff, mypy, pytest, frontend build, go/cargo/cmake tests\n"
    if ext == ".md":
        return f"# {p.stem}\n\n{purpose}\n"
    if ext == ".toml":
        return h("#") + ("[project]\nname = \"strategy-validation-lab\"\nversion = \"0.1.0\"\n" if p.name == "pyproject.toml" else "")
    if p.name == "go.mod":
        return "module svl/validator\n\ngo 1.22\n"
    if p.name == "package.json":
        return json.dumps({"name": "svl-frontend", "private": True, "version": "0.1.0"}, indent=2) + "\n"
    if p.name == "tsconfig.json":
        return json.dumps({"compilerOptions": {"strict": True, "target": "ES2022"}}, indent=2) + "\n"
    return h("#") + "\n"

# ----------------------------------------------------------------- actions
def all_specs(phases):
    return [(n, p, pu, d) for n, _, files in phases for p, pu, d in files]

def py_packages(paths):
    pk = set()
    for p in paths:
        if p.endswith(".py") and not p.startswith(("tests/", "scripts/")):
            for parent in Path(p).parents:
                if str(parent) != ".":
                    pk.add(str(parent))
    return pk

def generate(root, phases, force, dry):
    written = skipped = 0
    def put(rel, text):
        nonlocal written, skipped
        f = root / rel
        if f.exists() and (not force or rel == "README.md"):  # README kabhi overwrite nahi
            skipped += 1
            return
        print(("[dry] " if dry else "[new] ") + rel)
        if not dry:
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text, encoding="utf-8")
            if rel.endswith(".sh"):
                f.chmod(0o755)
        written += 1
    specs = all_specs(phases)
    for _, path, purpose, deps in specs:
        put(path, OVERRIDES.get(path) or render(path, purpose, deps))
        tp = test_path(path)
        if tp != "see tests/":
            mod = path[:-3].replace("/", ".")
            put(tp, OVERRIDES.get(tp) or (f'"""Import/wiring test for {path}"""\nimport importlib\n\n\n'
                    f'def test_module_imports():\n    importlib.import_module("{mod}")\n'))
    for pk in py_packages([s[1] for s in specs]):
        put(f"{pk}/__init__.py", OVERRIDES.get(f"{pk}/__init__.py", ""))
        if pk.split("/")[0] not in ("tests",):
            put(f"tests/unit/{pk}/__init__.py", "")
    put("tests/__init__.py", ""); put("tests/unit/__init__.py", "")
    print(f"\nDone: {written} files, {skipped} skipped (already exist).")

def write_plan(root, dry):
    specs = all_specs(PHASES)
    graph = {p: set(d) for _, p, _, d in specs}
    for d in list(graph.values()):
        for x in d:
            graph.setdefault(x, set())
    order = list(TopologicalSorter(graph).static_order())
    info = {p: (n, pu) for n, p, pu, _ in specs}
    md = ["# BUILD ORDER (dependency topological order)\n",
          "| # | File | Phase | Pehle chahiye | Test |", "|---|---|---|---|---|"]
    for i, p in enumerate(order, 1):
        md.append(f"| {i} | `{p}` | {info.get(p, ('?',))[0]} | {', '.join(f'`{d}`' for d in sorted(graph[p])) or '-'} | `{test_path(p)}` |")
    wiring = {p: {"phase": n, "purpose": pu, "depends_on": d, "test": test_path(p)} for n, p, pu, d in specs}
    if not dry:
        (root / "docs/architecture").mkdir(parents=True, exist_ok=True)
        (root / "docs/architecture/BUILD_ORDER.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        (root / "docs/architecture/WIRING_MAP.json").write_text(json.dumps(wiring, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Plan files: docs/architecture/BUILD_ORDER.md, WIRING_MAP.json")

def verify(root):
    specs = all_specs(PHASES)
    known = {p for _, p, _, _ in specs}
    missing = [p for p in known if not (root / p).exists()]
    bad_deps = [(p, d) for _, p, _, ds in specs for d in ds if d not in known]
    try:
        list(TopologicalSorter({p: set(d) for _, p, _, d in specs}).static_order())
    except Exception as e:
        print("CYCLE in dependencies:", e); return 1
    print(f"Files expected: {len(known)} | missing: {len(missing)} | unknown deps: {len(bad_deps)}")
    for m in sorted(missing)[:30]: print("  MISSING", m)
    for p, d in bad_deps[:30]: print(f"  UNKNOWN DEP {p} -> {d}")
    return 1 if missing or bad_deps else 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="strategy-validation-lab")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--phase", type=int, action="append")
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    root = Path(a.root)
    if a.plan:
        for n, title, files in PHASES:
            print(f"Phase {n:>2}: {title}  ({len(files)} files)")
        return 0
    if a.verify:
        return verify(root)
    if a.test:
        import subprocess
        return subprocess.call([sys.executable, "-m", "pytest", "-q"], cwd=str(root))
    chosen = PHASES if a.all else [p for p in PHASES if a.phase and p[0] in a.phase]
    if not chosen:
        ap.print_help(); return 1
    generate(root, chosen, a.force, a.dry_run)
    if a.all:
        write_plan(root, a.dry_run)
    return 0

if __name__ == "__main__":
    sys.exit(main())

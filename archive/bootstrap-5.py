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
    paths = {r.path for r in create_app().routes}
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

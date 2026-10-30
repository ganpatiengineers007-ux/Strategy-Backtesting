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

"""Reports/runs read-only. run_id strict (path traversal band)."""
import json
import re
from pathlib import Path

from data.provenance import is_synthetic_path

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


def safe_id(run_id):
    if not isinstance(run_id, str) or not _ID.match(run_id):
        raise ValueError("invalid run_id")
    return run_id


def _run_record(run_id, root):
    f = Path(root) / safe_id(run_id) / "run.json"
    if not f.exists():
        return {}
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _provenance(record):
    if "dataset_synthetic" in record:
        synthetic = bool(record["dataset_synthetic"])
    else:
        synthetic = is_synthetic_path(record.get("dataset_id", ""))
    return {"synthetic": synthetic, "data_label": record.get("data_label") or ("synthetic" if synthetic else "real")}


def get_report(run_id, root="runs"):
    f = Path(root) / safe_id(run_id) / "report.json"
    if not f.exists():
        raise KeyError(run_id)
    report = json.loads(f.read_text(encoding="utf-8"))
    record = _run_record(run_id, root)
    report.setdefault("dataset_id", record.get("dataset_id"))
    for k, v in _provenance(record or report).items():
        report.setdefault(k, v)
    return report


def get_run(run_id, root="runs"):
    f = Path(root) / safe_id(run_id) / "run.json"
    if not f.exists():
        raise KeyError(run_id)
    record = json.loads(f.read_text(encoding="utf-8"))
    for k, v in _provenance(record).items():
        record.setdefault(k, v)
    return record


def list_runs(root="runs"):
    ids = sorted(p.parent.name for p in Path(root).glob("*/run.json")) if Path(root).exists() else []
    out = []
    for run_id in ids:
        record = _run_record(run_id, root)
        prov = _provenance(record)
        out.append({"run_id": record.get("run_id"), "strategy_id": record.get("strategy_id"),
                    "status": record.get("status"), "reason": record.get("reason"),
                    "validation_status": record.get("validation_status"), "dataset_id": record.get("dataset_id"),
                    "synthetic": prov["synthetic"], "data_label": prov["data_label"],
                    "created_at": record.get("created_at")})
    return out

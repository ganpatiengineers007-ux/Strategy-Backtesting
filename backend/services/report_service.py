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

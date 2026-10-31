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

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

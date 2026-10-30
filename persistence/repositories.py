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

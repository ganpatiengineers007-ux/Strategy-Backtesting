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

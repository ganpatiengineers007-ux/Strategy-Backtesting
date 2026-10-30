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

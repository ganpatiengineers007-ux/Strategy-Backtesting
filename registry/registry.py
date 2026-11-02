"""Registry entry point: manifests discover, validate, strategy load.

Production fix: ek kharab manifest se poori registry ab nahi girti. Kharab strategy
self.errors me record hoti hai aur baaki strategies chalti rehti hain.
"""
import importlib
import logging
from pathlib import Path

from registry import compatibility
from registry.metadata import load_manifest
from registry.versioning import source_hash as _hash
from strategies.validation import validate_manifest

log = logging.getLogger("registry")


class Registry:
    def __init__(self, strategies_dir=None):
        self.dir = Path(strategies_dir) if strategies_dir else Path(__file__).resolve().parent.parent / "strategies"
        self.records = {}
        self.errors = {}

    def discover(self):
        self.records.clear()
        self.errors.clear()
        for d in sorted(self.dir.iterdir()):
            mf = d / "manifest.yaml"
            if not (d.is_dir() and mf.exists()):
                continue
            try:
                m = load_manifest(mf)
                errs = validate_manifest(m) + compatibility.check(m)
                if errs:
                    raise ValueError(f"invalid manifest: {errs}")
                sid = m["id"]
                if sid in self.records:
                    raise ValueError(f"duplicate strategy id: {sid}")
                self.records[sid] = {"manifest": m, "dir": d}
            except Exception as e:  # noqa: BLE001 - ek kharab strategy poori registry na roke
                self.errors[d.name] = f"{type(e).__name__}: {e}"
                log.error("strategy %s skip: %s", d.name, self.errors[d.name])
        return sorted(self.records)

    def _rec(self, sid):
        if sid not in self.records:
            self.discover()
        if sid not in self.records:
            hint = f" (manifest error: {self.errors[sid]})" if sid in self.errors else ""
            raise KeyError(f"unknown strategy: {sid}{hint}")
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

"""Registry entry point: manifests discover, validate, strategy load.

Discovery scans every strategy root in the repository (`strategies/`,
`all_strategies/`, `engines/`, `external/`) so a strategy is registered no
matter where its manifest lives. A single bad manifest never takes down the
whole registry: the failure is recorded in `self.errors` and the remaining
strategies keep working.
"""
import importlib
import logging
import os
from pathlib import Path

from registry import compatibility
from registry.metadata import load_manifest
from registry.versioning import source_hash as _hash
from strategies.validation import validate_manifest

log = logging.getLogger("registry")

_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_ROOTS = ("strategies", "all_strategies", "engines", "external")
_SKIP_DIRS = {"__pycache__", ".git", ".venv", "node_modules", ".pytest_cache", "target", "build", "dist"}


class Registry:
    def __init__(self, strategies_dir=None, strategy_dirs=None):
        if strategies_dir is not None:
            dirs = [Path(strategies_dir)]
        elif strategy_dirs is not None:
            dirs = [Path(d) for d in strategy_dirs]
        else:
            env_dirs = [d for d in os.environ.get("SVL_STRATEGY_DIRS", "").split(os.pathsep) if d.strip()]
            dirs = [Path(d) for d in env_dirs] if env_dirs else [_ROOT / name for name in _DEFAULT_ROOTS]
        self.dirs = [d for d in dirs if d.exists()]
        self.dir = self.dirs[0] if self.dirs else _ROOT / "strategies"
        self.records = {}
        self.errors = {}

    def _manifest_dirs(self):
        for root in self.dirs:
            found = []
            for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
                dirnames[:] = sorted(d for d in dirnames if d not in _SKIP_DIRS)
                if "manifest.yaml" in filenames:
                    found.append(Path(dirpath))
            for path in sorted(found):
                yield path

    def discover(self):
        self.records.clear()
        self.errors.clear()
        for d in self._manifest_dirs():
            mf = d / "manifest.yaml"
            try:
                m = load_manifest(mf)
                errs = validate_manifest(m) + compatibility.check(m)
                if errs:
                    raise ValueError(f"invalid manifest: {errs}")
                sid = m["id"]
                if sid in self.records:
                    existing = self.records[sid]["dir"]
                    raise ValueError(f"duplicate strategy id: {sid} (already registered from {existing})")
                self.records[sid] = {"manifest": m, "dir": d}
            except Exception as e:  # noqa: BLE001 - ek kharab strategy poori registry na roke
                key = d.name
                if key in self.errors:
                    key = str(d.relative_to(_ROOT)) if d.is_relative_to(_ROOT) else str(d)
                self.errors[key] = f"{type(e).__name__}: {e}"
                log.error("strategy %s skip: %s", d, self.errors[key])
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

"""Source hash = strategy.py + manifest.yaml ka sha256 (run ke saath save hota hai)."""
import hashlib
from pathlib import Path


def source_hash(strategy_dir):
    h = hashlib.sha256()
    for name in ("manifest.yaml", "strategy.py"):
        f = Path(strategy_dir) / name
        if f.exists():
            h.update(f.read_bytes())
    return h.hexdigest()

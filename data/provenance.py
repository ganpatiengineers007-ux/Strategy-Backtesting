"""Data provenance labels. Sample files are synthetic and must stay labelled."""
from pathlib import Path


def is_synthetic_path(path) -> bool:
    p = Path(str(path))
    name = p.name.lower()
    parts = {part.lower() for part in p.parts}
    return "samples" in parts or name.startswith("sample") or "synthetic" in name


def data_label(path) -> str:
    return "synthetic" if is_synthetic_path(path) else "real"

"""Minimal schema check: required keys + basic types (no external dependency)."""
import json
from pathlib import Path

_T = {"string": str, "number": (int, float), "integer": int, "array": list,
      "object": dict, "boolean": bool, "null": type(None)}


def load(name):
    return json.loads((Path(__file__).parent / name).read_text(encoding="utf-8"))


def check(obj, schema):
    errs = [f"missing: {k}" for k in schema.get("required", []) if k not in obj]
    for k, spec in schema.get("properties", {}).items():
        if k not in obj:
            continue
        types = spec["type"] if isinstance(spec["type"], list) else [spec["type"]]
        v = obj[k]
        ok = any(isinstance(v, _T[t]) and not (t in ("number", "integer") and isinstance(v, bool)) for t in types)
        if not ok:
            errs.append(f"bad type: {k}={v!r} expected {types}")
    return errs

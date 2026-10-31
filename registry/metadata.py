"""Minimal manifest parser (flat `key: value`, [list], {k: v}). Koi yaml dependency nahi."""
from pathlib import Path


def _scalar(s):
    s = s.strip()
    if s in ("true", "True"):
        return True
    if s in ("false", "False"):
        return False
    for cast in (int, float):
        try:
            return cast(s)
        except ValueError:
            # Expected for non-numeric strings
            pass
    return s.strip("'\"")


def _value(s):
    s = s.strip()
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        return [_scalar(x) for x in inner.split(",")] if inner else []
    if s.startswith("{") and s.endswith("}"):
        inner, d = s[1:-1].strip(), {}
        for part in (inner.split(",") if inner else []):
            k, _, v = part.partition(":")
            d[k.strip()] = _scalar(v)
        return d
    return _scalar(s)


def parse_manifest_text(text):
    out = {}
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        k, _, v = line.partition(":")
        out[k.strip()] = _value(v)
    return out


def load_manifest(path):
    return parse_manifest_text(Path(path).read_text(encoding="utf-8"))

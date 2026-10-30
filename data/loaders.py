"""Entry point: source choose -> load -> normalize -> validate -> Dataset (hash + quality)."""
import hashlib
from pathlib import Path

from data.models import Dataset
from data.normalizer import normalize, BASE
from data.quality_report import build_report
from data.sources import csv_source, parquet_source
from data.validators import validate

BASE_FIELDS = {"open", "high", "low", "close", "volume"}


def load_dataset(path, dataset_id=None, symbol="UNKNOWN", timeframe="UNKNOWN", timezone="UTC"):
    p = Path(path)
    ext = p.suffix.lower()
    if ext == ".csv":
        rows = csv_source.read_rows(p)
    elif ext == ".parquet":
        rows = parquet_source.read_rows(p)
    else:
        raise ValueError(f"unsupported source: {ext}")
    content_hash = hashlib.sha256(p.read_bytes()).hexdigest()
    try:
        bars = normalize(rows)
        issues = validate(bars)
    except (KeyError, ValueError) as e:
        bars, issues = [], [{"level": "ERROR", "code": "SCHEMA", "msg": str(e)}]
    fields = set(BASE_FIELDS)
    for b in bars:
        fields.update(b.extras)
    q = build_report(issues)
    return Dataset(dataset_id or p.stem, symbol, timeframe, bars, timezone, ext.lstrip("."), "1.0",
                   content_hash, fields, q["status"], q)

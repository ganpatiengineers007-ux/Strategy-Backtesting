from pathlib import Path

from contracts import schema_check

TS = Path(__file__).resolve().parents[2] / "frontend/src/types"


def _fields(schema_name, ts_file):
    text = (TS / ts_file).read_text(encoding="utf-8")
    return [k for k in schema_check.load(schema_name)["required"] if f"{k}:" not in text]


def test_ts_types_cover_schema_fields():
    assert _fields("trade.schema.json", "backtest.ts") == []
    assert _fields("run.schema.json", "backtest.ts") == []
    assert _fields("report.schema.json", "report.ts") == []
    assert _fields("strategy.schema.json", "strategy.ts") == []

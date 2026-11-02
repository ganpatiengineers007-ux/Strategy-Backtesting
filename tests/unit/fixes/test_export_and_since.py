"""Regression: hub export ISO IST timestamp likhta hai (backtest loader ke saath compatible)."""
from data.timestamps import parse_ts
from fyers_hub import cli


def test_export_writes_iso_ist():
    rows = [(1791776700, 100.0, 101.0, 99.0, 100.0, 10.0)]   # 2026-10-12 09:15 IST
    out = list(cli._export_rows(rows))
    ts = out[0][0]
    assert ts == "2026-10-12T09:15:00", ts
    parse_ts(ts)   # raise nahi hona chahiye
    assert out[0][1:] == (100.0, 101.0, 99.0, 100.0, 10.0)

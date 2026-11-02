"""Regression: windowed derive ab poore bucket nahi bigaadta (safe_since)."""
from datetime import date

from fyers_hub.ingest.live import safe_since
from fyers_hub.process.resample import derive
from fyers_hub.storage import db as dbm
from fyers_hub.timeutil import day_start_epoch


def _minute_rows(d, n=375, base=100.0):
    start = day_start_epoch(d) + 9 * 3600 + 15 * 60
    return [(start + i * 60, base + i, base + i + 1, base + i - 1, base + i, 10.0) for i in range(n)]


def test_windowed_derive_keeps_completed_buckets():
    conn = dbm.connect(":memory:")
    sym = "NSE:SBIN-EQ"
    d1, d2 = date(2026, 10, 12), date(2026, 10, 13)
    dbm.upsert_candles(conn, sym, "1", _minute_rows(d1) + _minute_rows(d2))
    derive(conn, sym, "30")
    q = "SELECT ts,open,high,low,close,volume FROM candles WHERE symbol=? AND tf='30' ORDER BY ts"
    snap = conn.execute(q, (sym,)).fetchall()
    now = day_start_epoch(d2) + 10 * 3600 + 7 * 60   # live loop jaisa mid-day time
    derive(conn, sym, "30", base="1", since_ts=safe_since("30", now))
    assert conn.execute(q, (sym,)).fetchall() == snap


def test_daily_based_tf_uses_full_history():
    conn = dbm.connect(":memory:")
    now = day_start_epoch(date(2026, 10, 13)) + 10 * 3600
    assert safe_since("15D", now) is None
    assert safe_since("D", now) is None

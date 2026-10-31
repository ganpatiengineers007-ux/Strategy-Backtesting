"""Data quality check: kharab OHLC, duplicate, negative volume, 1-minute candles me gaps."""
from __future__ import annotations

import sqlite3
from collections import defaultdict

from fyers_hub.process.resample import parse_tf
from fyers_hub.timeutil import ist_date, session_for


def check_candles(rows, symbol: str, tf: str) -> dict:
    bad_ohlc = neg_vol = dupes = 0
    seen = set()
    per_day: dict = defaultdict(int)
    for ts, o, h, l, c, v in rows:
        if ts in seen:
            dupes += 1
        seen.add(ts)
        if h < max(o, c, l) - 1e-9 or l > min(o, c, h) + 1e-9 or min(o, h, l, c) <= 0:
            bad_ohlc += 1
        if v < 0:
            neg_vol += 1
        per_day[ist_date(ts)] += 1
    rep = {"rows": len(rows), "bad_ohlc": bad_ohlc, "negative_volume": neg_vol, "duplicates": dupes, "short_days": {}}
    kind, n = parse_tf(tf)
    if kind == "m":
        o_min, c_min = session_for(symbol)
        expected = (c_min - o_min) // n
        for d, cnt in per_day.items():
            if cnt < expected * 0.9:
                rep["short_days"][d.isoformat()] = f"{cnt}/{expected}"
    return rep


def check_db(conn: sqlite3.Connection, symbol: str, tf: str) -> dict:
    rows = conn.execute(
        "SELECT ts,open,high,low,close,volume FROM candles WHERE symbol=? AND tf=? ORDER BY ts", (symbol, tf)
    ).fetchall()
    return check_candles(rows, symbol, tf)

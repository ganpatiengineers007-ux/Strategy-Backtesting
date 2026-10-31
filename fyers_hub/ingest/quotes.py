"""Live bhav (latest quote) hub ke quotes table me."""
from __future__ import annotations

import sqlite3

from fyers_hub.storage.db import now_ts


def poll_quotes(api, conn: sqlite3.Connection, symbols: list[str]) -> int:
    rows = api.quotes(symbols)
    ts = now_ts()
    conn.executemany(
        "INSERT OR REPLACE INTO quotes VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        [(q["symbol"], q["ltp"], q["open"], q["high"], q["low"], q["prev_close"], q["volume"],
          q["change_pct"], q["bid"], q["ask"], q["ts_exchange"], ts) for q in rows if q.get("symbol")],
    )
    conn.commit()
    return len(rows)

"""Purani candles khinchna (chunk me, resume ke saath) aur hub me save karna."""
from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from typing import Callable, Iterable

from fyers_hub.process.resample import derive, parse_tf
from fyers_hub.storage.db import now_ts, upsert_candles


def chunk_days(tf: str) -> int:
    """Fyers ek call me kitne din ka data deta hai (conservative)."""
    kind, n = parse_tf(tf)
    if kind == "s":
        return 25
    if kind == "d":
        return 360
    return 100 if n <= 30 else 390


def plan_chunks(start: date, end: date, tf: str) -> list[tuple[date, date]]:
    step = chunk_days(tf)
    out, cur = [], start
    while cur <= end:
        stop = min(cur + timedelta(days=step - 1), end)
        out.append((cur, stop))
        cur = stop + timedelta(days=1)
    return out


def _done(conn, symbol, tf, a, b) -> bool:
    return conn.execute(
        "SELECT 1 FROM fetch_log WHERE symbol=? AND tf=? AND range_from=? AND range_to=? AND status='ok'",
        (symbol, tf, a.isoformat(), b.isoformat()),
    ).fetchone() is not None


def backfill(api, conn: sqlite3.Connection, symbols: Iterable[str], tfs: Iterable[str], start: date, end: date,
             derive_tfs: Iterable[str] = (), progress: Callable[[str], None] = print, today: date | None = None) -> dict:
    """Har symbol x tf ke liye chunk-wise khinch kar save. Poore ho chuke purane chunk dobara nahi khinchte."""
    today = today or date.today()
    summary: dict = {}
    for sym in symbols:
        summary[sym] = {}
        for tf in tfs:
            total = 0
            for a, b in plan_chunks(start, end, tf):
                if b < today and _done(conn, sym, tf, a, b):
                    continue
                try:
                    rows = api.history(sym, tf, a, b)
                except Exception as e:  # noqa: BLE001 - ek symbol fail hone se baaki na ruke
                    progress(f"  ! {sym} {tf} {a}..{b}: {e}")
                    conn.execute("INSERT OR REPLACE INTO fetch_log VALUES (?,?,?,?,?,?,?)",
                                 (sym, tf, a.isoformat(), b.isoformat(), "error", 0, now_ts()))
                    conn.commit()
                    continue
                total += upsert_candles(conn, sym, tf, rows)
                conn.execute("INSERT OR REPLACE INTO fetch_log VALUES (?,?,?,?,?,?,?)",
                             (sym, tf, a.isoformat(), b.isoformat(), "ok", len(rows), now_ts()))
                conn.commit()
            summary[sym][tf] = total
            progress(f"{sym} {tf}: +{total} candles")
        for t in derive_tfs:
            n = derive(conn, sym, t)
            summary[sym][t] = n
            if n:
                progress(f"{sym} {t}: {n} candles (derived)")
    return summary

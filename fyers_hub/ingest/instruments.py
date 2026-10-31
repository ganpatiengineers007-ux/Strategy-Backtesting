"""Fyers symbol master (public CSV) -> instruments table. Lot size, expiry, universe ke liye."""
from __future__ import annotations

import csv
import io
import sqlite3
import urllib.request

from fyers_hub.storage.db import now_ts

MASTER_URL = "https://public.fyers.in/sym_details/{name}.csv"
SEGMENTS = ("NSE_CM", "NSE_FO", "NSE_CD", "BSE_CM", "BSE_FO", "MCX_COM")

# CSV ka column layout (Fyers docs ke hisaab se). `symbols --inspect` se apne data se match karke dekh lena.
C_NAME, C_TYPE, C_LOT, C_TICK, C_ISIN, C_EXPIRY, C_TICKER = 1, 2, 3, 4, 5, 8, 9


def download(segment: str, timeout: int = 60) -> str:
    with urllib.request.urlopen(MASTER_URL.format(name=segment), timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _i(x):
    v = _f(x)
    return int(v) if v is not None else None


def parse_master(text: str, segment: str):
    for row in csv.reader(io.StringIO(text)):
        if len(row) <= C_TICKER or ":" not in row[C_TICKER]:
            continue
        ticker = row[C_TICKER].strip()
        exch = ticker.split(":", 1)[0]
        name = row[C_NAME].strip()
        underlying = name.split()[0] if name else None
        opt = ticker[-2:] if ticker.endswith(("CE", "PE")) and segment.endswith(("FO", "COM", "CD")) else None
        strike = None
        if opt and underlying and ticker.startswith(f"{exch}:{underlying}"):
            tail = ticker[len(exch) + 1 + len(underlying) + 5:-2]  # 5 char = expiry code (YYMDD / YYMMM)
            strike = _f(tail)
        yield {
            "symbol": ticker, "name": name, "segment": segment, "exchange": exch, "inst_type": row[C_TYPE],
            "lot_size": _i(row[C_LOT]), "tick_size": _f(row[C_TICK]), "expiry_epoch": _i(row[C_EXPIRY]) or None,
            "underlying": underlying, "strike": strike, "option_type": opt, "isin": row[C_ISIN] or None,
        }


def load_into_db(conn: sqlite3.Connection, segment: str, text: str) -> int:
    ts = now_ts()
    rows = [(r["symbol"], r["name"], r["segment"], r["exchange"], r["inst_type"], r["lot_size"], r["tick_size"],
             r["expiry_epoch"], r["underlying"], r["strike"], r["option_type"], r["isin"], ts)
            for r in parse_master(text, segment)]
    conn.executemany("INSERT OR REPLACE INTO instruments VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    conn.commit()
    return len(rows)

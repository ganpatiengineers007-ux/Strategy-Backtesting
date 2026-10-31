"""SQLite data hub. Ek file (~/.fyers_hub/hub.db), WAL mode - reader aur writer saath chal sakte hain."""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);

CREATE TABLE IF NOT EXISTS instruments (
  symbol TEXT PRIMARY KEY, name TEXT, segment TEXT, exchange TEXT, inst_type TEXT,
  lot_size INTEGER, tick_size REAL, expiry_epoch INTEGER, underlying TEXT,
  strike REAL, option_type TEXT, isin TEXT, updated_at INTEGER
);
CREATE INDEX IF NOT EXISTS ix_instr_under ON instruments(underlying, expiry_epoch);

-- tf: '5S','1','2','5','15','60','D','15D' ... ; ts = candle start, UTC epoch seconds
CREATE TABLE IF NOT EXISTS candles (
  symbol TEXT NOT NULL, tf TEXT NOT NULL, ts INTEGER NOT NULL,
  open REAL, high REAL, low REAL, close REAL, volume REAL, derived INTEGER DEFAULT 0,
  PRIMARY KEY (symbol, tf, ts)
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS quotes (
  symbol TEXT PRIMARY KEY, ltp REAL, open REAL, high REAL, low REAL, prev_close REAL,
  volume REAL, change_pct REAL, bid REAL, ask REAL, ts_exchange INTEGER, fetched_at INTEGER
);

CREATE TABLE IF NOT EXISTS option_chain (
  underlying TEXT NOT NULL, expiry INTEGER NOT NULL, strike REAL NOT NULL, opt_type TEXT NOT NULL,
  ts INTEGER NOT NULL, symbol TEXT, spot REAL, ltp REAL, bid REAL, ask REAL,
  oi REAL, oi_change REAL, volume REAL,
  iv REAL, delta REAL, gamma REAL, theta REAL, vega REAL, rho REAL,
  PRIMARY KEY (underlying, expiry, strike, opt_type, ts)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS ix_chain_ts ON option_chain(underlying, ts);

CREATE TABLE IF NOT EXISTS fetch_log (
  symbol TEXT NOT NULL, tf TEXT NOT NULL, range_from TEXT NOT NULL, range_to TEXT NOT NULL,
  status TEXT, rows INTEGER, fetched_at INTEGER,
  PRIMARY KEY (symbol, tf, range_from, range_to)
);
"""


def connect(path: str | Path, check_same_thread: bool = True) -> sqlite3.Connection:
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=30, check_same_thread=check_same_thread)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.executescript(SCHEMA)
    conn.execute("INSERT OR IGNORE INTO meta(key,value) VALUES('schema_version','1')")
    conn.commit()
    return conn


def upsert_candles(conn: sqlite3.Connection, symbol: str, tf: str, rows, derived: bool = False) -> int:
    data = [(symbol, tf, int(r[0]), r[1], r[2], r[3], r[4], r[5], 1 if derived else 0) for r in rows]
    conn.executemany(
        "INSERT OR REPLACE INTO candles(symbol,tf,ts,open,high,low,close,volume,derived) VALUES (?,?,?,?,?,?,?,?,?)",
        data,
    )
    conn.commit()
    return len(data)


def available_tfs(conn: sqlite3.Connection, symbol: str) -> dict[str, int]:
    cur = conn.execute("SELECT tf, COUNT(*) FROM candles WHERE symbol=? GROUP BY tf", (symbol,))
    return {tf: n for tf, n in cur.fetchall()}


def now_ts() -> int:
    return int(time.time())

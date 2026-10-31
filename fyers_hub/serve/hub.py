"""Strategies ke liye ek hi darwaza: DataHub. Strategy seedha Fyers ya SQLite ko nahi chhuti.

    from fyers_hub.serve.hub import DataHub
    hub = DataHub()
    bars = hub.candles("NSE:NIFTY50-INDEX", "5", start="2025-01-01")     # kisi bhi tf me
    for bar in hub.iter_bars("NSE:SBIN-EQ", "15", "2025-01-01"): ...      # event-driven backtest
    chain = hub.option_chain("NSE:NIFTY50-INDEX")                          # greeks ke saath
"""
from __future__ import annotations

import sqlite3
from collections import namedtuple
from datetime import date, datetime
from pathlib import Path
from typing import Iterator

from fyers_hub.process.resample import norm_tf, pick_base, resample
from fyers_hub.settings import get_settings
from fyers_hub.storage import db as dbm
from fyers_hub.timeutil import IST, day_start_epoch, parse_day, session_for

Bar = namedtuple("Bar", "ts open high low close volume")
CHAIN_COLS = ("underlying expiry strike opt_type ts symbol spot ltp bid ask oi oi_change volume "
              "iv delta gamma theta vega rho").split()


def _to_epoch(x, end: bool = False) -> int | None:
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return int(x)
    if isinstance(x, datetime):
        return int((x if x.tzinfo else x.replace(tzinfo=IST)).timestamp())
    d = parse_day(x)
    return day_start_epoch(d) + (86400 if end else 0)


class DataHub:
    def __init__(self, db_path: str | Path | None = None, conn: sqlite3.Connection | None = None):
        self.conn = conn or dbm.connect(db_path or get_settings().db_path)

    # ---------- candles ----------
    def candles(self, symbol: str, tf: str, start=None, end=None, limit: int | None = None,
                as_df: bool = False, auto_derive: bool = True):
        """end = us din ko shamil (date dene par). Stored na ho to base se apne aap bana deta hai."""
        tf = norm_tf(tf)
        a, b = _to_epoch(start), _to_epoch(end, end=True)
        rows = self._fetch(symbol, tf, a, b)
        if not rows and auto_derive:
            base = pick_base(tf, dbm.available_tfs(self.conn, symbol))
            if base:
                raw = self._fetch(symbol, base, None, b)
                rows = [r for r in resample(raw, tf, session_for(symbol)[0]) if a is None or r[0] >= a]
        if limit:
            rows = rows[-limit:]
        bars = [Bar(*r) for r in rows]
        if not as_df:
            return bars
        import pandas as pd  # optional dependency

        df = pd.DataFrame(bars, columns=Bar._fields)
        if not df.empty:
            df.index = pd.to_datetime(df.pop("ts"), unit="s", utc=True).tz_convert(IST)
            df.index.name = "time"
        return df

    def _fetch(self, symbol, tf, a, b):
        q, args = "SELECT ts,open,high,low,close,volume FROM candles WHERE symbol=? AND tf=?", [symbol, tf]
        if a is not None:
            q += " AND ts>=?"
            args.append(a)
        if b is not None:
            q += " AND ts<?"
            args.append(b)
        return self.conn.execute(q + " ORDER BY ts", args).fetchall()

    def iter_bars(self, symbol: str, tf: str, start=None, end=None) -> Iterator[Bar]:
        yield from self.candles(symbol, tf, start, end)

    def multi(self, symbols: list[str], tf: str, start=None, end=None) -> dict[str, list[Bar]]:
        return {s: self.candles(s, tf, start, end) for s in symbols}

    # ---------- quotes ----------
    def latest_quote(self, symbol: str) -> dict | None:
        cur = self.conn.execute("SELECT * FROM quotes WHERE symbol=?", (symbol,))
        row = cur.fetchone()
        return dict(zip([c[0] for c in cur.description], row)) if row else None

    # ---------- options ----------
    def expiries(self, underlying: str) -> list[int]:
        cur = self.conn.execute("SELECT DISTINCT expiry FROM option_chain WHERE underlying=? ORDER BY expiry", (underlying,))
        return [r[0] for r in cur.fetchall()]

    def option_chain(self, underlying: str, expiry=None, ts: int | None = None, as_df: bool = False):
        """Latest (ya diye gaye ts ke pehle ka) snapshot. expiry None = sabse nazdiki."""
        q = "SELECT MAX(ts) FROM option_chain WHERE underlying=?"
        args: list = [underlying]
        if ts is not None:
            q += " AND ts<=?"
            args.append(ts)
        snap = self.conn.execute(q, args).fetchone()[0]
        if snap is None:
            return [] if not as_df else self._df([])
        if expiry is None:  # sabse nazdiki, jo abhi expire nahi hui
            exp = self.conn.execute("SELECT MIN(expiry) FROM option_chain WHERE underlying=? AND ts=? AND expiry>=?",
                                    (underlying, snap, snap)).fetchone()[0]
        elif isinstance(expiry, (int, float)) and expiry >= 10**9:
            exp = int(expiry)
        else:  # date ya 'YYYY-MM-DD' - us din ki expiry
            d = parse_day(expiry)
            r = self.conn.execute("SELECT expiry FROM option_chain WHERE underlying=? AND ts=? "
                                  "AND expiry>=? AND expiry<? LIMIT 1",
                                  (underlying, snap, day_start_epoch(d), day_start_epoch(d) + 86400)).fetchone()
            exp = r[0] if r else None
        if exp is None:
            return [] if not as_df else self._df([])
        cur = self.conn.execute("SELECT " + ",".join(CHAIN_COLS) + " FROM option_chain "
                                "WHERE underlying=? AND expiry=? AND ts=? ORDER BY strike, opt_type", (underlying, exp, snap))
        rows = [dict(zip(CHAIN_COLS, r)) for r in cur.fetchall()]
        return self._df(rows) if as_df else rows

    @staticmethod
    def _df(rows):
        import pandas as pd

        return pd.DataFrame(rows, columns=CHAIN_COLS)

    def atm(self, underlying: str, expiry=None, ts: int | None = None) -> dict | None:
        rows = self.option_chain(underlying, expiry, ts)
        if not rows or not rows[0]["spot"]:
            return None
        spot = rows[0]["spot"]
        strike = min({r["strike"] for r in rows}, key=lambda k: abs(k - spot))
        return {"spot": spot, "strike": strike,
                "CE": next((r for r in rows if r["strike"] == strike and r["opt_type"] == "CE"), None),
                "PE": next((r for r in rows if r["strike"] == strike and r["opt_type"] == "PE"), None)}

    # ---------- universe / coverage ----------
    def universe(self, kind: str = "equity", exchange: str | None = None, limit: int | None = None) -> list[str]:
        cond = {"equity": "symbol LIKE '%-EQ'", "index": "symbol LIKE '%-INDEX'",
                "future": "symbol LIKE '%FUT'", "option": "option_type IN ('CE','PE')"}[kind]
        q, args = f"SELECT symbol FROM instruments WHERE {cond}", []
        if exchange:
            q += " AND exchange=?"
            args.append(exchange)
        q += " ORDER BY symbol" + (f" LIMIT {int(limit)}" if limit else "")
        return [r[0] for r in self.conn.execute(q, args)]

    def coverage(self) -> list[tuple]:
        """(symbol, tf, rows, first_ts, last_ts)"""
        return self.conn.execute(
            "SELECT symbol, tf, COUNT(*), MIN(ts), MAX(ts) FROM candles GROUP BY symbol, tf ORDER BY symbol, tf"
        ).fetchall()

"""Kisi bhi timeframe ki candle banana: 2m/5m/15m..., 5S/10S..., 1D, 15D (N weekdays).

Intraday bucket session-open se anchor hote hain (NSE 09:15, MCX 09:00) - isliye 5m ki pehli candle 09:15 se banti hai.
'ND' (jaise 15D) = N weekdays (Mon-Fri) ke block, ek fixed anchor tareekh se gine jate hain - holiday se block nahi khisakte,
aur purana data baad me jodne par bhi bucket wahi rehte hain."""
from __future__ import annotations

import sqlite3
from datetime import date

from fyers_hub.storage.db import available_tfs, upsert_candles
from fyers_hub.timeutil import day_start_epoch, ist_date, session_for

ANCHOR = date(2015, 1, 5)  # Monday


def parse_tf(tf: str) -> tuple[str, int]:
    t = str(tf).strip().upper()
    if t == "D":
        return "d", 1
    if t.endswith("S") and t[:-1].isdigit():
        return "s", int(t[:-1])
    if t.endswith("D") and t[:-1].isdigit():
        return "d", int(t[:-1])
    if t.isdigit() and int(t) > 0:
        return "m", int(t)
    raise ValueError(f"timeframe samajh nahi aaya: {tf!r}")


def norm_tf(tf: str) -> str:
    kind, n = parse_tf(tf)
    return "D" if kind == "d" and n == 1 else (f"{n}S" if kind == "s" else (f"{n}D" if kind == "d" else str(n)))


def tf_seconds(tf: str) -> int | None:
    kind, n = parse_tf(tf)
    return n if kind == "s" else (n * 60 if kind == "m" else None)


def weekday_index(d: date) -> int:
    weeks, rem = divmod((d - ANCHOR).days, 7)
    return weeks * 5 + min(rem, 5)


def bucket_start(ts: int, tf: str, open_min: int) -> int:
    kind, n = parse_tf(tf)
    step = n if kind == "s" else n * 60
    base = day_start_epoch(ist_date(ts)) + open_min * 60
    return base + ((ts - base) // step) * step


def resample(rows, tf: str, open_min: int = 555) -> list[tuple]:
    """rows: (ts,o,h,l,c,v) ts ke hisaab se sorted. Return same shape."""
    kind, n = parse_tf(tf)
    out: list[list] = []
    cur_key = None
    for ts, o, h, l, c, v in rows:
        if kind == "d":
            key = weekday_index(ist_date(ts)) // n
            start = ts
        else:
            key = start = bucket_start(ts, tf, open_min)
        if key != cur_key:
            out.append([start, o, h, l, c, v])
            cur_key = key
        else:
            b = out[-1]
            b[2] = max(b[2], h)
            b[3] = min(b[3], l)
            b[4] = c
            b[5] += v
    return [tuple(b) for b in out]


def pick_base(target: str, available) -> str | None:
    """Target banane ke liye sabse bada chhota-divisor timeframe jo maujood ho."""
    tk, tn = parse_tf(target)
    best, best_key = None, -1
    for a in available:
        try:
            ak, an = parse_tf(a)
        except ValueError:
            continue
        if norm_tf(a) == norm_tf(target):
            continue
        if tk == "d":
            ok = ak == "d" and tn % an == 0 and an < tn
            key = an
        else:
            ts_t, ts_a = tf_seconds(target), tf_seconds(a)
            ok = ak in ("s", "m") and ts_a is not None and ts_a < ts_t and ts_t % ts_a == 0
            key = ts_a if ok else -1
        if ok and key > best_key:
            best, best_key = a, key
    return best


def derive(conn: sqlite3.Connection, symbol: str, target: str, base: str | None = None,
           since_ts: int | None = None) -> int:
    """Hub me padi base candles se target tf bana kar hub me hi save karta hai."""
    target = norm_tf(target)
    base = base or pick_base(target, available_tfs(conn, symbol))
    if not base:
        return 0
    q = "SELECT ts,open,high,low,close,volume FROM candles WHERE symbol=? AND tf=?"
    args: list = [symbol, base]
    if since_ts is not None:
        q += " AND ts>=?"
        args.append(since_ts)
    rows = conn.execute(q + " ORDER BY ts", args).fetchall()
    if not rows:
        return 0
    open_min, _ = session_for(symbol)
    return upsert_candles(conn, symbol, target, resample(rows, target, open_min), derived=True)

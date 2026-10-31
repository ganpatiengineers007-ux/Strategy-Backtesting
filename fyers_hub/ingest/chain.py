"""Option chain snapshot + greeks (IV, delta, gamma, theta, vega, rho) hub me."""
from __future__ import annotations

import sqlite3

from fyers_hub.process.greeks import greeks, implied_vol
from fyers_hub.storage.db import now_ts
from fyers_hub.timeutil import expiry_close_epoch


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _rows_from_chain(underlying: str, data: dict, expiry_epoch: int, ts: int, rate: float, div: float = 0.0):
    items = data.get("optionsChain") or []
    spot = None
    for it in items:  # underlying wali entry: option_type khali ya strike <= 0
        if not it.get("option_type") or (_num(it.get("strike_price")) or 0) <= 0:
            spot = _num(it.get("ltp"))
            break
    exp_close = expiry_close_epoch(expiry_epoch, underlying)
    T = max(exp_close - ts, 0) / (365.0 * 24 * 3600)
    out = []
    for it in items:
        ot = (it.get("option_type") or "").upper()
        k = _num(it.get("strike_price"))
        if ot not in ("CE", "PE") or not k or k <= 0:
            continue
        ltp, bid, ask = _num(it.get("ltp")), _num(it.get("bid")), _num(it.get("ask"))
        px = (bid + ask) / 2 if bid and ask and bid > 0 and ask > 0 else ltp
        iv = d = g = th = vg = rh = None
        if spot and px and T > 0:
            iv = implied_vol(px, spot, k, T, rate, div, ot == "CE")
            if iv:
                gr = greeks(spot, k, T, rate, div, iv, ot == "CE")
                d, g, th, vg, rh = gr["delta"], gr["gamma"], gr["theta"], gr["vega"], gr["rho"]
        out.append((underlying, exp_close, k, ot, ts, it.get("symbol"), spot, ltp, bid, ask,
                    _num(it.get("oi")), _num(it.get("oich")), _num(it.get("volume")), iv, d, g, th, vg, rh))
    return out


def snapshot_chain(api, conn: sqlite3.Connection, underlying: str, strikecount: int = 10, n_expiries: int = 2,
                   rate: float = 0.07, div: float = 0.0, ts: int | None = None) -> int:
    """Nazdiki n_expiries ki chain khinch kar greeks ke saath save. Return: rows."""
    ts = ts or now_ts()
    first = api.option_chain(underlying, strikecount)
    expiries = [int(e["expiry"]) for e in (first.get("expiryData") or []) if e.get("expiry")]
    total = 0
    for i in range(max(1, n_expiries)):
        if i == 0:
            data, exp = first, (expiries[0] if expiries else 0)
        elif i < len(expiries):
            data, exp = api.option_chain(underlying, strikecount, expiries[i]), expiries[i]
        else:
            break
        if not exp:
            continue
        rows = _rows_from_chain(underlying, data, exp, ts, rate, div)
        conn.executemany("INSERT OR REPLACE INTO option_chain VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
        conn.commit()
        total += len(rows)
    return total


def prune_chain(conn: sqlite3.Connection, keep_days: int = 30) -> int:
    cur = conn.execute("DELETE FROM option_chain WHERE ts < ?", (now_ts() - keep_days * 86400,))
    conn.commit()
    return cur.rowcount

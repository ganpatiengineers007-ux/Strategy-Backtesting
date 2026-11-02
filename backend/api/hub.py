"""/hub/*: Fyers data hub ka stored + live data (sirf padhna). Frontend ka Live page yahin se bharta hai."""
import time

from backend.api.common import guarded, make_router


def _hub():
    from fyers_hub.serve.hub import DataHub

    return DataHub()


def _clamp(n, lo, hi):
    return max(lo, min(hi, int(n)))


def status():
    h = _hub()
    try:
        n, last = h.conn.execute("SELECT COUNT(*), MAX(fetched_at) FROM quotes").fetchone()
        series = h.conn.execute("SELECT COUNT(*) FROM (SELECT 1 FROM candles GROUP BY symbol, tf)").fetchone()[0]
        instruments = h.conn.execute("SELECT COUNT(*) FROM instruments").fetchone()[0]
        age = None if last is None else max(0, int(time.time()) - int(last))
        return {"quotes": n, "last_quote_age_s": age, "candle_series": series, "instruments": instruments}
    finally:
        h.conn.close()


def quotes(limit: int = 50):
    h = _hub()
    try:
        cur = h.conn.execute("SELECT * FROM quotes ORDER BY fetched_at DESC LIMIT ?", (_clamp(limit, 1, 500),))
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]
    finally:
        h.conn.close()


def coverage():
    h = _hub()
    try:
        return [{"symbol": s, "tf": tf, "rows": n, "first_ts": a, "last_ts": b} for s, tf, n, a, b in h.coverage()]
    finally:
        h.conn.close()


def candles(symbol: str, tf: str = "1", limit: int = 200):
    h = _hub()
    try:
        return [list(b) for b in h.candles(symbol, tf, limit=_clamp(limit, 1, 2000))]
    finally:
        h.conn.close()


def chain(underlying: str):
    h = _hub()
    try:
        rows = h.option_chain(underlying)
        return {"underlying": underlying, "spot": rows[0]["spot"] if rows else None, "rows": rows}
    finally:
        h.conn.close()


router = make_router()
if router is not None:
    router.get("/hub/status")(guarded(status))
    router.get("/hub/quotes")(guarded(quotes))
    router.get("/hub/coverage")(guarded(coverage))
    router.get("/hub/candles")(guarded(candles))
    router.get("/hub/chain")(guarded(chain))

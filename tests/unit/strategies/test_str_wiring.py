"""STR08/STR10 asli logic engine se jude hain; baaki candle-adhoori strategies BLOCKED dikhti hain."""
import datetime as dt
import math
import random

from backtest.engine import run_backtest
from data.models import Bar, Dataset
from registry.registry import Registry
from strategies._positions import to_quantlab_bars


def _bars(days=8, seed=3):
    random.seed(seed)
    bars, p = [], 100.0
    for day in range(days):
        base = dt.datetime(2026, 10, 12 + day, 9, 15)
        for m in range(375):
            t = base + dt.timedelta(minutes=m)
            p *= 1 + random.gauss(0, 0.0012) + 0.0004 * math.sin(m / 9)
            hi, lo = p * (1 + abs(random.gauss(0, 0.0015))), p * (1 - abs(random.gauss(0, 0.0015)))
            vol = 1000 + random.randint(0, 800) + (4000 if random.random() < 0.03 else 0)
            bars.append(Bar(t.strftime("%Y-%m-%dT%H:%M:%S"), p, hi, lo, p * (1 + random.gauss(0, 0.0004)), vol))
    return bars


def _ds(bars):
    return Dataset("t", "NIFTY", "1m", bars, quality_status="OK")


def test_fvg_causal_no_lookahead():
    """Prefix par nikali positions poore data ki positions se mel khaani chahiye."""
    inner = Registry().load("fvg")._inner
    bars = _bars()
    full = inner.positions(to_quantlab_bars(bars))
    for k in (700, 1500, 2300):
        part = inner.positions(to_quantlab_bars(bars[:k]))
        assert list(part[:k]) == list(full[:k])


def test_str08_and_str10_run_and_trade():
    reg = Registry()
    res = run_backtest(_ds(_bars()), reg.load("fvg"))
    assert res.status == "COMPLETED" and len(res.trades) > 0
    r10 = run_backtest(_ds(_bars()), reg.load("session_ignition"))
    assert r10.status == "COMPLETED"  # trades data par nirbhar: hone zaroori nahi, par crash nahi


def test_book_strategies_blocked_not_silent():
    reg = Registry()
    for sid in ("obi_delta", "microstructure", "spoof_ml", "iceberg", "volume_profile", "reversal_ai", "stat_arb", "latency_arb"):
        res = run_backtest(_ds(_bars(2)), reg.load(sid))
        assert res.status == "BLOCKED" and res.reason.startswith("MISSING_DATA"), sid

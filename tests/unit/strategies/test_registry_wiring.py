"""Registry must expose every strategy, including the ones from external/all_strategies."""
import datetime as dt
import math
import random

from backtest.engine import run_backtest
from data.models import Bar, Dataset
from registry.registry import Registry

EXPECTED = {
    "obi_delta", "stat_arb", "latency_arb", "microstructure", "spoof_ml",
    "volume_profile", "reversal_ai", "fvg", "iceberg", "session_ignition",
    "mean_reversion", "gamma_blast", "three_pm_momentum", "sweep",
    "liquidity_sweep", "gamma_vwap", "delta_vwap", "vega_iv",
    "theta_straddle", "greeks_confluence",
}

BLOCKED = {
    "obi_delta", "stat_arb", "latency_arb", "microstructure", "spoof_ml",
    "volume_profile", "reversal_ai", "iceberg", "theta_straddle",
}


def _bars(days=8, seed=3):
    random.seed(seed)
    bars, price = [], 100.0
    for day in range(days):
        base = dt.datetime(2026, 10, 12 + day, 9, 15)
        for minute in range(375):
            t = base + dt.timedelta(minutes=minute)
            price *= 1 + random.gauss(0, 0.0012) + 0.0004 * math.sin(minute / 9)
            high = price * (1 + abs(random.gauss(0, 0.0015)))
            low = price * (1 - abs(random.gauss(0, 0.0015)))
            bars.append(Bar(t.strftime("%Y-%m-%dT%H:%M:%S"), price, high, low,
                            price * (1 + random.gauss(0, 0.0004)), 1000 + random.randint(0, 800)))
    return bars


def _ds(bars):
    return Dataset("t", "NIFTY", "1m", bars, quality_status="OK")


def test_every_strategy_is_registered():
    reg = Registry()
    assert set(reg.discover()) == EXPECTED
    assert reg.errors == {}


def test_unrunnable_strategies_are_blocked_with_reason():
    reg = Registry()
    ds = _ds(_bars(2))
    for sid in BLOCKED:
        res = run_backtest(ds, reg.load(sid))
        assert res.status == "BLOCKED", sid
        assert res.reason and res.reason.startswith(("MISSING_DATA", "UNSUPPORTED")), sid
        assert reg.manifest(sid).get("blocked_reason"), sid


def test_mean_reversion_and_liquidity_sweep_run():
    reg = Registry()
    ds = _ds(_bars())
    for sid in ("mean_reversion", "liquidity_sweep"):
        res = run_backtest(ds, reg.load(sid))
        assert res.status == "COMPLETED", (sid, res.reason)

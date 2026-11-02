"""Regression: live sweep trader - order reject par position ki state galat na ho."""
import os
import sys
import types

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))


def _load_sweep():
    try:
        import dhanhq  # noqa: F401
    except ImportError:
        stub = types.ModuleType("dhanhq")

        class DhanContext:
            def __init__(self, *a, **k):
                pass

        class dhanhq_client:
            def __init__(self, ctx):
                pass

        class MarketFeed:
            NSE_FNO = "NSE_FNO"
            Quote = "Quote"

            def __init__(self, *a, **k):
                pass

        stub.DhanContext = DhanContext
        stub.dhanhq = dhanhq_client
        stub.MarketFeed = MarketFeed
        sys.modules["dhanhq"] = stub
    scripts = os.path.join(_REPO, "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    import sweep_strategy
    return sweep_strategy


class _FakeApi:
    def __init__(self, ok=True):
        self.ok = ok

    def place_order(self, **kw):
        if not self.ok:
            raise RuntimeError("RMS: margin kam hai")
        return {"orderId": "T1"}

    def historical_daily_data(self, **kw):
        raise RuntimeError("test: no history")


def _strategy(sw, api):
    sw.DRY_RUN = False
    sw.journal_trade = lambda *a, **k: None
    s = sw.SweepStrategy(api, depth=None)
    s.atr = 10.0
    return s


def test_rejected_entry_is_not_recorded():
    sw = _load_sweep()
    old = sw.DRY_RUN
    try:
        s = _strategy(sw, _FakeApi(ok=False))
        s._enter("LONG", 22000.0, 21980.0, "R22000")
        assert s.position is None
        assert s.trades_today == 0
    finally:
        sw.DRY_RUN = old


def test_accepted_entry_is_recorded():
    sw = _load_sweep()
    old = sw.DRY_RUN
    try:
        s = _strategy(sw, _FakeApi(ok=True))
        s._enter("LONG", 22000.0, 21980.0, "R22000")
        assert s.position is not None
        assert s.trades_today == 1
    finally:
        sw.DRY_RUN = old


def test_rejected_exit_keeps_position_and_sets_cooldown():
    sw = _load_sweep()
    old = sw.DRY_RUN
    try:
        api = _FakeApi(ok=True)
        s = _strategy(sw, api)
        s._enter("LONG", 22000.0, 21980.0, "R22000")
        assert s.position is not None
        api.ok = False
        s._exit(21975.0, "stop-loss")
        assert s.position is not None          # exit reject: position khuli hi rahni chahiye
        assert s.realized_pnl == 0.0           # galat PnL record nahi
        assert s._retry_after > 0
    finally:
        sw.DRY_RUN = old


def test_successful_exit_clears_position():
    sw = _load_sweep()
    old = sw.DRY_RUN
    try:
        s = _strategy(sw, _FakeApi(ok=True))
        s._enter("LONG", 22000.0, 21980.0, "R22000")
        s._exit(21975.0, "stop-loss")
        assert s.position is None
    finally:
        sw.DRY_RUN = old

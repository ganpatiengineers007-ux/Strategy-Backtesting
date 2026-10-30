from backtest.engine import run_backtest
from tests._helpers import BuyAtIndex, make_bars, make_dataset

NO_COST = {"slippage_bps": 0.0, "fee_pct": 0.0}


def test_entry_is_next_bar_open_not_signal_close():
    bars = make_bars(20)
    res = run_backtest(make_dataset(bars), BuyAtIndex({"at": 1}), NO_COST)
    t = res.trades[0]
    assert t["entry_ts"] == bars[2].ts
    assert t["entry_price"] == bars[2].open and t["entry_price"] != bars[1].close


def test_missing_required_data_is_blocked():
    class Needs(BuyAtIndex):
        required_data = ("option_chain",)
    res = run_backtest(make_dataset(make_bars(10)), Needs(), NO_COST)
    assert res.status == "BLOCKED" and res.reason == "MISSING_DATA:option_chain"


def test_bad_quality_is_blocked():
    ds = make_dataset(make_bars(10))
    ds.quality_status = "BLOCKED"
    assert run_backtest(ds, BuyAtIndex(), NO_COST).status == "BLOCKED"

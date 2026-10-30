from backtest.engine import run_backtest
from data.models import Bar
from tests._helpers import BuyAtIndex, make_bars, make_dataset

NO_COST = {"slippage_bps": 0.0, "fee_pct": 0.0}


def test_changing_future_does_not_change_past_equity():
    bars = make_bars(60)
    tampered = bars[:31] + [Bar(b.ts, b.open * 3, b.high * 3, b.low * 3, b.close * 3, b.volume) for b in bars[31:]]
    a = run_backtest(make_dataset(bars), BuyAtIndex({"at": 1}), NO_COST)
    b = run_backtest(make_dataset(tampered), BuyAtIndex({"at": 1}), NO_COST)
    assert a.equity[:31] == b.equity[:31]
    assert a.trades[0]["entry_ts"] == b.trades[0]["entry_ts"]

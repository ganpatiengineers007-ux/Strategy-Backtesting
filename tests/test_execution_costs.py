from backtest.engine import run_backtest
from tests._helpers import BuyAtIndex, make_bars, make_dataset


def test_costs_reduce_pnl():
    ds = make_dataset(make_bars(30))
    free = run_backtest(ds, BuyAtIndex({"at": 1}), {"slippage_bps": 0.0, "fee_pct": 0.0})
    costly = run_backtest(ds, BuyAtIndex({"at": 1}), {"slippage_bps": 20.0, "fee_pct": 0.002})
    assert costly.trades[0]["pnl"] < free.trades[0]["pnl"] and costly.trades[0]["fees"] > 0

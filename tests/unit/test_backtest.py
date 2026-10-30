from backtest.engine import run_backtest
from tests._helpers import BuyAtIndex, make_bars, make_dataset


def test_runs_and_closes_position():
    res = run_backtest(make_dataset(make_bars(30)), BuyAtIndex({"at": 2}))
    assert res.status == "COMPLETED" and len(res.trades) == 1

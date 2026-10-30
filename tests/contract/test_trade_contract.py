from backtest.engine import run_backtest
from contracts import schema_check
from tests._helpers import BuyAtIndex, make_bars, make_dataset


def test_trades_match_contract():
    res = run_backtest(make_dataset(make_bars(20)), BuyAtIndex({"at": 1}))
    assert res.trades
    for t in res.trades:
        assert not schema_check.check(t, schema_check.load("trade.schema.json"))

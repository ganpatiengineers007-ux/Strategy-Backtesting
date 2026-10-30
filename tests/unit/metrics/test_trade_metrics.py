from metrics import trade_metrics


def test_trade_metrics():
    m = trade_metrics.compute([{"pnl": 10, "fees": 1}, {"pnl": -5, "fees": 1}, {"pnl": 5, "fees": 1}])
    assert m["n_trades"] == 3 and m["profit_factor"] == 3.0 and m["fees_total"] == 3

from backtest.engine import run_backtest
from metrics import compute_all
from tests._helpers import BuyAtIndex, make_bars, make_dataset


def test_compute_all_keys():
    ds = make_dataset(make_bars(30))
    m = compute_all(run_backtest(ds, BuyAtIndex({"at": 2})), ds)
    assert {"total_return_pct", "max_drawdown_pct", "n_trades", "win_rate_pct", "expectancy"} <= set(m)

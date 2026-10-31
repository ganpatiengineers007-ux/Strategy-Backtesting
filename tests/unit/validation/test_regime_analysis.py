from backtest.engine import run_backtest
from tests._helpers import BuyEvery, make_dataset, make_days
from validation import regime_analysis as ra


def test_decide():
    pos, neg = [{"pnl": 5}] * 3, [{"pnl": -5}] * 3
    assert ra.decide({"high_vol": pos, "low_vol": pos})[0] == "PASS"
    assert ra.decide({"high_vol": pos, "low_vol": neg})[0] == "FAIL"
    assert ra.decide({"high_vol": pos[:1], "low_vol": pos[:1]})[0] == "UNAVAILABLE"


def test_run_splits_trades_into_two_regimes():
    ds = make_dataset(make_days(30, 20))
    res = run_backtest(ds, BuyEvery({"n": 6}))
    out = ra.run(ds, res)
    assert set(out["regimes"]) == {"high_vol", "low_vol"}
    assert sum(r["trades"] for r in out["regimes"].values()) == len(res.trades)

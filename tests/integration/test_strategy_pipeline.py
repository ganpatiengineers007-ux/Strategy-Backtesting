from backtest.engine import run_backtest
from cli.commands import make_sample_csv
from data.loaders import load_dataset
from metrics import compute_all
from registry.registry import Registry


def test_pipeline(tmp_path):
    ds = load_dataset(make_sample_csv(tmp_path / "s.csv", days=15))
    res = run_backtest(ds, Registry().load("three_pm_momentum"))
    assert res.status == "COMPLETED" and "n_trades" in compute_all(res, ds)

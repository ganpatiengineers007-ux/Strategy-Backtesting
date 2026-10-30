from backtest.engine import run_backtest
from cli.commands import make_sample_csv
from data.loaders import load_dataset
from metrics import compute_all
from registry.registry import Registry


def test_two_runs_identical(tmp_path):
    ds = load_dataset(make_sample_csv(tmp_path / "s.csv", days=15))
    a = run_backtest(ds, Registry().load("three_pm_momentum"))
    b = run_backtest(ds, Registry().load("three_pm_momentum"))
    assert a.to_dict() == b.to_dict() and compute_all(a, ds) == compute_all(b, ds)
    assert Registry().source_hash("three_pm_momentum") == Registry().source_hash("three_pm_momentum")

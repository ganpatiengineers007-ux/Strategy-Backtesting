import time

from backtest.engine import run_backtest
from cli.commands import make_sample_csv
from data.loaders import load_dataset
from registry.registry import Registry


def test_5000_bars_under_20_seconds(tmp_path):
    ds = load_dataset(make_sample_csv(tmp_path / "s.csv", days=70))
    assert len(ds.bars) >= 5000
    t = time.perf_counter()
    run_backtest(ds, Registry().load("three_pm_momentum"))
    assert time.perf_counter() - t < 20

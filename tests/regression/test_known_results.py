import json
from pathlib import Path

from backtest.engine import run_backtest
from cli.commands import make_sample_csv
from data.loaders import load_dataset
from registry.registry import Registry

FIX = Path(__file__).resolve().parents[1] / "fixtures"


def test_known_result(tmp_path):
    exp = json.loads((FIX / "expected_results.json").read_text(encoding="utf-8"))
    ds = load_dataset(make_sample_csv(tmp_path / "s.csv", days=exp["days"], seed=exp["seed"]))
    res = run_backtest(ds, Registry().load(exp["strategy"]))
    assert len(res.trades) == exp["n_trades"]
    assert abs(sum(t["pnl"] for t in res.trades) - exp["total_pnl"]) < 0.01

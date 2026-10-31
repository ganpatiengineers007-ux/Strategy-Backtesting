import os

from backend.api import backtests, validation
from cli.commands import make_sample_csv


def test_validation_start_with_options(tmp_path):
    make_sample_csv(tmp_path / "data" / "s.csv", days=30)
    os.environ.update({"DATA_DIR": str(tmp_path / "data"), "RUNS_ROOT": str(tmp_path / "runs")})
    os.environ.pop("BACKGROUND_WORKER", None)
    job = validation.start({"strategy_id": "three_pm_momentum", "dataset": "s.csv", "validation": {"split": 0.6, "windows": 3}})
    assert job["status"] == "SUCCEEDED"
    rid = job["result"]["run_id"]
    v = validation.get_one(rid)
    assert len(v["checks"]["walk_forward"].get("windows", [])) in (0, 3)
    assert set(backtests.get_results(rid)) == {"run_id", "status", "reason", "metrics", "trades", "equity"}


def test_bad_validation_options_rejected(tmp_path):
    try:
        validation.start({"strategy_id": "x", "dataset": "s.csv", "validation": {"windows": 99}})
        raise AssertionError("expected ValueError")
    except ValueError:
        pass

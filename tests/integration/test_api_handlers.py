import os

from backend.api import backtests, comparisons, datasets, reports, strategies, validation
from cli.commands import make_sample_csv


def _env(tmp_path):
    make_sample_csv(tmp_path / "data" / "s.csv", days=30)
    os.environ["DATA_DIR"], os.environ["RUNS_ROOT"] = str(tmp_path / "data"), str(tmp_path / "runs")


def _raises(exc, fn, *a):
    try:
        fn(*a)
    except exc:
        return True
    return False


def test_full_api_flow(tmp_path):
    _env(tmp_path)
    assert {s["id"] for s in strategies.list_all()} >= {"gamma_blast", "three_pm_momentum"}
    assert strategies.get_one("gamma_blast")["required_data"] == ["option_chain", "oi"]
    assert datasets.list_all()[0]["file"] == "s.csv"
    job = backtests.start({"strategy_id": "three_pm_momentum", "dataset": "s.csv"})
    assert job["status"] == "SUCCEEDED"
    rid = job["result"]["run_id"]
    assert backtests.get_one(job["job_id"])["status"] == "SUCCEEDED"
    assert backtests.get_one(rid)["run_id"] == rid and rid in [r["run_id"] for r in backtests.list_runs()]
    assert validation.get_one(rid)["status"] in ("PASS", "FAIL", "INCOMPLETE")
    rep = reports.get_one(rid)
    assert "metrics" in rep and len(rep["equity"]) > 10
    assert len(comparisons.create({"run_ids": [rid, rid]})["runs"]) == 2


def test_blocked_strategy_job_succeeds_but_run_blocked(tmp_path):
    _env(tmp_path)
    job = backtests.start({"strategy_id": "gamma_blast", "dataset": "s.csv"})
    assert job["status"] == "SUCCEEDED" and job["result"]["status"] == "BLOCKED"


def test_bad_inputs_rejected(tmp_path):
    _env(tmp_path)
    assert _raises(ValueError, reports.get_one, "../etc")
    assert _raises(ValueError, reports.get_one, "..")
    assert _raises(KeyError, reports.get_one, "run-does-not-exist")
    assert _raises(ValueError, backtests.start, {"strategy_id": "x"})
    assert _raises(ValueError, comparisons.create, {"run_ids": ["only-one"]})
    job = backtests.start({"strategy_id": "three_pm_momentum", "dataset": "../../etc/passwd"})
    assert job["status"] == "FAILED" and "invalid dataset" in job["error"]
    job = backtests.start({"strategy_id": "nope", "dataset": "s.csv"})
    assert job["status"] == "FAILED"

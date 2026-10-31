import os

from backend.jobs.isolated import child_env, run_isolated
from backend.services.backtest_service import run_full
from cli.commands import make_sample_csv


def test_child_env_has_no_secrets():
    os.environ["SVL_SECRET_TEST"] = "x"
    try:
        env = child_env(60, 512)
        assert "SVL_SECRET_TEST" not in env and env["SVL_MEM_MB"] == "512" and "PYTHONPATH" in env
    finally:
        os.environ.pop("SVL_SECRET_TEST", None)


def test_isolated_matches_inline(tmp_path):
    csv = make_sample_csv(tmp_path / "s.csv", days=15)
    req = {"strategy_id": "three_pm_momentum", "data_path": str(csv), "out_root": str(tmp_path / "iso"), "params": None, "config": None}
    iso = run_isolated(req, timeout=120, mem_mb=2048)["record"]
    inline, _ = run_full("three_pm_momentum", str(csv), out_root=str(tmp_path / "inl"))
    assert iso["status"] == inline["status"] and iso["dataset_hash"] == inline["dataset_hash"]
    assert iso["validation_status"] == inline["validation_status"]


def test_isolated_failure_is_reported(tmp_path):
    csv = make_sample_csv(tmp_path / "s.csv", days=5)
    try:
        run_isolated({"strategy_id": "no_such_strategy", "data_path": str(csv), "out_root": str(tmp_path / "o")}, timeout=60)
        raise AssertionError("expected RuntimeError")
    except RuntimeError as e:
        assert "isolated run failed" in str(e)

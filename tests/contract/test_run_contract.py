from backend.services.backtest_service import run_full
from cli.commands import make_sample_csv
from contracts import schema_check


def test_run_record_matches_contract(tmp_path):
    rec, _ = run_full("three_pm_momentum", make_sample_csv(tmp_path / "s.csv", days=10), out_root=str(tmp_path / "r"))
    assert not schema_check.check(rec, schema_check.load("run.schema.json"))

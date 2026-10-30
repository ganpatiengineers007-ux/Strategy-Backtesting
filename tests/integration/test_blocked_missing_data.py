from backend.services.backtest_service import run_full
from cli.commands import make_sample_csv


def test_option_strategy_blocked_without_option_chain(tmp_path):
    csv = make_sample_csv(tmp_path / "s.csv", days=10)
    record, _ = run_full("gamma_blast", csv, out_root=str(tmp_path / "runs"))
    assert record["status"] == "BLOCKED" and record["reason"].startswith("MISSING_DATA")
    assert record["validation_status"] == "BLOCKED"

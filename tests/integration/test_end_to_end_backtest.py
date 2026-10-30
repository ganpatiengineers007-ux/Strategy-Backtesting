from pathlib import Path

from backend.services.backtest_service import run_full
from cli.commands import make_sample_csv
from contracts import schema_check


def test_full_flow_creates_verified_artifacts(tmp_path):
    csv = make_sample_csv(tmp_path / "s.csv", days=40)
    record, paths = run_full("three_pm_momentum", csv, out_root=str(tmp_path / "runs"))
    assert record["status"] in ("COMPLETED", "HALTED")
    assert not schema_check.check(record, schema_check.load("run.schema.json"))
    for k in ("json", "html", "csv"):
        assert Path(paths[k]).exists()
    assert (tmp_path / "runs" / "audit.jsonl").exists()

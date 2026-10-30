from backend.services.backtest_service import run_full
from cli.commands import make_sample_csv
from contracts import schema_check
import json


def test_report_matches_contract(tmp_path):
    _, paths = run_full("three_pm_momentum", make_sample_csv(tmp_path / "s.csv", days=10), out_root=str(tmp_path / "r"))
    report = json.loads(open(paths["json"], encoding="utf-8").read())
    assert not schema_check.check(report, schema_check.load("report.schema.json"))

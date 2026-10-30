import json
from pathlib import Path

from backend.services.backtest_service import run_full
from cli.commands import make_sample_csv


def test_report_files_have_content(tmp_path):
    _, paths = run_full("three_pm_momentum", make_sample_csv(tmp_path / "s.csv", days=15), out_root=str(tmp_path / "r"))
    assert "<table>" in Path(paths["html"]).read_text(encoding="utf-8")
    assert "metrics" in json.loads(Path(paths["json"]).read_text(encoding="utf-8"))
    assert Path(paths["csv"]).read_text(encoding="utf-8").startswith("entry_ts,exit_ts")

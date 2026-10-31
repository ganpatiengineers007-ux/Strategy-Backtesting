import json

from cli import main
from cli.commands import make_sample_csv


def test_cli_optimize_runs(tmp_path, capsys):
    csv = make_sample_csv(tmp_path / "s.csv", days=40)
    grid = json.dumps({"stop_pct": [0.3, 0.5], "target_pct": [0.8, 1.0]})
    assert main.main(["optimize", "--strategy", "three_pm_momentum", "--data", csv, "--grid", grid,
                      "--out", str(tmp_path / "o")]) == 0
    out = capsys.readouterr().out
    assert "trials=4" in out and (tmp_path / "o" / "experiments.jsonl").exists()

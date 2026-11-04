import json
import sqlite3

from persistence.backup import create_backup, verify_restore


def test_backup_and_restore_round_trip(tmp_path):
    runs = tmp_path / "runs"
    run = runs / "run-test"
    run.mkdir(parents=True)
    (run / "run.json").write_text(json.dumps({"run_id": "run-test", "status": "COMPLETED"}), encoding="utf-8")
    (run / "report.json").write_text(json.dumps({"run_id": "run-test", "synthetic": True}), encoding="utf-8")
    db = runs / "svl.sqlite3"
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE runs (run_id TEXT PRIMARY KEY)")
        conn.execute("INSERT INTO runs VALUES ('run-test')")

    backup = create_backup(runs, tmp_path / "backups")
    assert (backup / "runs.tar.gz").exists()
    assert (backup / "svl.sqlite3").exists()
    result = verify_restore(backup)
    assert result["ok"] and result["run_dirs"] == 1 and result["database"] == "svl.sqlite3"

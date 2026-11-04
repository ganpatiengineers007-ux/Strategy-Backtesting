import sqlite3

from scripts.migrate import migrate


def test_migrations_are_idempotent(tmp_path):
    db = tmp_path / "db.sqlite3"
    assert migrate(db) == ["001_initial.sql"]
    assert migrate(db) == []
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0] == 0

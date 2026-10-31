"""SQLite run repository (stdlib). PostgreSQL adapter isi interface par baad me (migrations/001_initial.sql)."""
import json
import sqlite3
from contextlib import closing
from pathlib import Path

SCHEMA = ("CREATE TABLE IF NOT EXISTS runs (run_id TEXT PRIMARY KEY, strategy_id TEXT NOT NULL, "
          "status TEXT NOT NULL, created_at TEXT NOT NULL, record TEXT NOT NULL)")


class SqliteRunRepository:
    def __init__(self, path="runs/svl.sqlite3"):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path)) as c, c:
            c.execute(SCHEMA)

    def save(self, run_id, record):
        with closing(sqlite3.connect(self.path)) as c, c:
            c.execute("INSERT OR REPLACE INTO runs VALUES (?,?,?,?,?)",
                      (run_id, record["strategy_id"], record["status"], record["created_at"], json.dumps(record, default=str)))

    def get(self, run_id):
        with closing(sqlite3.connect(self.path)) as c:
            row = c.execute("SELECT record FROM runs WHERE run_id=?", (run_id,)).fetchone()
        if row is None:
            raise KeyError(run_id)
        return json.loads(row[0])

    def list_ids(self):
        with closing(sqlite3.connect(self.path)) as c:
            return [r[0] for r in c.execute("SELECT run_id FROM runs ORDER BY created_at")]

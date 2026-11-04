#!/usr/bin/env python3
"""Apply versioned SQLite migrations (idempotent, append-only)."""
import argparse
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "persistence" / "migrations" / "sqlite"


def migrate(path, migrations_dir=MIGRATIONS):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    applied = []
    with sqlite3.connect(str(path)) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
        done = {r[0] for r in conn.execute("SELECT version FROM schema_migrations")}
        for sql in sorted(Path(migrations_dir).glob("*.sql")):
            if sql.name in done:
                continue
            conn.executescript(sql.read_text(encoding="utf-8"))
            conn.execute("INSERT INTO schema_migrations(version, applied_at) VALUES (?, datetime('now'))", (sql.name,))
            applied.append(sql.name)
        conn.commit()
    return applied


def main(argv=None):
    p = argparse.ArgumentParser(description="Apply SQLite migrations.")
    p.add_argument("--sqlite", default=str(ROOT / "runs" / "svl.sqlite3"))
    args = p.parse_args(argv)
    for name in migrate(args.sqlite):
        print(f"applied {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

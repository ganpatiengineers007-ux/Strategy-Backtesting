#!/usr/bin/env python3
"""Create a runs/sqlite backup and optionally verify a restore."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from persistence.backup import create_backup, verify_restore  # noqa: E402


def main(argv=None):
    p = argparse.ArgumentParser(description="Back up runs/ and the SQLite DB (never deletes old backups).")
    p.add_argument("--runs-root", default=str(ROOT / "runs"))
    p.add_argument("--out-dir", default=str(ROOT / "backups"))
    p.add_argument("--database", default=None, help="SQLite path; default runs/svl.sqlite3 if present")
    p.add_argument("--verify-restore", metavar="BACKUP_DIR", help="Restore a backup into a temp dir and verify it")
    args = p.parse_args(argv)

    if args.verify_restore:
        result = verify_restore(args.verify_restore)
        print(json.dumps(result, indent=2))
        return 0

    backup = create_backup(args.runs_root, args.out_dir, args.database)
    print(backup)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

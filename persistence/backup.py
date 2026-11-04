"""Backup and restore verification for run artifacts and the SQLite database."""
import hashlib
import json
import shutil
import sqlite3
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _sqlite_copy(src, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(src)) as source, sqlite3.connect(str(dest)) as target:
        source.backup(target)
        target.execute("PRAGMA integrity_check")


def create_backup(runs_root="runs", out_dir="backups", database=None):
    """Create a timestamped archive. Existing backups are never deleted."""
    runs = Path(runs_root)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = out / f"svl-backup-{stamp}"
    backup.mkdir()
    archive = backup / "runs.tar.gz"

    with tarfile.open(archive, "w:gz") as tar:
        if runs.exists():
            tar.add(runs, arcname="runs")

    db = Path(database) if database else runs / "svl.sqlite3"
    db_copy = None
    if db.exists():
        db_copy = backup / db.name
        _sqlite_copy(db, db_copy)

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "runs_root": str(runs.resolve()),
        "archive": archive.name,
        "archive_sha256": _sha256(archive),
        "database": db_copy.name if db_copy else None,
        "database_sha256": _sha256(db_copy) if db_copy else None,
    }
    (backup / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return backup


def verify_restore(backup, workdir=None):
    """Restore into a temporary directory and verify files + SQLite integrity."""
    backup = Path(backup)
    manifest = json.loads((backup / "manifest.json").read_text(encoding="utf-8"))
    tmp_ctx = tempfile.TemporaryDirectory(dir=workdir) if workdir else tempfile.TemporaryDirectory()
    with tmp_ctx as tmp:
        target = Path(tmp)
        archive = backup / manifest["archive"]
        if _sha256(archive) != manifest["archive_sha256"]:
            raise ValueError("backup archive checksum mismatch")
        with tarfile.open(archive, "r:gz") as tar:
            tar.extractall(target, filter="data")
        restored_runs = target / "runs"
        if not restored_runs.is_dir():
            raise ValueError("restored archive has no runs/ directory")
        restored_db = None
        if manifest.get("database"):
            restored_db = target / manifest["database"]
            shutil.copy2(backup / manifest["database"], restored_db)
            if _sha256(restored_db) != manifest.get("database_sha256"):
                raise ValueError("restored database checksum mismatch")
            with sqlite3.connect(str(restored_db)) as conn:
                status = conn.execute("PRAGMA integrity_check").fetchone()[0]
            if status != "ok":
                raise ValueError(f"restored database integrity_check: {status}")
        run_dirs = [p for p in restored_runs.iterdir() if p.is_dir()]
        return {"ok": True, "restored_to": str(target), "run_dirs": len(run_dirs),
                "database": restored_db.name if restored_db else None}

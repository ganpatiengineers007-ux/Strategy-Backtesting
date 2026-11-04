import json
import os
import threading
import uuid
from pathlib import Path

from backend.jobs.job_status import Job, JobStatus


class JobQueue:
    """In-memory queue with optional JSON persistence for restart visibility.

    Set ``JOB_STATE_DIR`` to persist job state. Jobs that were RUNNING when the
    process stopped are marked FAILED on the next start (no silent data loss).
    """

    def __init__(self, store_dir=None):
        self.jobs, self._lock = {}, threading.Lock()
        self._store = Path(store_dir) if store_dir else None
        if self._store is not None:
            self._store.mkdir(parents=True, exist_ok=True)
            self._load()

    def _path(self, job_id):
        return self._store / f"{job_id}.json" if self._store is not None else None

    def _write_locked(self, job):
        path = self._path(job.job_id)
        if path is None:
            return
        payload = {"job_id": job.job_id, "payload": job.payload, "status": job.status.value,
                   "result": job.result, "error": job.error}
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        os.replace(tmp, path)

    def _load(self):
        for path in sorted(self._store.glob("*.json")):
            try:
                row = json.loads(path.read_text(encoding="utf-8"))
                job = Job(row["job_id"], row.get("payload") or {}, JobStatus(row.get("status", "QUEUED")),
                          row.get("result"), row.get("error"))
            except (OSError, ValueError, KeyError):
                continue
            if job.status == JobStatus.RUNNING:
                job.status, job.error = JobStatus.FAILED, "worker restarted before completion"
                self._write_locked(job)
            self.jobs[job.job_id] = job

    def submit(self, payload):
        with self._lock:
            job = Job(f"job-{uuid.uuid4().hex}", payload)
            self.jobs[job.job_id] = job
            self._write_locked(job)
            return job

    def get(self, job_id):
        return self.jobs[job_id]

    def save(self, job):
        with self._lock:
            self._write_locked(job)

    def next_queued(self):
        return next((j for j in self.jobs.values() if j.status == JobStatus.QUEUED), None)

    def claim_next(self):
        """Atomically pehla QUEUED job RUNNING bana kar deta hai."""
        with self._lock:
            job = self.next_queued()
            if job is not None:
                job.status = JobStatus.RUNNING
                self._write_locked(job)
            return job

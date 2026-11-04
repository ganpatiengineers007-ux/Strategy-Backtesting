"""Import/wiring test for backend/jobs/queue.py"""
import importlib

from backend.jobs.job_status import JobStatus
from backend.jobs.queue import JobQueue


def test_module_imports():
    importlib.import_module("backend.jobs.queue")


def test_persisted_queue_survives_restart(tmp_path):
    q = JobQueue(str(tmp_path / "jobs"))
    queued = q.submit({"x": 1})
    running = q.claim_next()
    assert running.job_id == queued.job_id
    reloaded = JobQueue(str(tmp_path / "jobs"))
    assert reloaded.get(running.job_id).status == JobStatus.FAILED
    assert "restarted" in reloaded.get(running.job_id).error

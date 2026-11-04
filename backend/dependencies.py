import os

from backend.jobs.queue import JobQueue
from persistence.repositories import RunRepository
from registry.registry import Registry

_QUEUE = None


def get_registry():
    return Registry()


def get_queue():
    global _QUEUE
    if _QUEUE is None:
        _QUEUE = JobQueue(os.environ.get("JOB_STATE_DIR"))
    return _QUEUE


def get_repository(root=None):
    url = os.environ.get("DATABASE_URL", "")
    if url.startswith("sqlite:///"):
        from persistence.database import SqliteRunRepository
        return SqliteRunRepository(url[len("sqlite:///"):])
    return RunRepository(root or os.environ.get("RUNS_ROOT", "runs"))

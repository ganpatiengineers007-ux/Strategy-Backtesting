import os

from backend.jobs.queue import JobQueue
from persistence.repositories import RunRepository
from registry.registry import Registry

_QUEUE = JobQueue()


def get_registry():
    return Registry()


def get_queue():
    return _QUEUE


def get_repository(root=None):
    url = os.environ.get("DATABASE_URL", "")
    if url.startswith("sqlite:///"):
        from persistence.database import SqliteRunRepository
        return SqliteRunRepository(url[len("sqlite:///"):])
    return RunRepository(root or os.environ.get("RUNS_ROOT", "runs"))

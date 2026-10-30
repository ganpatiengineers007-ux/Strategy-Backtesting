from backend.jobs.job_status import JobStatus
from backend.jobs.queue import JobQueue
from backend.jobs.worker import run_next


def test_success_and_failure_reason_kept():
    q = JobQueue()
    a, b = q.submit({"x": 1}), q.submit({"x": 2})
    run_next(q, lambda p: {"ok": p["x"]})
    assert a.status == JobStatus.SUCCEEDED and a.result == {"ok": 1}

    def boom(_):
        raise RuntimeError("data missing")
    run_next(q, boom)
    assert b.status == JobStatus.FAILED and "data missing" in b.error

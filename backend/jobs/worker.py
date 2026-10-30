"""Worker: job RUNNING -> SUCCEEDED/FAILED. Failure ka karan save rehta hai."""
from backend.jobs.job_status import JobStatus


def run_next(queue, handler):
    job = queue.next_queued()
    if job is None:
        return None
    job.status = JobStatus.RUNNING
    try:
        job.result = handler(job.payload)
        job.status = JobStatus.SUCCEEDED
    except Exception as e:  # noqa: BLE001 - failure reason save karna hai
        job.status, job.error = JobStatus.FAILED, f"{type(e).__name__}: {e}"
    return job

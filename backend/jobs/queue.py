import itertools
import threading

from backend.jobs.job_status import Job, JobStatus


class JobQueue:
    def __init__(self):
        self.jobs, self._ids, self._lock = {}, itertools.count(1), threading.Lock()

    def submit(self, payload):
        with self._lock:
            job = Job(f"job-{next(self._ids)}", payload)
            self.jobs[job.job_id] = job
            return job

    def get(self, job_id):
        return self.jobs[job_id]

    def next_queued(self):
        return next((j for j in self.jobs.values() if j.status == JobStatus.QUEUED), None)

    def claim_next(self):
        """Atomically pehla QUEUED job RUNNING bana kar deta hai."""
        with self._lock:
            job = self.next_queued()
            if job is not None:
                job.status = JobStatus.RUNNING
            return job

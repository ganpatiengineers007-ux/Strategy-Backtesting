import itertools

from backend.jobs.job_status import Job, JobStatus


class JobQueue:
    def __init__(self):
        self.jobs, self._ids = {}, itertools.count(1)

    def submit(self, payload):
        job = Job(f"job-{next(self._ids)}", payload)
        self.jobs[job.job_id] = job
        return job

    def get(self, job_id):
        return self.jobs[job_id]

    def next_queued(self):
        return next((j for j in self.jobs.values() if j.status == JobStatus.QUEUED), None)

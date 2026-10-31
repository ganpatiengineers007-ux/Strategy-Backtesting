"""Worker: job RUNNING -> SUCCEEDED/FAILED (failure ka karan save). BackgroundWorker = daemon thread."""
import threading

from backend.jobs.job_status import JobStatus


def run_next(queue, handler):
    job = queue.claim_next()
    if job is None:
        return None
    try:
        job.result = handler(job.payload)
        job.status = JobStatus.SUCCEEDED
    except Exception as e:  # noqa: BLE001 - failure reason save karna hai
        job.status, job.error = JobStatus.FAILED, f"{type(e).__name__}: {e}"
    return job


class BackgroundWorker:
    def __init__(self, queue, handler, interval=0.2):
        self.queue, self.handler, self.interval = queue, handler, interval
        self._stop, self._thread = threading.Event(), None

    def start(self):
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="svl-worker")
        self._thread.start()

    def _loop(self):
        while not self._stop.is_set():
            if run_next(self.queue, self.handler) is None:
                self._stop.wait(self.interval)

    def stop(self, timeout=5):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout)

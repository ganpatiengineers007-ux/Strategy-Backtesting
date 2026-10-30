from dataclasses import dataclass
from enum import Enum


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


@dataclass
class Job:
    job_id: str
    payload: dict
    status: JobStatus = JobStatus.QUEUED
    result: dict = None
    error: str = None

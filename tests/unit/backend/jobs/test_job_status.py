"""Import/wiring test for backend/jobs/job_status.py"""
import importlib


def test_module_imports():
    importlib.import_module("backend.jobs.job_status")

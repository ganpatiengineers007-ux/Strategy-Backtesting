"""Import/wiring test for backend/jobs/run_job.py"""
import importlib


def test_module_imports():
    importlib.import_module("backend.jobs.run_job")

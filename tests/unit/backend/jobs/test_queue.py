"""Import/wiring test for backend/jobs/queue.py"""
import importlib


def test_module_imports():
    importlib.import_module("backend.jobs.queue")

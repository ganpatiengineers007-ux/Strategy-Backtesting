"""Import/wiring test for backend/middleware/request_id.py"""
import importlib


def test_module_imports():
    importlib.import_module("backend.middleware.request_id")

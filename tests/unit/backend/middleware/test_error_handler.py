"""Import/wiring test for backend/middleware/error_handler.py"""
import importlib


def test_module_imports():
    importlib.import_module("backend.middleware.error_handler")

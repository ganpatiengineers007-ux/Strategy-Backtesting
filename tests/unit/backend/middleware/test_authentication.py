"""Import/wiring test for backend/middleware/authentication.py"""
import importlib


def test_module_imports():
    importlib.import_module("backend.middleware.authentication")

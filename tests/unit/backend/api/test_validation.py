"""Import/wiring test for backend/api/validation.py"""
import importlib


def test_module_imports():
    importlib.import_module("backend.api.validation")

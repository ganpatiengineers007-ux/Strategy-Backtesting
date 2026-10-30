"""Import/wiring test for backend/adapters/go_adapter.py"""
import importlib


def test_module_imports():
    importlib.import_module("backend.adapters.go_adapter")

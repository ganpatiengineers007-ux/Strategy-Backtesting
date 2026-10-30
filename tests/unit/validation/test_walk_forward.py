"""Import/wiring test for validation/walk_forward.py"""
import importlib


def test_module_imports():
    importlib.import_module("validation.walk_forward")

"""Import/wiring test for validation/robustness.py"""
import importlib


def test_module_imports():
    importlib.import_module("validation.robustness")

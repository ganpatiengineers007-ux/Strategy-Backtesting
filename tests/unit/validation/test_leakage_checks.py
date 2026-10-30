"""Import/wiring test for validation/leakage_checks.py"""
import importlib


def test_module_imports():
    importlib.import_module("validation.leakage_checks")

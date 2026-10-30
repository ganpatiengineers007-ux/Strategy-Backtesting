"""Import/wiring test for validation/cross_validation.py"""
import importlib


def test_module_imports():
    importlib.import_module("validation.cross_validation")

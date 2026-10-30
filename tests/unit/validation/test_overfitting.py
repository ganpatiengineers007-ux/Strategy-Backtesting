"""Import/wiring test for validation/overfitting.py"""
import importlib


def test_module_imports():
    importlib.import_module("validation.overfitting")

"""Import/wiring test for strategies/validation.py"""
import importlib


def test_module_imports():
    importlib.import_module("strategies.validation")

"""Import/wiring test for validation/regime_analysis.py"""
import importlib


def test_module_imports():
    importlib.import_module("validation.regime_analysis")

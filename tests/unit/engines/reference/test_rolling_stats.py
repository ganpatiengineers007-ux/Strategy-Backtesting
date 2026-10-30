"""Import/wiring test for engines/reference/rolling_stats.py"""
import importlib


def test_module_imports():
    importlib.import_module("engines.reference.rolling_stats")

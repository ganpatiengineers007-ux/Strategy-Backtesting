"""Import/wiring test for metrics/confidence_intervals.py"""
import importlib


def test_module_imports():
    importlib.import_module("metrics.confidence_intervals")

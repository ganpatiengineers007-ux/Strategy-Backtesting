"""Import/wiring test for metrics/return_metrics.py"""
import importlib


def test_module_imports():
    importlib.import_module("metrics.return_metrics")

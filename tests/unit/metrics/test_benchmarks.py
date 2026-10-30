"""Import/wiring test for metrics/benchmarks.py"""
import importlib


def test_module_imports():
    importlib.import_module("metrics.benchmarks")

"""Import/wiring test for metrics/accuracy.py"""
import importlib


def test_module_imports():
    importlib.import_module("metrics.accuracy")

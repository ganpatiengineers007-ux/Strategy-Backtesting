"""Import/wiring test for metrics/risk_metrics.py"""
import importlib


def test_module_imports():
    importlib.import_module("metrics.risk_metrics")

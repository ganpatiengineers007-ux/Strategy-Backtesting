"""Import/wiring test for observability/tracing.py"""
import importlib


def test_module_imports():
    importlib.import_module("observability.tracing")

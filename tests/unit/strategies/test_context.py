"""Import/wiring test for strategies/context.py"""
import importlib


def test_module_imports():
    importlib.import_module("strategies.context")

"""Import/wiring test for strategies/examples/example_strategy.py"""
import importlib


def test_module_imports():
    importlib.import_module("strategies.examples.example_strategy")

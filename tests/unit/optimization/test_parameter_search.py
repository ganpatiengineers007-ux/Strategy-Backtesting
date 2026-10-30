"""Import/wiring test for optimization/parameter_search.py"""
import importlib


def test_module_imports():
    importlib.import_module("optimization.parameter_search")

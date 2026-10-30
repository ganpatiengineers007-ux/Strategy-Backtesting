"""Import/wiring test for optimization/constraints.py"""
import importlib


def test_module_imports():
    importlib.import_module("optimization.constraints")

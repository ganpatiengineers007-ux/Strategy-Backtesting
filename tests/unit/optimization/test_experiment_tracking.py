"""Import/wiring test for optimization/experiment_tracking.py"""
import importlib


def test_module_imports():
    importlib.import_module("optimization.experiment_tracking")

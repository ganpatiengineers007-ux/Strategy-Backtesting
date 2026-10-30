"""Import/wiring test for strategies/three_pm_momentum/strategy.py"""
import importlib


def test_module_imports():
    importlib.import_module("strategies.three_pm_momentum.strategy")

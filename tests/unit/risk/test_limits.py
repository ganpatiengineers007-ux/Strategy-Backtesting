"""Import/wiring test for risk/limits.py"""
import importlib


def test_module_imports():
    importlib.import_module("risk.limits")

"""Import/wiring test for strategies/base.py"""
import importlib


def test_module_imports():
    importlib.import_module("strategies.base")

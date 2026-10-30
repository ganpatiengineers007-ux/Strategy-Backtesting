"""Import/wiring test for strategies/models.py"""
import importlib


def test_module_imports():
    importlib.import_module("strategies.models")

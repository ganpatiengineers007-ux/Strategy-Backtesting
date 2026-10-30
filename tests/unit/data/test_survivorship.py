"""Import/wiring test for data/survivorship.py"""
import importlib


def test_module_imports():
    importlib.import_module("data.survivorship")

"""Import/wiring test for data/models.py"""
import importlib


def test_module_imports():
    importlib.import_module("data.models")

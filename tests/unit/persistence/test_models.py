"""Import/wiring test for persistence/models.py"""
import importlib


def test_module_imports():
    importlib.import_module("persistence.models")

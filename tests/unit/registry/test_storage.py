"""Import/wiring test for registry/storage.py"""
import importlib


def test_module_imports():
    importlib.import_module("registry.storage")

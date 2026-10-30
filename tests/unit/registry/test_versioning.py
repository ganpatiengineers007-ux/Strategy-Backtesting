"""Import/wiring test for registry/versioning.py"""
import importlib


def test_module_imports():
    importlib.import_module("registry.versioning")

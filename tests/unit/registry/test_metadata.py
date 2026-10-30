"""Import/wiring test for registry/metadata.py"""
import importlib


def test_module_imports():
    importlib.import_module("registry.metadata")

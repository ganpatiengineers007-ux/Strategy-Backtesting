"""Import/wiring test for registry/lifecycle.py"""
import importlib


def test_module_imports():
    importlib.import_module("registry.lifecycle")

"""Import/wiring test for registry/permissions.py"""
import importlib


def test_module_imports():
    importlib.import_module("registry.permissions")

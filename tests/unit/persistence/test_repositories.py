"""Import/wiring test for persistence/repositories.py"""
import importlib


def test_module_imports():
    importlib.import_module("persistence.repositories")

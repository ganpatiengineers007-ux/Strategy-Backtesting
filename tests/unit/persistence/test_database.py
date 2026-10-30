"""Import/wiring test for persistence/database.py"""
import importlib


def test_module_imports():
    importlib.import_module("persistence.database")

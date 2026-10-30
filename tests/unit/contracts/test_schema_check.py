"""Import/wiring test for contracts/schema_check.py"""
import importlib


def test_module_imports():
    importlib.import_module("contracts.schema_check")

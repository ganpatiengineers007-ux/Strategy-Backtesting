"""Import/wiring test for persistence/audit.py"""
import importlib


def test_module_imports():
    importlib.import_module("persistence.audit")

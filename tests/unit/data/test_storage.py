"""Import/wiring test for data/storage.py"""
import importlib


def test_module_imports():
    importlib.import_module("data.storage")

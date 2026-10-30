"""Import/wiring test for data/loaders.py"""
import importlib


def test_module_imports():
    importlib.import_module("data.loaders")

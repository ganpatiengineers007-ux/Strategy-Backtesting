"""Import/wiring test for data/normalizer.py"""
import importlib


def test_module_imports():
    importlib.import_module("data.normalizer")

"""Import/wiring test for data/sources/csv_source.py"""
import importlib


def test_module_imports():
    importlib.import_module("data.sources.csv_source")

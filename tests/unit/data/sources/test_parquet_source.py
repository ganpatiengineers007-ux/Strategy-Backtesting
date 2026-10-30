"""Import/wiring test for data/sources/parquet_source.py"""
import importlib


def test_module_imports():
    importlib.import_module("data.sources.parquet_source")

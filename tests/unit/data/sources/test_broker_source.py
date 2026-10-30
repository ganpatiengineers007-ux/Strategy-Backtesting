"""Import/wiring test for data/sources/broker_source.py"""
import importlib


def test_module_imports():
    importlib.import_module("data.sources.broker_source")

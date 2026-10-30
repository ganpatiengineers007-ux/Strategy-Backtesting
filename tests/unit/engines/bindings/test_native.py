"""Import/wiring test for engines/bindings/native.py"""
import importlib


def test_module_imports():
    importlib.import_module("engines.bindings.native")

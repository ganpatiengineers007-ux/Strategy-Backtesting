"""Import/wiring test for validation/out_of_sample.py"""
import importlib


def test_module_imports():
    importlib.import_module("validation.out_of_sample")

"""Import/wiring test for reporting/generator.py"""
import importlib


def test_module_imports():
    importlib.import_module("reporting.generator")

"""Import/wiring test for reporting/charts.py"""
import importlib


def test_module_imports():
    importlib.import_module("reporting.charts")

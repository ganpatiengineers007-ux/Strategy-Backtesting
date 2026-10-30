"""Import/wiring test for reporting/csv_export.py"""
import importlib


def test_module_imports():
    importlib.import_module("reporting.csv_export")

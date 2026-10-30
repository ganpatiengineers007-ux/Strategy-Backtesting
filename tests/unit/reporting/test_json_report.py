"""Import/wiring test for reporting/json_report.py"""
import importlib


def test_module_imports():
    importlib.import_module("reporting.json_report")

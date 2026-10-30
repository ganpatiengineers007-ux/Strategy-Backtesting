"""Import/wiring test for reporting/html_report.py"""
import importlib


def test_module_imports():
    importlib.import_module("reporting.html_report")

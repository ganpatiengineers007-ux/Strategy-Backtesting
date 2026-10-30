"""Import/wiring test for data/quality_report.py"""
import importlib


def test_module_imports():
    importlib.import_module("data.quality_report")

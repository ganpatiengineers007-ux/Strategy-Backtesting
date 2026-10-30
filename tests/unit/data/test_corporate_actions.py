"""Import/wiring test for data/corporate_actions.py"""
import importlib


def test_module_imports():
    importlib.import_module("data.corporate_actions")

"""Import/wiring test for cli/main.py"""
import importlib


def test_module_imports():
    importlib.import_module("cli.main")

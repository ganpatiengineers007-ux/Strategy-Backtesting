"""Import/wiring test for cli/commands.py"""
import importlib


def test_module_imports():
    importlib.import_module("cli.commands")

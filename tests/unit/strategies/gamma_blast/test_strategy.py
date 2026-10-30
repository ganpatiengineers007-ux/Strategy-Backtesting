"""Import/wiring test for strategies/gamma_blast/strategy.py"""
import importlib


def test_module_imports():
    importlib.import_module("strategies.gamma_blast.strategy")

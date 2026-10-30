"""Import/wiring test for risk/drawdown.py"""
import importlib


def test_module_imports():
    importlib.import_module("risk.drawdown")

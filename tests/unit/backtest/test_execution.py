"""Import/wiring test for backtest/execution.py"""
import importlib


def test_module_imports():
    importlib.import_module("backtest.execution")

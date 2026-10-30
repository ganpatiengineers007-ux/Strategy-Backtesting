"""Import/wiring test for backtest/fees.py"""
import importlib


def test_module_imports():
    importlib.import_module("backtest.fees")

"""Import/wiring test for backtest/slippage.py"""
import importlib


def test_module_imports():
    importlib.import_module("backtest.slippage")

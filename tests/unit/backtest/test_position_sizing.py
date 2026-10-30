"""Import/wiring test for backtest/position_sizing.py"""
import importlib


def test_module_imports():
    importlib.import_module("backtest.position_sizing")

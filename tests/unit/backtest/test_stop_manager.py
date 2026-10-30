"""Import/wiring test for backtest/stop_manager.py"""
import importlib


def test_module_imports():
    importlib.import_module("backtest.stop_manager")

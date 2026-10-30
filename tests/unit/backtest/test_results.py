"""Import/wiring test for backtest/results.py"""
import importlib


def test_module_imports():
    importlib.import_module("backtest.results")

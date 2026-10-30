"""Import/wiring test for backtest/portfolio.py"""
import importlib


def test_module_imports():
    importlib.import_module("backtest.portfolio")

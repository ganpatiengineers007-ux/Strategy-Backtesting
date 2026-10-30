"""Import/wiring test for backtest/orders.py"""
import importlib


def test_module_imports():
    importlib.import_module("backtest.orders")

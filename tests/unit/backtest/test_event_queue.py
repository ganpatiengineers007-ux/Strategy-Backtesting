"""Import/wiring test for backtest/event_queue.py"""
import importlib


def test_module_imports():
    importlib.import_module("backtest.event_queue")

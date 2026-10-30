"""Import/wiring test for backend/api/backtests.py"""
import importlib


def test_module_imports():
    importlib.import_module("backend.api.backtests")

"""Import/wiring test for backend/schemas/strategy.py"""
import importlib


def test_module_imports():
    importlib.import_module("backend.schemas.strategy")

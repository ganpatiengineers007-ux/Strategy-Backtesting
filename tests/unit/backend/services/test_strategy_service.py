"""Import/wiring test for backend/services/strategy_service.py"""
import importlib


def test_module_imports():
    importlib.import_module("backend.services.strategy_service")

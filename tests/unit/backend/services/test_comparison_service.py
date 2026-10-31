"""Import/wiring test for backend/services/comparison_service.py"""
import importlib


def test_module_imports():
    importlib.import_module("backend.services.comparison_service")

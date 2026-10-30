"""Import/wiring test for backend/services/validation_service.py"""
import importlib


def test_module_imports():
    importlib.import_module("backend.services.validation_service")

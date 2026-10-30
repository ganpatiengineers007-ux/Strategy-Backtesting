"""Import/wiring test for backend/schemas/validation.py"""
import importlib


def test_module_imports():
    importlib.import_module("backend.schemas.validation")

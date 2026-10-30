"""Import/wiring test for backend/app.py"""
import importlib


def test_module_imports():
    importlib.import_module("backend.app")

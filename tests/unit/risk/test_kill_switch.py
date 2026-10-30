"""Import/wiring test for risk/kill_switch.py"""
import importlib


def test_module_imports():
    importlib.import_module("risk.kill_switch")

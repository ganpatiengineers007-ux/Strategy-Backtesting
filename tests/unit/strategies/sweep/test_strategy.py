"""Import/wiring test for strategies/sweep/strategy.py (STR14)"""
import importlib


def test_module_imports():
    importlib.import_module("strategies.sweep.strategy")


def test_strategy_instance():
    from strategies.sweep.strategy import SweepStrategy
    s = SweepStrategy({"stop_pct": 0.5, "target_pct": 1.0})
    assert s.strategy_id == "sweep"
    assert s.params["stop_pct"] == 0.5
    assert s.params["target_pct"] == 1.0

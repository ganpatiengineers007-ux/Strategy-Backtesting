import importlib

from backend.services import strategy_service


def test_module_imports():
    importlib.import_module("backend.services.strategy_service")


def test_readiness_exposes_runnable_and_blocked():
    rows = {s["id"]: s for s in strategy_service.list_strategies()}
    assert rows["gamma_blast"]["status"] == "RUNNABLE"
    assert rows["theta_straddle"]["status"] == "BLOCKED"
    assert "short option legs" in rows["theta_straddle"]["reason"]
    assert rows["volume_profile"]["runnable"] is False

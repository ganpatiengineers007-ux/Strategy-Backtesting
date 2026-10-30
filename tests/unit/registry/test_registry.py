from registry.lifecycle import can_transition
from registry.registry import Registry


def test_discover_and_load():
    reg = Registry()
    assert {"gamma_blast", "three_pm_momentum"} <= set(reg.discover())
    s = reg.load("three_pm_momentum", {"stop_pct": 0.7})
    assert s.params["stop_pct"] == 0.7 and s.params["target_pct"] == 1.0
    assert len(reg.source_hash("gamma_blast")) == 64


def test_lifecycle():
    assert can_transition("DRAFT", "VALIDATED") and not can_transition("DRAFT", "APPROVED")

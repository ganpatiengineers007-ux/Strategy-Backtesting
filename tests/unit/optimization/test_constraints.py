from optimization.constraints import DEFAULT_RULES, satisfies


def test_stop_must_be_below_target():
    assert satisfies({"stop_pct": 0.5, "target_pct": 1.0}, DEFAULT_RULES)
    assert not satisfies({"stop_pct": 2.0, "target_pct": 1.0}, DEFAULT_RULES)
    assert satisfies({"x": 1}, DEFAULT_RULES)

from registry.permissions import can, require


def test_roles():
    assert can("viewer", "list") and not can("viewer", "run_backtest")
    assert can("analyst", "run_backtest") and not can("analyst", "approve")
    assert can("admin", "approve") and not can("nobody", "list")
    try:
        require("analyst", "approve")
        raise AssertionError("expected PermissionError")
    except PermissionError:
        pass

from risk.limits import RiskLimits
from risk.manager import RiskManager


def test_position_limit_and_drawdown_kill():
    rm = RiskManager(RiskLimits(max_position_pct=50, max_drawdown_pct=10))
    assert rm.check_order(100, 100, 10000) == (False, "MAX_POSITION")
    assert rm.check_order(40, 100, 10000) == (True, "")
    assert rm.after_bar(10000) is False
    assert rm.after_bar(8900) is True and rm.kill.reason.startswith("MAX_DRAWDOWN")
    assert rm.check_order(1, 1, 10000) == (False, "KILL_SWITCH")

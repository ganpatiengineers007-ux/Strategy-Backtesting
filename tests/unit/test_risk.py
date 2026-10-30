from risk.manager import RiskManager


def test_default_allows_small_order():
    assert RiskManager().check_order(1, 100, 10000) == (True, '')

from backtest.fills import resolve_exit
from data.models import Bar


def test_ambiguous_candle_is_conservative():
    assert resolve_exit(Bar("t", 100, 110, 90, 105), 95, 108) == (95, "STOP_AMBIGUOUS_CONSERVATIVE")


def test_gap_down_fills_at_open():
    assert resolve_exit(Bar("t", 90, 92, 88, 91), 95, 108) == (90, "STOP")


def test_target_only_and_none():
    assert resolve_exit(Bar("t", 100, 110, 99, 105), 95, 108) == (108, "TARGET")
    assert resolve_exit(Bar("t", 100, 101, 99, 100), 95, 108) is None

from backtest.execution import ExecutionModel
from data.models import Bar
from backtest.portfolio import Position


def test_costs_direction_and_amounts():
    m = ExecutionModel(slippage_bps=10, fee_pct=0.001)
    px, fee = m.fill_entry(100.0, 10)
    assert abs(px - 100.1) < 1e-9 and abs(fee - 1.001) < 1e-9
    px, fee = m.fill_exit(100.0, 10)
    assert abs(px - 99.9) < 1e-9 and abs(fee - 0.999) < 1e-9


def test_negative_costs_rejected_and_exit_rule():
    try:
        ExecutionModel(-1, 0)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    pos = Position(1, 100.0, "t", 95.0, 108.0, 0.0)
    assert ExecutionModel().check_exit(pos, Bar("t", 100, 110, 90, 105)) == (95.0, "STOP_AMBIGUOUS_CONSERVATIVE")

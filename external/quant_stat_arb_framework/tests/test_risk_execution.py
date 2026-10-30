import pandas as pd
from quantstrat.config import RiskConfig, StrategyConfig
from quantstrat.models import Signal, Side
from quantstrat.risk import RiskManager
from quantstrat.execution import DryRunExecutor

def test_risk_sizing_and_dry_run():
    sc = StrategyConfig()
    rm = RiskManager(RiskConfig(risk_fraction=0.01), sc)
    sig = Signal(pd.Timestamp("2025-01-01"), Side.BUY, -2.1, 1000, 10, "TEST")
    intent = rm.create_order_intent(sig, 100000)
    assert intent is not None
    assert intent.quantity > 0
    assert intent.stop_price < intent.reference_price < intent.target_price
    ex = DryRunExecutor()
    result = ex.submit(intent)
    assert result.accepted and result.dry_run
    assert len(ex.orders) == 1

def test_live_mode_is_blocked():
    import pytest
    with pytest.raises(ValueError):
        DryRunExecutor(dry_run=False)

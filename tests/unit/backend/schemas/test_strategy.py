from backend.schemas.strategy import StrategySummary


def test_summary_and_live_flag():
    m = {"id": "x", "version": "0.1.0", "required_data": ["oi"], "execution_modes": ["backtest"], "live_trading": {"enabled": False}}
    s = StrategySummary.from_manifest(m)
    assert s.id == "x" and s.live_trading_enabled is False and s.required_data == ["oi"]
    m["live_trading"] = {"enabled": True}
    assert StrategySummary.from_manifest(m).live_trading_enabled is True

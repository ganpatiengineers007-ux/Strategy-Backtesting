from backend.services.backtest_service import load_config


def test_yaml_config_loaded_and_policy_key_removed():
    cfg = load_config()
    assert cfg["slippage_bps"] == 2.0 and cfg["fee_pct"] == 0.0003
    assert cfg["max_drawdown_pct"] == 30.0 and "on_violation" not in cfg

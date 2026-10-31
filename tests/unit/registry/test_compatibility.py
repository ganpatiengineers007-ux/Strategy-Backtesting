from registry import compatibility as c

OK = {"execution_modes": ["backtest"], "live_trading": {"enabled": False}}


def test_checks():
    assert c.check(OK, "0.1.0") == []
    assert "EXECUTION_MODE_BACKTEST_MISSING" in c.check({"execution_modes": ["paper"]}, "0.1.0")
    assert "LIVE_TRADING_NOT_ALLOWED" in c.check({**OK, "live_trading": {"enabled": True}}, "0.1.0")
    assert "LIVE_TRADING_NOT_ALLOWED" in c.check({**OK, "live_trading": True}, "0.1.0")
    assert c.check({**OK, "min_engine_version": "0.2"}, "0.1.0")[0].startswith("ENGINE_TOO_OLD")
    assert c.check({**OK, "min_engine_version": "0.1.0"}, "0.1.0") == []
    assert c.check({**OK, "min_engine_version": "x.y"}, "0.1.0") == ["BAD_MIN_ENGINE_VERSION"]


def test_real_manifests_are_compatible():
    from registry.registry import Registry
    reg = Registry()
    for sid in reg.discover():
        assert c.check(reg.manifest(sid)) == [], sid

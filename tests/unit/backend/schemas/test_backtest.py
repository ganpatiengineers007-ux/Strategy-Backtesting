from backend.schemas.backtest import BacktestRequest


def _bad(d):
    try:
        BacktestRequest.from_dict(d)
    except ValueError:
        return True
    return False


def test_valid_and_defaults():
    r = BacktestRequest.from_dict({"strategy_id": " s ", "dataset": "a.csv", "validation": {"split": 0.8, "windows": 5}})
    assert r.strategy_id == "s" and r.params == {} and r.validation["windows"] == 5


def test_rejects_bad_input():
    assert _bad("x") and _bad({"strategy_id": "s"}) and _bad({"strategy_id": "s", "dataset": ""})
    assert _bad({"strategy_id": "s", "dataset": "a.csv", "typo_key": 1})
    assert _bad({"strategy_id": "s", "dataset": "a.csv", "params": [1]})
    assert _bad({"strategy_id": "s", "dataset": "a.csv", "validation": {"split": 2}})
    assert _bad({"strategy_id": "s", "dataset": "a.csv", "validation": {"windows": True}})

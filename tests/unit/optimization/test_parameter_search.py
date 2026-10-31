from optimization import parameter_search as ps
from optimization.constraints import DEFAULT_RULES
from tests._helpers import BuyEvery, make_dataset, make_days


def test_grid():
    assert len(ps.grid({"a": [1, 2], "b": [3, 4, 5]})) == 6


def test_search_uses_holdout_and_counts_trials(tmp_path):
    ds = make_dataset(make_days(40, 20))
    space = {"n": [6, 8], "stop_pct": [0.5, 1.0], "target_pct": [0.4, 2.0]}
    out = ps.search(ds, lambda p: BuyEvery(p), space, rules=DEFAULT_RULES, track_root=str(tmp_path))
    assert out["n_trials"] == 4  # stop<target rule: 2 valid stop/target combos x 2 n
    assert out["status"] in ("PASS", "FAIL", "UNAVAILABLE") and "warning" in out
    from optimization.experiment_tracking import read
    assert len(read(tmp_path)) >= out["n_trials"]


def test_no_eligible_trials_is_unavailable():
    ds = make_dataset(make_days(5, 20))
    out = ps.search(ds, lambda p: BuyEvery(p), {"n": [50]}, min_trades=999)
    assert out["status"] == "UNAVAILABLE"

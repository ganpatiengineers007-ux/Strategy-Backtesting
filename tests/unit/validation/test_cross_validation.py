from tests._helpers import BuyEvery, make_dataset, make_days
from validation import cross_validation as cv


def test_decide_rules():
    f = lambda t, e: {"trades": t, "expectancy": e}  # noqa: E731
    assert cv.decide([f(1, 1), f(1, 1)])[0] == "UNAVAILABLE"
    assert cv.decide([f(5, 1), f(5, 2), f(5, -1)])[0] == "PASS"
    assert cv.decide([f(5, 1), f(5, -2), f(5, -1)])[0] == "FAIL"


def test_run_returns_folds():
    ds = make_dataset(make_days(30, 20))
    out = cv.run(ds, lambda: BuyEvery({"n": 6}), folds=4)
    assert len(out["folds"]) == 4 and out["status"] in ("PASS", "FAIL")

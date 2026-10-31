from tests._helpers import BuyEvery, make_dataset, make_days
from validation import robustness as rb


def test_variants_only_float_params():
    v = rb.variants({"stop_pct": 1.0, "n": 6})
    assert len(v) == 2 and all(x["n"] == 6 for x in v)


def test_decide():
    assert rb.decide(-1, [1])[0] == "UNAVAILABLE"
    assert rb.decide(1, [])[1] == "NO_FLOAT_PARAMS"
    assert rb.decide(1, [1, 1, 1, -1])[0] == "PASS"
    assert rb.decide(1, [1, -1, -1, -1])[0] == "FAIL"


def test_run_smoke():
    ds = make_dataset(make_days(30, 20))
    out = rb.run(ds, lambda: BuyEvery({"n": 6, "stop_pct": 1.0, "target_pct": 2.0}))
    assert out["status"] in ("PASS", "FAIL", "UNAVAILABLE")

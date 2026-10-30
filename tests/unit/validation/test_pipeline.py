from tests._helpers import BuyAtIndex, make_bars, make_dataset
from validation.pipeline import overall_status, run_validation


def test_overall_status_rules():
    assert overall_status({"a": {"status": "PASS"}, "b": {"status": "UNAVAILABLE"}}) == "INCOMPLETE"
    assert overall_status({"a": {"status": "FAIL"}, "b": {"status": "UNAVAILABLE"}}) == "FAIL"
    assert overall_status({"a": {"status": "PASS"}}) == "PASS"


def test_pipeline_never_passes_unimplemented_checks():
    res = run_validation(make_dataset(make_bars(200)), lambda: BuyAtIndex({"at": 1}))
    assert "leakage" in res["checks"] and res["status"] != "PASS"
    assert res["checks"]["cross_validation"]["status"] == "UNAVAILABLE"

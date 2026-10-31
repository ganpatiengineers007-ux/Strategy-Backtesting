from data.corporate_actions import apply_dividends, apply_splits
from data.models import Bar


def _bars():
    return [Bar("2024-01-01T09:15:00", 100, 102, 98, 100, 10), Bar("2024-01-02T09:15:00", 50, 51, 49, 50, 20)]


def test_split_adjusts_only_before_date_and_original_untouched():
    orig = _bars()
    out = apply_splits(orig, [{"date": "2024-01-02", "ratio": 2.0}])
    assert out[0].close == 50.0 and out[0].volume == 20.0 and out[1].close == 50.0 and out[1].volume == 20
    assert orig[0].close == 100  # original nahi badla


def test_dividend_factor():
    out = apply_dividends(_bars(), [{"date": "2024-01-02", "amount": 10.0}])
    assert abs(out[0].close - 90.0) < 1e-9 and out[1].close == 50


def test_bad_inputs():
    for fn, arg in ((apply_splits, [{"date": "2024-01-02", "ratio": 0}]), (apply_dividends, [{"date": "2024-01-02", "amount": 100.0}])):
        try:
            fn(_bars(), arg)
            raise AssertionError("expected ValueError")
        except ValueError:
            pass

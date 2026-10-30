from indicators.trend import ema, sma


def test_sma_and_ema():
    assert sma([1, 2, 3, 4, 5], 3) == [None, None, 2.0, 3.0, 4.0]
    e = ema([1, 2, 3, 4, 5], 3)
    assert e[:2] == [None, None] and e[2] == 2.0 and abs(e[3] - 3.0) < 1e-12

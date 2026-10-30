from indicators.volatility import atr, true_range
from tests._helpers import make_bars


def test_atr_positive_and_warmup():
    bars = make_bars(30)
    a = atr(bars, 14)
    assert a[12] is None and a[13] > 0
    assert all(t >= 0 for t in true_range(bars))

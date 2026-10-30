from data.models import Bar
from indicators.volume import obv, vwap


def test_vwap_first_bar_and_daily_reset():
    bars = [Bar("2024-01-01T09:15:00", 10, 12, 8, 10, 100), Bar("2024-01-02T09:15:00", 20, 22, 18, 20, 50)]
    v = vwap(bars)
    assert abs(v[0] - 10.0) < 1e-9 and abs(v[1] - 20.0) < 1e-9
    assert obv(bars) == [0.0, 50.0]

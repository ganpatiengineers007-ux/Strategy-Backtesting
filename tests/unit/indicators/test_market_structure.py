from data.models import Bar
from indicators.market_structure import pivot_highs


def test_pivot_is_confirmed_after_right_bars():
    highs = [1, 2, 5, 2, 1, 2, 3]
    bars = [Bar(f"2024-01-01T09:{i:02d}:00", h, h, h, h) for i, h in enumerate(highs)]
    p = pivot_highs(bars, 2, 2)
    assert p == [{"index": 2, "confirm_index": 4, "price": 5}]

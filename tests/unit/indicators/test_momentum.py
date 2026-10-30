from indicators.momentum import roc, rsi


def test_rsi_bounds_and_roc():
    up = rsi([float(i) for i in range(1, 30)], 14)
    assert up[14] == 100.0 and up[0] is None
    mixed = [x for x in rsi([10, 11, 10.5, 12, 11, 13, 12, 14, 13, 15, 14, 16, 15, 17, 16, 18], 14) if x is not None]
    assert all(0 <= x <= 100 for x in mixed)
    assert roc([100, 110], 1) == [None, 10.000000000000009] or abs(roc([100, 110], 1)[1] - 10) < 1e-9

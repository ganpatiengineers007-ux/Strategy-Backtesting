import math

from engines.bindings import native
from engines.reference.rolling_stats import rolling_mean as ref


def test_native_matches_reference():
    vals = [1.0, 2.0, 3.0, 4.0, 5.0, 9.0, 2.5]
    a, b = native.rolling_mean(vals, 3), ref(vals, 3)
    assert len(a) == len(b)
    for x, y in zip(a, b):
        assert (math.isnan(x) and math.isnan(y)) or abs(x - y) < 1e-9


def test_known_values():  # C++ aur Rust tests me bhi yahi values hain
    r = ref([1, 2, 3, 4, 5], 3)
    assert math.isnan(r[0]) and math.isnan(r[1]) and r[2:] == [2.0, 3.0, 4.0]

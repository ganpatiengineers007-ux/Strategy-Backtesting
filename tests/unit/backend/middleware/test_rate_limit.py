from backend.middleware.rate_limit import SlidingWindowLimiter


def test_sliding_window_blocks_and_recovers():
    limiter = SlidingWindowLimiter(limit=2, window_seconds=60)
    assert limiter.allow("a", now=1)
    assert limiter.allow("a", now=2)
    assert not limiter.allow("a", now=3)
    assert limiter.allow("b", now=3)
    assert limiter.allow("a", now=62)
    assert limiter.retry_after("a", now=4) >= 1


def test_zero_limit_disables():
    limiter = SlidingWindowLimiter(limit=0)
    assert all(limiter.allow("x", now=i) for i in range(10))

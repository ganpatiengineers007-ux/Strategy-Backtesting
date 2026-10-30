from observability.health import check_health


def test_health_ok():
    h = check_health()
    assert h["status"] == "ok" and h["strategies"] >= 2

from data.survivorship import check


def test_statuses():
    assert check({"2020-01-01": ["A"]})["status"] == "UNAVAILABLE"
    assert check({"2020-01-01": ["A", "B"], "2024-01-01": ["A", "B"]})["status"] == "WARN"
    r = check({"2020-01-01": ["A", "B"], "2024-01-01": ["A", "C"]})
    assert r["status"] == "PASS" and r["dropped"] == ["B"] and r["added"] == ["C"] and r["churn_pct"] == 50.0

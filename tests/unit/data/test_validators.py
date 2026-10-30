from data.models import Bar
from data.validators import validate


def codes(bars):
    return {i["code"] for i in validate(bars)}


def test_inconsistent_ohlc_and_duplicates():
    assert "OHLC_INCONSISTENT" in codes([Bar("2024-01-01T09:15:00", 100, 90, 95, 99)])
    ok = Bar("2024-01-01T09:15:00", 100, 101, 99, 100)
    assert "DUPLICATE_TS" in codes([ok, ok])


def test_clean_data_has_no_issues():
    assert validate([Bar("2024-01-01T09:15:00", 100, 101, 99, 100), Bar("2024-01-01T09:20:00", 100, 102, 99, 101)]) == []

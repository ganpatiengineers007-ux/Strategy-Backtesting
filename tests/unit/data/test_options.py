from data.options import days_to_expiry, quality_status, validate_chain

GOOD = {"ts": "2024-01-01T09:15:00", "underlying": "NIFTY", "expiry": "2024-01-04", "strike": 21000, "option_type": "CE",
        "lot_size": 25, "bid": 100.0, "ask": 101.0}


def test_good_row_and_days():
    assert validate_chain([GOOD]) == [] and quality_status([]) == "PASS"
    assert days_to_expiry("2024-01-01T09:15:00", "2024-01-04") == 3


def test_bad_rows_flagged():
    bad = [dict(GOOD, strike=0), dict(GOOD, lot_size=0), dict(GOOD, option_type="XX"), dict(GOOD, expiry="2023-12-01"),
           dict(GOOD, bid=5, ask=1), dict(GOOD, expiry=""), dict(GOOD, expiry="not-a-date")]
    codes = [i["code"] for i in validate_chain(bad)]
    assert codes == ["BAD_STRIKE", "BAD_LOT_SIZE", "BAD_OPTION_TYPE", "EXPIRED_CONTRACT", "BAD_BID_ASK", "MISSING_FIELDS", "BAD_VALUE"]
    assert quality_status(validate_chain(bad)) == "BLOCKED"

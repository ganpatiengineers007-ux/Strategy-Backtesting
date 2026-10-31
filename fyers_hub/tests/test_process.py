import math
from datetime import datetime

from fyers_hub.process.greeks import bs_price, greeks, implied_vol
from fyers_hub.process.quality import check_candles
from fyers_hub.process.resample import bucket_start, derive, norm_tf, parse_tf, pick_base, resample, weekday_index
from fyers_hub.process.ticks import TickAggregator
from fyers_hub.storage.db import upsert_candles
from fyers_hub.timeutil import IST


def ist(y, m, d, hh=0, mm=0, ss=0):
    return int(datetime(y, m, d, hh, mm, ss, tzinfo=IST).timestamp())


def minute_rows(day, n=375, start=(9, 15), price=100.0):
    t0 = ist(*day, *start)
    return [(t0 + 60 * i, price + i, price + i + 1, price + i - 1, price + i + 0.5, 10) for i in range(n)]


def test_parse_and_norm():
    assert parse_tf("5S") == ("s", 5) and parse_tf("15") == ("m", 15) and parse_tf("15D") == ("d", 15)
    assert norm_tf("1D") == "D" and norm_tf("d") == "D"


def test_5m_anchored_at_915_and_ohlcv():
    rows = minute_rows((2025, 1, 6), n=15)
    out = resample(rows, "5", 555)
    assert len(out) == 3
    assert out[0][0] == ist(2025, 1, 6, 9, 15)
    assert out[0][1] == rows[0][1] and out[0][4] == rows[4][4]
    assert out[0][2] == max(r[2] for r in rows[:5]) and out[0][3] == min(r[3] for r in rows[:5])
    assert out[0][5] == 50


def test_full_day_counts():
    rows = minute_rows((2025, 1, 6))
    assert len(resample(rows, "5", 555)) == 75
    assert len(resample(rows, "15", 555)) == 25
    assert len(resample(rows, "60", 555)) == 7  # 09:15 ... 15:15 (aakhri adhoori)
    assert bucket_start(ist(2025, 1, 6, 9, 20), "15", 555) == ist(2025, 1, 6, 9, 15)


def test_15_weekday_blocks_are_deterministic():
    from collections import Counter
    from datetime import date, timedelta

    t, rows = date(2025, 1, 6), []
    while len(rows) < 45:
        if t.weekday() < 5:
            rows.append((ist(t.year, t.month, t.day, 0, 0), 10, 11, 9, 10.5, 100))
        t += timedelta(days=1)
    out = resample(rows, "15D")
    expected = Counter(weekday_index(date.fromtimestamp(r[0] + 43200)) // 15 for r in rows)
    assert [o[5] for o in out] == [100 * expected[k] for k in sorted(expected)]
    # shuru ke kuch din hata do - baaki buckets ka total wahi rehta hai (bucket tareekh se bandhe hain)
    out2 = resample(rows[3:], "15D")
    assert out2[-1][5] == out[-1][5] and out2[-2][5] == out[-2][5]


def test_pick_base():
    assert pick_base("5", ["1", "D"]) == "1"
    assert pick_base("15", ["1", "5"]) == "5"
    assert pick_base("15D", ["1", "D"]) == "D"
    assert pick_base("10S", ["5S", "1"]) == "5S"
    assert pick_base("7", ["5", "1"]) == "1"  # 7 min = 5 ka multiple nahi
    assert pick_base("1", ["1"]) is None


def test_derive_in_db(conn):
    upsert_candles(conn, "NSE:SBIN-EQ", "1", minute_rows((2025, 1, 6)))
    assert derive(conn, "NSE:SBIN-EQ", "5") == 75
    n = conn.execute("SELECT COUNT(*), MIN(derived) FROM candles WHERE tf='5'").fetchone()
    assert n == (75, 1)


def test_mcx_session_anchor():
    rows = minute_rows((2025, 1, 6), n=10, start=(9, 0))
    out = resample(rows, "5", 540)
    assert out[0][0] == ist(2025, 1, 6, 9, 0)


def test_greeks_parity_and_iv_roundtrip():
    S, K, T, r, q = 24000.0, 24100.0, 7 / 365, 0.07, 0.0
    c, p = bs_price(S, K, T, r, q, 0.15, True), bs_price(S, K, T, r, q, 0.15, False)
    assert math.isclose(c - p, S * math.exp(-q * T) - K * math.exp(-r * T), rel_tol=1e-9)
    iv = implied_vol(c, S, K, T, r, q, True)
    assert math.isclose(iv, 0.15, abs_tol=1e-4)
    g = greeks(S, K, T, r, q, 0.15, True)
    gp = greeks(S, K, T, r, q, 0.15, False)
    assert 0 < g["delta"] < 1 and -1 < gp["delta"] < 0
    assert math.isclose(g["delta"] - gp["delta"], math.exp(-q * T), abs_tol=1e-9)
    assert g["gamma"] > 0 and g["vega"] > 0 and g["theta"] < 0
    assert implied_vol(0.0001, S, K, T, r, q, True) is None or implied_vol(0.0001, S, K, T, r, q, True) < 0.1
    assert implied_vol(1.0, S, K, 0, r, q, True) is None


def test_quality():
    rows = [(1, 10, 9, 11, 10, 5), (2, 10, 11, 9, 10, -1), (2, 10, 11, 9, 10, 1)]
    r = check_candles(rows, "NSE:X-EQ", "5S")
    assert r["bad_ohlc"] == 1 and r["negative_volume"] == 1 and r["duplicates"] == 1
    day = minute_rows((2025, 1, 6), n=100)
    assert check_candles(day, "NSE:X-EQ", "1")["short_days"]


def test_tick_aggregator_5s_and_1m():
    bars = []
    agg = TickAggregator(("5S", "1"), on_bar=lambda s, tf, b: bars.append((tf, b)))
    t0 = ist(2025, 1, 6, 9, 15, 0)
    ticks = [(0, 100, 1000), (2, 101, 1010), (4, 99, 1015), (5, 102, 1030), (61, 103, 1100)]
    for dt, px, cum in ticks:
        agg.add("NSE:SBIN-EQ", t0 + dt, px, cum)
    fives = [b for tf, b in bars if tf == "5S"]
    assert fives[0] == (t0, 100, 101, 99, 99, 15)
    assert [b for tf, b in bars if tf == "1"][0][0] == t0
    agg.flush()
    assert any(tf == "1" and b[0] == t0 + 60 for tf, b in bars)

import os
from datetime import date

from fyers_hub import cli
from fyers_hub.client.api import ApiError, FyersApi
from fyers_hub.client.limiter import RateLimiter
from fyers_hub.ingest import instruments
from fyers_hub.ingest.chain import snapshot_chain
from fyers_hub.ingest.history import backfill, plan_chunks
from fyers_hub.ingest.live import run_live
from fyers_hub.ingest.quotes import poll_quotes
from fyers_hub.serve.hub import DataHub
from fyers_hub.settings import get_settings
from fyers_hub.timeutil import IST
from datetime import datetime

SYM = "NSE:SBIN-EQ"


def ist(y, m, d, hh=0, mm=0):
    return int(datetime(y, m, d, hh, mm, tzinfo=IST).timestamp())


class FakeModel:
    def __init__(self):
        self.calls = []
        self.chain_expiries = [ist(2025, 1, 9, 10), ist(2025, 1, 16, 10)]

    def history(self, data):
        self.calls.append(("history", data["resolution"], data["range_from"], data["range_to"]))
        if data["resolution"] == "D":
            return {"s": "ok", "candles": [[ist(2025, 1, 6), 100, 110, 95, 105, 1000],
                                          [ist(2025, 1, 7), 105, 112, 101, 108, 900]]}
        t0 = ist(2025, 1, 6, 9, 15)
        return {"s": "ok", "candles": [[t0 + 60 * i, 100 + i, 101 + i, 99 + i, 100.5 + i, 10] for i in range(375)]}

    def quotes(self, data):
        return {"s": "ok", "d": [{"n": s, "s": "ok", "v": {"lp": 101.5, "open_price": 100, "high_price": 102,
                                                              "low_price": 99, "prev_close_price": 100, "volume": 5000,
                                                              "chp": 1.5, "bid": 101.4, "ask": 101.6, "tt": 1}}
                                for s in data["symbols"].split(",")]}

    def optionchain(self, data):
        self.calls.append(("chain", data["timestamp"]))
        items = [{"symbol": "NSE:NIFTY50-INDEX", "option_type": "", "strike_price": -1, "ltp": 24000}]
        for k in (23900, 24000, 24100):
            for ot, px in (("CE", max(24000 - k, 0) + 120), ("PE", max(k - 24000, 0) + 110)):
                items.append({"symbol": f"NSE:NIFTYX{k}{ot}", "option_type": ot, "strike_price": k, "ltp": px,
                              "bid": px - 1, "ask": px + 1, "oi": 1000, "oich": 10, "volume": 500})
        return {"s": "ok", "data": {"optionsChain": items,
                                    "expiryData": [{"date": "x", "expiry": str(e)} for e in self.chain_expiries]}}

    def get_profile(self):
        return {"s": "ok", "data": {}}


def make_api(model=None):
    return FyersApi(model=model or FakeModel(), limiter=RateLimiter(1000, 100000), sleep=lambda x: None)


def test_plan_chunks():
    ch = plan_chunks(date(2024, 1, 1), date(2024, 12, 31), "1")
    assert ch[0][0] == date(2024, 1, 1) and ch[-1][1] == date(2024, 12, 31)
    assert all((b - a).days < 100 for a, b in ch) and len(ch) == 4


def test_api_parsing_and_errors():
    api = make_api()
    rows = api.history(SYM, "D", date(2025, 1, 1), date(2025, 1, 31))
    assert rows[0] == (ist(2025, 1, 6), 100.0, 110.0, 95.0, 105.0, 1000.0)
    q = api.quotes([SYM, "NSE:TCS-EQ"])
    assert q[0]["symbol"] == SYM and q[0]["ltp"] == 101.5

    class Bad:
        def history(self, data):
            return {"s": "error", "message": "limit exceeded"}

    try:
        make_api(Bad()).history(SYM, "1", date(2025, 1, 1), date(2025, 1, 2))
        assert False
    except ApiError:
        pass


def test_backfill_resume_and_derive(conn):
    m = FakeModel()
    api = make_api(m)
    summ = backfill(api, conn, [SYM], ["1", "D"], date(2025, 1, 1), date(2025, 1, 31), derive_tfs=["5", "15D"],
                    progress=lambda s: None, today=date(2025, 2, 1))
    assert summ[SYM]["1"] == 375 and summ[SYM]["D"] == 2 and summ[SYM]["5"] == 75
    n_calls = len(m.calls)
    backfill(api, conn, [SYM], ["1", "D"], date(2025, 1, 1), date(2025, 1, 31), progress=lambda s: None,
             today=date(2025, 2, 1))
    assert len(m.calls) == n_calls  # poore ho chuke chunk dobara nahi khinche


def test_hub_candles_auto_derive_and_range(conn):
    api = make_api()
    backfill(api, conn, [SYM], ["1", "D"], date(2025, 1, 1), date(2025, 1, 31), progress=lambda s: None,
             today=date(2025, 2, 1))
    hub = DataHub(conn=conn)
    assert len(hub.candles(SYM, "1")) == 375
    assert len(hub.candles(SYM, "7")) == 54  # stored nahi - 1m se on-the-fly (375/7 upar se 54 buckets)
    assert len(hub.candles(SYM, "5", start="2025-01-06", end="2025-01-06")) == 75
    assert hub.candles(SYM, "5", start="2025-01-07") == []
    assert len(hub.candles(SYM, "1", limit=10)) == 10
    assert list(hub.iter_bars(SYM, "D"))[0].close == 105.0
    assert hub.coverage()[0][0] == SYM


def test_quotes_and_live_loop(conn):
    api = make_api()
    assert poll_quotes(api, conn, [SYM]) == 1
    assert DataHub(conn=conn).latest_quote(SYM)["ltp"] == 101.5
    tick = [ist(2025, 1, 6, 10, 0)]
    run_live(api, conn, [SYM], ["NSE:NIFTY50-INDEX"], derive_tfs=["5"], max_cycles=2, now=lambda: tick[0] + 0,
             sleep=lambda s: tick.__setitem__(0, tick[0] + 100), log=lambda m: None)
    assert DataHub(conn=conn).candles(SYM, "1")  # live candles aayi
    assert conn.execute("SELECT COUNT(*) FROM option_chain").fetchone()[0] > 0


def test_option_chain_greeks_and_hub(conn):
    api = make_api()
    ts = ist(2025, 1, 6, 11, 0)
    n = snapshot_chain(api, conn, "NSE:NIFTY50-INDEX", n_expiries=2, ts=ts)
    assert n == 12  # 3 strikes x CE/PE x 2 expiries
    hub = DataHub(conn=conn)
    assert len(hub.expiries("NSE:NIFTY50-INDEX")) == 2
    chain = hub.option_chain("NSE:NIFTY50-INDEX")
    assert len(chain) == 6 and chain[0]["spot"] == 24000
    ce = next(r for r in chain if r["strike"] == 24000 and r["opt_type"] == "CE")
    pe = next(r for r in chain if r["strike"] == 24000 and r["opt_type"] == "PE")
    assert ce["iv"] and 0.3 < ce["delta"] < 0.7 and pe["delta"] < 0 and ce["gamma"] > 0 and ce["theta"] < 0
    second = hub.option_chain("NSE:NIFTY50-INDEX", expiry="2025-01-16")
    assert len(second) == 6 and second[0]["expiry"] != chain[0]["expiry"]
    atm = hub.atm("NSE:NIFTY50-INDEX")
    assert atm["strike"] == 24000 and atm["CE"]["opt_type"] == "CE"


def test_instruments_parse(conn):
    row = lambda *c: ",".join(c)  # noqa: E731
    text = "\n".join([
        row("1010000000001", "SBIN-EQ", "0", "1", "0.05", "INE062A01020", "0915-1530", "2025-01-01", "", "NSE:SBIN-EQ"),
        row("1011000000002", "NIFTY 25 Jan 23500 CE", "14", "75", "0.05", "", "0915-1530", "2025-01-01", "1737966600",
            "NSE:NIFTY25JAN23500CE"),
    ])
    rows = list(instruments.parse_master(text, "NSE_FO"))
    assert rows[0]["symbol"] == "NSE:SBIN-EQ" and rows[0]["lot_size"] == 1
    assert rows[1]["strike"] == 23500.0 and rows[1]["option_type"] == "CE" and rows[1]["underlying"] == "NIFTY"
    assert instruments.load_into_db(conn, "NSE_FO", text) == 2
    assert DataHub(conn=conn).universe("equity") == ["NSE:SBIN-EQ"]


def test_cli_init_and_doctor():
    s = get_settings()
    assert cli.main(["init"]) == 0
    assert (s.home / ".env").exists() and s.db_path.exists()
    assert oct(os.stat(s.home / ".env").st_mode & 0o777) == "0o600"
    assert cli.main(["doctor"]) == 0
    assert cli.main(["derive", "--symbols", SYM, "--to", "5"]) == 0

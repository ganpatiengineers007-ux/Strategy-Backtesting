"""/hub/* handlers: asli (temp) hub DB par."""
import time

from fyers_hub.storage import db as dbm


def _seed(path):
    conn = dbm.connect(path)
    now = int(time.time())
    dbm.upsert_candles(conn, "NSE:X-EQ", "1", [(now - 120, 1, 2, 0.5, 1.5, 10), (now - 60, 1.5, 2.5, 1, 2, 12)])
    conn.execute("INSERT INTO quotes VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ("NSE:X-EQ", 2.0, 1, 2.5, 0.5, 1, 100, 1.5, 1.9, 2.1, now, now))
    row = ("NSE:X-INDEX", now + 86400, 100.0, "CE", now, "SYM", 101.0, 3.0, 2.9, 3.1, 500.0, 5.0, 50.0, 0.2, 0.5, 0.01, -0.1, 0.2, 0.0)
    conn.execute("INSERT INTO option_chain VALUES (" + ",".join("?" * 19) + ")", row)
    conn.commit()
    conn.close()


def test_hub_handlers(tmp_path, monkeypatch):
    from backend.api import hub

    db = tmp_path / "hub.db"
    monkeypatch.setenv("HUB_DB_PATH", str(db))
    _seed(db)
    s = hub.status()
    assert s["quotes"] == 1 and s["candle_series"] == 1 and s["last_quote_age_s"] <= 5
    assert hub.quotes(10)[0]["symbol"] == "NSE:X-EQ"
    assert hub.coverage()[0]["rows"] == 2
    c = hub.candles("NSE:X-EQ", "1", 10)
    assert len(c) == 2 and c[-1][4] == 2
    ch = hub.chain("NSE:X-INDEX")
    assert ch["spot"] == 101.0 and ch["rows"][0]["opt_type"] == "CE"


def test_hub_empty_db(tmp_path, monkeypatch):
    from backend.api import hub

    monkeypatch.setenv("HUB_DB_PATH", str(tmp_path / "empty.db"))
    assert hub.status()["last_quote_age_s"] is None
    assert hub.chain("NSE:NOPE-INDEX") == {"underlying": "NSE:NOPE-INDEX", "spot": None, "rows": []}
    assert hub.candles("NSE:NOPE-EQ", "1") == []

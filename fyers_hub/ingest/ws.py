"""Websocket live feed (Fyers SDK) -> ticks -> 5-second / 1-minute candles -> hub.
NOTE: ye hissa Fyers ke live market me hi test ho sakta hai (offline tests me sirf TickAggregator test hota hai)."""
from __future__ import annotations

import threading
import time

from fyers_hub.auth import flow
from fyers_hub.process.ticks import TickAggregator
from fyers_hub.storage import db as dbm


def run_ws(settings, symbols: list[str], tfs=("5S", "1"), log=print) -> None:
    try:
        from fyers_apiv3.FyersWebsocket import data_ws
    except ImportError as e:
        raise RuntimeError("fyers-apiv3 install nahi hai: pip install fyers-apiv3") from e

    tok = flow.ensure_token(settings)
    conn = dbm.connect(settings.db_path, check_same_thread=False)
    lock = threading.Lock()

    def save(symbol, tf, bar):
        with lock:
            dbm.upsert_candles(conn, symbol, tf, [bar])

    agg = TickAggregator(tfs, on_bar=save)

    def on_message(msg):
        if not isinstance(msg, dict) or "ltp" not in msg or not msg.get("symbol"):
            return
        ts = int(msg.get("last_traded_time") or msg.get("exch_feed_time") or time.time())
        agg.add(msg["symbol"], ts, float(msg["ltp"]), msg.get("vol_traded_today"))

    sock = data_ws.FyersDataSocket(
        access_token=f"{settings.app_id}:{tok.access_token}", log_path=str(settings.log_dir), litemode=False,
        write_to_file=False, reconnect=True,
        on_connect=lambda: (sock.subscribe(symbols=symbols, data_type="SymbolUpdate"), log("ws connected")),
        on_close=lambda m: log("ws closed"), on_error=lambda m: log(f"ws error: {m}"), on_message=on_message,
    )
    sock.connect()
    try:
        sock.keep_running()
    except KeyboardInterrupt:
        pass
    except Exception as e:  # noqa: BLE001
        import logging
        log = logging.getLogger("fyers_hub.ingest.ws")
        log.exception("WebSocket keep_running error")
    finally:
        agg.flush()

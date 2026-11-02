"""Live loop (polling): bhav + option chain + aaj ki 1-minute candles. Market band ho to chup rehta hai.
5-second jaisi tez candles ke liye ws.py (websocket) use karo."""
from __future__ import annotations

import time
from datetime import date
from typing import Callable

from fyers_hub.ingest.chain import snapshot_chain
from fyers_hub.ingest.quotes import poll_quotes
from fyers_hub.process.resample import derive, parse_tf
from fyers_hub.storage.db import upsert_candles
from fyers_hub.timeutil import ist_date, is_market_open, day_start_epoch


def safe_since(tf, now):
    """derive() ke liye since_ts. Purana window (now - 3 din) candles kharab karta tha.

    Minute/second tf: din ki shuruaat se. Session open (09:15) se pehle koi candle nahi hoti,
    isliye din ke andar ke sab bucket poore rahte hain. Daily-based tf (jaise 15D): None = poori
    history, kyunki adhoora window ka block pehle se saved candle ko overwrite karta tha.
    """
    if parse_tf(tf)[0] == "d":
        return None
    return day_start_epoch(ist_date(now))


def run_live(api, conn, watchlist: list[str], underlyings: list[str], derive_tfs=(), quote_every: int = 5,
             chain_every: int = 60, candle_every: int = 60, candle_symbols: list[str] | None = None,
             rate: float = 0.07, n_expiries: int = 2, max_cycles: int | None = None,
             now: Callable[[], float] = time.time, sleep: Callable[[float], None] = time.sleep,
             log: Callable[[str], None] = print) -> None:
    candle_symbols = watchlist if candle_symbols is None else candle_symbols
    last = {"q": 0.0, "c": 0.0, "k": 0.0}
    cycles = 0
    while max_cycles is None or cycles < max_cycles:
        cycles += 1
        t = now()
        open_syms = [s for s in watchlist if is_market_open(s, t)]
        if open_syms:
            if t - last["q"] >= quote_every:
                last["q"] = t
                try:
                    poll_quotes(api, conn, open_syms)
                except Exception as e:  # noqa: BLE001
                    log(f"quotes error: {e}")
            if t - last["c"] >= chain_every:
                last["c"] = t
                for u in underlyings:
                    if is_market_open(u, t):
                        try:
                            snapshot_chain(api, conn, u, n_expiries=n_expiries, rate=rate, ts=int(t))
                        except Exception as e:  # noqa: BLE001
                            log(f"chain {u} error: {e}")
            if t - last["k"] >= candle_every:
                last["k"] = t
                today = ist_date(t)
                for s in candle_symbols:
                    if not is_market_open(s, t):
                        continue
                    try:
                        upsert_candles(conn, s, "1", api.history(s, "1", today, today))
                        for tf in derive_tfs:
                            derive(conn, s, tf, since_ts=safe_since(tf, t))
                    except Exception as e:  # noqa: BLE001
                        log(f"candles {s} error: {e}")
        sleep(1)

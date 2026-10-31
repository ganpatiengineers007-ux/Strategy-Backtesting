"""Live ticks (LTP + din ka cumulative volume) se candles banana - 5 second, 1 minute, koi bhi tf."""
from __future__ import annotations

from typing import Callable

from fyers_hub.process.resample import bucket_start, norm_tf
from fyers_hub.timeutil import session_for


class TickAggregator:
    def __init__(self, tfs=("5S", "1"), on_bar: Callable[[str, str, tuple], None] | None = None):
        self.tfs = [norm_tf(t) for t in tfs]
        self.on_bar = on_bar or (lambda sym, tf, bar: None)
        self._cur: dict = {}      # (symbol, tf) -> [bucket, o, h, l, c, v]
        self._last_cum: dict = {}  # symbol -> cumulative volume

    def add(self, symbol: str, ts: int, ltp: float, cum_volume: float | None = None) -> None:
        vol = 0.0
        if cum_volume is not None:
            prev = self._last_cum.get(symbol)
            if prev is None:
                vol = 0.0  # pehla tick: din ka purana volume is candle me mat jodo
            else:
                vol = cum_volume - prev if cum_volume >= prev else cum_volume  # naya din: cumulative reset
            self._last_cum[symbol] = cum_volume
        open_min, _ = session_for(symbol)
        for tf in self.tfs:
            b = bucket_start(ts, tf, open_min)
            key = (symbol, tf)
            cur = self._cur.get(key)
            if cur is None or cur[0] != b:
                if cur is not None:
                    self.on_bar(symbol, tf, tuple(cur))
                self._cur[key] = [b, ltp, ltp, ltp, ltp, vol]
            else:
                cur[2] = max(cur[2], ltp)
                cur[3] = min(cur[3], ltp)
                cur[4] = ltp
                cur[5] += vol

    def flush(self) -> None:
        """Din ke end par bachi hui (adhuri) candles bhi bhej do."""
        for (symbol, tf), cur in list(self._cur.items()):
            self.on_bar(symbol, tf, tuple(cur))
        self._cur.clear()

    def forming(self, symbol: str, tf: str) -> tuple | None:
        cur = self._cur.get((symbol, norm_tf(tf)))
        return tuple(cur) if cur else None

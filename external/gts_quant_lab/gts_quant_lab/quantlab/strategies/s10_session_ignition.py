"""Session-open volatility ignition (Tokyo / London / New York). Opening range + volume surge breakout,
pure price/time/volume. One trade per session, flat at window end or if price closes back inside the range."""
from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
from .base import Strategy

SESSIONS = {"tokyo": 0, "london": 8 * 60, "newyork": 13 * 60 + 30}   # UTC minute-of-day


@dataclass
class SessionConfig:
    or_min: int = 5
    trade_min: int = 35
    vol_mult: float = 1.5
    base_win: int = 60
    sessions: tuple = ("tokyo", "london", "newyork")


class SessionIgnitionStrategy(Strategy):
    name = "S10 Session-Open Ignition"

    def __init__(self, cfg: SessionConfig | None = None):
        self.cfg = cfg or SessionConfig()

    def positions(self, bars) -> np.ndarray:
        c = self.cfg
        n = bars.n
        pos = np.zeros(n)
        mod = ((bars.ts % 86400) // 60).astype(int)
        for name in c.sessions:
            for i0 in np.nonzero(mod == SESSIONS[name])[0]:
                i1 = i0 + c.or_min
                end = min(i0 + c.trade_min, n)
                if i0 < c.base_win or i1 >= n:
                    continue
                or_hi, or_lo = bars.high[i0:i1].max(), bars.low[i0:i1].min()
                base_vol = np.median(bars.volume[i0 - c.base_win:i0])
                cur = 0
                for i in range(i1, end):
                    if cur == 0:
                        surge = bars.volume[i] >= c.vol_mult * base_vol
                        if surge and bars.close[i] > or_hi:
                            cur = 1
                        elif surge and bars.close[i] < or_lo:
                            cur = -1
                        if cur == 0:
                            continue
                    elif (cur == 1 and bars.close[i] < or_hi) or (cur == -1 and bars.close[i] > or_lo):
                        break
                    pos[i] = cur
        return pos

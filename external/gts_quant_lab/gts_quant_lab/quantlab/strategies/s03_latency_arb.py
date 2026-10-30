"""Singapore style - cross-venue latency arbitrage + liquidity-sweep (stop-run) reversal."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from .base import Strategy
from ..utils import rmax, rmin, rmean, shift, to_position


def estimate_lead_lag(a, b, max_lag: int = 20) -> int:
    """k>0 => venue A leads venue B by k ticks (argmax of corr(ra[t], rb[t+k]))."""
    ra, rb = np.diff(a), np.diff(b)
    best, bk = -2.0, 0
    for k in range(0, max_lag + 1):
        x, y = (ra[:len(ra) - k], rb[k:]) if k else (ra, rb)
        c = np.corrcoef(x, y)[0, 1]
        if c > best:
            best, bk = c, k
    return bk


@dataclass
class LatencyArbConfig:
    enter_bps: float = 2.0     # must exceed fees + half-spread + safety
    exit_bps: float = 0.5
    max_hold: int = 30


class LatencyArbStrategy(Strategy):
    """data = (lead_mid, lag_mid). Trades the lagging venue toward the leader's price."""
    name = "S03a Cross-Venue Latency Arb (Singapore)"

    def __init__(self, cfg: LatencyArbConfig | None = None):
        self.cfg = cfg or LatencyArbConfig()

    def positions(self, data) -> np.ndarray:
        lead, lag = (np.asarray(d, float) for d in data)
        edge_bps = (lead - lag) / lag * 1e4
        return to_position(edge_bps, self.cfg.enter_bps, self.cfg.exit_bps, self.cfg.max_hold)


@dataclass
class SweepConfig:
    lookback: int = 30
    vol_mult: float = 2.0
    wick_ratio: float = 0.5
    max_hold: int = 8


class LiquiditySweepStrategy(Strategy):
    """Wick beyond the prior swing high/low on a volume spike that closes back inside => fade the stop-run."""
    name = "S03b Liquidity Sweep Reversal (Singapore)"

    def __init__(self, cfg: SweepConfig | None = None):
        self.cfg = cfg or SweepConfig()

    def positions(self, bars) -> np.ndarray:
        c = self.cfg
        ref_hi, ref_lo = shift(rmax(bars.high, c.lookback), 1, np.nan), shift(rmin(bars.low, c.lookback), 1, np.nan)
        vbase = shift(rmean(bars.volume, c.lookback), 1, np.nan)
        rng = np.maximum(bars.high - bars.low, 1e-12)
        up_wick = (bars.high - np.maximum(bars.open, bars.close)) / rng
        dn_wick = (np.minimum(bars.open, bars.close) - bars.low) / rng
        spike = bars.volume > c.vol_mult * vbase
        sweep_up = (bars.high > ref_hi) & (bars.close < ref_hi) & spike & (up_wick > c.wick_ratio)
        sweep_dn = (bars.low < ref_lo) & (bars.close > ref_lo) & spike & (dn_wick > c.wick_ratio)
        pos = np.zeros(bars.n)
        cur, held, stop = 0, 0, 0.0
        for i in range(bars.n):
            if cur != 0:
                held += 1
                if held >= c.max_hold or (cur == -1 and bars.close[i] > stop) or (cur == 1 and bars.close[i] < stop):
                    cur = 0
            if cur == 0:
                if sweep_up[i]:
                    cur, held, stop = -1, 0, bars.high[i]
                elif sweep_dn[i]:
                    cur, held, stop = 1, 0, bars.low[i]
            pos[i] = cur
        return pos

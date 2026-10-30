"""Multi-feature neural reversal model with 4-phase confirmation gate and embargoed walk-forward training."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from .base import Strategy
from ..ml import walk_forward_probs
from ..utils import rmean, rstd, rmax, rmin, shift, zscore, EPS


@dataclass
class ReversalConfig:
    horizon: int = 5
    z_win: int = 50
    exhaust_z: float = 0.8
    vol_z: float = 0.0
    p_thr: float = 0.53
    min_train: int = 400
    retrain_every: int = 150
    epochs: int = 30
    hold: int = 5


def reversal_features(b) -> np.ndarray:
    c, o, h, l = b.close, b.open, b.high, b.low
    r1 = np.diff(c, prepend=c[0]) / c
    r5 = (c - shift(c, 5, c[0])) / c
    rng = (h - l) / c
    cols = [
        r1 / (rstd(r1, 50) + EPS),                                   # 1 bar-return z
        r5 / (rstd(r1, 50) * np.sqrt(5) + EPS),                      # 2 5-bar return z
        zscore(b.volume, 50),                                        # 3 volume z
        b.delta / (b.volume + EPS),                                  # 4 delta ratio
        rmean(b.delta, 5) / (rmean(b.volume, 5) + EPS),              # 5 smoothed delta ratio
        zscore(rng, 50),                                             # 6 range z
        (c - l) / np.maximum(h - l, 1e-12),                          # 7 close location
        b.obi,                                                       # 8 book imbalance
        zscore(b.spread, 50),                                        # 9 spread z
        zscore(b.ntrades, 50),                                       # 10 tick-rate z
        (c - rmean(c, 20)) / (rstd(c, 20) + EPS),                    # 11 distance to local mean
        rstd(r1, 5) / (rstd(r1, 50) + EPS),                          # 12 vol ratio
    ]
    return np.column_stack(cols)


class ReversalAIStrategy(Strategy):
    name = "S07 Multi-Feature Reversal AI (4-phase)"

    def __init__(self, cfg: ReversalConfig | None = None):
        self.cfg = cfg or ReversalConfig()

    def probs(self, b) -> np.ndarray:
        c = self.cfg
        X = reversal_features(b)
        y = np.full(b.n, np.nan)
        y[:-c.horizon] = (b.close[c.horizon:] > b.close[:-c.horizon]).astype(float)
        return walk_forward_probs(X, y, c.min_train, c.retrain_every, c.horizon, c.epochs)

    def phases(self, b):
        c = self.cfg
        X = reversal_features(b)
        p = self.probs(b)
        z5, vz, dr5 = X[:, 1], X[:, 2], X[:, 4]
        prev_c = shift(b.close, 1, b.close[0])
        p1_long, p1_short = z5 <= -c.exhaust_z, z5 >= c.exhaust_z            # exhaustion
        p2_long = (vz >= c.vol_z) & (dr5 > 0)                                # climax volume, buyers absorbing
        p2_short = (vz >= c.vol_z) & (dr5 < 0)
        p3_long, p3_short = p >= c.p_thr, p <= 1 - c.p_thr                   # model agrees
        p4_long = (b.close > b.open) & (b.close > prev_c)                    # confirmation bar
        p4_short = (b.close < b.open) & (b.close < prev_c)
        return (p1_long & p2_long & p3_long & p4_long), (p1_short & p2_short & p3_short & p4_short)

    def positions(self, b) -> np.ndarray:
        c = self.cfg
        long_, short_ = self.phases(b)
        pos = np.zeros(b.n)
        cur, held = 0, 0
        for i in range(b.n):
            if cur:
                held += 1
                if held >= c.hold:
                    cur = 0
            if cur == 0:
                if long_[i]:
                    cur, held = 1, 0
                elif short_[i]:
                    cur, held = -1, 0
            pos[i] = cur
        return pos

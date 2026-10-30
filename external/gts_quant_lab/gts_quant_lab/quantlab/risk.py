"""Risk overlays: volatility targeting, Kelly cap, drawdown kill-switch (latching)."""
from __future__ import annotations
import numpy as np
from .utils import rstd, EPS


def vol_scale(ret, target_ann_vol: float, ppy: float, win: int = 500, max_lev: float = 3.0) -> np.ndarray:
    sd = rstd(ret, win) * np.sqrt(ppy)
    s = np.clip(target_ann_vol / (sd + EPS), 0.0, max_lev)
    return np.where(np.isnan(s), 1.0, s)


def kelly_fraction(mean: float, var: float, cap: float = 0.25) -> float:
    return float(np.clip(0.5 * mean / (var + EPS), 0.0, cap))   # half-Kelly, capped


def apply_kill_switch(pnl, max_dd: float) -> np.ndarray:
    """Zero all pnl after equity drawdown >= max_dd (latched; needs manual reset in live)."""
    pnl = np.array(pnl, dtype=float)
    eq = np.cumprod(1.0 + pnl)
    dd = 1.0 - eq / np.maximum.accumulate(eq)
    hit = np.nonzero(dd >= max_dd)[0]
    if len(hit):
        pnl[hit[0] + 1:] = 0.0
    return pnl


class KillSwitch:
    """Live-style latch: trips on drawdown or daily loss; stays tripped until reset()."""
    def __init__(self, max_dd: float = 0.1, max_daily_loss: float = 0.03):
        self.max_dd, self.max_daily_loss = max_dd, max_daily_loss
        self.peak, self.day_start, self.tripped = 1.0, 1.0, False

    def new_day(self, equity: float):
        self.day_start = equity

    def update(self, equity: float) -> bool:
        self.peak = max(self.peak, equity)
        if 1 - equity / self.peak >= self.max_dd or 1 - equity / self.day_start >= self.max_daily_loss:
            self.tripped = True
        return self.tripped

    def reset(self):
        self.tripped = False

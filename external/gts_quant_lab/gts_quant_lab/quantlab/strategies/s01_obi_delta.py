"""US style - Order-book imbalance (depth-weighted L2) + cumulative-delta divergence."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from .base import Strategy
from ..utils import ema, rmax, rmin, shift, to_position


@dataclass
class OBIDeltaConfig:
    depth: int = 5
    decay: float = 0.5          # level weight exp(-decay*k): near levels matter more
    ema_span: int = 20
    div_win: int = 100
    div_weight: float = 0.4
    enter: float = 0.25
    exit: float = 0.05
    max_hold: int = 200


class OBIDeltaStrategy(Strategy):
    name = "S01 OBI + Delta Divergence (US)"

    def __init__(self, cfg: OBIDeltaConfig | None = None):
        self.cfg = cfg or OBIDeltaConfig()

    def features(self, book):
        c = self.cfg
        d = min(c.depth, book.levels)
        w = np.exp(-c.decay * np.arange(d))
        bid, ask = (book.bid_sz[:, :d] * w).sum(1), (book.ask_sz[:, :d] * w).sum(1)
        obi = ema((bid - ask) / (bid + ask + 1e-9), c.ema_span)
        cd = np.cumsum(book.trade_sz * book.trade_side)
        mid, h = book.mid, c.div_win // 2
        lo, hi = rmin(mid, c.div_win), rmax(mid, c.div_win)
        band = 0.1 * (hi - lo)
        pslope, dslope = mid - shift(mid, h), cd - shift(cd, h)
        bull = (mid <= lo + band) & (pslope < 0) & (dslope > 0)   # price weak, aggressive buying rising
        bear = (mid >= hi - band) & (pslope > 0) & (dslope < 0)
        div = np.nan_to_num(bull.astype(float) - bear.astype(float))
        return obi, div, cd

    def positions(self, book) -> np.ndarray:
        c = self.cfg
        obi, div, _ = self.features(book)
        return to_position(obi + c.div_weight * div, c.enter, c.exit, c.max_hold)

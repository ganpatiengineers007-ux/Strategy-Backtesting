"""Market data containers."""
from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np


@dataclass
class BookSeries:
    """Tick-level L2 snapshots + trade prints. Arrays are (n, levels) or (n,).
    trade_side: +1 buyer-aggressor, -1 seller-aggressor, 0 no trade at this tick."""
    ts: np.ndarray
    bid_px: np.ndarray
    bid_sz: np.ndarray
    ask_px: np.ndarray
    ask_sz: np.ndarray
    trade_px: np.ndarray
    trade_sz: np.ndarray
    trade_side: np.ndarray
    truth: dict = field(default_factory=dict)   # synthetic ground-truth labels (optional)

    @property
    def n(self) -> int:
        return len(self.ts)

    @property
    def levels(self) -> int:
        return self.bid_px.shape[1]

    @property
    def mid(self) -> np.ndarray:
        return 0.5 * (self.bid_px[:, 0] + self.ask_px[:, 0])

    @property
    def spread(self) -> np.ndarray:
        return self.ask_px[:, 0] - self.bid_px[:, 0]


@dataclass
class Bars:
    ts: np.ndarray
    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    volume: np.ndarray
    delta: np.ndarray      # signed aggressor volume
    ntrades: np.ndarray
    obi: np.ndarray        # mean book imbalance in the bar
    spread: np.ndarray

    @property
    def n(self) -> int:
        return len(self.ts)


def book_to_bars(book: BookSeries, ticks_per_bar: int) -> Bars:
    k = ticks_per_bar
    m = book.n // k
    sl = slice(0, m * k)
    mid = book.mid[sl].reshape(m, k)
    tsz = book.trade_sz[sl].reshape(m, k)
    tsd = book.trade_side[sl].reshape(m, k)
    bsz = book.bid_sz[sl, :3].sum(1)
    asz = book.ask_sz[sl, :3].sum(1)
    obi = ((bsz - asz) / (bsz + asz + 1e-9)).reshape(m, k).mean(1)
    return Bars(
        ts=book.ts[sl].reshape(m, k)[:, -1], open=mid[:, 0], high=mid.max(1), low=mid.min(1),
        close=mid[:, -1], volume=tsz.sum(1), delta=(tsz * tsd).sum(1),
        ntrades=(tsd != 0).sum(1).astype(float), obi=obi, spread=book.spread[sl].reshape(m, k).mean(1))

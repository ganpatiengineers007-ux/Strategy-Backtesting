"""Iceberg-order tracking: best level keeps refilling while being hit => hidden size; follow the hidden side."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from .base import Strategy
from ..utils import rsum, to_position


@dataclass
class IcebergConfig:
    win: int = 150
    min_events: int = 10
    ratio: float = 0.5
    refill_tol: float = 0.5
    max_hold: int = 150


class IcebergStrategy(Strategy):
    name = "S09 Iceberg Detection"

    def __init__(self, cfg: IcebergConfig | None = None):
        self.cfg = cfg or IcebergConfig()

    def refill_flags(self, book):
        c = self.cfg
        sz, side = book.trade_sz[1:], book.trade_side[1:]
        same_b = book.bid_px[1:, 0] >= book.bid_px[:-1, 0]      # bid held (did not fall) while being hit
        same_a = book.ask_px[1:, 0] <= book.ask_px[:-1, 0]
        d_b = book.bid_sz[1:, 0] - book.bid_sz[:-1, 0]
        d_a = book.ask_sz[1:, 0] - book.ask_sz[:-1, 0]
        sell, buy = side == -1, side == 1
        rb = sell & same_b & (d_b > -c.refill_tol * sz)       # sells hit bid but displayed size did not drop
        ra = buy & same_a & (d_a > -c.refill_tol * sz)
        pad = lambda x: np.concatenate(([False], x))
        return pad(sell), pad(rb), pad(buy), pad(ra)

    def score(self, book) -> np.ndarray:
        c = self.cfg
        sell, rb, buy, ra = (rsum(f.astype(float), c.win) for f in self.refill_flags(book))
        hidden_buyer = (sell >= c.min_events) & (rb / np.maximum(sell, 1) >= c.ratio)
        hidden_seller = (buy >= c.min_events) & (ra / np.maximum(buy, 1) >= c.ratio)
        s = hidden_buyer.astype(float) - hidden_seller.astype(float)
        return np.where(np.isnan(sell), np.nan, s)

    def positions(self, book) -> np.ndarray:
        return to_position(self.score(book), 1.0, 0.5, self.cfg.max_hold)

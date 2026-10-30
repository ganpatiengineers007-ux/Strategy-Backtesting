"""Russia style - microstructure signal processing: order-flow absorption, Kyle-lambda, VPIN toxicity filter."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from .base import Strategy
from ..utils import ema, rsum, rstd, shift, to_position, EPS


def vpin(trade_sz, trade_side, bucket_vol: float, n_buckets: int = 20) -> np.ndarray:
    """Volume-synchronised probability of informed trading, mapped back to tick index (causal)."""
    out = np.full(len(trade_sz), np.nan)
    buys = sells = 0.0
    hist = []
    for i, (v, s) in enumerate(zip(trade_sz, trade_side)):
        if s > 0:
            buys += v
        elif s < 0:
            sells += v
        if buys + sells >= bucket_vol:
            hist.append(abs(buys - sells) / (buys + sells)); buys = sells = 0.0
        if len(hist) >= n_buckets:
            out[i] = np.mean(hist[-n_buckets:])
        elif len(hist):
            out[i] = np.nan
    return out


def kyle_lambda(mid, signed_vol, win: int) -> np.ndarray:
    """Rolling price impact per unit signed volume: cov(dP, q) / var(q)."""
    dp = np.diff(mid, prepend=mid[0])
    n = len(mid)
    out = np.full(n, np.nan)
    sq, sp, sqq, sqp = rsum(signed_vol, win), rsum(dp, win), rsum(signed_vol ** 2, win), rsum(signed_vol * dp, win)
    cov = sqp / win - (sq / win) * (sp / win)
    var = sqq / win - (sq / win) ** 2
    out[:] = cov / (var + EPS)
    return out


@dataclass
class MicroConfig:
    win: int = 80
    flow_z: float = 1.0
    price_tol: float = 0.3
    smooth: int = 10
    enter: float = 0.6
    exit: float = 0.2
    max_hold: int = 150
    vpin_cut: float = 0.9      # >= this fraction of the running max VPIN -> halve size
    vpin_bucket: float = 400.0  # volume per VPIN bucket (calibrate to instrument; fixed => causal)


class MicrostructureStrategy(Strategy):
    name = "S04 Microstructure Absorption (Russia)"

    def __init__(self, cfg: MicroConfig | None = None):
        self.cfg = cfg or MicroConfig()

    def score(self, book) -> np.ndarray:
        c = self.cfg
        q = book.trade_sz * book.trade_side
        mid = book.mid
        dp = np.diff(mid, prepend=mid[0])
        zv = rsum(q, c.win) / (rstd(q, c.win) * np.sqrt(c.win) + EPS)
        zr = rsum(dp, c.win) / (rstd(dp, c.win) * np.sqrt(c.win) + EPS)
        buy_abs = (zv < -c.flow_z) & (zr > -c.price_tol)     # heavy selling, price does not fall
        sell_abs = (zv > c.flow_z) & (zr < c.price_tol)      # heavy buying, price does not rise
        raw = np.where(buy_abs | sell_abs, -zv, 0.0)
        return ema(np.nan_to_num(raw), c.smooth)

    def positions(self, book) -> np.ndarray:
        c = self.cfg
        pos = to_position(self.score(book), c.enter, c.exit, c.max_hold)
        v = vpin(book.trade_sz, book.trade_side, bucket_vol=c.vpin_bucket)
        # causal percentile: compare to expanding max of history instead of future-looking quantile
        hi = np.fmax.accumulate(np.nan_to_num(v))
        toxic = np.nan_to_num(v) >= c.vpin_cut * hi
        return np.where(toxic & (hi > 0), 0.5 * pos, pos)

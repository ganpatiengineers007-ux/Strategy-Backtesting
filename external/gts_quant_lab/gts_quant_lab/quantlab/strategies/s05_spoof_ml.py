"""Japan style - ML spoofing/layering detector. Large far-level size appears, vanishes unfilled => the
manipulator's real intent is the opposite side. Two MLPs (bullish / bearish aftermath), causal features."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from .base import Strategy
from ..ml import MLP
from ..utils import rmax, rmean, rsum, zscore, to_position, EPS


@dataclass
class SpoofConfig:
    win: int = 15
    base_win: int = 200
    train_frac: float = 0.6
    enter: float = 0.6
    exit: float = 0.3
    max_hold: int = 25
    epochs: int = 40
    pos_weight: float = 15.0


def spoof_features(book, win: int = 15, base_win: int = 200) -> np.ndarray:
    L = min(5, book.levels)
    far_b, far_a = book.bid_sz[:, 1:L].sum(1), book.ask_sz[:, 1:L].sum(1)
    sell_vol = np.where(book.trade_side == -1, book.trade_sz, 0.0)
    buy_vol = np.where(book.trade_side == 1, book.trade_sz, 0.0)
    cols = []
    for far, fills in ((far_b, sell_vol), (far_a, buy_vol)):
        peak = rmax(far, win)
        base = rmean(far, base_win)
        cols += [np.log1p(peak / (base + EPS)),            # how big was the recent peak vs normal
                 (peak - far) / (peak + EPS),              # share that has vanished since the peak
                 rsum(fills, win) / (peak + EPS),          # fills vs peak (low => cancelled, not traded)
                 np.log1p(far / (base + EPS))]
    top = (book.bid_sz[:, 0] - book.ask_sz[:, 0]) / (book.bid_sz[:, 0] + book.ask_sz[:, 0] + EPS)
    cols += [top, zscore(book.spread, base_win)]
    X = np.column_stack(cols)
    X[:base_win] = np.nan
    return X


class SpoofMLStrategy(Strategy):
    """fit(book) needs book.truth['spoof_dir'] (+1 bullish aftermath, -1 bearish). In production feed labels
    from surveillance/annotated data. Trades only the out-of-sample part (after train_frac)."""
    name = "S05 ML Spoofing Detection (Japan)"

    def __init__(self, cfg: SpoofConfig | None = None, seed: int = 0):
        self.cfg, self.seed = cfg or SpoofConfig(), seed
        self.m_up = self.m_dn = None

    def fit(self, book):
        c = self.cfg
        X = spoof_features(book, c.win, c.base_win)
        cut = int(book.n * c.train_frac)
        y = book.truth["spoof_dir"]
        ok = ~np.isnan(X[:cut]).any(1)
        self.m_up = MLP(X.shape[1], (16, 8), seed=self.seed).fit(X[:cut][ok], (y[:cut][ok] > 0), c.epochs, pos_weight=c.pos_weight)
        self.m_dn = MLP(X.shape[1], (16, 8), seed=self.seed + 1).fit(X[:cut][ok], (y[:cut][ok] < 0), c.epochs, pos_weight=c.pos_weight)
        return self

    def probs(self, book):
        X = spoof_features(book, self.cfg.win, self.cfg.base_win)
        ok = ~np.isnan(X).any(1)
        pu, pd = np.zeros(book.n), np.zeros(book.n)
        pu[ok], pd[ok] = self.m_up.predict_proba(X[ok]), self.m_dn.predict_proba(X[ok])
        return pu, pd

    def positions(self, book) -> np.ndarray:
        c = self.cfg
        if self.m_up is None:
            self.fit(book)
        pu, pd = self.probs(book)
        pos = to_position(pu - pd, c.enter, c.exit, c.max_hold)
        pos[:int(book.n * c.train_frac)] = 0.0                # never trade in-sample
        return pos

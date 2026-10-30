"""China style - cross-sectional mean-reversion/momentum stat-arb (dollar-neutral) + Kalman pair trading."""
from __future__ import annotations
from dataclasses import dataclass
import warnings
import numpy as np
from .base import Strategy
from ..utils import rmean2, rstd2, to_position, EPS


@dataclass
class StatArbConfig:
    rev_lb: int = 3
    mom_lb: int = 40
    z_win: int = 60
    w_rev: float = 0.7
    w_mom: float = 0.3
    gross: float = 1.0
    max_w: float = 0.15


def _cs_z(s):
    return (s - np.nanmean(s, 1, keepdims=True)) / (np.nanstd(s, 1, keepdims=True) + EPS)


class CrossSectionalStatArb(Strategy):
    name = "S02 Cross-Sectional StatArb (China)"

    def __init__(self, cfg: StatArbConfig | None = None):
        self.cfg = cfg or StatArbConfig()

    def positions(self, prices) -> np.ndarray:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)   # all-NaN warm-up rows
            return self._positions(prices)

    def _positions(self, prices) -> np.ndarray:
        c = self.cfg
        lp = np.log(np.asarray(prices, float))
        r = np.diff(lp, axis=0, prepend=lp[:1])
        resid = r - r.mean(1, keepdims=True)                       # strip market factor
        rev = rmean2(resid, c.rev_lb) * c.rev_lb / (rstd2(resid, c.z_win) * np.sqrt(c.rev_lb) + EPS)
        mom = rmean2(resid, c.mom_lb) - rmean2(resid, c.rev_lb) * c.rev_lb / c.mom_lb
        s = c.w_rev * _cs_z(-rev) + c.w_mom * _cs_z(mom)
        w = np.nan_to_num(s - np.nanmean(s, 1, keepdims=True))
        w = w / (np.abs(w).sum(1, keepdims=True) + EPS) * c.gross
        w = np.clip(w, -c.max_w, c.max_w)
        w = w - w.mean(1, keepdims=True)                           # stay dollar-neutral after clipping
        return w / (np.abs(w).sum(1, keepdims=True) + EPS) * c.gross


class KalmanPair:
    """y = beta_t * x + alpha_t with random-walk state; returns causal spread z-score (innovation / its std)."""
    def __init__(self, delta: float = 1e-4, obs_var: float = 1e-3):
        self.delta, self.ve = delta, obs_var

    def run(self, x, y):
        n = len(x)
        theta, P = np.zeros(2), np.zeros((2, 2))
        Vw = self.delta / (1 - self.delta) * np.eye(2)
        beta, alpha, z, e_all = np.zeros(n), np.zeros(n), np.zeros(n), np.zeros(n)
        for t in range(n):
            H = np.array([x[t], 1.0])
            P = P + Vw
            yhat = H @ theta
            Q = H @ P @ H + self.ve
            e = y[t] - yhat
            K = P @ H / Q
            theta = theta + K * e
            P = P - np.outer(K, H) @ P
            beta[t], alpha[t], e_all[t], z[t] = theta[0], theta[1], e, e / np.sqrt(Q)
        return beta, alpha, e_all, z

    @staticmethod
    def half_life(spread) -> float:
        s = np.asarray(spread, float)
        ds, lag = np.diff(s), s[:-1] - s[:-1].mean()
        b = (lag @ ds) / (lag @ lag + EPS)
        phi = 1.0 + b
        return float(-np.log(2) / np.log(phi)) if 0 < phi < 1 else float("inf")

    def positions(self, x, y, enter=2.0, exit_=0.5, max_hold=None):
        beta, _, _, z = self.run(np.log(x), np.log(y))
        z[:50] = 0.0                                               # filter warm-up
        return to_position(-z, enter, exit_, max_hold), beta

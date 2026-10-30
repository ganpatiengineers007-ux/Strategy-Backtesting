"""Vectorised backtester: positions decided at t execute from t+lag (no look-ahead), costs on turnover."""
from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
from .utils import shift
from . import risk


@dataclass
class Result:
    name: str
    sharpe: float
    total_return: float
    max_dd: float
    hit_rate: float
    n_trades: int
    turnover: float
    pnl: np.ndarray = field(repr=False, default=None)

    def summary(self) -> dict:
        return {"name": self.name, "sharpe": round(self.sharpe, 2), "total_return_%": round(100 * self.total_return, 2),
                "max_dd_%": round(100 * self.max_dd, 2), "hit_rate_%": round(100 * self.hit_rate, 1),
                "trades": self.n_trades, "turnover": round(self.turnover, 1)}


def _metrics(name, pnl, eff, ppy) -> Result:
    sd = pnl.std()
    sharpe = float(pnl.mean() / sd * np.sqrt(ppy)) if sd > 0 else 0.0
    eq = np.cumprod(1.0 + pnl)
    dd = float(np.max(1.0 - eq / np.maximum.accumulate(eq))) if len(eq) else 0.0
    # per-trade hit rate (single-asset series)
    wins, trades, cur, curpos = 0, 0, 0.0, 0.0
    if eff.ndim == 1:
        for p, x in zip(eff, pnl):
            if p != curpos:
                if curpos != 0:
                    trades += 1; wins += cur > 0
                cur, curpos = 0.0, p
            cur += x
        if curpos != 0:
            trades += 1; wins += cur > 0
        turnover = float(np.abs(np.diff(eff, prepend=0.0)).sum())
    else:
        trades, turnover = int((np.abs(np.diff(eff, axis=0)).sum(1) > 1e-9).sum()), float(np.abs(np.diff(eff, axis=0)).sum())
    return Result(name, sharpe, float(eq[-1] - 1.0) if len(eq) else 0.0, dd,
                  wins / trades if trades else 0.0, trades, turnover, pnl)


def run_backtest(price, position, cost_bps: float = 1.0, lag: int = 1, ppy: float = 252 * 390,
                 name: str = "", vol_target: float | None = None, kill_dd: float | None = None) -> Result:
    price = np.asarray(price, float)
    pos = np.asarray(position, float)
    ret = np.zeros_like(price)
    ret[1:] = price[1:] / price[:-1] - 1.0
    eff = shift(pos, lag)
    if vol_target:
        eff = eff * shift(risk.vol_scale(ret, vol_target, ppy), 1, fill=1.0)
    pnl = eff * ret - np.abs(np.diff(eff, prepend=0.0)) * cost_bps / 1e4
    if kill_dd:
        pnl = risk.apply_kill_switch(pnl, kill_dd)
    return _metrics(name, pnl, eff, ppy)


def run_panel_backtest(prices, weights, cost_bps: float = 2.0, lag: int = 1, ppy: float = 252, name: str = "") -> Result:
    prices = np.asarray(prices, float)
    W = np.nan_to_num(np.asarray(weights, float))
    ret = np.zeros_like(prices)
    ret[1:] = prices[1:] / prices[:-1] - 1.0
    eff = np.vstack([np.zeros((lag, W.shape[1])), W[:len(W) - lag]]) if lag else W
    pnl = (eff * ret).sum(1) - np.abs(np.diff(eff, axis=0, prepend=np.zeros((1, W.shape[1])))).sum(1) * cost_bps / 1e4
    return _metrics(name, pnl, eff, ppy)

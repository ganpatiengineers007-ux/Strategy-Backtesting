"""Fast, dependency-light numerical helpers (numpy only). All rolling ops are trailing (causal)."""
from __future__ import annotations
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

EPS = 1e-12


def ema(x, span: float) -> np.ndarray:
    x = np.nan_to_num(np.asarray(x, dtype=float))
    out = np.empty_like(x)
    if len(x) == 0:
        return out
    a = 2.0 / (span + 1.0)
    out[0] = x[0]
    for i in range(1, len(x)):
        out[i] = out[i - 1] + a * (x[i] - out[i - 1])
    return out


def _pad(n: int, w: int, vals: np.ndarray) -> np.ndarray:
    out = np.full(n, np.nan)
    out[w - 1:] = vals
    return out


def rsum(x, w: int) -> np.ndarray:
    x = np.nan_to_num(np.asarray(x, dtype=float))
    if len(x) < w:
        return np.full(len(x), np.nan)
    c = np.concatenate(([0.0], np.cumsum(x)))
    return _pad(len(x), w, c[w:] - c[:-w])


def rmean(x, w: int) -> np.ndarray:
    return rsum(x, w) / w


def rstd(x, w: int) -> np.ndarray:
    x = np.nan_to_num(np.asarray(x, dtype=float))
    m, m2 = rmean(x, w), rmean(x * x, w)
    return np.sqrt(np.maximum(m2 - m * m, 0.0) * w / max(w - 1, 1))


def rmax(x, w: int) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    if len(x) < w:
        return np.full(len(x), np.nan)
    return _pad(len(x), w, sliding_window_view(x, w).max(axis=1))


def rmin(x, w: int) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    if len(x) < w:
        return np.full(len(x), np.nan)
    return _pad(len(x), w, sliding_window_view(x, w).min(axis=1))


def zscore(x, w: int) -> np.ndarray:
    return (np.asarray(x, float) - rmean(x, w)) / (rstd(x, w) + EPS)


def shift(x, k: int = 1, fill: float = 0.0) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    out = np.full_like(x, fill)
    if k == 0:
        return x.copy()
    if 0 < k < len(x):
        out[k:] = x[:-k]
    return out


def rmean2(x: np.ndarray, w: int) -> np.ndarray:
    """Rolling mean along axis 0 for a (T, N) array (causal, NaN warm-up)."""
    T = x.shape[0]
    out = np.full(x.shape, np.nan)
    if T < w:
        return out
    c = np.vstack([np.zeros((1, x.shape[1])), np.cumsum(x, axis=0)])
    out[w - 1:] = (c[w:] - c[:-w]) / w
    return out


def rstd2(x: np.ndarray, w: int) -> np.ndarray:
    m, m2 = rmean2(x, w), rmean2(x * x, w)
    return np.sqrt(np.maximum(m2 - m * m, 0.0) * w / max(w - 1, 1))


def to_position(score, enter: float, exit_: float = 0.0, max_hold: int | None = None,
                allow_short: bool = True, min_hold: int = 0) -> np.ndarray:
    """Hysteresis state machine: score>=enter -> long, <=-enter -> short, exit when it
    decays through exit_ (or max_hold). NaN score = flat. Decision at t uses score[t] only."""
    score = np.asarray(score, dtype=float)
    out = np.zeros(len(score))
    pos, held = 0, 0
    for i, s in enumerate(score):
        if np.isnan(s):
            pos, held = 0, 0
            continue
        if pos == 0:
            if s >= enter:
                pos, held = 1, 0
            elif allow_short and s <= -enter:
                pos, held = -1, 0
        else:
            held += 1
            lapsed = (pos == 1 and s <= exit_) or (pos == -1 and s >= -exit_)
            if (lapsed and held >= min_hold) or (max_hold is not None and held >= max_hold):
                pos, held = 0, 0
        out[i] = pos
    return out

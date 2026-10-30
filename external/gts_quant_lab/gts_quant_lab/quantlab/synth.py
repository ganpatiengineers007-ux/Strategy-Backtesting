"""Synthetic market generators with *planted* microstructure effects, so every strategy pipeline can be
verified end-to-end offline. Results on this data prove the code works - NOT that the edge exists live."""
from __future__ import annotations
from datetime import datetime, timezone
import numpy as np
from .types import BookSeries, Bars


def make_book(n: int = 30000, levels: int = 5, seed: int = 7, tick: float = 0.01, start: float = 100.0) -> BookSeries:
    r = np.random.default_rng(seed)
    a = np.zeros(n)
    e = r.normal(size=n)
    for t in range(1, n):
        a[t] = 0.98 * a[t - 1] + 0.2 * e[t]                      # latent order-flow pressure
    iceberg, spoof_dir, spoof_layer = np.zeros(n), np.zeros(n), np.zeros(n)
    for s in range(1000, n - 500, 1700):
        iceberg[s:s + 300] = r.choice([-1.0, 1.0])               # +1 hidden buyer absorbing sells
    for s in range(1450, n - 100, 1300):
        if iceberg[s:s + 40].any():
            continue
        side = r.choice([-1.0, 1.0])                             # +1 fake bid layering, bearish after cancel
        spoof_layer[s:s + 12] = side
        spoof_dir[s + 12:s + 32] = -side
    ret = 0.0035 * a + 0.004 * iceberg + 0.0125 * r.normal(size=n) + 0.015 * spoof_dir
    mid = start + np.cumsum(ret)
    spread = tick * (1 + (r.random(n) < 0.3))
    mu = np.log(np.array([180, 220, 260, 300, 340, 380, 420, 460][:levels], float))
    nb, na = r.normal(size=(n, levels)), r.normal(size=(n, levels))
    lb, la = np.zeros((n, levels)), np.zeros((n, levels))
    lb[0] = la[0] = mu
    for t in range(1, n):
        lb[t] = lb[t - 1] + 0.05 * (mu - lb[t - 1]) + 0.03 * nb[t]
        la[t] = la[t - 1] + 0.05 * (mu - la[t - 1]) + 0.03 * na[t]
    tilt = 0.4 * np.clip(a, -2.5, 2.5)[:, None]
    bid_sz, ask_sz = np.exp(lb + tilt), np.exp(la - tilt)
    p_buy = 1.0 / (1.0 + np.exp(-1.2 * a))
    p_buy = np.where(iceberg > 0, 0.35, np.where(iceberg < 0, 0.65, p_buy))
    has = r.random(n) < 0.75
    side = np.where(r.random(n) < p_buy, 1.0, -1.0) * has
    size = r.gamma(2.0, 15.0, n) * has
    dep_b, dep_a = np.zeros(n), np.zeros(n)
    for t in range(1, n):
        sell = size[t] if side[t] == -1 else 0.0
        buy = size[t] if side[t] == 1 else 0.0
        if iceberg[t] > 0:
            sell = 0.0                                           # hidden buyer refills the bid
        if iceberg[t] < 0:
            buy = 0.0
        dep_b[t], dep_a[t] = 0.8 * dep_b[t - 1] + sell, 0.8 * dep_a[t - 1] + buy
    bid_sz[:, 0] = np.maximum(bid_sz[:, 0] - dep_b, 5.0)
    ask_sz[:, 0] = np.maximum(ask_sz[:, 0] - dep_a, 5.0)
    lay = np.nonzero(spoof_layer != 0)[0]
    for t in lay:
        (bid_sz if spoof_layer[t] > 0 else ask_sz)[t, 1:4] *= 6.0
    k = np.arange(levels) * tick
    bid0 = np.floor((mid - spread / 2) / tick) * tick          # quantise to the tick grid
    mid = bid0 + spread / 2
    bid_px = bid0[:, None] - k[None, :]
    ask_px = (bid0 + spread)[:, None] + k[None, :]
    return BookSeries(ts=np.arange(n, dtype=float), bid_px=bid_px, bid_sz=bid_sz, ask_px=ask_px, ask_sz=ask_sz,
                      trade_px=mid + side * spread / 2, trade_sz=size, trade_side=side,
                      truth={"a": a, "iceberg": iceberg, "spoof_dir": spoof_dir, "spoof_layer": spoof_layer})


def make_two_venues(book: BookSeries, lag: int = 3, noise_bps: float = 0.3, seed: int = 3):
    """Leader venue = book mid; follower = same price `lag` ticks later + noise."""
    r = np.random.default_rng(seed)
    a = book.mid
    b = np.concatenate((np.full(lag, a[0]), a[:-lag])) + r.normal(0, 1, len(a)) * a * noise_bps / 1e4
    return a, b


def make_panel(T: int = 2500, N: int = 24, seed: int = 11) -> np.ndarray:
    """(T, N) prices: market factor + OU idiosyncratic mean-reversion + slow idiosyncratic drift (momentum)."""
    r = np.random.default_rng(seed)
    mkt = r.normal(0.0002, 0.006, T)
    beta = r.uniform(0.6, 1.4, N)
    x, mu = np.zeros((T, N)), np.zeros((T, N))
    for t in range(1, T):
        x[t] = 0.90 * x[t - 1] + 0.004 * r.normal(size=N)
        mu[t] = 0.995 * mu[t - 1] + 0.00004 * r.normal(size=N)
    return np.exp(np.log(50.0) + np.cumsum(beta * mkt[:, None] + mu, axis=0) + x)


SESSION_OPEN_MIN = {"tokyo": 0, "london": 8 * 60, "newyork": 13 * 60 + 30}   # UTC minute-of-day


def make_session_bars(days: int = 40, seed: int = 5, base_vol: float = 0.0004) -> Bars:
    """1-minute bars with vol/volume ignition after Tokyo/London/NY opens, plus planted liquidity sweeps
    (wick beyond recent extreme then reversal) and displacement->pullback->continuation (FVG) events."""
    r = np.random.default_rng(seed)
    n = days * 1440
    t0 = int(datetime(2026, 1, 5, tzinfo=timezone.utc).timestamp())
    ts = t0 + 60.0 * np.arange(n)
    mod = (np.arange(n) % 1440)
    sig = np.full(n, base_vol)
    burst = np.zeros(n)
    drift = np.zeros(n)
    for d in range(days):
        for om in SESSION_OPEN_MIN.values():
            i0 = d * 1440 + om
            m = np.arange(0, 120)
            idx = i0 + m
            ok = idx < n
            burst[idx[ok]] += 2.0 * np.exp(-m[ok] / 25.0)
            direc = r.choice([-1.0, 1.0])
            drift[i0:i0 + 5] += direc * 0.6
            drift[i0 + 5:i0 + 35] += direc * 0.25
    sig = sig * (1 + burst)
    ret = sig * (r.normal(size=n) + drift)
    ev_disp = r.choice(np.arange(200, n - 60), size=n // 400, replace=False)
    ev_sweep = r.choice(np.arange(200, n - 60), size=n // 500, replace=False)
    for t in ev_disp:
        d = r.choice([-1.0, 1.0]); s = sig[t]
        ret[t] = d * 6 * s; ret[t + 1] = d * 0.5 * s
        ret[t + 2:t + 7] = -d * 1.0 * s; ret[t + 7:t + 25] = d * 0.6 * s
    sweep_dir = {}
    for t in ev_sweep:
        d = r.choice([-1.0, 1.0]); sweep_dir[t] = d
        ret[t + 1:t + 8] += -d * 0.7 * sig[t]
    close = 100.0 * np.exp(np.cumsum(ret))
    open_ = np.concatenate(([100.0], close[:-1]))
    wick = np.abs(r.normal(size=(2, n))) * 0.3 * sig * close
    high = np.maximum(open_, close) + wick[0]
    low = np.minimum(open_, close) - wick[1]
    vol = 100 * (1 + burst) * np.exp(r.normal(0, 0.25, n)) * (1 + 0.2 * np.abs(ret) / sig)
    for t, d in sweep_dir.items():
        if d > 0:
            high[t] = high[t - 30:t].max() * (1 + 0.0006)
        else:
            low[t] = low[t - 30:t].min() * (1 - 0.0006)
        vol[t] *= 4.0
    delta = vol * np.tanh(ret / (sig + 1e-12)) * 0.5
    return Bars(ts=ts, open=open_, high=high, low=low, close=close, volume=vol, delta=delta,
                ntrades=vol / 2, obi=np.zeros(n), spread=np.full(n, 0.01))

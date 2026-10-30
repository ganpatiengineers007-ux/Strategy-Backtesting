"""Plain-assert tests (run: python tests/test_all.py  or  pytest)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from quantlab.synth import make_book, make_two_venues, make_panel, make_session_bars
from quantlab.types import book_to_bars, BookSeries
from quantlab.backtest import run_backtest, run_panel_backtest
from quantlab.ml import MLP
from quantlab import risk
from quantlab.strategies import *
from quantlab.strategies.s06_volume_profile import build_profile
from quantlab.strategies.s04_microstructure import vpin, kyle_lambda

BOOK = make_book(12000)
BARS = book_to_bars(BOOK, 20)
SESS = make_session_bars(15)


def _cut(book, k):
    f = {n: getattr(book, n)[:k] for n in ("ts", "bid_px", "bid_sz", "ask_px", "ask_sz", "trade_px", "trade_sz", "trade_side")}
    return BookSeries(**f)


def _cut_bars(b, k):
    return type(b)(**{n: getattr(b, n)[:k] for n in b.__dataclass_fields__})


def _valid(pos, n):
    assert len(pos) == n and not np.isnan(pos).any() and np.abs(pos).max() <= 1.0 + 1e-9


def test_tick_strategies_valid_and_causal():
    for S in (OBIDeltaStrategy, MicrostructureStrategy, IcebergStrategy, VolumeProfileStrategy):
        full = S().positions(BOOK)
        _valid(full, BOOK.n)
        k = 7000
        part = S().positions(_cut(BOOK, k))
        assert np.array_equal(full[:k - 1], part[:k - 1]), f"look-ahead in {S.__name__}"


def test_bar_strategies_valid_and_causal():
    for S in (FVGStrategy, LiquiditySweepStrategy, SessionIgnitionStrategy):
        full = S().positions(SESS)
        _valid(full, SESS.n)
        k = 12000
        part = S().positions(_cut_bars(SESS, k))
        assert np.array_equal(full[:k - 40], part[:k - 40]), f"look-ahead in {S.__name__}"


def test_ml_strategies():
    s = SpoofMLStrategy()
    pos = s.positions(BOOK)
    _valid(pos, BOOK.n)
    assert not pos[:int(BOOK.n * s.cfg.train_frac)].any(), "must not trade in-sample"
    r = ReversalAIStrategy()
    _valid(r.positions(BARS), BARS.n)
    p = r.probs(BARS)
    k = 450
    assert np.allclose(np.nan_to_num(p[:k]), np.nan_to_num(r.probs(_cut_bars(BARS, k))[:k])), "walk-forward leak"


def test_stat_arb_and_kalman():
    px = make_panel(800, 12)
    w = CrossSectionalStatArb().positions(px)
    assert w.shape == px.shape and np.allclose(w.sum(1), 0, atol=1e-9)
    assert np.all(np.abs(w).sum(1) <= 1.0 + 1e-9)
    res = run_panel_backtest(px, w, 2.0)
    assert np.isfinite(res.sharpe)
    r = np.random.default_rng(0)
    x = np.cumsum(r.normal(0, 0.01, 1500)) + 4.0
    y = 1.5 * x + 0.2 + 0.02 * np.sin(np.arange(1500) / 6.0) + r.normal(0, 0.003, 1500)
    beta, _, _, z = KalmanPair().run(x, y)
    assert abs(beta[-1] - 1.5) < 0.2
    assert 0 < KalmanPair.half_life(0.02 * np.sin(np.arange(1500) / 6.0) + r.normal(0, 0.01, 1500)) < 1e6


def test_latency_arb_lead_lag():
    a, b = make_two_venues(BOOK, lag=3)
    assert estimate_lead_lag(a, b, 10) == 3
    pos = LatencyArbStrategy().positions((a, b))
    _valid(pos, BOOK.n)
    assert run_backtest(b, pos, 0.5).total_return > 0


def test_volume_profile_math():
    p = np.array([10.0] * 50 + [10.1] * 10 + [9.9] * 10 + [10.5] * 2)
    v = np.ones(len(p)); v[:50] = 5
    pr = build_profile(p, v, 0.1)
    assert abs(pr["poc"] - 10.0) < 0.1 and pr["val"] <= pr["poc"] <= pr["vah"]


def test_microstructure_helpers():
    v = vpin(BOOK.trade_sz, BOOK.trade_side, 400.0, 10)
    assert np.nanmin(v) >= 0 and np.nanmax(v) <= 1
    assert kyle_lambda(BOOK.mid, BOOK.trade_sz * BOOK.trade_side, 100).shape == (BOOK.n,)


def test_backtest_engine_no_lookahead_and_costs():
    r = np.random.default_rng(1)
    px = 100 * np.exp(np.cumsum(r.normal(0, 0.001, 5000)))
    ret = np.zeros_like(px); ret[1:] = px[1:] / px[:-1] - 1
    cheat = np.sign(ret)                              # knows the same bar: lag=0 wins, lag=1 must not
    assert run_backtest(px, cheat, 0, lag=0).total_return > 1.0
    assert abs(run_backtest(px, cheat, 0, lag=1).total_return) < 0.5
    flat = run_backtest(px, np.zeros_like(px), 5.0)
    assert flat.total_return == 0 and flat.n_trades == 0
    alt = np.tile([1.0, -1.0], 2500)
    assert run_backtest(px, alt, 5.0).total_return < run_backtest(px, alt, 0.0).total_return


def test_risk_and_mlp():
    pnl = np.array([0.01] * 10 + [-0.05] * 5 + [0.02] * 10)
    out = risk.apply_kill_switch(pnl, 0.1)
    assert out[-1] == 0 and (out != pnl).any()
    ks = risk.KillSwitch(0.1, 0.03)
    assert ks.update(0.96) and ks.tripped
    ks.reset(); assert not ks.tripped
    r = np.random.default_rng(0)
    X = r.normal(size=(2000, 2)); y = ((X[:, 0] * X[:, 1]) > 0).astype(float)      # XOR-like, non-linear
    m = MLP(2, (16, 8), lr=0.02).fit(X, y, epochs=60)
    assert ((m.predict_proba(X) > 0.5) == (y > 0.5)).mean() > 0.9


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for f in fns:
        f(); print("PASS", f.__name__)
    print(f"{len(fns)}/{len(fns)} passed")

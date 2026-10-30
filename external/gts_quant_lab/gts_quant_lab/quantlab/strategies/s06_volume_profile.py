"""Australia style - Volume Profile / Point of Control. Prior-session POC/VAH/VAL; acceptance-retest
continuation and failed-excursion re-entry to value (target POC). No time-series indicators."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from .base import Strategy


def build_profile(prices, vols, bin_size: float, va_pct: float = 0.70) -> dict | None:
    prices, vols = np.asarray(prices, float), np.asarray(vols, float)
    m = vols > 0
    if m.sum() < 10:
        return None
    p, v = prices[m], vols[m]
    pmin = p.min()
    idx = ((p - pmin) / bin_size).astype(int)
    prof = np.bincount(idx, weights=v)
    poc = int(np.argmax(prof))
    lo = hi = poc
    acc, target = prof[poc], va_pct * prof.sum()
    while acc < target and (lo > 0 or hi < len(prof) - 1):
        up = prof[hi + 1] if hi + 1 < len(prof) else -1.0
        dn = prof[lo - 1] if lo - 1 >= 0 else -1.0
        if up >= dn:
            hi += 1; acc += prof[hi]
        else:
            lo -= 1; acc += prof[lo]
    c = lambda i: pmin + (i + 0.5) * bin_size
    return {"poc": c(poc), "vah": c(hi) + bin_size / 2, "val": c(lo) - bin_size / 2}


@dataclass
class VPConfig:
    session_ticks: int = 3000
    bin_size: float = 0.02
    accept_ticks: int = 30
    tol: float = 0.03
    reentry_ticks: int = 20
    max_hold: int = 400


class VolumeProfileStrategy(Strategy):
    name = "S06 Volume Profile POC (Australia)"

    def __init__(self, cfg: VPConfig | None = None):
        self.cfg = cfg or VPConfig()

    def positions(self, book) -> np.ndarray:
        c = self.cfg
        n, mid = book.n, book.mid
        pos = np.zeros(n)
        for s0 in range(c.session_ticks, n, c.session_ticks):
            prof = build_profile(book.trade_px[s0 - c.session_ticks:s0], book.trade_sz[s0 - c.session_ticks:s0], c.bin_size)
            if prof is None:
                continue
            poc, vah, val = prof["poc"], prof["vah"], prof["val"]
            cur, held, stop, tgt = 0, 0, 0.0, 0.0
            above = below = inside = 0
            exc_hi, exc_lo = -np.inf, np.inf
            seen_above = seen_below = retest_up = retest_dn = False
            for i in range(s0, min(s0 + c.session_ticks, n)):
                x = mid[i]
                above = above + 1 if x > vah else 0
                below = below + 1 if x < val else 0
                inside = inside + 1 if val <= x <= vah else 0
                exc_hi, exc_lo = max(exc_hi, x), min(exc_lo, x)
                if cur != 0:
                    held += 1
                    hit_stop = (cur == 1 and x < stop) or (cur == -1 and x > stop)
                    hit_tgt = (cur == 1 and x >= tgt) or (cur == -1 and x <= tgt)
                    if hit_stop or hit_tgt or held >= c.max_hold:
                        cur = 0
                else:
                    if above >= c.accept_ticks:
                        seen_above = True
                    if below >= c.accept_ticks:
                        seen_below = True
                    # Rule A: accepted above VAH, pulled back to VAH, bounced => continuation long
                    if seen_above and abs(x - vah) <= c.tol:
                        retest_up = True
                    if retest_up and x > vah + c.tol:
                        cur, held, stop, tgt = 1, 0, vah - 2 * c.tol, x + 4 * c.tol
                        seen_above = retest_up = False
                    if seen_below and abs(x - val) <= c.tol:
                        retest_dn = True
                    if cur == 0 and retest_dn and x < val - c.tol:
                        cur, held, stop, tgt = -1, 0, val + 2 * c.tol, x - 4 * c.tol
                        seen_below = retest_dn = False
                    # Rule B: failed excursion (went outside value, came back in for N ticks) => back to POC
                    if cur == 0 and inside >= c.reentry_ticks:
                        if exc_hi > vah + c.tol and x > poc:
                            cur, held, stop, tgt = -1, 0, exc_hi, poc
                        elif exc_lo < val - c.tol and x < poc:
                            cur, held, stop, tgt = 1, 0, exc_lo, poc
                        exc_hi, exc_lo = -np.inf, np.inf
                pos[i] = cur
        return pos

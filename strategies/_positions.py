"""quantlab ki positions(bars) style (vectorised) strategies ko engine ke on_bar interface se jodta hai.

Engine long-only hai: positions > 0 => BUY, baaki sab => EXIT. Short (-1) side ignore hoti hai.
Positions poore dataset par ek baar nikalti hain (cache); quantlab ka niyam hai ki row t ka faisla sirf t tak ke data se hota hai,
aur engine entry agle bar ke open par bharta hai. Ye niyam tests/unit/strategies/test_str_wiring.py me jaancha jaata hai.
Stop-loss quantlab ka apna andar hai, par bahar nahi aata; position sizing ke liye ek safety stop (stop_pct, default 1%) lagta hai."""
import sys
from pathlib import Path

import numpy as np

_EXTERNAL_ROOT = Path(__file__).resolve().parent.parent / "external"
if str(_EXTERNAL_ROOT) not in sys.path:
    sys.path.insert(0, str(_EXTERNAL_ROOT))

from gts_quant_lab.gts_quant_lab.quantlab.types import Bars  # noqa: E402
from strategies.base import Strategy  # noqa: E402
from strategies.models import Signal  # noqa: E402


def to_quantlab_bars(bars) -> Bars:
    """Engine ke Bar objects -> quantlab Bars. ts: dukaan ka wall-clock (IST) ko 'UTC jaisa' epoch maana jaata hai.
    delta/obi/spread/ntrades candles me nahi hote => 0 (jo strategies inhe maangti hain unhe required_data se roka jaata hai)."""
    n = len(bars)
    ts = np.array([b.ts[:10] + "T" + b.ts[11:19] for b in bars], dtype="datetime64[s]").astype("int64")
    col = lambda name: np.array([getattr(b, name) for b in bars], dtype=float)
    z = np.zeros(n)
    return Bars(ts=ts, open=col("open"), high=col("high"), low=col("low"), close=col("close"), volume=col("volume"),
                delta=z.copy(), ntrades=z.copy(), obi=z.copy(), spread=z.copy())


class PositionsAdapter(Strategy):
    required_data = ()

    def _make_inner(self):
        raise NotImplementedError

    def __init__(self, params=None):
        super().__init__(params)
        self.params.setdefault("stop_pct", 1.0)
        self._inner = self._make_inner()
        self._cache = (None, None)

    def positions(self, bars):
        key = id(bars)
        if self._cache[0] != key:
            self._cache = (key, np.asarray(self._inner.positions(to_quantlab_bars(bars)), dtype=float))
        return self._cache[1]

    def on_bar(self, ctx):
        want_long = self.positions(ctx._bars)[ctx.index] > 0
        if ctx.position is None:
            if not want_long:
                return None
            px = ctx.bar.close
            return Signal("BUY", stop_loss=round(px * (1 - self.params["stop_pct"] / 100), 2), reason=self.strategy_id)
        return None if want_long else Signal("EXIT", reason=f"{self.strategy_id}_flat")

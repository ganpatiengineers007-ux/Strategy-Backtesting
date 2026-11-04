"""STR11 mean_reversion: real quantstrat logic wired into the registry engine.

The external framework emits BUY/SELL signals from a rolling Z-score with
volume confirmation. This adapter converts those signals into the engine's
long/flat position stream (the engine is long-only, so a SELL simply closes an
open long). No look-ahead is introduced: the external strategy uses only data
up to each row and the engine fills at the next bar open.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_EXTERNAL_ROOT = Path(__file__).resolve().parent.parent.parent / "external"
if str(_EXTERNAL_ROOT) not in sys.path:
    sys.path.insert(0, str(_EXTERNAL_ROOT))

from strategies._positions import PositionsAdapter  # noqa: E402
from quant_stat_arb_framework.src.quantstrat.config import StrategyConfig  # noqa: E402
from quant_stat_arb_framework.src.quantstrat.strategy import MeanReversionStrategy  # noqa: E402

_CONFIG_KEYS = (
    "lookback", "z_entry", "entry_mode", "volume_lookback", "volume_multiplier",
    "atr_period", "stop_atr", "target_atr", "require_orderbook",
    "min_book_imbalance", "require_oi", "min_oi_change_pct", "allow_long", "allow_short",
)


def _to_frame(bars):
    index = pd.to_datetime([b.ts for b in bars])
    return pd.DataFrame(
        {
            "open": [float(b.open) for b in bars],
            "high": [float(b.high) for b in bars],
            "low": [float(b.low) for b in bars],
            "close": [float(b.close) for b in bars],
            "volume": [float(b.volume) for b in bars],
        },
        index=index,
    )


class MeanReversionAdapter(PositionsAdapter):
    strategy_id = "mean_reversion"
    required_data = ()

    def _make_inner(self):
        values = {k: self.params[k] for k in _CONFIG_KEYS if k in self.params}
        return MeanReversionStrategy(StrategyConfig(**values))

    def positions(self, bars):
        key = id(bars)
        if self._cache[0] != key:
            frame = _to_frame(bars)
            positions = np.zeros(len(bars), dtype=float)
            current = 0
            for signal in self._inner.generate_signals(frame):
                i = frame.index.get_loc(signal.timestamp)
                current = 1 if signal.side.value == "BUY" else -1
                positions[i] = current
            self._cache = (key, positions)
        return self._cache[1]

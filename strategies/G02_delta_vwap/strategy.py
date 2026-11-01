"""G02 Delta + VWAP trend  (plug-in adapter, Greeks strategy G02)

असली लॉजिक: all_strategies/greeks/delta_vwap_strategy.py  (backtest वाली वही फ़ाइल)
v0 long-only है: सिर्फ़ BUY/EXIT signal। short side अभी नहीं।
"""
import sys
from pathlib import Path

# repo root = strategies/<यह फ़ोल्डर>/strategy.py से तीन ऊपर
_CORE = Path(__file__).resolve().parent.parent.parent / "all_strategies" / "greeks"
if str(_CORE) not in sys.path:
    sys.path.insert(0, str(_CORE))

from strategies.base import Strategy  # noqa: E402
import gamma_vwap_strategy as G  # noqa: E402,F401  (core engine + साझा नियम)
import delta_vwap_strategy as MOD  # noqa: E402
from gts_bridge import decide  # noqa: E402


class DeltaVwapAdapter(Strategy):
    strategy_id = "delta_vwap"
    required_data = ()

    def on_bar(self, ctx):
        # MOD.signal(rows, i, vwap) से +1/-1/0 लेकर Signal(BUY/EXIT) बनाता है
        return decide(ctx, MOD.signal, G, sl_atr=None, tg_atr=3.0, label="delta_vwap")

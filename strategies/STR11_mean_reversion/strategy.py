"""Adapter for STR11 mean_reversion (external quantstrat). Wraps MeanReversionStrategy for Registry plug-in."""
import sys
from pathlib import Path

_EXTERNAL_ROOT = Path(__file__).resolve().parent.parent.parent / "external"
if str(_EXTERNAL_ROOT) not in sys.path:
    sys.path.insert(0, str(_EXTERNAL_ROOT))

from strategies.base import Strategy

from quant_stat_arb_framework.src.quantstrat.strategy import MeanReversionStrategy  # noqa: E402


class MeanReversionAdapter(Strategy):
    strategy_id = "mean_reversion"
    required_data = ()

    def __init__(self, params=None):
        super().__init__(params)
        self._inner = MeanReversionStrategy.__new__(MeanReversionStrategy)

    def on_bar(self, ctx):
        return None

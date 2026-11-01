"""Adapter for STR05 spoof_ml (external quantlab). Wraps SpoofMLStrategy for Registry plug-in."""
import sys
from pathlib import Path

_EXTERNAL_ROOT = Path(__file__).resolve().parent.parent.parent / "external"
if str(_EXTERNAL_ROOT) not in sys.path:
    sys.path.insert(0, str(_EXTERNAL_ROOT))

from strategies.base import Strategy

from gts_quant_lab.gts_quant_lab.quantlab.strategies.s05_spoof_ml import SpoofMLStrategy  # noqa: E402


class SpoofMLAdapter(Strategy):
    strategy_id = "spoof_ml"
    required_data = ()

    def __init__(self, params=None):
        super().__init__(params)
        self._inner = SpoofMLStrategy()

    def on_bar(self, ctx):
        return None

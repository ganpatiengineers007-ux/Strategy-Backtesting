"""Adapter for STR01 obi_delta (external quantlab). Wraps OBIDeltaStrategy for Registry plug-in."""
import sys
from pathlib import Path

_EXTERNAL_ROOT = Path(__file__).resolve().parent.parent.parent / "external"
if str(_EXTERNAL_ROOT) not in sys.path:
    sys.path.insert(0, str(_EXTERNAL_ROOT))

from strategies.base import Strategy

from gts_quant_lab.gts_quant_lab.quantlab.strategies.s01_obi_delta import OBIDeltaStrategy  # noqa: E402


class ObiDeltaAdapter(Strategy):
    strategy_id = "obi_delta"
    required_data = ()

    def __init__(self, params=None):
        super().__init__(params)
        self._inner = OBIDeltaStrategy()

    def on_bar(self, ctx):
        return None

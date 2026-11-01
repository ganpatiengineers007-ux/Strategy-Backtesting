"""Adapter for STR03 latency_arb (external quantlab). Wraps LatencyArbStrategy for Registry plug-in."""
import sys
from pathlib import Path

_EXTERNAL_ROOT = Path(__file__).resolve().parent.parent.parent / "external"
if str(_EXTERNAL_ROOT) not in sys.path:
    sys.path.insert(0, str(_EXTERNAL_ROOT))

from strategies.base import Strategy

from gts_quant_lab.gts_quant_lab.quantlab.strategies.s03_latency_arb import LatencyArbStrategy  # noqa: E402


class LatencyArbAdapter(Strategy):
    strategy_id = "latency_arb"
    required_data = ()

    def __init__(self, params=None):
        super().__init__(params)
        self._inner = LatencyArbStrategy()

    def on_bar(self, ctx):
        return None

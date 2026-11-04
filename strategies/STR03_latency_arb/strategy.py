"""Adapter for STR03 latency_arb (external quantlab). Wraps LatencyArbStrategy for Registry plug-in."""
import sys
from pathlib import Path

_EXTERNAL_ROOT = Path(__file__).resolve().parent.parent.parent / "external"
if str(_EXTERNAL_ROOT) not in sys.path:
    sys.path.insert(0, str(_EXTERNAL_ROOT))

from strategies._blocked import BookBackedStrategy

from gts_quant_lab.gts_quant_lab.quantlab.strategies.s03_latency_arb import LatencyArbStrategy  # noqa: E402


class LatencyArbAdapter(BookBackedStrategy):
    strategy_id = "latency_arb"
    required_data = ('second_venue_feed',)
    blocked_reason = "requires synchronized feeds from two venues; only one OHLCV candle feed is available"

    def __init__(self, params=None):
        super().__init__(params, LatencyArbStrategy())

"""Adapter for STR07 reversal_ai (external quantlab). Wraps ReversalAIStrategy for Registry plug-in."""
import sys
from pathlib import Path

_EXTERNAL_ROOT = Path(__file__).resolve().parent.parent.parent / "external"
if str(_EXTERNAL_ROOT) not in sys.path:
    sys.path.insert(0, str(_EXTERNAL_ROOT))

from strategies._blocked import BookBackedStrategy

from gts_quant_lab.gts_quant_lab.quantlab.strategies.s07_reversal_ai import ReversalAIStrategy  # noqa: E402


class ReversalAIAdapter(BookBackedStrategy):
    strategy_id = "reversal_ai"
    required_data = ('l2_book', 'tick_trades')
    blocked_reason = "requires L2 book imbalance, delta, spread and trade-count features; OHLCV candles do not provide them"

    def __init__(self, params=None):
        super().__init__(params, ReversalAIStrategy())

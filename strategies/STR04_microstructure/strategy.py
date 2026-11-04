"""Adapter for STR04 microstructure (external quantlab). Wraps MicrostructureStrategy for Registry plug-in."""
import sys
from pathlib import Path

_EXTERNAL_ROOT = Path(__file__).resolve().parent.parent.parent / "external"
if str(_EXTERNAL_ROOT) not in sys.path:
    sys.path.insert(0, str(_EXTERNAL_ROOT))

from strategies._blocked import BookBackedStrategy

from gts_quant_lab.gts_quant_lab.quantlab.strategies.s04_microstructure import MicrostructureStrategy  # noqa: E402


class MicrostructureAdapter(BookBackedStrategy):
    strategy_id = "microstructure"
    required_data = ('l2_book', 'tick_trades')
    blocked_reason = "requires level-2 order book and tick trades for VPIN/Kyle-lambda; OHLCV candles lack trade-side data"

    def __init__(self, params=None):
        super().__init__(params, MicrostructureStrategy())

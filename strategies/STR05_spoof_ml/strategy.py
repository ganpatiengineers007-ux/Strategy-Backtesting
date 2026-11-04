"""Adapter for STR05 spoof_ml (external quantlab). Wraps SpoofMLStrategy for Registry plug-in."""
import sys
from pathlib import Path

_EXTERNAL_ROOT = Path(__file__).resolve().parent.parent.parent / "external"
if str(_EXTERNAL_ROOT) not in sys.path:
    sys.path.insert(0, str(_EXTERNAL_ROOT))

from strategies._blocked import BookBackedStrategy

from gts_quant_lab.gts_quant_lab.quantlab.strategies.s05_spoof_ml import SpoofMLStrategy  # noqa: E402


class SpoofMLAdapter(BookBackedStrategy):
    strategy_id = "spoof_ml"
    required_data = ('l2_book', 'tick_trades')
    blocked_reason = "requires level-2 book + labelled spoofing episodes; OHLCV candles contain neither depth nor labels"

    def __init__(self, params=None):
        super().__init__(params, SpoofMLStrategy())

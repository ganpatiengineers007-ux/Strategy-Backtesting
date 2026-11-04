"""Adapter for STR01 obi_delta (external quantlab). Wraps OBIDeltaStrategy for Registry plug-in."""
import sys
from pathlib import Path

_EXTERNAL_ROOT = Path(__file__).resolve().parent.parent.parent / "external"
if str(_EXTERNAL_ROOT) not in sys.path:
    sys.path.insert(0, str(_EXTERNAL_ROOT))

from strategies._blocked import BookBackedStrategy

from gts_quant_lab.gts_quant_lab.quantlab.strategies.s01_obi_delta import OBIDeltaStrategy  # noqa: E402


class ObiDeltaAdapter(BookBackedStrategy):
    strategy_id = "obi_delta"
    required_data = ('l2_book',)
    blocked_reason = "requires level-2 order-book depth and trade tape; OHLCV candles do not contain OBI/delta"

    def __init__(self, params=None):
        super().__init__(params, OBIDeltaStrategy())

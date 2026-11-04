"""Adapter for STR09 iceberg (external quantlab). Wraps IcebergStrategy for Registry plug-in."""
import sys
from pathlib import Path

_EXTERNAL_ROOT = Path(__file__).resolve().parent.parent.parent / "external"
if str(_EXTERNAL_ROOT) not in sys.path:
    sys.path.insert(0, str(_EXTERNAL_ROOT))

from strategies._blocked import BookBackedStrategy

from gts_quant_lab.gts_quant_lab.quantlab.strategies.s09_iceberg import IcebergStrategy  # noqa: E402


class IcebergAdapter(BookBackedStrategy):
    strategy_id = "iceberg"
    required_data = ('l2_book', 'tick_trades')
    blocked_reason = "requires best-level order-book refill events; OHLCV candles do not expose displayed depth"

    def __init__(self, params=None):
        super().__init__(params, IcebergStrategy())

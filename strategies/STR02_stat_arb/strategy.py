"""Adapter for STR02 stat_arb (external quantlab). Wraps CrossSectionalStatArb for Registry plug-in."""
import sys
from pathlib import Path

_EXTERNAL_ROOT = Path(__file__).resolve().parent.parent.parent / "external"
if str(_EXTERNAL_ROOT) not in sys.path:
    sys.path.insert(0, str(_EXTERNAL_ROOT))

from strategies._blocked import BookBackedStrategy

from gts_quant_lab.gts_quant_lab.quantlab.strategies.s02_stat_arb import CrossSectionalStatArb  # noqa: E402


class StatArbAdapter(BookBackedStrategy):
    strategy_id = "stat_arb"
    required_data = ('multi_asset',)
    blocked_reason = "requires a synchronized multi-asset price panel; single-symbol OHLCV candles cannot form cross-sectional weights"

    def __init__(self, params=None):
        super().__init__(params, CrossSectionalStatArb())

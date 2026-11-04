"""Adapter for STR06 volume_profile (external quantlab). Wraps VolumeProfileStrategy for Registry plug-in."""
import sys
from pathlib import Path

_EXTERNAL_ROOT = Path(__file__).resolve().parent.parent.parent / "external"
if str(_EXTERNAL_ROOT) not in sys.path:
    sys.path.insert(0, str(_EXTERNAL_ROOT))

from strategies._blocked import BookBackedStrategy

from gts_quant_lab.gts_quant_lab.quantlab.strategies.s06_volume_profile import VolumeProfileStrategy  # noqa: E402


class VolumeProfileAdapter(BookBackedStrategy):
    strategy_id = "volume_profile"
    required_data = ('tick_trades',)
    blocked_reason = "requires per-trade prices/volumes to build a volume profile; OHLCV bar volume is not a trade tape"

    def __init__(self, params=None):
        super().__init__(params, VolumeProfileStrategy())

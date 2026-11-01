"""Adapter for STR06 volume_profile (external quantlab). Wraps VolumeProfileStrategy for Registry plug-in."""
import sys
from pathlib import Path

_EXTERNAL_ROOT = Path(__file__).resolve().parent.parent.parent / "external"
if str(_EXTERNAL_ROOT) not in sys.path:
    sys.path.insert(0, str(_EXTERNAL_ROOT))

from strategies.base import Strategy

from gts_quant_lab.gts_quant_lab.quantlab.strategies.s06_volume_profile import VolumeProfileStrategy  # noqa: E402


class VolumeProfileAdapter(Strategy):
    strategy_id = "volume_profile"
    required_data = ()

    def __init__(self, params=None):
        super().__init__(params)
        self._inner = VolumeProfileStrategy()

    def on_bar(self, ctx):
        return None

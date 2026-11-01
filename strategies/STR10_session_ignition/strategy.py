"""Adapter for STR10 session_ignition (external quantlab). Wraps SessionIgnitionStrategy for Registry plug-in."""
import sys
from pathlib import Path

_EXTERNAL_ROOT = Path(__file__).resolve().parent.parent.parent / "external"
if str(_EXTERNAL_ROOT) not in sys.path:
    sys.path.insert(0, str(_EXTERNAL_ROOT))

from strategies.base import Strategy

from gts_quant_lab.gts_quant_lab.quantlab.strategies.s10_session_ignition import SessionIgnitionStrategy  # noqa: E402


class SessionIgnitionAdapter(Strategy):
    strategy_id = "session_ignition"
    required_data = ()

    def __init__(self, params=None):
        super().__init__(params)
        self._inner = SessionIgnitionStrategy()

    def on_bar(self, ctx):
        return None

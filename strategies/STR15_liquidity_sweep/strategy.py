"""STR15 liquidity_sweep: the S03b wick/volume-spike reversal from external quantlab."""
import sys
from pathlib import Path

_EXTERNAL_ROOT = Path(__file__).resolve().parent.parent.parent / "external"
if str(_EXTERNAL_ROOT) not in sys.path:
    sys.path.insert(0, str(_EXTERNAL_ROOT))

from strategies._positions import PositionsAdapter  # noqa: E402
from gts_quant_lab.gts_quant_lab.quantlab.strategies.s03_latency_arb import LiquiditySweepStrategy  # noqa: E402


class LiquiditySweepAdapter(PositionsAdapter):
    strategy_id = "liquidity_sweep"
    required_data = ()

    def _make_inner(self):
        return LiquiditySweepStrategy()

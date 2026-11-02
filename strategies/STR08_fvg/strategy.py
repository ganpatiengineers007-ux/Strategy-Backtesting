"""STR08 fvg: quantlab S08 (Fair Value Gap) ka asli logic, candles (OHLC) par chalta hai."""
from strategies._positions import PositionsAdapter
from gts_quant_lab.gts_quant_lab.quantlab.strategies.s08_fvg import FVGStrategy


class FVGAdapter(PositionsAdapter):
    strategy_id = "fvg"

    def _make_inner(self):
        return FVGStrategy()

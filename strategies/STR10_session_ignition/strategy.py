"""STR10 session_ignition: quantlab S10 ka asli logic, NSE open (9:15 IST) ke opening range + volume surge breakout par."""
from strategies._positions import PositionsAdapter
from gts_quant_lab.gts_quant_lab.quantlab.strategies import s10_session_ignition as s10
from gts_quant_lab.gts_quant_lab.quantlab.strategies.s10_session_ignition import SessionConfig, SessionIgnitionStrategy

s10.SESSIONS.setdefault("nse", 9 * 60 + 15)  # ts wall-clock IST ko UTC jaisa maana gaya hai (to_quantlab_bars)


class SessionIgnitionAdapter(PositionsAdapter):
    strategy_id = "session_ignition"

    def _make_inner(self):
        return SessionIgnitionStrategy(SessionConfig(sessions=("nse",)))

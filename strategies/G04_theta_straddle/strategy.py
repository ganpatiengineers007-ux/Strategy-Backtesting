"""G04 Theta short-straddle (plug-in adapter, Greeks strategy G04).

This strategy sells an ATM call and put (short straddle). The registry Signal
contract is long-only (BUY/EXIT) and has no option legs / short side, so this
strategy cannot produce a faithful backtest here. It stays registered and
visible, but the engine blocks it with a clear reason instead of faking a
long-only proxy. The standalone version lives in
all_strategies/greeks/theta_straddle_strategy.py.
"""
from strategies.base import Strategy


class ThetaStraddleAdapter(Strategy):
    strategy_id = "theta_straddle"
    required_data = ()
    blocked_reason = ("requires short option legs (two-leg short straddle); "
                      "the current Signal v0 engine is long-only and cannot model short options")

    def on_bar(self, ctx):
        raise RuntimeError(f"{self.strategy_id}: {self.blocked_reason}")

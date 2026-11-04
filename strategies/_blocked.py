"""Shared guard for strategies that need data the bar engine does not have."""
from strategies.base import Strategy


class BookBackedStrategy(Strategy):
    """A book/tick strategy that is discoverable but cannot run on OHLCV candles.

    The engine blocks it from ``required_data`` before ``on_bar`` is called. If
    somebody bypasses the engine, ``on_bar`` fails loudly with the same reason
    instead of silently returning a fake signal.
    """

    blocked_reason = "requires level-2 order-book/tick data, not available in OHLCV candle datasets"

    def __init__(self, params=None, inner=None):
        super().__init__(params)
        self._inner = inner

    def on_bar(self, ctx):
        raise RuntimeError(f"{self.strategy_id}: {self.blocked_reason}")

import numpy as np
import pandas as pd
from quantstrat.config import StrategyConfig
from quantstrat.strategy import MeanReversionStrategy

def test_strategy_returns_valid_signal_objects():
    rng = np.random.default_rng(2)
    n = 500
    x = np.zeros(n)
    for i in range(1, n):
        x[i] = 0.8 * x[i-1] + rng.normal()
    close = 100 + x * 4
    idx = pd.date_range("2025-01-01", periods=n, freq="min")
    op = np.r_[close[0], close[:-1]]
    spread = np.full(n, 1.0)
    df = pd.DataFrame({"open": op, "high": np.maximum(op, close)+spread,
                       "low": np.minimum(op, close)-spread, "close": close,
                       "volume": np.full(n, 1000.0)}, index=idx)
    cfg = StrategyConfig(lookback=20, z_entry=1.0, volume_lookback=5,
                         atr_period=5, volume_multiplier=0.5)
    signals = MeanReversionStrategy(cfg).generate_signals(df)
    assert isinstance(signals, list)
    assert all(s.side.value in {"BUY", "SELL"} for s in signals)

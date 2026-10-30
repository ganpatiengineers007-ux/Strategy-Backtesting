import logging
import numpy as np
import pandas as pd
from quantstrat import StrategyConfig, RiskConfig, MeanReversionStrategy, RiskManager
from quantstrat.backtest import run_backtest

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

def synthetic_bars(n=1500, seed=7):
    rng = np.random.default_rng(seed)
    # Illustrative mean-reverting price process, not market data.
    x = np.zeros(n)
    for i in range(1, n):
        x[i] = 0.92 * x[i-1] + rng.normal(0, 1)
    close = 22000 + x * 18
    open_ = np.r_[close[0], close[:-1]]
    spread = rng.uniform(2, 12, n)
    high, low = np.maximum(open_, close) + spread, np.minimum(open_, close) - spread
    volume = rng.integers(1000, 5000, n).astype(float)
    return pd.DataFrame({"open": open_, "high": high, "low": low,
                         "close": close, "volume": volume},
                        index=pd.date_range("2025-01-01", periods=n, freq="min"))

if __name__ == "__main__":
    data = synthetic_bars()
    sc = StrategyConfig(lookback=40, z_entry=1.8, volume_lookback=20,
                        atr_period=14, entry_mode="cross_back")
    rc = RiskConfig(risk_fraction=0.005, max_notional_fraction=0.5)
    strategy = MeanReversionStrategy(sc)
    signals = strategy.generate_signals(data)
    result = run_backtest(data, signals, RiskManager(rc, sc))
    print(f"Signals: {len(signals)} | Trades: {len(result.trades)}")
    print(f"Final equity: {result.final_equity:,.2f}")
    if not result.trades.empty:
        print(result.trades.tail())

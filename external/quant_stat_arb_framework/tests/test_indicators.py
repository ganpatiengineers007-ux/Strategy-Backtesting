import numpy as np
import pandas as pd
import pytest
from quantstrat.indicators import rolling_zscore, atr, validate_ohlcv

def sample():
    idx = pd.date_range("2025-01-01", periods=40, freq="min")
    close = pd.Series(np.arange(40, dtype=float) + 100, index=idx)
    return pd.DataFrame({"open": close, "high": close + 1, "low": close - 1,
                         "close": close, "volume": 100.0}, index=idx)

def test_zscore_uses_full_window():
    z = rolling_zscore(sample()["close"], 10)
    assert z.iloc[:9].isna().all()
    assert np.isfinite(z.iloc[-1])

def test_atr_positive_after_warmup():
    a = atr(sample(), 14)
    assert a.iloc[:13].isna().all()
    assert (a.dropna() > 0).all()

def test_validate_rejects_missing_column():
    with pytest.raises(ValueError):
        validate_ohlcv(sample().drop(columns=["volume"]))

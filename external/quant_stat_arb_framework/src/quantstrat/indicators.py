import numpy as np
import pandas as pd

REQUIRED_OHLCV = {"open", "high", "low", "close", "volume"}

def validate_ohlcv(frame: pd.DataFrame) -> None:
    missing = REQUIRED_OHLCV.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if frame.empty:
        raise ValueError("Input data is empty")
    if not frame.index.is_monotonic_increasing:
        raise ValueError("DataFrame index must be sorted ascending")
    if frame.index.has_duplicates:
        raise ValueError("DataFrame index must not contain duplicates")
    if (frame["volume"] < 0).any():
        raise ValueError("Volume cannot be negative")

def rolling_zscore(close: pd.Series, window: int) -> pd.Series:
    # Mean and sample standard deviation are calculated from the trailing window.
    # min_periods=window prevents a signal before a full estimation sample exists.
    mean = close.rolling(window, min_periods=window).mean()
    std = close.rolling(window, min_periods=window).std(ddof=1)
    # A zero standard deviation makes the score undefined; return NaN, never infinity.
    std = std.replace(0.0, np.nan)
    return (close - mean) / std

def true_range(frame: pd.DataFrame) -> pd.Series:
    prev_close = frame["close"].shift(1)
    ranges = pd.concat([
        frame["high"] - frame["low"],
        (frame["high"] - prev_close).abs(),
        (frame["low"] - prev_close).abs(),
    ], axis=1)
    return ranges.max(axis=1)

def atr(frame: pd.DataFrame, period: int) -> pd.Series:
    # Wilder-style smoothing: EWM alpha=1/period, with a full initial period.
    tr = true_range(frame)
    return tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()

def book_imbalance(frame: pd.DataFrame) -> pd.Series:
    # (bid depth - ask depth) / (bid depth + ask depth), bounded to [-1, +1].
    if not {"bid_size", "ask_size"}.issubset(frame.columns):
        return pd.Series(np.nan, index=frame.index)
    denom = (frame["bid_size"] + frame["ask_size"]).replace(0, np.nan)
    return (frame["bid_size"] - frame["ask_size"]) / denom

def oi_change_pct(frame: pd.DataFrame) -> pd.Series:
    if "oi" not in frame.columns:
        return pd.Series(np.nan, index=frame.index)
    prior = frame["oi"].shift(1).replace(0, np.nan)
    return (frame["oi"] - prior) / prior * 100.0

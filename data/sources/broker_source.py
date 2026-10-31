"""Broker API source: Fyers implementation using fyers_hub."""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from typing import Optional

from fyers_hub.auth import flow
from fyers_hub.client.api import FyersApi
from fyers_hub.client.limiter import RateLimiter
from fyers_hub.settings import get_settings


@dataclass
class BrokerConfig:
    symbol: str
    resolution: str
    from_date: date
    to_date: date


def read_rows(config: BrokerConfig) -> list[dict]:
    """
    Read historical data from Fyers broker.
    
    Args:
        config: BrokerConfig with symbol, resolution, from_date, to_date
        
    Returns:
        List of dict rows with OHLCV data
    """
    settings = get_settings()
    settings.require_app()
    
    api = FyersApi(
        model=None,  # Will use real Fyers API
        limiter=RateLimiter(settings.max_per_sec, settings.max_per_min),
    )
    
    # Ensure we have a valid token
    flow.ensure_token(settings)
    
    raw = api.history(config.symbol, config.resolution, config.from_date, config.to_date)
    
    rows = []
    for c in raw:
        rows.append({
            "ts": c[0],
            "open": c[1],
            "high": c[2],
            "low": c[3],
            "close": c[4],
            "volume": c[5],
        })
    return rows


def read_rows_simple(symbol: str, resolution: str, from_date: date, to_date: date) -> list[dict]:
    """
    Simplified interface for reading rows from Fyers.
    
    Args:
        symbol: Trading symbol (e.g., "NSE:SBIN-EQ")
        resolution: Timeframe (e.g., "1", "5", "D")
        from_date: Start date
        to_date: End date
        
    Returns:
        List of dict rows with OHLCV data
    """
    config = BrokerConfig(symbol=symbol, resolution=resolution, from_date=from_date, to_date=to_date)
    return read_rows(config)

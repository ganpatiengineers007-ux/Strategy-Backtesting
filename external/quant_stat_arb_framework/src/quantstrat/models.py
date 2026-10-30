from dataclasses import dataclass
from enum import Enum
from typing import Optional

class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

@dataclass(frozen=True)
class Signal:
    timestamp: object
    side: Side
    z_score: float
    reference_price: float
    atr: float
    reason: str

@dataclass(frozen=True)
class OrderIntent:
    timestamp: object
    side: Side
    quantity: int
    reference_price: float
    stop_price: float
    target_price: float
    risk_amount: float
    reason: str

@dataclass
class Position:
    side: Side
    quantity: int
    entry_price: float
    stop_price: float
    target_price: float
    entry_timestamp: object
    risk_amount: float

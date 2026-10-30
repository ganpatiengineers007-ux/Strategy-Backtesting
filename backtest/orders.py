from dataclasses import dataclass


@dataclass
class Order:
    side: str
    qty: int
    stop_loss: float = None
    target: float = None
    reason: str = ""

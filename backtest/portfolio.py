"""Single-instrument long-only portfolio."""
from dataclasses import dataclass


@dataclass
class Position:
    qty: int
    entry_price: float
    entry_ts: str
    stop: float
    target: float
    entry_fee: float


class Portfolio:
    def __init__(self, cash):
        self.cash, self.position, self.trades = cash, None, []

    def open(self, qty, price, ts, stop, target, fee):
        self.cash -= qty * price + fee
        self.position = Position(qty, price, ts, stop, target, fee)

    def close(self, price, ts, fee, reason):
        p = self.position
        self.cash += p.qty * price - fee
        self.trades.append({"entry_ts": p.entry_ts, "exit_ts": ts, "entry_price": p.entry_price,
                            "exit_price": price, "qty": p.qty,
                            "pnl": (price - p.entry_price) * p.qty - p.entry_fee - fee,
                            "fees": p.entry_fee + fee, "reason": reason})
        self.position = None

    def equity(self, price):
        return self.cash + (self.position.qty * price if self.position else 0.0)

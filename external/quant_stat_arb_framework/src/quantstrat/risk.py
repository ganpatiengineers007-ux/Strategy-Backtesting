import math
from .config import RiskConfig, StrategyConfig
from .models import Signal, OrderIntent

class RiskManager:
    def __init__(self, risk_config: RiskConfig, strategy_config: StrategyConfig):
        self.risk = risk_config
        self.strategy = strategy_config

    def create_order_intent(self, signal: Signal, equity: float) -> OrderIntent | None:
        if equity <= 0 or signal.reference_price <= 0 or signal.atr <= 0:
            return None
        # Cash risk budget = current equity * configured risk fraction.
        risk_budget = equity * self.risk.risk_fraction
        stop_distance = signal.atr * self.strategy.stop_atr
        raw_qty = math.floor(risk_budget / stop_distance)
        # Apply quantity step and notional cap independently.
        qty = (raw_qty // self.risk.quantity_step) * self.risk.quantity_step
        notional_cap_qty = math.floor(
            equity * self.risk.max_notional_fraction / signal.reference_price
        )
        qty = min(qty, notional_cap_qty)
        if qty < self.risk.min_quantity:
            return None

        if signal.side.value == "BUY":
            stop = signal.reference_price - stop_distance
            target = signal.reference_price + signal.atr * self.strategy.target_atr
        else:
            stop = signal.reference_price + stop_distance
            target = signal.reference_price - signal.atr * self.strategy.target_atr

        return OrderIntent(signal.timestamp, signal.side, qty, signal.reference_price,
                           stop, target, qty * stop_distance, signal.reason)

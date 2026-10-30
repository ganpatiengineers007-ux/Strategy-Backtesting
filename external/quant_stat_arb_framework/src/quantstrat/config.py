from dataclasses import dataclass

@dataclass(frozen=True)
class StrategyConfig:
    lookback: int = 50
    z_entry: float = 2.0
    entry_mode: str = "cross_back"  # cross_back or touch
    volume_lookback: int = 20
    volume_multiplier: float = 1.0
    atr_period: int = 14
    stop_atr: float = 1.5
    target_atr: float = 2.0
    require_orderbook: bool = False
    min_book_imbalance: float = 0.05
    require_oi: bool = False
    min_oi_change_pct: float = 0.0
    allow_long: bool = True
    allow_short: bool = True

    def __post_init__(self):
        if self.lookback < 5 or self.volume_lookback < 2 or self.atr_period < 2:
            raise ValueError("lookback, volume_lookback and atr_period are too small")
        if self.z_entry <= 0 or self.stop_atr <= 0 or self.target_atr <= 0:
            raise ValueError("threshold and ATR multiples must be positive")
        if self.entry_mode not in {"cross_back", "touch"}:
            raise ValueError("entry_mode must be 'cross_back' or 'touch'")
        if self.volume_multiplier < 0:
            raise ValueError("volume_multiplier cannot be negative")

@dataclass(frozen=True)
class RiskConfig:
    risk_fraction: float = 0.005
    max_notional_fraction: float = 1.0
    min_quantity: int = 1
    quantity_step: int = 1

    def __post_init__(self):
        if not 0 < self.risk_fraction <= 0.05:
            raise ValueError("risk_fraction must be in (0, 0.05]")
        if not 0 < self.max_notional_fraction <= 1:
            raise ValueError("max_notional_fraction must be in (0, 1]")
        if self.min_quantity < 1 or self.quantity_step < 1:
            raise ValueError("quantity settings must be positive")

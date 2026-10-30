"""Risk limits (config/risk_policy.json se aate hain)."""
from dataclasses import dataclass


@dataclass
class RiskLimits:
    max_position_pct: float = 100.0
    max_drawdown_pct: float = 30.0
    on_violation: str = "halt"

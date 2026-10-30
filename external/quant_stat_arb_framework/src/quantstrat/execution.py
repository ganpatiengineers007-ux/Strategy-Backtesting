import logging
from dataclasses import dataclass
from .models import OrderIntent

log = logging.getLogger(__name__)

@dataclass
class ExecutionResult:
    accepted: bool
    dry_run: bool
    message: str
    order_id: str | None = None

class DryRunExecutor:
    """Safe default executor: validates and records intents; never contacts a broker."""
    def __init__(self, dry_run: bool = True):
        if not dry_run:
            raise ValueError("This package ships only a dry-run executor; live routing is intentionally disabled.")
        self.dry_run = True
        self.orders: list[OrderIntent] = []

    def submit(self, intent: OrderIntent) -> ExecutionResult:
        if intent.quantity <= 0 or intent.reference_price <= 0:
            log.error("Rejected invalid order intent: %s", intent)
            return ExecutionResult(False, True, "INVALID_ORDER_INTENT")
        self.orders.append(intent)
        log.info("DRY_RUN order recorded: %s", intent)
        return ExecutionResult(True, True, "DRY_RUN_RECORDED", f"DRY-{len(self.orders):06d}")
